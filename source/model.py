"""Single source of truth for fabrication profiles and assembled placements (mm)."""
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'source/config.json').read_text())
PARTS, INSTANCES, HARDWARE, FASTENERS, JOINTS = {}, [], [], [], []
WALLS=[]   # wall-facet instances in facet order (facet 1 first)
FIGURES=[]   # placements of the thermo-clay family figures (one per storey)

def rect(w,h): return [[0,0],[w,0],[w,h],[0,h]]
def poly(n,r,cx=0,cy=0,angle=0):
    return [[cx+r*math.cos(math.radians(angle+i*360/n)),cy+r*math.sin(math.radians(angle+i*360/n))] for i in range(n)]
def bounds(points):
    xs,ys=zip(*points); return min(xs),min(ys),max(xs),max(ys)
def inside_polygon(x,y,poly):
    inside=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside
def edge_distance(x,y,poly):
    distances=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
        distances.append(math.hypot(x-a[0]-t*dx,y-a[1]-t*dy))
    return min(distances)
def cutrect(x,y,w,h): return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def add(pid,name,t,outer,cuts=None,holes=None,color='wood',category='Structure',note=''):
    if outer[-1]==outer[0]:outer=outer[:-1]
    x0,y0,x1,y1=bounds(outer)
    outer=[[x-x0,y-y0] for x,y in outer]
    cuts=[[[x-x0,y-y0] for x,y in c] for c in (cuts or [])]
    holes=[dict(h,x=h['x']-x0,y=h['y']-y0) for h in (holes or [])]
    starters=[]
    for i,c in enumerate(cuts):
        a,b,d,e=bounds(c); diameter=min(CFG['starter_diameter'],d-a-4,e-b-4)
        if diameter>=6:
            sx,sy=a+diameter/2+2,b+diameter/2+2
            if not inside_polygon(sx,sy,c) or edge_distance(sx,sy,c)<diameter/2+1.99:
                cx=sum(v[0] for v in c)/len(c);cy=sum(v[1] for v in c)/len(c)
                vx,vy=min(c,key=lambda v:(v[1],v[0]))
                for step in range(1,101):
                    f=step/100;sx=vx+(cx-vx)*f;sy=vy+(cy-vy)*f
                    if inside_polygon(sx,sy,c) and edge_distance(sx,sy,c)>=diameter/2+2:break
                else:raise ValueError('No safe starter location: '+pid)
            starters.append({'id':f'S{i+1:02}','x':sx,'y':sy,'diameter':diameter,'cut':i+1})
    for i,hole in enumerate(holes):hole['id']=f'H{i+1:02}'
    PARTS[pid]={'id':pid,'name':name,'thickness':t,'outer':outer,'cuts':cuts,'holes':holes,'starters':starters,'width':x1-x0,'height':y1-y0,'color':CFG['colors'][color],'category':category,'note':note,'origin_shift':[x0,y0]}
    return pid
def hole(x,y,d,depth=None,purpose='Through hole'):
    return {'x':x,'y':y,'diameter':d,'depth':depth,'purpose':purpose}
def put(pid,origin=(0,0,0),u=(1,0,0),v=(0,1,0),group='Fixed',label=None):
    w=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    inst={'id':f'{pid}-{sum(i["part"]==pid for i in INSTANCES)+1:02}','part':pid,'design_part':pid,'label':label or PARTS[pid]['name'],'origin':list(origin),'u':list(u),'v':list(v),'w':list(w),'group':group}
    INSTANCES.append(inst);return inst
def facet_angle(pid):
    """Outer normal angle (degrees) of wall facet W01-W12."""
    return -75+30*(int(pid[1:])-1)
def upright(pid,x,y,z,group='Fixed',axis='xz',label=None):
    return put(pid,(x,y,z),(1,0,0),(0,0,1),group,label) if axis=='xz' else put(pid,(x,y,z),(0,1,0),(0,0,1),group,label)

def vertical_plate(pid,a,b,z,inside,group='Fixed'):
    """Vertical plate whose face runs a->b in plan (from height z), thickness toward the `inside` plan point."""
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);u=(dx/l,dy/l,0)
    if u[1]*(inside[0]-a[0])-u[0]*(inside[1]-a[1])<0:a,b=b,a;u=(-u[0],-u[1],0)
    return put(pid,(a[0],a[1],z),u,(0,0,1),group)

def build():
    PARTS.clear();INSTANCES.clear();HARDWARE.clear();FASTENERS.clear();JOINTS.clear();FIGURES.clear();WALLS.clear()
    T=CFG['thickness']; base=T['floor']; bt=T['base']; wall=T['wall']; pitch=CFG['floor_pitch']; H=CFG['wall_height']
    scale=H/450; q=lambda value:value*scale
    WH=CFG['wall_hinge'];doors=CFG['doors'];door_ids=[doors['main'],doors['veranda']]
    door_w,door_h,sill=q(50),q(96),wall
    a=CFG['tower_diameter']/2*math.cos(math.pi/12)
    width=2*(a-wall)*math.tan(math.pi/12)-1
    floor_r=(a-wall-CFG['moving_clearance'])/math.cos(math.pi/12)
    floor_points=poly(12,floor_r,floor_r,floor_r)
    hinge_x=CFG['tower_diameter']/2+WH['axis_offset']
    half=CFG['base_diameter']/2
    # The stone plinth lifts the house: G is the ground-floor top, every storey is measured from it.
    # The round base B01 is bt thick; the plinth height runs from its top to the ground-floor top.
    PL=CFG['plinth'];G=bt+PL['height'];tops=[G+k*pitch for k in range(4)]
    # Corner gussets: low ones 26 above each floor, high ones 20 below the ceiling (clear of the floor ledges).
    gusset_dz=(q(26),pitch-base-q(20))
    door_corners={round((facet_angle(p)+side)/30)%12 for p in door_ids for side in (-15,15)}
    def gusset_height(corner,level,dz):
        return door_h if corner in door_corners and level==0 and dz==gusset_dz[0] else dz
    # Gusset plan shape: blunt inner edge at radius GI (half-width GW), reaching GR along each wall face from the corner.
    GI,GW,GR=q(150),q(10),q(22)
    post_width=q(18);post_t=T['structure']
    posts=[(q(x),q(y)) for x,y in [(-145,10),(127,10),(-68,128),(50,128)]]
    feet=[(x,y-24) for x,y in posts]
    # Veranda frame: pu runs along its wall facet, pv points from the outer deck edge toward the wall.
    ver=CFG['veranda'];vth=math.radians(facet_angle(ver['facet']))
    pn=(math.cos(vth),math.sin(vth),0);pu=(-pn[1],pn[0],0);pv=(-pn[0],-pn[1],0)
    reach=a+ver['wall_gap']+ver['depth']
    po=(pn[0]*reach-pu[0]*ver['width']/2,pn[1]*reach-pu[1]*ver['width']/2,G)
    # Round foundation: a fine polygon for nesting/templates, a true circle for CAD and DXF.
    add('B01','Round grey base',bt,poly(180,half,half,half),color='gray',note=f'Circle D{2*half:g}, centered on the tower; paint plain grey. The stone plinth, the veranda skirt and both entrance stairs are glued on top, and the hidden drawer slides on it. Cut with a jigsaw or router trammel, then sand the edge fair.')
    PARTS['B01']['outercircle']=[half,half,half]
    put('B01',(-half,-half,0))
    # Stone plinth: 12 facet panels between B01 and a 12-sided ground-floor plate, with a hidden drawer bay.
    Ap,tp=PL['apothem'],PL['panel'];ph=G-base-bt;r0=Ap/math.cos(math.pi/12)
    fholes=[dict(hole(r0+x+12,r0+y+12,3.2,None,'SC3 foot-block screw clearance; countersink underside D6 x 1.5'),entry='bottom',countersink=6,countersink_depth=1.5) for x,y in feet]
    add('F00','Ground floor plate / plinth top',base,poly(12,r0,r0,r0),holes=fholes,color='stone',note=f'Twelve-sided plate, {2*Ap:g} across flats: the ground floor and the top of the stone plinth, its rim showing 8 mm outside the walls. Screw the four A04 feet on from below (SC3) before gluing it onto the plinth.')
    put('F00',(-r0,-r0,G-base))
    add('A04','Rear frame foot block (solid wood)',12,rect(24,24),holes=[dict(hole(12,12,2.0,10,'SC3 blind pilot from bottom'),entry='bottom')],category='Purchased wood',note='Four 24 x 24 x 12 blocks. Glue to F00 and the frame post; SC3 enters through the F00 underside.')
    for x,y in feet:
        block=put('A04',(x,y,G))
        FASTENERS.append({'id':f'FS-Base-{len(FASTENERS)+1}','type':'SC3','diameter':3,'length':16,'head_diameter':6,'head_height':1.5,'origin':[x+12,y+12,G-base],'axis':[0,0,1],'parts':['F00-01',block['id']],'pilot':2.0,'pilot_depth':10,'note':'3 x 16 mm countersunk wood screw from the F00 underside into the 12 mm solid wood foot block. D3.2 clearance through F00; D2 pilot 10 mm into block. Fit before F00 goes onto the plinth.'})
    DR=PL['drawer'];dang=math.radians(DR['direction']);e_out=(math.cos(dang),math.sin(dang));e_side=(-e_out[1],e_out[0])
    def dpt(rho,w):return (rho*e_out[0]+w*e_side[0],rho*e_out[1]+w*e_side[1])
    def rho_face(w):return (Ap-tp-abs(w)*math.sin(math.pi/12))/math.cos(math.pi/12)
    pw=2*(Ap-tp)*math.tan(math.pi/12)-1
    add('PL1','Stone plinth panel',tp,rect(pw,ph),color='stone',note=f'Ten panels, {ph:g} tall, standing on B01 under F00; glue both long edges. The two facets on the drawer side are the drawer front instead.')
    add('DR4','Hidden drawer front panel',tp,[[0,0],[pw-14,0],[pw-14,5],[pw,5],[pw,ph-1],[0,ph-1]],color='stone',category='Structure',note='Two panels meeting at the corner like the plinth; the 14 x5 notches form a finger pull under the corner. Paint stone so the drawer stays hidden.')
    for i in range(12):
        angle=-75+i*30;th=math.radians(angle);n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0)
        offset=(angle-DR['direction']+180)%360-180
        if abs(abs(offset)-15)<1e-6:
            # Drawer front: the notched end of each panel sits at the corner the drawer slides along.
            if offset<0:put('DR4',(n[0]*(Ap-tp)-u[0]*pw/2,n[1]*(Ap-tp)-u[1]*pw/2,bt),u,(0,0,1),'Drawer')
            else:put('DR4',(n[0]*Ap+u[0]*pw/2,n[1]*Ap+u[1]*pw/2,bt),(-u[0],-u[1],0),(0,0,1),'Drawer')
        else:put('PL1',(n[0]*(Ap-tp)-u[0]*pw/2,n[1]*(Ap-tp)-u[1]*pw/2,bt),u,(0,0,1))
    hw,back,dh_=DR['half_width'],DR['back'],DR['height'];front=rho_face(hw)-.5;gfront=rho_face(hw+7)-.5
    add('DR2','Drawer side',tp,rect(front-back,dh_),category='Structure',note='Two sides; glue to the back and bottom, then to the front panels with small corner blocks.')
    add('DR3','Drawer back',tp,rect(2*hw-12,dh_),category='Structure')
    add('DR1','Drawer bottom',T['furniture'],rect(front-back-tp,2*hw-12),category='Structure',note='Slides directly on B01: wax the underside.')
    for w in (hw,-hw):vertical_plate('DR2',dpt(back,w),dpt(front,w),bt,dpt(0,0),'Drawer')
    vertical_plate('DR3',dpt(back,-hw+tp),dpt(back,hw-tp),bt,dpt(0,0),'Drawer')
    bo=dpt(back+tp,-hw+tp);put('DR1',(bo[0],bo[1],bt),(e_out[0],e_out[1],0),(e_side[0],e_side[1],0),'Drawer')
    add('DG1','Drawer guide wall',tp,rect(gfront-(back-6.5),ph),note='Two guide walls glued between B01 and F00; they also carry F00 over the drawer bay.')
    add('DB1','Drawer back stop',tp,rect(2*hw+2,ph),note='Glued between the guide walls; the closed drawer rests against it.')
    for w in (hw+1,-hw-1):vertical_plate('DG1',dpt(back-6.5,w),dpt(gfront,w),bt,dpt(0,w*2))
    vertical_plate('DB1',dpt(back-.5,-hw-1),dpt(back-.5,hw+1),bt,dpt(back-10,0))
    allowance=CFG['fabrication']['pillar_clearance']
    post_slots=[cutrect(floor_r+x-allowance/2,floor_r+y-post_t-allowance/2,post_width+allowance,post_t+allowance) for x,y in posts]
    add('F01','First / second floor',base,floor_points,cuts=post_slots,color='wood',note='Slide both levels over the four continuous P01 pillars. Glue divided panels over 4 x4 mm supports; dry-fit the pillar openings with measured plywood.')
    attic_holes=[]
    for angle in (60,120):
        th=math.radians(angle);attic_holes.append(hole(floor_r+q(145)*math.cos(th),floor_r+q(145)*math.sin(th),3.2,None,'BL1 roof turn-button pivot clearance'))
    add('F02','Attic floor with roof-lock pivot holes',base,floor_points,holes=attic_holes,color='wood',note='Two D3.2 vertical pivot holes for the roof retaining turn-buttons. Do not use F01 as the attic floor.')
    for k in range(1,4):put('F02' if k==3 else 'F01',(-floor_r,-floor_r,tops[k]-base),group='Fixed',label='Attic floor' if k==3 else f'Floor {k+1}')
    # Wall facets: six fixed at the back; three facets in each moving half.
    for i in range(12):
        angle=-75+i*30;th=math.radians(angle); n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0)
        group='WallRight' if i<3 else 'WallLeft' if i>8 else 'Fixed'
        pid=f'W{i+1:02}';cuts=[]
        for level in range(3):
            if pid in door_ids and level==0:cuts.append(cutrect((width-door_w)/2,0,door_w,door_h))
            elif i%2==1:cuts.append(cutrect((width-q(40))/2,level*pitch+q(54),q(40),q(60)))
        holes=[]
        # Facets beside a hinge axis (0 or 180 degrees) carry the wall hinge leaves.
        hinge_end='start' if round(angle-15)%180==0 else 'end' if round(angle+15)%180==0 else None
        # All mounting pilots are in solid edge strips, away from window cutouts.
        if hinge_end:
            hx=WH['hole_x']-(hinge_x*math.sin(math.pi/12)-width/2)
            if hinge_end=='end':hx=width-hx
            for cy in WH['centers']:
                for dy in WH['hole_y']:
                    holes.append(hole(hx,cy-WH['height']/2+dy,WH['pilot_diameter'],wall,'Hinge pilot; confirm actual leaf template'))
        # Walls are named by what they carry, so identical facets get the same name (and later the same ID).
        feats=([('main' if pid==doors['main'] else 'veranda')+' door'] if pid in door_ids else [])+(['windows'] if i%2==1 else [])+(['hinge pilots'] if hinge_end else [])
        kind='Opening wall' if group!='Fixed' else 'Fixed wall'
        name=kind+(' with '+' and '.join(feats) if feats else ', plain')
        note=('Opening walls are 2 mm lower for roof clearance; keep their seams clear. ' if group!='Fixed' else 'Fill the exterior seams of the fixed shell. ')+'Glue J01 corner gussets inside. The wall map shows which facets it fills.'
        add(pid,name,wall,rect(width,H-(2 if group!='Fixed' else 0)),cuts,holes,'blue','Walls',note=note)
        origin=(n[0]*(a-wall)-u[0]*width/2,n[1]*(a-wall)-u[1]*width/2,G)
        wallinst=put(pid,origin,u,(0,0,1),group,label=f'Wall facet {i+1:02}');WALLS.append(wallinst)
        if hinge_end:
            if 'A02' not in PARTS:add('A02','Hinge backing block (solid wood)',8,rect(18,28),holes=[hole(9,14-WH['height']/2+dy,WH['pilot_diameter'],WH['pilot_depth']-wall,'Hinge backing pilot') for dy in WH['hole_y']],category='Purchased wood',note='Buy 8 x 18 mm solid wood strip; cut twelve 28 mm blocks. Glue to wall inside before drilling from actual hinge leaf.')
            hx=holes[0]['x']
            for cy in WH['centers']:
                bo=(origin[0]+u[0]*(hx-9)-n[0]*8,origin[1]+u[1]*(hx-9)-n[1]*8,G+cy-14)
                block=put('A02',bo,u,(0,0,1),group)
                if 'A06' not in PARTS:add('A06','Hinge packing shim',WH['packing_thickness'],rect(10,WH['height']),holes=[hole(5,dy,2.2) for dy in WH['hole_y']],category='Purchased packing',note='Twelve rigid 0.9 mm shims (card, veneer or plastic), one beneath each wall hinge leaf. Confirm thickness and barrel axis with actual hardware; cut with knife or scissors, not jigsaw.')
                put('A06',(origin[0]+u[0]*(hx-5)+n[0]*wall,origin[1]+u[1]*(hx-5)+n[1]*wall,G+cy-WH['height']/2),u,(0,0,1),group)
                outline=[[bo[0]+n[0]*8+u[0]*xx,bo[1]+n[1]*8+u[1]*xx,bo[2]+zz] for xx,zz in [(0,0),(18,0),(18,28),(0,28)]]
                JOINTS.append({'id':f'J-Hinge-{i}-{int(cy)}','type':'J3 reinforced screwed butt joint','parts':[wallinst['id'],block['id']],'position':[bo[0]+n[0]*8+u[0]*9,bo[1]+n[1]*8+u[1]*9,G+cy],'axis':[-n[0],-n[1],0],'outline':outline,'glue':'PVA on 18 x 28 backing face; clamp before pilot drilling'})
            stand=wall+WH['leaf_thickness']+WH['packing_thickness']
            for h in PARTS[pid]['holes']:
                head=[origin[0]+u[0]*h['x']+n[0]*stand,origin[1]+u[1]*h['x']+n[1]*stand,G+h['y']]
                FASTENERS.append({'id':f'FS-{pid}-{h["id"]}','type':'SC1','diameter':2.0,'length':12.0,'head_diameter':4.0,'head_height':1.0,'origin':head,'axis':[-n[0],-n[1],0],'parts':[wallinst['id']],'pilot':WH['pilot_diameter'],'pilot_depth':WH['pilot_depth'],'note':'2 x 12 mm countersunk wood screw; nominal length includes head. Passes hinge, packing, 6 mm wall, into 8 mm backing.'})
        # Window: horizontal bars at the bottom and top, vertical bars at the sides and one in the middle (inside the
        # frame, touching both horizontal bars), and a horizontal bar glued across the outside at mid-height.
        for j,c in enumerate(cuts):
            x,y,x2,y2=bounds(c)
            if pid in door_ids and j==0:continue
            if 'D01' not in PARTS:
                add('D01','Window horizontal bar',3,rect(q(40)+7.2,3.6),color='cream',category='Exterior',note='Three per window: the bottom and top frame bars, and the crossbar glued across the outside of the frame at mid-height.')
                add('D02','Window vertical bar',3,rect(3.6,q(60)),color='cream',category='Exterior',note='Three per window: the two side frame bars, and the middle bar set inside the frame between the bottom and top bars.')
            for fid,dx,dz,r in [('D01',-3.6,-3.6,wall),('D01',-3.6,q(60),wall),('D02',-3.6,0,wall),('D02',q(40),0,wall),('D02',(q(40)-3.6)/2,0,wall),('D01',-3.6,(q(60)-3.6)/2,wall+3)]:
                put(fid,(origin[0]+u[0]*(x+dx)+n[0]*r,origin[1]+u[1]*(x+dx)+n[1]*r,G+y+dz),u,(0,0,1),group)
        if 'D03' not in PARTS:add('D03','White eave fascia',3,rect(width,8),color='cream',category='Exterior',note='One fascia per wall facet at eave. Never glue across hinge seams or the front closing edges.')
        yy=PARTS[pid]['height']-8;put('D03',(origin[0]+n[0]*wall,origin[1]+n[1]*wall,G+yy),u,(0,0,1),group)
    # Hinge axes outside the two side corners. Copper/brass hardware is reference geometry.
    for group,sign in [('WallRight',1),('WallLeft',-1)]:
        for z in (G+c for c in WH['centers']):
            HARDWARE.append({'id':f'HG-{group}-{int(z)}','kind':'Wall butt hinge','group':group,'position':[sign*hinge_x,0,z],'height':CFG['wall_hinge']['height'],'width':CFG['wall_hinge']['open_width'],'note':'Use A06 packing to align the barrel outside the corner; confirm leaf holes on the hardware checking template.'})
    # Magnetic catches and stops, four neodymium magnets in all. Each opening shell carries a solid-wood MC1 block just
    # under the attic floor (a magnet in F02 holds the shell shut) and a steel disc low on its hinge facet (a magnet in
    # a GP1 garden post on B01 stops the shell at the open angle and holds it there). The plain steel discs ride on the
    # walls, so no magnet pair can be fitted the wrong way round.
    MG,WC,WS=CFG['magnets'],CFG['wall_catch'],CFG['wall_stop'];CL,CD,CT=WC['block'];cd=CD-MG['disc_pocket'][0]/2-4;mg=f'D{MG["magnet"][0]:g} x {MG["magnet"][1]:g} mm'
    bed=f'Bed it in slow 2-part epoxy {MG["pocket"][1]-MG["magnet"][1]:g} mm below the surface and fill the recess with epoxy, so the magnet can never come loose.'
    add('MC1','Magnetic wall catch block (solid wood)',CT,rect(CL,CD),holes=[hole(CL/2,cd,MG['disc_pocket'][0],MG['disc_pocket'][1],'Steel disc recess, top face')],category='Purchased wood',note=f'Two {CL:g} x {CD:g} x {CT:g} mm blocks from 12 mm board, one glued inside each opening shell {WC["x"]:g} mm from the front seam, top {WC["gap"]:g} mm under the attic floor. Epoxy a D{MG["disc"][0]:g} x {MG["disc"][1]:g} steel disc flush into the top recess.')
    z_catch=tops[3]-base-WC['gap']-CT
    PARTS['F02']['note']+=f' Two blind D{MG["pocket"][0]:g} pockets in the underside, near the front seam, hold the wall-catch magnets.'
    for group,k,x0 in (('WallRight',0,WC['x']),('WallLeft',11,width-WC['x']-CL)):
        wi=WALLS[k];o,u,n=wi['origin'],wi['u'],wi['w']
        put('MC1',(o[0]+u[0]*x0,o[1]+u[1]*x0,z_catch),u,(-n[0],-n[1],0),group)
        cx,cy=o[0]+u[0]*(x0+CL/2)-n[0]*cd,o[1]+u[1]*(x0+CL/2)-n[1]*cd   # disc 4 mm from the block's inner edge, clear of the floor edge
        PARTS['F02']['holes'].append(dict(hole(cx+floor_r,cy+floor_r,MG['pocket'][0],MG['pocket'][1],'Wall-catch magnet pocket'),entry='bottom',id=f'H{len(PARTS["F02"]["holes"])+1:02}'))
        HARDWARE.append({'id':f'MG-Catch-{group}','kind':'Catch magnet','group':'Fixed','position':[cx,cy,tops[3]-base],'height':MG['magnet'][1],'width':MG['magnet'][0],'note':f'{mg} magnet in the F02 underside over the {group} catch block. '+bed})
        HARDWARE.append({'id':f'SD-Catch-{group}','kind':'Steel disc','group':group,'position':[cx,cy,z_catch+CT],'height':MG['disc'][1],'width':MG['disc'][0],'note':'Epoxied flush into the MC1 top recess.'})
    s,zc=WS['post'],WS['top']/2
    def spin(p,c,deg):
        t=math.radians(deg);x,y=p[0]-c[0],p[1]-c[1];return (c[0]+x*math.cos(t)-y*math.sin(t),c[1]+x*math.sin(t)+y*math.cos(t))
    add('GP1','Garden stop post (solid wood)',s,rect(s,G+WS['top']-bt),holes=[dict(hole(s/2,G+zc-bt,MG['pocket'][0],MG['pocket'][1],'Stop magnet pocket, wall-side face'),entry='bottom')],category='Purchased wood',note=f'Two posts from {s:g} x {s:g} mm square strip, standing on B01 where the opened shells meet them at {WS["angle"]:g} degrees. Glue the foot and screw it from below (SC3); the {mg} magnet faces the wall. '+bed+' Round the top and paint it like a garden lamp post.')
    for group,sign,k,xc in (('WallRight',1,2,WS['contact_x']),('WallLeft',-1,9,width-WS['contact_x'])):
        wi=WALLS[k];o,u,n=wi['origin'],wi['u'],wi['w'];deg=sign*WS['angle']
        face=(o[0]+u[0]*xc+n[0]*wall,o[1]+u[1]*xc+n[1]*wall)   # steel disc centre on the outer face, walls closed
        pc=spin(face,(sign*hinge_x,0),deg);nn=spin(n,(0,0),deg);tt=spin(u,(0,0),deg)
        # The post's wall-side face lies parallel to the opened facet, WS gap in front of it, centred on the disc.
        corner=(pc[0]+nn[0]*WS['gap']-tt[0]*s/2,pc[1]+nn[1]*WS['gap']-tt[1]*s/2)
        post=put('GP1',(corner[0],corner[1],bt),(tt[0],tt[1],0),(0,0,1))
        PARTS[wi['part']]['holes'].append(dict(hole(xc,zc,MG['disc_pocket'][0],MG['disc_pocket'][1],'Steel disc recess for the garden stop, outer face'),id=f'H{len(PARTS[wi["part"]]["holes"])+1:02}'))
        foot=(corner[0]+(tt[0]+nn[0])*s/2,corner[1]+(tt[1]+nn[1])*s/2)
        PARTS['B01']['holes'].append(dict(hole(foot[0]+half,foot[1]+half,3.2,None,'SC3 stop-post screw clearance; countersink underside D6 x 1.5'),entry='bottom',countersink=6,countersink_depth=1.5,id=f'H{len(PARTS["B01"]["holes"])+1:02}'))
        FASTENERS.append({'id':f'FS-Stop-{group}','type':'SC3','diameter':3,'length':16,'head_diameter':6,'head_height':1.5,'origin':[foot[0],foot[1],0],'axis':[0,0,1],'parts':['B01-01',post['id']],'pilot':2.0,'pilot_depth':12,'note':'3 x 16 mm countersunk wood screw up through B01 into the end grain of the stop post; glue the foot as well.'})
        HARDWARE.append({'id':f'MG-Stop-{group}','kind':'Stop magnet','group':'Fixed','position':[pc[0]+nn[0]*WS['gap'],pc[1]+nn[1]*WS['gap'],G+zc],'height':MG['magnet'][1],'width':MG['magnet'][0],'note':f'{mg} magnet in the GP1 face toward the {group} shell. '+bed})
        HARDWARE.append({'id':f'SD-Stop-{group}','kind':'Steel disc','group':group,'position':[face[0],face[1],G+zc],'height':MG['disc'][1],'width':MG['disc'][0],'note':f'Epoxied flush into the {wi["part"]} outer-face recess.'})
    # Structural posts and ledges entirely in the fixed rear half.
    add('P01','Continuous rear frame pillar',post_t,rect(post_width,3*pitch-base-12),color='wood',note='Four one-piece pillars on 12 mm foot blocks. Slide the two F01 levels over their rectangular openings, then seat F02 on the pillar tops. Keep the supplied 8 mm plywood thickness.')
    for x,y in posts:upright('P01',x,y,G+12,axis='xz')
    add('L01','Rear floor support ledge',6,rect(width-16,12),note=f'Twelve ledges: four per elevated floor, directly under it. Top faces at Z{tops[1]-base:g}, Z{tops[2]-base:g} and Z{tops[3]-base:g}.')
    for idx in (3,4,7,8):
        th=math.radians(-75+idx*30);n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0);v=(-n[0],-n[1],0)
        for k in range(1,4):
            put('L01',(n[0]*(a-wall)-u[0]*(width-16)/2,n[1]*(a-wall)-u[1]*(width-16)/2,tops[k]-base-6),u,v)
    # One room divider per storey: front-to-back wall on the house axis with a cloth-tape hinged door.
    PT=CFG['partition'];xp=PT['x']
    yb=(a-wall-wall/2*math.cos(math.radians(75)))/math.sin(math.radians(75))-.5;yf=-yb+PT['front_gap']
    Lp=yb-yf;clear=pitch-base;d0=PT['door_y']-yf;d1=d0+PT['door_width'];dh=PT['door_height'];notch=yb-(GI-.5)
    outline=[[0,0],[d0,0],[d0,dh],[d1,dh],[d1,0],[Lp,0]]
    for gz in gusset_dz:outline+=[[Lp,gz-.5],[Lp-notch,gz-.5],[Lp-notch,gz+6.5],[Lp,gz+6.5]]
    outline+=[[Lp,clear],[0,clear]]
    add('PT1','Room divider wall',wall,outline,color='cream',category='Walls',note=f'Three dividers, one per storey, {Lp:.1f} long and {clear:g} tall between floor and ceiling. The rear notches slip over the corner gussets; the front edge stays {PT["front_gap"]:g} mm clear of the closing walls. The {PT["door_width"]:g} x {dh:g} doorway sits {d0:g} mm from the front end, next to the opening walls; door leaves are not part of this plan.')
    raised_rear=gusset_height(3,0,gusset_dz[0])!=gusset_dz[0]
    if raised_rear:
        ground_outline=[[0,0],[d0,0],[d0,dh],[d1,dh],[d1,0],[Lp,0]]
        for dz in gusset_dz:
            gz=gusset_height(3,0,dz)
            ground_outline+=[[Lp,gz-.5],[Lp-notch,gz-.5],[Lp-notch,gz+6.5],[Lp,gz+6.5]]
        ground_outline+=[[Lp,clear],[0,clear]]
        PARTS['PT1']['note']=PARTS['PT1']['note'].replace('Three dividers, one per storey,','Two upper-storey dividers,')
        add('PT2','Room divider wall with raised gusset clearance',wall,ground_outline,color='cream',category='Walls',note=PARTS['PT1']['note'].replace('Two upper-storey dividers,','One ground-floor divider,')+' The lower rear notch clears the gusset raised above the veranda door.')
    for k in range(3):put('PT2' if raised_rear and k==0 else 'PT1',(xp-wall/2,yf,tops[k]),(0,1,0),(0,0,1))
    from architecture import entrances_and_veranda, dormer
    entrances_and_veranda(globals(),width,a,bt,pu,pv,pn,po,G)
    # Roof panels are planar triangles, not fake mesh sheets.
    finial_height=3+q(30)
    roof_z=G+H;roof_peak=CFG['height']-CFG['fabrication']['base_lift']-finial_height;roof_h=roof_peak-roof_z
    roof_a=CFG['roof_diameter']/2*math.cos(math.pi/12)-3*roof_h/math.hypot(CFG['roof_diameter']/2*math.cos(math.pi/12),roof_h)
    slant=math.hypot(roof_a,roof_h);rw=2*roof_a*math.tan(math.pi/12)-2
    topcut=3*roof_a/roof_h;topwidth=rw*topcut/slant
    add('R01','Roof triangular panel',3,[[0,0],[rw,0],[rw/2+topwidth/2,slant-topcut],[rw/2-topwidth/2,slant-topcut]],color='red',category='Roof',note='Eleven standard panels plus special R06. Assemble over the roof-angle jig; glue interior cloth seam tapes, then fill and paint exterior seams.')
    from architecture import dormer_layout
    roof={'z':roof_z,'h':roof_h,'a':roof_a,'slant':slant,'rw':rw,'scale':scale}
    dormer_cut=dormer_layout(roof)['cut'];dcw=dormer_cut[1][0]-dormer_cut[0][0];dch=dormer_cut[2][1]-dormer_cut[0][1]
    add('R06','Roof panel with attic dormer opening',3,PARTS['R01']['outer'],[dormer_cut],color='red',category='Roof',note=f'One special front-right panel with the dormer opening, {dcw:g} x {dch:.1f}. Cut while supported; the dormer sides stand on the skin beside it.')
    for j in range(12):
        th=math.radians(-75+j*30);n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0);v=(-n[0]*roof_a/slant,-n[1]*roof_a/slant,roof_h/slant)
        put('R06' if j==1 else 'R01',(n[0]*roof_a-u[0]*rw/2,n[1]*roof_a-u[1]*rw/2,roof_z),u,v,'Roof')
    dormer(globals(),roof)
    # Eave backing ring kept below the sloping skins, seated on short roof support blocks.
    ringr=q(182)
    add('R02','Roof eave reinforcement ring',6,poly(12,ringr,ringr,ringr),[poly(12,ringr-16,ringr,ringr)],color='red',category='Roof',note='Glue to 12 padded internal cleats at the eave. Ring lifts off with roof; do not glue to fixed walls.')
    put('R02',(-ringr,-ringr,roof_z),group='Roof')
    add('R03','Roof top cap',3,poly(12,7,7,7),color='red',category='Roof');put('R03',(-7,-7,roof_peak),group='Roof')
    add('FN01','White roof finial',4,[[q(x),q(y)] for x,y in [[0,0],[16,0],[14,5],[11,7],[13,10],[14,14],[12,18],[10,21],[10,25],[8,30],[6,25],[6,21],[4,18],[2,14],[3,10],[5,7],[2,5]]],color='cream',category='Roof',note='File and round the tip. Never lift the roof by this ornament.')
    upright('FN01',-q(8),2,roof_peak+3,group='Roof')
    cleat_r=q(170);cleat_z=roof_z+6;cleat_run=roof_a*(1-6/roof_h)-cleat_r;cleat_rise=roof_h*(1-cleat_r/roof_a)-6
    add('R04','Roof sloping support cleat',12,[[0,0],[cleat_run,0],[0,cleat_rise]],color='red',category='Purchased wood',note='Twelve triangular cleats cut from 12 mm solid wood. Glue bottom to roof ring and slope to roof skin. Wood grain along the sloping edge.')
    for j in range(12):
        th=math.radians(-75+j*30);n=(math.cos(th),math.sin(th));u=(n[0],n[1],0);v=(0,0,1);t=(n[1],-n[0],0)
        put('R04',(n[0]*cleat_r-t[0]*6,n[1]*cleat_r-t[1]*6,cleat_z),u,v,'Roof')
    add('E08','Roof retaining turn-button',3,rect(38,16),holes=[hole(8,8,3.2)],color='cream',category='Roof',note='Two horizontal captive turn-buttons, 3 mm above roof ring. Rotate 90 degrees toward center to unlock. Set pivot friction; use threadlocker on cap nuts.')
    for idx,angle in enumerate((60,120)):
        th=math.radians(angle);n=(math.cos(th),math.sin(th),0);u=(-n[1],n[0],0);r=q(145);z=roof_z+9
        tab=put('E08',(n[0]*(r-8)-u[0]*8,n[1]*(r-8)-u[1]*8,z),(n[0],n[1],0),u,'RoofLocks')
        head=[n[0]*r,n[1]*r,tops[3]-base-.5]
        FASTENERS.append({'id':f'FS-RoofPivot-{idx}','type':'BL1','diameter':3,'length':25,'head_diameter':6,'head_height':2,'origin':head,'axis':[0,0,1],'parts':['F02-01',tab['id']],'pilot':3.2,'pilot_depth':None,'stack_mm':[.5,base,8,.5,.5,3,.5,.5,.5,.5,.5,.5],'note':'M3 x 25 pan-head machine screw; eight steel washers (0.5 mm each, five above the button), one nylon washer (0.5 mm), 8 mm spacer, M3 domed cap nut. Stack 21.5 mm; 3.5 mm thread engagement; verify nut cavity >=3.8 mm.'})
        HARDWARE.append({'id':f'RP-{idx}','kind':'Captive roof pivot','group':'RoofLocks','position':head,'height':25,'width':16})
    add('R05','Roof assembly angle jig',wall,[[0,0],[roof_a,0],[0,roof_h]],color='wood',category='Tools',note='Two temporary jigs. Do not install in finished attic; use them to check roof slope before gluing.')
    # Chimney is attached to a roof panel above rear side (small, lightweight hollow box).
    def roofoutside(x,y):return roof_peak-(roof_h/roof_a)*(x+y)/math.sqrt(2)+3*slant/roof_a
    chimney_x,chimney_y,chimney_width=q(64),q(66),q(21)
    ctop=roofoutside(chimney_x,chimney_y)+q(53)
    for pid,x,y,length,axis,ref in [('CH01',chimney_x,chimney_y+3,chimney_width,'xz',chimney_y),('CH02',chimney_x,chimney_y+chimney_width,chimney_width,'xz',chimney_y+chimney_width-3),('CH03',chimney_x,chimney_y+3,chimney_width-6,'yz',chimney_x),('CH04',chimney_x+chimney_width-3,chimney_y+3,chimney_width-6,'yz',chimney_x+chimney_width-3)]:
        z0=roofoutside(x,ref) if axis=='xz' else roofoutside(ref,y)
        z1=roofoutside(x+length,ref) if axis=='xz' else roofoutside(ref,y+length)
        add(pid,'Chimney '+pid[-2:]+' sloped side',3,[[0,z0],[length,z1],[length,ctop],[0,ctop]],color='cream',category='Exterior',note='Short lower edge seats on roof. Sand across 3 mm thickness to match roof slope.')
        upright(pid,x,y,min(z0,z1),group='Roof',axis=axis)
    add('E07','Chimney cap',3,rect(q(21)+8,q(21)+8),color='red',category='Exterior')
    put('E07',(q(64)-4,q(66)-4,ctop),group='Roof')
    # Interior furniture. All parts are plywood, with broad glued joints.
    furniture_start=len(INSTANCES)
    furnish(tops)
    # Preview furniture scales as an assembly; it has no fabrication stock.
    furniture_ids={i['part'] for i in INSTANCES[furniture_start:]}
    for pid in furniture_ids:
        p=PARTS[pid]
        for key in ('outer','cuts'):
            if key=='outer':p[key]=[[q(x),q(y)] for x,y in p[key]]
            else:p[key]=[[[q(x),q(y)] for x,y in loop] for loop in p[key]]
        for key in ('width','height','thickness'):p[key]=q(p[key])
        for h in p['holes']+p['starters']:
            for key in ('x','y','diameter'):h[key]=q(h[key])
    for pid in furniture_ids:PARTS[pid]['starters']=[]
    for inst in INSTANCES[furniture_start:]:
        x,y,z=inst['origin'];level=max((top for top in tops if top<=z+1e-6),default=0)
        inst['origin']=[q(x),q(y),level+q(z-level)]
    place_figures(tops,a-wall)
    vr=(a-wall)/math.cos(math.pi/12);tipx=vr-GR*math.sin(math.pi/12);tipy=GR*math.cos(math.pi/12)
    add('J01','Wall corner plywood gusset',6,[[GI,-GW],[tipx,-tipy],[vr,0],[tipx,tipy],[GI,GW]],color='blue',category='Walls',note=f'Fifty-four gussets. Their two long edges glue flat against both walls, {GR-.5:g} mm along each; the blunt inner edge keeps them clear of the rear posts. Lower gussets start 26 mm above their floor, upper ones 20 mm below the ceiling; beside both doors the ground-floor low gussets sit 96 mm up, just above the door openings.')
    # Ground-floor low gussets on either side of a door would cross the opening: they move up above it.
    for j in range(12):
        if j in (0,6,9):continue
        th=math.radians(j*30);u=(math.cos(th),math.sin(th),0);v=(-math.sin(th),math.cos(th),0)
        group='WallLeft' if j in (7,8) else 'WallRight' if j in (10,11) else 'Fixed'
        for k in range(3):
            for dz in gusset_dz:
                # Beside a door the low gusset moves up to the top of the door opening.
                dz=gusset_height(j,k,dz)
                origin=(u[0]*GI-v[0]*tipy,u[1]*GI-v[1]*tipy,tops[k]+dz)
                inst=put('J01',origin,u,v,group)
                for side in (-1,1):
                    vx,vy=u[0]*vr,u[1]*vr;tx,ty=u[0]*tipx+v[0]*side*tipy,u[1]*tipx+v[1]*side*tipy
                    sx,sy=vx+(tx-vx)*.5/GR,vy+(ty-vy)*.5/GR
                    angle=th+side*math.pi/12;axis=[math.cos(angle),math.sin(angle),0]
                    wallid=WALLS[(j+2+(1 if side==1 else 0))%12]['id']
                    JOINTS.append({'id':f'J-Corner-{j}-{k}-{dz}-{side}','type':'J2 angled gusset joint','parts':[inst['id'],wallid],'position':[(sx+tx)/2,(sy+ty)/2,origin[2]+3],'axis':axis,'outline':[[sx,sy,origin[2]],[tx,ty,origin[2]],[tx,ty,origin[2]+6],[sx,sy,origin[2]+6]],'glue':f'PVA on the {GR-.5:g} x6 mm contact face. Keep the corner at 150 degrees during cure.'})
    add('T01','Printer and blade-entry test coupon',6,rect(100,70),cuts=[cutrect(15,15,30,30)],holes=[hole(70,25,10),hole(70,50,6)],category='Tools',note='Temporary test only. Check 100 mm width with ruler; drill S01 and test jigsaw blade entry before main cuts.')
    add('T02','Joint clearance test coupon',6,rect(100,60),cuts=[cutrect(10,15,6.3,30),cutrect(40,15,6.6,30),cutrect(70,15,6.9,30)],category='Tools',note='Drill each narrow slot with a 3 mm bit chain and finish with file. Choose fit using measured stock; structural joints are glued and supported.')
    for pid in ('R05','T01','T02'):
        for _ in range(2 if pid=='R05' else 1):put(pid,(500,0,0),group='Tools')
    for pid,p in PARTS.items():p['quantity']=sum(i['part']==pid for i in INSTANCES)
    for pid in list(PARTS):
        if PARTS[pid]['quantity']==0:del PARTS[pid]
    # Both doorway openings are notches open to the lower exterior edge.
    for pid in door_ids:
        p=PARTS[pid];doorcut=p['cuts'].pop(0);x,y,x2,y2=bounds(doorcut)
        p['outer']=[[0,0],[x,0],[x,y2],[x2,y2],[x2,0],[width,0],[width,p['height']],[0,p['height']]]
        p['starters']=p['starters'][1:]
        for j,starter in enumerate(p['starters']):starter['id']=f'S{j+1:02}';starter['cut']=j+1
    merge_identical()
    # Furniture and miniature accessories only decorate the 3D view.
    for p in PARTS.values():
        p['optional']=p['category'] in ('Furniture','Accessories','Figures')
        p['render_only']=p['optional']
        if p['render_only']:p['starters']=[]
    # Window counts come from the actual wall cut-outs (per wall level) plus the dormer opening.
    windows=[0,0,0]
    for pid,p in PARTS.items():
        if p['category']=='Walls' and pid.startswith('W'):
            for c in p['cuts']:windows[int(bounds(c)[1]//pitch)]+=p['quantity']
    windows.append(len(PARTS['DM01']['cuts'])*PARTS['DM01']['quantity'])
    # One table of display offsets shared by the STEP exports and the preview renders.
    # The veranda is permanent: it stays put when the walls open and only moves outward in the exploded view.
    travel=DR['travel']
    views={'open_angle':WS['angle'],'open':{'Roof':[0,0,300],'Drawer':[e_out[0]*travel,e_out[1]*travel,0]},'exploded':{'WallRight':[230,-40,0],'WallLeft':[-230,-40,0],'Roof':[0,0,420],'Porch':[pn[0]*150,pn[1]*150,0],'Furniture':[0,-80,0],'Figures':[0,-80,0],'Drawer':[e_out[0]*250,e_out[1]*250,0]}}
    # Dimension annotations for the 3D viewer: lines (a-b, optional extension lines), level marks and labels.
    total=roof_peak+finial_height;deck_top=G+T['wall'];dims=[]
    def dim(label,a,b,ext=(),group=None):dims.append({'kind':'line','label':label,'a':list(a),'b':list(b),'ext':[list(map(list,e)) for e in ext],'group':group})
    def mark(label,p,group=None):dims.append({'kind':'label','label':label,'p':list(p),'group':group})
    sx,sy=Ap+40,40
    dim(f'{total:g} total height',(-half-30,60,0),(-half-30,60,total))
    dim(f'D{2*half:g} grey base',(-half,-half-40,0),(half,-half-40,0),[((-half,0,0),(-half,-half-40,0)),((half,0,0),(half,-half-40,0))])
    dim(f'Plinth {G:g} (base {bt:g} + stone {PL["height"]:g})',(0,-Ap-25,0),(0,-Ap-25,G))
    names=['Ground floor','Floor 1','Floor 2','Attic floor']
    for k in range(3):dim(f'{pitch:g}',(sx,sy,tops[k]),(sx,sy,tops[k+1]))
    for k,z in enumerate(tops):mark(f'{names[k]} Z{z:g}',(sx+10,sy,z))
    dim(f'Roof {roof_h:.0f} (about {math.degrees(math.atan(roof_h/roof_a)):.0f} degrees)',(sx,sy,roof_z),(sx,sy,roof_peak))
    dim(f'{finial_height:g} finial',(sx,sy,roof_peak),(sx,sy,total))
    mark(f'Eave Z{roof_z:g}',(sx+10,sy,roof_z));mark(f'Top Z{total:g}',(sx+10,sy,total))
    dim(f'Drawer pulls out {travel:g}',(*dpt(r0,hw+30),bt),(*dpt(r0+travel,hw+30),bt),[((*dpt(r0,0),bt),(*dpt(r0,hw+30),bt))])
    mark(f'Hidden drawer {2*hw:g} x {front-back:.0f} x {dh_:g} (inside {2*hw-12:g} x {front-back-tp:.0f} x {dh_-4:g})',(*dpt((front+back)/2,0),bt+dh_+4),'Drawer')
    def vp(x,y,z):return (po[0]+pu[0]*x+pv[0]*y,po[1]+pu[1]*x+pv[1]*y,z)
    dim(f'Deck Z{deck_top:g}',vp(ver['width']+20,0,bt),vp(ver['width']+20,0,deck_top),[(vp(ver['width'],0,deck_top),vp(ver['width']+20,0,deck_top))])
    dim(f'Veranda {ver["width"]:g}',vp(0,-20,deck_top),vp(ver['width'],-20,deck_top),[(vp(0,0,deck_top),vp(0,-20,deck_top)),(vp(ver['width'],0,deck_top),vp(ver['width'],-20,deck_top))])
    st=CFG['stairs']
    mark(f'{st["risers"]} risers x {(deck_top-bt)/st["risers"]:.0f}, treads {st["tread"]:g}',vp(-30,50,deck_top))
    en=(math.cos(math.radians(facet_angle(doors['main']))),math.sin(math.radians(facet_angle(doors['main']))))
    mark(f'Entrance: {st["risers"]} risers x {(G-bt)/st["risers"]:.1f}',(en[0]*(Ap+40),en[1]*(Ap+40),G+10))
    mark(f'Room divider {Lp:.0f} x {clear:g}, doorway {PT["door_width"]:g} x {dh:g}',(xp,PT['door_y']+PT['door_width']/2,G+dh+12))
    for f in FIGURES:mark(f'{f["name"]} {f["height"]:.0f} (clay)',(f['top'][0],f['top'][1],f['top'][2]+8),'Figures')
    import clay
    figs={f['key']:dict(clay.stats(f['key']),mesh=clay.packed(f['key'])) for f in FIGURES}
    # Every figure must pass upright through every doorway, turned sideways if that is narrower, with
    # figures.door_clearance to spare. The exterior doors lose the height of the E10 threshold in their notch.
    doorways=[{'name':f'Main entrance ({doors["main"]})','width':door_w,'height':door_h-sill},{'name':f'Veranda door ({doors["veranda"]})','width':door_w,'height':door_h-sill},{'name':'Room divider doorway (PT1)','width':PT['door_width'],'height':PT['door_height']}]
    cw,chh=CFG['figures']['door_clearance'];fit=[]
    for f in FIGURES:
        st=clay.stats(f['key']);narrow=min(st['width'],st['length'])
        for dw in doorways:fit.append({'figure':f['name'],'doorway':dw['name'],'figure_width':round(narrow,1),'figure_height':round(st['height'],1),'spare_width':round(dw['width']-narrow,1),'spare_height':round(dw['height']-st['height'],1),'fits':dw['width']-narrow>=cw and dw['height']-st['height']>=chh})
    order=', '.join(f'{f["name"]} {f["where"]}' for f in FIGURES)
    side=['right','back-right','back','back-left','left','front-left','front','front-right'][round(DR['direction']%360/45)%8]
    fh=CFG['figures']['heights']
    changes=[f'Magnetic wall catches: an MC1 solid-wood block inside each opening shell, {WC["gap"]:g} mm under the attic floor; a {mg} neodymium magnet in the F02 underside holds the shell shut against a steel disc',
      f'Magnetic wall stops: a {WS["post"]:g} mm square GP1 garden post on the base stops each shell at {WS["angle"]:g} degrees (it used to swing freely) and its magnet holds the shell open; renders, viewer and the wall-swing check now open to {WS["angle"]:g} degrees',
      'Four magnets in all, each bedded in epoxy below the surface; the plain steel discs ride on the walls, so no pair can be fitted the wrong way round',
      f'Hidden drawer turned to {DR["direction"]:g} degrees ({side}) so it slides out clear of the stop posts and veranda',
      f'Clay figures are smaller so each passes upright through every doorway, including the {PT["door_width"]:g} mm room-divider doorways: '+', '.join(f'{clay.NAMES[k]} {fh[k]:g} mm' for k in ('pappa','mamma','troll'))+' (were 80 / 66 / 56)',
      'Toy-safe finish: the book asks for primer, paint and varnish declared to EN 71-3 and names example products of each type']
    new={'MC1','GP1'};changed={'F02','B01',WALLS[2]['part'],WALLS[9]['part']}
    for pid,p in PARTS.items():
        if pid in new:p['revision']='new'
        elif pid in changed:p['revision']='changed'
    derived={'views':views,'doorways':doorways,'figure_fit':fit,'dimensions':dims,'changes':changes,'figures':list(FIGURES),'drawer':{'direction':list(e_out),'side':side,'angle':DR['direction'],'travel':travel,'width':2*hw,'depth':front-back,'height':dh_},'plinth_height':PL['height'],'ground_floor':G,'total_height':total,'wall_width':width,'floor_radius':floor_r,'roof_slant':slant,'roof_panel_width':rw,'floor_tops':tops,'clear_room_height':pitch-base,'hinge_axes':{'WallRight':[hinge_x,0],'WallLeft':[-hinge_x,0]},'roof_eave':roof_z,'windows_per_floor':windows,'veranda_size':[ver['width'],ver['depth']],'veranda_facet':ver['facet'],'base_thickness':bt,'facets':[{'facet':k+1,'part':w['part'],'id':w['id'],'group':w['group']} for k,w in enumerate(WALLS)],'doors':doors,'reference_style':f'original/ photos: red hipped veranda on {ver["facet"]} ({facet_angle(ver["facet"])} degrees), white shaped columns and railings, gabled main entrance on {doors["main"]}'}
    data={'config':CFG,'parts':PARTS,'instances':INSTANCES,'hardware':HARDWARE,'fasteners':FASTENERS,'joints':JOINTS,'derived':derived,'clay':figs}
    from fabrication import redesign_panels
    redesign_panels(data)
    return data

def fabrication_parts(data):
    """Only profiles that belong in CAD plans, cutting files and the build inventory."""
    return {pid:p for pid,p in data['parts'].items() if not p.get('render_only')}

def profile_variants(p):
    """Manufacturing signatures under in-plane quarter turns, with each frame's transform.

    Match full profiles, not bounding boxes. Winding, vertex start and drilling order
    do not change a part. Face-specific holes and countersink depths do.
    """
    stock=p['category'] if p['category'] in ('Purchased wood','Purchased packing') else 'Plywood'
    optional=p['category'] in ('Furniture','Accessories','Figures')
    def loop(points):
        pts=tuple(points)
        return min(seq[k:]+seq[:k] for seq in (pts,pts[::-1]) for k in range(len(seq)))
    for c,s in ((1,0),(0,1),(-1,0),(0,-1)):
        rotated=[[c*x-s*y,s*x+c*y] for x,y in p['outer']]
        x0,y0,_,_=bounds(rotated)
        def point(x,y):return (round(c*x-s*y-x0,6),round(s*x+c*y-y0,6))
        outer=loop([point(x,y) for x,y in p['outer']])
        cuts=tuple(sorted(loop([point(x,y) for x,y in cut]) for cut in p['cuts']))
        holes=[]
        for h in p['holes']:
            x,y=point(h['x'],h['y'])
            holes.append(json.dumps([x,y,h['diameter'],h.get('depth'),h.get('entry','top'),h.get('countersink'),h.get('countersink_depth')]))
        circle=p.get('outercircle')
        circle=(*point(*circle[:2]),circle[2]) if circle else ()
        yield (p['thickness'],stock,optional,outer,cuts,tuple(sorted(holes)),circle),(c,s,x0,y0)

def profile_key(p):
    return min(key for key,_ in profile_variants(p))

def merge_identical():
    """Interchangeable profiles share a build ID, including furniture and rotated strips.

    Each placement keeps its design role, paint and world geometry. Internal copy
    IDs remain unique so joints and moving hardware can identify their placements.
    Required and optional stock lists remain separate.
    """
    groups={};first={}
    frames={}
    for pid,p in PARTS.items():
        key,frame=min(profile_variants(p),key=lambda item:item[0]);frames[pid]=frame
        groups.setdefault(first.setdefault(key,pid),[]).append(pid)
    names={v:k for k,v in CFG['colors'].items()};renamed={}
    for keep,members in groups.items():
        if len(members)==1:continue
        labels=[PARTS[m]['name'] for m in members]
        if len(set(labels))>1:
            # Shared trailing words ("Main entrance step tread" + "Veranda step tread" -> "Step tread").
            common=[]
            for ws in zip(*[n.split()[::-1] for n in labels]):
                if len({w.lower() for w in ws})>1:break
                common.insert(0,ws[0].lower())
            prefix=[]
            for ws in zip(*[n.split() for n in labels]):
                if len({w.lower() for w in ws})>1:break
                prefix.append(ws[0].lower())
            shared=prefix+common
            PARTS[keep]['name']=' '.join(shared).capitalize() if len(shared)>1 else ' / '.join(dict.fromkeys(labels))
        notes=list(dict.fromkeys(PARTS[m]['note'] for m in members if PARTS[m]['note']))
        PARTS[keep]['note']=' '.join(notes)
        paint=Counter();k=0
        for inst in INSTANCES:
            if inst['part'] not in members:continue
            pid=inst['part']
            if pid!=keep:
                # Both frames map to the same normalized profile. Map the kept
                # profile back into this copy's original frame before placing it.
                ck,sk,kx,ky=frames[keep];ci,si,ix,iy=frames[pid]
                c,s=ci*ck+si*sk,ci*sk-si*ck
                dx,dy=ci*(ix-kx)+si*(iy-ky),-si*(ix-kx)+ci*(iy-ky)
                o,u,v=inst['origin'],inst['u'],inst['v']
                inst['origin']=[o[n]+u[n]*dx+v[n]*dy for n in range(3)]
                inst['u']=[u[n]*c+v[n]*s for n in range(3)]
                inst['v']=[-u[n]*s+v[n]*c for n in range(3)]
            colour=PARTS[inst['part']]['color'];paint[(colour,inst['label'])]+=1
            if colour!=PARTS[keep]['color']:inst['color']=colour
            k+=1;renamed[inst['id']]=f'{keep}-{k:02}';inst['id']=renamed[inst['id']];inst['part']=keep
        PARTS[keep]['note']+=' Uses: '+ '; '.join(f'{n} {label.lower()} ({names.get(c,c)})' for (c,label),n in paint.items())+'.'
        for m in members[1:]:del PARTS[m]
        PARTS[keep]['quantity']=k
    for item in JOINTS+FASTENERS:item['parts']=[renamed.get(x,x) for x in item['parts']]
    for h in HARDWARE:
        if 'door' in h:h['door']=renamed.get(h['door'],h['door'])
        if 'moves_with' in h:h['moves_with']=[renamed.get(x,x) for x in h['moves_with']]

def instance_box(inst):
    p=PARTS[inst['part']];o,u,v,w=inst['origin'],inst['u'],inst['v'],inst['w']
    pts=[[o[k]+u[k]*x+v[k]*y+w[k]*t for k in range(3)] for x,y in p['outer'] for t in (0,p['thickness'])]
    return [min(q[k] for q in pts) for k in range(3)],[max(q[k] for q in pts) for k in range(3)]

ROOMS=[('ground floor','kitchen'),('floor 1','living room'),('floor 2','bedrooms'),('attic','attic')]
def place_figures(tops,inner):
    """Stand one thermo-clay Moomin on each storey (config figures.levels) in the front-most free spot, so
    it is seen when the walls open, turned a little toward the middle. Clear of furniture, posts and divider."""
    import clay
    fc=CFG['figures'];codes={'pappa':'FG1','mamma':'FG2','troll':'FG3'}
    obstacles=[instance_box(i) for i in INSTANCES if i['group'] in ('Fixed','Furniture','RoofLocks','Drawer') and (PARTS[i['part']]['category'] not in ('Walls','Exterior') or i['part'] in ('PT1','PT2')) and i['part'] not in ('F00','F01','F02')]
    cands=sorted(((x,y) for x in range(-130,131,4) for y in range(-130,121,4)),key=lambda c:(c[1],abs(c[0])))
    for level,key in enumerate(fc['levels']):
        z=tops[level];hull=clay.footprint(key);h=clay.stats(key)['height'];best=None
        for cx,cy in cands:
            # Facing the front, preferably turned toward the middle; straight ahead if that is all that fits.
            for yaw,extra in ((-90+fc['turn']*((cx<0)-(cx>0)),0),(-90,6)):
                th=math.radians(yaw);pts=[(cx+x*math.cos(th)-y*math.sin(th),cy+x*math.sin(th)+y*math.cos(th)) for x,y in hull]
                if any(math.hypot(px,py)>inner-28 for px,py in pts):continue
                xs,ys=zip(*pts);lo=[min(xs),min(ys),z];hi=[max(xs),max(ys),z+h]
                if any(all(min(hi[k],ob[1][k])-max(lo[k],ob[0][k])>-3 for k in range(3)) for ob in obstacles):continue
                cost=cy+abs(cx)*.05+extra
                if best is None or cost<best[0]:best=(cost,cx,cy,yaw)
                break
        if best is None:raise ValueError(f'No free spot for {key} on level {level}')
        _,cx,cy,yaw=best
        FIGURES.append({'id':f'{codes[key]}-01','code':codes[key],'key':key,'name':clay.NAMES[key],'level':level,'room':f'{ROOMS[level][0].capitalize()}, {ROOMS[level][1]}','where':f'in the {ROOMS[level][1]} on the {ROOMS[level][0]}','x':cx,'y':cy,'z':z,'yaw':yaw,'height':round(h,1),'top':[cx,cy,z+h],'revision':'new'})

def furnish(tops):
    def part(pid,name,w,h,t=4,color='wood',note=''):
        if pid not in PARTS:add(pid,name,t,rect(w,h),color=color,category='Furniture',note=note)
    def box(prefix,name,x,y,z,w,d,h,color='cream',shelves=0,group='Furniture'):
        part(prefix+'A',name+' side',d,h,color=color);part(prefix+'B',name+' top / bottom / shelf',w-8,d-3,color=color);part(prefix+'C',name+' back',w-8,h-8,3,color)
        upright(prefix+'A',x,y,z,group,axis='yz');upright(prefix+'A',x+w-4,y,z,group,axis='yz')
        for zz in [z,z+h-4]+[z+(j+1)*(h-8)/(shelves+1) for j in range(shelves)]:put(prefix+'B',(x+4,y,zz),group=group)
        upright(prefix+'C',x+4,y+d,z+4,group)
    def table(prefix,name,x,y,z,w,d,h,color='wood',support_depth=None):
        support_depth=d-12 if support_depth is None else support_depth
        part(prefix+'A',name+' tabletop',w,d,color=color);part(prefix+'B',name+' pedestal side',support_depth,h-4,color=color)
        inset=(d-support_depth)/2
        put(prefix+'A',(x,y,z+h-4),group='Furniture');upright(prefix+'B',x+8,y+inset,z,'Furniture',axis='yz');upright(prefix+'B',x+w-12,y+inset,z,'Furniture',axis='yz')
    def seat(prefix,name,x,y,z,w,d,h,back,color):
        part(prefix+'A',name+' seat',w,d,color=color);part(prefix+'B',name+' side / leg',d,h-4,color=color);part(prefix+'C',name+' back',w,back,color=color)
        put(prefix+'A',(x,y,z+h-4),group='Furniture');upright(prefix+'B',x,y,z,'Furniture',axis='yz');upright(prefix+'B',x+w-4,y,z,'Furniture',axis='yz');upright(prefix+'C',x,y+d+4,z,'Furniture')
    def bed(prefix,name,x,y,z):
        part(prefix+'A',name+' mattress platform',54,104,color='cream');part(prefix+'B',name+' head / foot',54,34,color='ochre');part(prefix+'C',name+' support',96,18,color='wood')
        put(prefix+'A',(x,y+4,z+18),group='Furniture');upright(prefix+'B',x,y+4,z,'Furniture');upright(prefix+'B',x,y+112,z,'Furniture')
        upright(prefix+'C',x+4,y+8,z,'Furniture',axis='yz');upright(prefix+'C',x+46,y+8,z,'Furniture',axis='yz')
    # Room layouts per storey; the divider runs along X0 with its door opening at Y20-60 swinging into +X.
    g,f1,f2,at=tops
    # Small size adjustments make furniture blanks interchangeable. Cabinets and
    # dining-table supports share 37 x48 sides; sink shelves share the bed ends.
    box('K1','Kitchen cupboard',-118,-20,g,76,37,48,'sage',1)
    box('K2','Cooker',-125,36,g,44,37,48,'cream')
    table('K3','Dining table',10,-110,g,90,60,41)
    for x,y in [(30,-44),(66,-44),(-50,-135)]:seat('K4','Dining chair',x,y,g,28,28,24,53,'ochre')
    box('K5','Sink cabinet',60,22,g,62,37,48,'sage')
    add('K6','Sink rim',3,rect(26,20),[cutrect(5,5,16,10)],color='cream',category='Furniture',note='Drill small interior opening and file; glue a painted card basin beneath.')
    put('K6',(82,32,g+48),group='Furniture')
    add('K7','Cooker burner discs',3,poly(12,5,5,5),color='ink',category='Furniture')
    for x,y in [(-118,43),(-100,43),(-118,61),(-100,61)]:put('K7',(x,y,g+48),group='Furniture')
    seat('V1','Sofa',-122,-43,f1,88,44,25,55,'rose')
    seat('V2','Armchair',58,-118,f1,40,40,25,55,'sage')
    # Coffee table and desk share tops; their centered supports reuse chair parts.
    table('V3','Coffee table',10,-70,f1,60,38,24,'ochre',support_depth=28)
    box('V4','Bookcase',-119,36,f1,48,28,98,'cream',3)
    table('V5','Writing desk',67,4,f1,60,38,44,support_depth=21)
    seat('K4','Dining chair',94,-36,f1,28,28,24,53,'ochre')
    box('V6','Decorative stove',-50,-128,f1,32,29,56,'ink')
    bed('U1','Bed',-122,-76,f2);bed('U1','Bed',59,-76,f2)
    box('U2','Wardrobe',8,-125,f2,64,32,100,'sage',1)
    # Bedside sides reuse chair seats. Dresser shelves reuse bookcase shelves,
    # its back reuses the cooker back, and its sides reuse washstand/chest panels.
    box('U3','Bedside table',-59,-35,f2,26,28,28,'ochre')
    box('U3','Bedside table',27,-35,f2,26,28,28,'ochre')
    box('U4','Dresser',-98,-115,f2,48,28,44,'cream',1)
    table('U5','Washstand',89,42,f2,44,28,40,'cream')
    box('N1','Attic chest',-61,-53,at,52,31,32,'wood')
    # Bench sides reuse chair sides; its seat and back use the same blank.
    seat('N2','Attic bench',35,-39,at,62,28,24,28,'ochre')
    add('N3','Telescope silhouette',4,[[0,0],[42,0],[48,8],[42,16],[0,16]],color='ochre',category='Furniture',note='Decorative plywood telescope silhouette on a broad glued pedestal.')
    add('N4','Telescope pedestal',4,[[0,0],[32,0],[20,38],[12,38]],color='wood',category='Furniture')
    upright('N4',-55,0,at,'Furniture');upright('N3',-63,0,at+38,'Furniture')
    # Separate supervised-use accessory kit, shown in CAD outside assembly.
    add('X01','Miniature book',3,rect(12,18),color='ochre',category='Accessories',note='Small part: separate adult-supervised accessory set for ages 3-5.')
    add('X02','Miniature picture frame',3,rect(24,30),[cutrect(5,5,14,20)],color='cream',category='Accessories')
    add('X03','Miniature plate',3,poly(16,10,10,10),color='cream',category='Accessories')
    add('X04','Miniature flowerpot silhouette',4,[[0,0],[16,0],[20,20],[12,20],[12,35],[8,35],[8,20],[-4,20]],color='sage',category='Accessories')
    for pid,q in [('X01',12),('X02',4),('X03',6),('X04',3)]:
        for j in range(q):put(pid,(500+j*28,-100,0),group='Accessories')

if __name__=='__main__':
    data=build(); (ROOT/'output/parts.json').write_text(json.dumps(data,indent=2));print(f'{len(PARTS)} profiles, {len(INSTANCES)} instances')
