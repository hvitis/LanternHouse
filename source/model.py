"""Single source of truth for fabrication profiles and assembled placements (mm)."""
from __future__ import annotations
import itertools, json, math, sys
from collections import Counter
from pathlib import Path

sys.modules.setdefault('model', sys.modules[__name__])

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'source/config.json').read_text())
PARTS, INSTANCES, HARDWARE, FASTENERS, JOINTS = {}, [], [], [], []
WALLS=[]   # wall-facet instances in facet order (facet 1 first)
BOUGHT=('Purchased wood','Purchased packing','Purchased metal')   # bought and cut by hand, never nested on plywood
FIGURES=[]   # placements of the thermo-clay figures
DOOR_SWEEPS=[]   # plan boxes the room doors swing through, kept clear when figures are placed

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
def cutrect_dogbone(x,y,w,h,r=2.0):
    from shapely.geometry import box, Point
    from shapely.ops import unary_union
    rect = box(x, y, x+w, y+h)
    corners = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
    circles = [Point(cx, cy).buffer(r, quad_segs=8) for cx, cy in corners]
    u = unary_union([rect] + circles)
    return list(u.exterior.coords)[:-1]
def add(pid,name,t,outer,cuts=None,holes=None,color='wood',category='Structure',note=''):
    if outer[-1]==outer[0]:outer=outer[:-1]
    x0,y0,x1,y1=bounds(outer)
    outer=[[x-x0,y-y0] for x,y in outer]
    cuts=[[[x-x0,y-y0] for x,y in c] for c in (cuts or [])]
    holes=[dict(h,x=h['x']-x0,y=h['y']-y0) for h in (holes or [])]
    starters=[]
    for i,c in enumerate(cuts):
        cx=sum(v[0] for v in c)/len(c);cy=sum(v[1] for v in c)/len(c)
        r_fit=edge_distance(cx,cy,c) if inside_polygon(cx,cy,c) else 0
        a,b,d,e=bounds(c); diameter=min(CFG['starter_diameter'],d-a-4,e-b-4,2*(r_fit-2))
        if diameter>=6:
            sx,sy=a+diameter/2+2,b+diameter/2+2
            if not inside_polygon(sx,sy,c) or edge_distance(sx,sy,c)<diameter/2+1.99:
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
    PARTS.clear();INSTANCES.clear();HARDWARE.clear();FASTENERS.clear();JOINTS.clear();FIGURES.clear();WALLS.clear();DOOR_SWEEPS.clear()
    T=CFG['thickness']; base=T['floor']; bt=T['base']; wall=T['wall']; pitch=CFG['floor_pitch']; H=CFG['wall_height']
    scale=H/450; q=lambda value:value*scale
    WH=CFG['wall_hinge'];doors=CFG['doors'];door_ids=[doors['main'],doors['veranda'],doors['back']]
    door_w,door_h,sill=q(50),q(96),T['structure']   # the threshold is as tall as the veranda deck is thick
    BD=CFG['back_door'];SL=CFG['shell_lift'];WN=CFG['windows'];LT=CFG['lighting']
    # Optional lighting: one wire runs from the plinth up behind the left rear pillar through every floor.
    def wire_hole(r):return dict(hole(LT['at'][0]+r,LT['at'][1]+r,LT['wire_hole'],None,'Optional LED wire hole'),entry='top')
    a=CFG['tower_diameter']/2*math.cos(math.pi/12)
    width=2*(a-wall)*math.tan(math.pi/12)-1
    floor_r=(a-wall-CFG['moving_clearance'])/math.cos(math.pi/12)
    floor_points=poly(12,floor_r,floor_r,floor_r)
    hinge_x=CFG['tower_diameter']/2+WH['axis_offset']
    half=CFG['base_diameter']/2
    # The stone plinth lifts the house: G is the ground-floor top, every storey is measured from it.
    # The round base B01 is bt thick; the plinth height runs from its top to the ground-floor top.
    PL=CFG['plinth'];G=bt+PL['height'];tops=[G+k*pitch for k in range(4)]
    # Corner braces: low ones 26 above each floor, high ones 20 below the ceiling (clear of the floor supports).
    gusset_dz=(q(26),pitch-base-q(20))
    door_corners={round((facet_angle(p)+side)/30)%12 for p in door_ids for side in (-15,15)}
    # Corner braces, cut from the wall plywood and laid flat: RD deep from the wall faces, reaching GR along a
    # neighbouring facet from each corner they hold (GS where a brace is raised over a door).
    GT,GR,GS,RD=wall,q(32),q(22),q(17)
    post_width=q(18);post_t=T['structure']
    posts=[(q(x),q(y)) for x,y in [(-145,10),(127,10),(-68,128),(50,128)]]
    feet=[(x,y-24) for x,y in posts]
    # Veranda frame: pu runs along its wall facet, pv points from the outer deck edge toward the wall.
    ver=CFG['veranda'];vth=math.radians(facet_angle(ver['facet']))
    pn=(math.cos(vth),math.sin(vth),0);pu=(-pn[1],pn[0],0);pv=(-pn[0],-pn[1],0)
    reach=a+ver['wall_gap']+ver['depth']
    po=(pn[0]*reach-pu[0]*ver['width']/2,pn[1]*reach-pu[1]*ver['width']/2,G)
    # Round foundation: a fine polygon for nesting/templates, a true circle for CAD and DXF.
    add('B01','Round green base',bt,poly(180,half,half,half),color='green',note=f'Circle D{2*half:g}, centered on the tower; paint plain green. The stone plinth, the veranda skirt and both entrance stairs are glued on top, and the hidden drawer slides on it. Cut with a jigsaw or router trammel, then sand the edge fair.')
    PARTS['B01']['outercircle']=[half,half,half]
    put('B01',(-half,-half,0))
    # Stone plinth: 12 facet panels between B01 and a 12-sided ground-floor plate, with a hidden drawer bay.
    Ap,tp=PL['apothem'],PL['panel'];ph=G-base-bt;r0=Ap/math.cos(math.pi/12)
    fholes=[dict(hole(r0+x+12,r0+y+12,3.2,None,'SC3 foot-block screw clearance; countersink underside D6 x 1.5'),entry='bottom',countersink=6,countersink_depth=1.5) for x,y in feet]+[wire_hole(r0)]
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
    # The box and its back stop only slide and stop the drawer: 3 mm. The stone front stays plinth-panel thick.
    db=T['detail']
    add('DR2','Drawer side',db,rect(front-back,dh_),category='Structure',note='Two sides; glue to the back and bottom, then to the front panels with small corner blocks.')
    add('DR3','Drawer back',db,rect(2*hw-2*db,dh_),category='Structure')
    # Captive stop: a hardwood dowel pushed up through B01 after the drawer is in rides in a slot in the drawer
    # bottom and stops it at the configured travel. The slot also keeps the drawer from wandering sideways.
    ST=DR['stop'];L1=front-back-db;sr=ST['dowel']/2;sm=ST['margin'];sx1=L1-12;sx0=sx1-(DR['travel']+2*sr+2*sm)
    # Follow both DR4 inner faces with a shallow point, so the bottom has two matching glue edges.
    # Keep the slot referenced to the original straight box, preserving the dowel position and travel.
    bottom_half=hw-db;bottom_edge=rho_face(bottom_half)-back-db;bottom_tip=rho_face(0)-back-db
    bottom=[[0,0],[bottom_edge,0],[bottom_tip,bottom_half],[bottom_edge,2*bottom_half],[0,2*bottom_half]]
    add('DR1','Pointed drawer bottom with stop slot',T['furniture'],bottom,cuts=[cutrect(sx0,hw-db-ST['slot']/2,sx1-sx0,ST['slot'])],category='Structure',note=f'Glue the two angled front edges to the inner faces of the DR4 panels. Keep the finger notches clear. Slides directly on B01: wax the underside. The DS1 dowel rides in the slot and stops the drawer at {DR["travel"]:g} mm.')
    for w in (hw,-hw):vertical_plate('DR2',dpt(back,w),dpt(front,w),bt,dpt(0,0),'Drawer')
    vertical_plate('DR3',dpt(back,-hw+db),dpt(back,hw-db),bt,dpt(0,0),'Drawer')
    bo=dpt(back+db,-hw+db);put('DR1',(bo[0],bo[1],bt),(e_out[0],e_out[1],0),(e_side[0],e_side[1],0),'Drawer')
    stop_at=dpt(back+db+sx1-sr-sm,0)   # closed: the dowel sits at the slot's front end
    add('DS1','Drawer stop dowel (hardwood)',bt+T['furniture']-.5,poly(16,sr,sr,sr),category='Purchased wood',note=f'One D{ST["dowel"]:g} mm hardwood dowel, {bt+T["furniture"]-.5:g} mm long. With the drawer in, push it up through the B01 hole into the drawer-bottom slot and glue it in from below: the drawer then stops at {DR["travel"]:g} mm and cannot be pulled out onto a child\'s feet.')
    put('DS1',(stop_at[0]-sr,stop_at[1]-sr,0))
    PARTS['B01']['holes'].append(dict(hole(stop_at[0]+half,stop_at[1]+half,ST['dowel'],None,'Drawer stop dowel hole'),id=f'H{len(PARTS["B01"]["holes"])+1:02}'))
    gback=back-.5-db   # the guide walls end flush with the back of the back stop
    add('DG1','Drawer guide wall',tp,rect(gfront-gback,ph),note='Two guide walls glued between B01 and F00; they also carry F00 over the drawer bay.')
    add('DB1','Drawer back stop',db,rect(2*hw+2,ph),note='Glued between the guide walls; the closed drawer rests against it.')
    for w in (hw+1,-hw-1):vertical_plate('DG1',dpt(gback,w),dpt(gfront,w),bt,dpt(0,w*2))
    vertical_plate('DB1',dpt(back-.5,-hw-1),dpt(back-.5,hw+1),bt,dpt(back-10,0))
    allowance=CFG['fabrication']['pillar_clearance']
    post_slots=[cutrect_dogbone(floor_r+x-allowance/2,floor_r+y-post_t-allowance/2,post_width+allowance,post_t+allowance,r=2.0) for x,y in posts]
    add('F01','First / second floor',base,floor_points,cuts=post_slots,holes=[wire_hole(floor_r)],color='wood',note='Slide both levels over the four continuous P01 pillars. Glue divided panels over interlocking finger joints and seam supports; pillar openings feature CNC dogbone fillets (R2.0 mm corner relief) at all four inside corners.')
    add('F02','Attic floor',base,floor_points,holes=[wire_hole(floor_r)],color='wood',note='Slide over pillars to top level. Do not use F01 as the attic floor.')
    for k in range(1,4):put('F02' if k==3 else 'F01',(-floor_r,-floor_r,tops[k]-base),group='Fixed',label='Attic floor' if k==3 else f'Floor {k+1}')
    # Windows: the wall itself keeps a solid cross between four panes (no thin glued bars to snap off). A one-piece
    # surround (frame over the cross, sill band and pediment hood) is glued on outside, PET glazing inside.
    win_w,win_h,bar,fb=WN['width'],WN['height'],WN['bar'],WN['frame'];pane_w,pane_h=(win_w-bar)/2,(win_h-bar)/2
    def panes(ox,oy):return [cutrect(ox+c*(pane_w+bar),oy+r*(pane_h+bar),pane_w,pane_h) for r in (0,1) for c in (0,1)]
    band,rise=WN['hood'];sb=WN['sill'];sw_=win_w+2*fb;top=sb+win_h+2*fb
    surround=[[0,0],[sw_,0],[sw_,top+band],[sw_/2,top+band+rise],[0,top+band]]
    add('WF1','Window surround (frame, sill and hood in one piece)',T['detail'],surround,[cutrect(fb+c*(pane_w+bar),sb+fb+r*(pane_h+bar),pane_w,pane_h) for r in (0,1) for c in (0,1)],color='cream',category='Exterior',
        note=f'One per tower window. Its cross lies over the solid cross left in the wall, so no bar is unsupported; glue the whole back face. {sw_:.1f} x {top+band+rise:.1f} mm, too big to swallow if it ever came off.')
    gz,gm=WN['glazing'];gs=.6   # side overlap: the hinge backing blocks stand 0.5 mm beside the window on two facets
    add('GZ1','Window glazing (clear PET)',gz,rect(win_w+2*gs,win_h+2*gm),color='cream',category='Purchased packing',note=f'Cut from {gz:g} mm clear PET (or PETG) sheet with a knife; glue inside over the opening, on the cross bars and the {gm:g} mm border, with clear craft glue. Never glass or acrylic that can shatter.')
    # Wall facets: six fixed at the back; three facets in each moving half.
    for i in range(12):
        angle=-75+i*30;th=math.radians(angle); n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0)
        group='WallRight' if i<3 else 'WallLeft' if i>8 else 'Fixed'
        pid=f'W{i+1:02}';cuts=[];windows=[]
        # The opening shells hang shell_lift above F00 on their hinges, so their bottom edges never rub the plinth.
        z0=G+(SL if group!='Fixed' else 0)
        for level in range(3):
            if pid==doors['back'] and level==0:cuts.append(cutrect(BD['start'],0,BD['width'],door_h))
            elif pid in door_ids and level==0:cuts.append(cutrect((width-door_w)/2,0,door_w,door_h))
            elif i%2==1:
                ox,oy=(width-win_w)/2,level*pitch+q(54);windows.append([ox,oy,win_w,win_h]);cuts+=panes(ox,oy)
        holes=[]
        # Facets beside a hinge axis (0 or 180 degrees) carry the wall hinge leaves.
        hinge_end='start' if round(angle-15)%180==0 else 'end' if round(angle+15)%180==0 else None
        # All mounting pilots are in solid edge strips, away from window cutouts. Both leaves of a hinge sit at the
        # same height, so the fixed facets carry their pilots shell_lift higher on the wall.
        hinge_dz=0 if group!='Fixed' else SL
        if hinge_end:
            hx=WH['hole_x']-(hinge_x*math.sin(math.pi/12)-width/2)
            if hinge_end=='end':hx=width-hx
            for cy in WH['centers']:
                for dy in WH['hole_y']:
                    holes.append(hole(hx,cy+hinge_dz-WH['height']/2+dy,WH['pilot_diameter'],wall,'Hinge screw clearance; confirm actual leaf template'))
        # Walls are named by what they carry, so identical facets get the same name (and later the same ID).
        kinds={doors['main']:'main',doors['veranda']:'veranda',doors['back']:'back'}
        feats=([kinds[pid]+' door'] if pid in door_ids else [])+(['windows'] if windows else [])+(['hinge pilots'] if hinge_end else [])
        kind='Opening wall' if group!='Fixed' else 'Fixed wall'
        name=kind+(' with '+' and '.join(feats) if feats else ', plain')
        note=(f'Opening walls are 2 mm lower for roof clearance and hang {SL:g} mm above F00; keep their seams clear. ' if group!='Fixed' else 'Fill the exterior seams of the fixed shell. ')+'Glue the J01 corner ribs (J02 brackets where no rib fits) inside. The wall map shows which facets it fills.'+(' Leave the cross between the four panes of each window solid.' if windows else '')
        add(pid,name,wall,rect(width,H-(2 if group!='Fixed' else 0)),cuts,holes,'blue','Walls',note=note)
        PARTS[pid]['windows']=windows
        origin=(n[0]*(a-wall)-u[0]*width/2,n[1]*(a-wall)-u[1]*width/2,z0)
        wallinst=put(pid,origin,u,(0,0,1),group,label=f'Wall facet {i+1:02}');WALLS.append(wallinst)
        if hinge_end:
            bp=WH['block_pilot'];hz=G+SL   # hinge heights are measured from here on both leaves
            if 'A02' not in PARTS:add('A02','Hinge backing block (solid wood)',8,rect(16,28),holes=[hole(8,14-WH['height']/2+dy,bp,8,f'D{bp:g} wood-screw pilot through the block') for dy in WH['hole_y']],category='Purchased wood',note=f'Buy 8 x 16 mm hardwood strip; cut twelve 28 mm blocks. Glue to the wall inside and let it cure, then drill D{bp:g} pilots through it from the real hinge leaf. For the M2.5 bolt option drill D2.7 instead.')
            hx=holes[0]['x']
            for cy in WH['centers']:
                bo=(origin[0]+u[0]*(hx-8)-n[0]*8,origin[1]+u[1]*(hx-8)-n[1]*8,hz+cy-14)
                block=put('A02',bo,u,(0,0,1),group)
                if 'A06' not in PARTS:add('A06','Hinge packing shim',WH['packing_thickness'],rect(10,WH['height']),holes=[hole(5,dy,2.2) for dy in WH['hole_y']],category='Purchased packing',note='Twelve rigid 0.9 mm shims (card, veneer or plastic), one beneath each wall hinge leaf. Confirm thickness and barrel axis with actual hardware; cut with knife or scissors, not jigsaw.')
                put('A06',(origin[0]+u[0]*(hx-5)+n[0]*wall,origin[1]+u[1]*(hx-5)+n[1]*wall,hz+cy-WH['height']/2),u,(0,0,1),group)
                outline=[[bo[0]+n[0]*8+u[0]*xx,bo[1]+n[1]*8+u[1]*xx,bo[2]+zz] for xx,zz in [(0,0),(16,0),(16,28),(0,28)]]
                JOINTS.append({'id':f'J-Hinge-{i}-{int(cy)}','type':'J3 reinforced screwed butt joint','parts':[wallinst['id'],block['id']],'position':[bo[0]+n[0]*8+u[0]*8,bo[1]+n[1]*8+u[1]*8,hz+cy],'axis':[-n[0],-n[1],0],'outline':outline,'glue':'PVA on 16 x 28 backing face; clamp before pilot drilling'})
            stand=wall+WH['leaf_thickness']+WH['packing_thickness']
            # The longest stock screw whose tip stays inside the 8 mm block; the bolt keeps 3 mm for its cap nut.
            sl=max(l for l in (10,12,16,20) if l<=stand+8.2);bl=min(l for l in (12,16,20,25) if l>=stand+8+3)
            for h in PARTS[pid]['holes']:
                head=[origin[0]+u[0]*h['x']+n[0]*stand,origin[1]+u[1]*h['x']+n[1]*stand,z0+h['y']]
                FASTENERS.append({'id':f'FS-{pid}-{h["id"]}','type':'SC1','diameter':2.5,'length':float(sl),'head_diameter':5.0,'head_height':1.2,'origin':head,'axis':[-n[0],-n[1],0],'parts':[wallinst['id']],'pilot':bp,'pilot_depth':8,'bolt_length':bl,'note':f'2.5 x {sl:g} mm countersunk wood screw (length includes the head): hinge {WH["leaf_thickness"]:g} + shim {WH["packing_thickness"]:g} + wall {wall:g} leave {sl-stand:.1f} mm of thread in the hardwood A02 block, into a D{bp:g} pilot. Bolt option: M2.5 x {bl:g} countersunk machine screw with an M2.5 dome cap nut inside, D2.7 through the block.'})
        for ox,oy,w_,h_ in windows:
            put('WF1',(origin[0]+u[0]*(ox-fb)+n[0]*wall,origin[1]+u[1]*(ox-fb)+n[1]*wall,z0+oy-fb-sb),u,(0,0,1),group)
            put('GZ1',(origin[0]+u[0]*(ox-gs)-n[0]*gz,origin[1]+u[1]*(ox-gs)-n[1]*gz,z0+oy-gm),u,(0,0,1),group)
        if 'D03' not in PARTS:add('D03','White eave fascia',3,rect(width,8),color='cream',category='Exterior',note='One fascia per wall facet at eave. Never glue across hinge seams or the front closing edges.')
        yy=PARTS[pid]['height']-8;put('D03',(origin[0]+n[0]*wall,origin[1]+n[1]*wall,z0+yy),u,(0,0,1),group)
    # Hinge axes outside the two side corners. Copper/brass hardware is reference geometry.
    for group,sign in [('WallRight',1),('WallLeft',-1)]:
        for z in (G+SL+c for c in WH['centers']):
            HARDWARE.append({'id':f'HG-{group}-{int(z)}','kind':'Wall butt hinge','group':group,'position':[sign*hinge_x,0,z],'height':CFG['wall_hinge']['height'],'width':CFG['wall_hinge']['open_width'],'note':'Use A06 packing to align the barrel outside the corner; confirm leaf holes on the hardware checking template.'})
    # Magnetic catches and stops, four neodymium magnets in all. Each opening shell carries a solid-wood MC1 block just
    # under the attic floor (a magnet in F02 holds the shell shut) and a steel disc low on its hinge facet (a magnet in
    # a GP1 garden post on B01 stops the shell at the open angle and holds it there). The plain steel discs ride on the
    # walls, so no magnet pair can be fitted the wrong way round.
    MG,WC,WS=CFG['magnets'],CFG['wall_catch'],CFG['wall_stop'];CL,CD,CT=WC['block'];cd=CD-MG['disc_pocket'][0]/2-4;mg=f'D{MG["magnet"][0]:g} x {MG["magnet"][1]:g} mm'
    # Every magnet is enclosed in solid wood: it drops into a blind bore from the hidden face, sits against a
    # skin of wood on the working face, and a glued hardwood dowel plug closes the bore behind it.
    skin,bore,plug=MG['skin'],MG['bore'],MG['plug']
    def enclosed(depth):return f'Drill the D{bore:g} bore {depth:g} mm deep from the hidden face (depth stop!), leaving {skin:g} mm of wood on the working face. Drop the {mg} magnet in against that skin, then glue a D{plug:g} hardwood dowel plug behind it with slow 2-part epoxy and sand it flush. No magnet surface is ever exposed.'
    add('MC1','Magnetic wall catch block (solid wood)',CT,rect(CL,CD),holes=[dict(hole(CL/2,cd,bore,CT-skin,'Enclosed catch magnet bore from the underside'),entry='bottom')],category='Purchased wood',note=f'Two {CL:g} x {CD:g} x {CT:g} mm hardwood blocks, one glued inside each opening shell {WC["x"]:g} mm from the front seam, top {WC["gap"]:g} mm under the attic floor. '+enclosed(CT-skin))
    z_catch=tops[3]-base-WC['gap']-CT
    PARTS['F02']['note']+=f' Two D{MG["disc_pocket"][0]:g} x {MG["disc_pocket"][1]:g} recesses in the underside, near the front seam, hold the steel discs the catch magnets pull on.'
    for group,k,x0 in (('WallRight',0,WC['x']),('WallLeft',11,width-WC['x']-CL)):
        wi=WALLS[k];o,u,n=wi['origin'],wi['u'],wi['w']
        put('MC1',(o[0]+u[0]*x0,o[1]+u[1]*x0,z_catch),u,(-n[0],-n[1],0),group)
        cx,cy=o[0]+u[0]*(x0+CL/2)-n[0]*cd,o[1]+u[1]*(x0+CL/2)-n[1]*cd   # disc 4 mm from the block's inner edge, clear of the floor edge
        PARTS['F02']['holes'].append(dict(hole(cx+floor_r,cy+floor_r,MG['disc_pocket'][0],MG['disc_pocket'][1],'Wall-catch steel disc recess'),entry='bottom',id=f'H{len(PARTS["F02"]["holes"])+1:02}'))
        HARDWARE.append({'id':f'MG-Catch-{group}','kind':'Catch magnet','group':group,'position':[cx,cy,z_catch+CT-skin-MG['magnet'][1]],'height':MG['magnet'][1],'width':MG['magnet'][0],'enclosed':skin,'note':f'{mg} magnet enclosed in the {group} MC1 block, {skin:g} mm under its top face.'})
        HARDWARE.append({'id':f'SD-Catch-{group}','kind':'Steel disc','group':'Fixed','position':[cx,cy,tops[3]-base],'height':MG['disc'][1],'width':MG['disc'][0],'note':'Epoxied flush into the F02 underside recess.'})
    s,zc=WS['post'],SL+WS['top']/2   # the stop disc rides on a lifted shell
    def spin(p,c,deg):
        t=math.radians(deg);x,y=p[0]-c[0],p[1]-c[1];return (c[0]+x*math.cos(t)-y*math.sin(t),c[1]+x*math.sin(t)+y*math.cos(t))
    dd,dz=WS['dowel']
    add('GP1','Garden stop post (solid wood)',s,rect(s,G+WS['top']-bt),holes=[hole(s/2,G+zc-bt,bore,s-skin,'Enclosed stop magnet bore from the back face')],category='Purchased wood',note=f'Two posts from {s:g} x {s:g} mm hardwood strip, standing on B01 where the opened shells meet them at {WS["angle"]:g} degrees. '+enclosed(s-skin)+f' Drill two D{dd:g} x 8 dowel holes in the foot to match B01, glue the dowels and the foot, and drive one SC3 from below. Stick a 1 mm felt dot on the wall-side face. Round the top and paint it like a garden lamp post.')
    for group,sign,k,xc in (('WallRight',1,2,WS['contact_x']),('WallLeft',-1,9,width-WS['contact_x'])):
        wi=WALLS[k];o,u,n=wi['origin'],wi['u'],wi['w'];deg=sign*WS['angle']
        face=(o[0]+u[0]*xc+n[0]*wall,o[1]+u[1]*xc+n[1]*wall)   # steel disc centre on the outer face, walls closed
        pc=spin(face,(sign*hinge_x,0),deg);nn=spin(n,(0,0),deg);tt=spin(u,(0,0),deg)
        # The post's wall-side face lies parallel to the opened facet, WS gap in front of it, centred on the disc.
        # Its back face (the bore entry) points away from the wall.
        corner=(pc[0]+nn[0]*WS['gap']-tt[0]*s/2,pc[1]+nn[1]*WS['gap']-tt[1]*s/2)
        post=put('GP1',(corner[0],corner[1],bt),(tt[0],tt[1],0),(0,0,1))
        PARTS[wi['part']]['holes'].append(dict(hole(xc,zc-SL,MG['disc_pocket'][0],MG['disc_pocket'][1],'Steel disc recess for the garden stop, outer face'),id=f'H{len(PARTS[wi["part"]]["holes"])+1:02}'))
        foot=(corner[0]+(tt[0]+nn[0])*s/2,corner[1]+(tt[1]+nn[1])*s/2)
        PARTS['B01']['holes'].append(dict(hole(foot[0]+half,foot[1]+half,3.2,None,'SC3 stop-post screw clearance; countersink underside D6 x 1.5'),entry='bottom',countersink=6,countersink_depth=1.5,id=f'H{len(PARTS["B01"]["holes"])+1:02}'))
        # Two alignment dowels take the side load, so the end-grain screw only holds the post down. They lie on a
        # line parallel to the B01 quarter seam (along X), 7 mm either side of the screw: inside the post's foot at
        # any post angle, and on the same base quarter as the screw.
        for t_ in (-1,1):
            PARTS['B01']['holes'].append(dict(hole(foot[0]+7*t_+half,foot[1]+half,dd,dz,'Stop-post alignment dowel hole, blind from the top'),id=f'H{len(PARTS["B01"]["holes"])+1:02}'))
        FASTENERS.append({'id':f'FS-Stop-{group}','type':'SC3','diameter':3,'length':16,'head_diameter':6,'head_height':1.5,'origin':[foot[0],foot[1],0],'axis':[0,0,1],'parts':['B01-01',post['id']],'pilot':2.0,'pilot_depth':12,'note':f'3 x 16 mm countersunk wood screw up through B01 into the end grain of the stop post; the post is also glued and located by two D{dd:g} dowels.'})
        HARDWARE.append({'id':f'MG-Stop-{group}','kind':'Stop magnet','group':'Fixed','position':[pc[0]+nn[0]*(WS['gap']+skin),pc[1]+nn[1]*(WS['gap']+skin),G+zc],'height':MG['magnet'][1],'width':MG['magnet'][0],'enclosed':skin,'note':f'{mg} magnet enclosed in the GP1 post facing the {group} shell, {skin:g} mm behind its face.'})
        HARDWARE.append({'id':f'SD-Stop-{group}','kind':'Steel disc','group':group,'position':[face[0],face[1],G+zc],'height':MG['disc'][1],'width':MG['disc'][0],'note':f'Epoxied flush into the {wi["part"]} outer-face recess.'})
    # Structural posts entirely in the fixed rear half. The elevated floors also rest on metal supports fitted after
    # production (not modelled).
    add('P01','Continuous rear frame pillar',post_t,rect(post_width,3*pitch-base-12),color='wood',note=f'Four one-piece pillars on 12 mm foot blocks. Slide the two F01 levels over their rectangular openings, then seat F02 on the pillar tops. Cut from {post_t:g} mm plywood: the F01 openings are {post_t+CFG["fabrication"]["pillar_clearance"]:g} mm wide.')
    for x,y in posts:upright('P01',x,y,G+12,axis='xz')
    # Corner braces. A J01 rib spans three facets of one shell (the whole middle facet and GR onto each neighbour),
    # so one piece holds two corners at 150 degrees and ties the shell's facets into one stiff section; a corner no
    # rib can take gets a two-wall J02 bracket. Nothing crosses a hinge or the front seam. Ribs are chosen to hold
    # the most corners, then to sit on facets without windows, because a rib raised over a door crosses its whole
    # middle facet. A brace is a list of consecutive facets; the corner between facets f and f+1 is (f-2)%12.
    shells={}
    for f,w_ in enumerate(WALLS):shells.setdefault(w_['group'],[]).append(f)
    def corners_of(span):return [(f-2)%12 for f in span[:-1]]
    def windowed(f):return bool(PARTS[WALLS[f]['part']]['windows'])
    braces=[]
    for F in shells.values():
        start=next(f for f in F if (f-1)%12 not in F);F=sorted(F,key=lambda f:(f-start)%12)   # round the shell, even across facet 12 -> 1
        best=max((pick for r in range(len(F)-1) for pick in itertools.combinations(range(1,len(F)-1),r)
                  if all(abs(m-n)>1 for m,n in itertools.combinations(pick,2))),
                 key=lambda pick:(2*len(pick),-sum(windowed(F[m]) for m in pick),-len(pick)))
        held={c for m in best for c in (m-1,m)}
        braces+=[(F[m-1],F[m],F[m+1]) for m in best]+[(F[c],F[c+1]) for c in range(len(F)-1) if c not in held]
    def brace_height(span,level,dz):
        """Beside a ground-floor door the low brace moves up to the top of the door opening."""
        return door_h if level==0 and dz==gusset_dz[0] and set(corners_of(span))&door_corners else dz
    def placed_braces(level,dz):
        """The braces at one height. A rib raised over a door would cross a window in its middle facet, so it
        splits into two brackets there."""
        for span in braces:
            z=brace_height(span,level,dz)
            if len(span)==3 and z!=dz and any(oy<z+GT+1 and oy+wh>z-1 for _,oy,_,wh in PARTS[WALLS[span[1]]['part']]['windows'] if oy<pitch):
                yield from ((s,z) for s in (span[:2],span[1:]))
            else:yield span,z
    # One room divider per storey: front-to-back wall on the house axis with a cloth-tape hinged door.
    PT=CFG['partition'];xp=PT['x']
    yb=(a-wall-wall/2*math.cos(math.radians(75)))/math.sin(math.radians(75))-.5;yf=-yb+PT['front_gap']
    # The rear notches reach 0.5 mm past the braces' inner edge at the divider faces (both edges run RD inside the walls).
    notch=yb-((a-wall-RD-wall/2*math.sin(math.pi/12))/math.cos(math.pi/12)-.5)
    Lp=yb-yf;clear=pitch-base-PT['top_gap'];d0=PT['door_y']-yf;d1=d0+PT['door_width'];dh=PT['door_height']   # top_gap: play under the ceiling for thick floors
    rear=next(s for s in braces if 3 in corners_of(s))   # the brace holding the rear corner the dividers meet
    outline=[[0,0],[d0,0],[d0,dh],[d1,dh],[d1,0],[Lp,0]]
    for gz in gusset_dz:outline+=[[Lp,gz-.5],[Lp-notch,gz-.5],[Lp-notch,gz+GT+.5],[Lp,gz+GT+.5]]
    outline+=[[Lp,clear],[0,clear]]
    add('PT1','Room divider wall',wall,outline,color='cream',category='Walls',note=f'Three dividers, one per storey, {Lp:.1f} long and {clear:g} tall, leaving {PT["top_gap"]:g} mm under the ceiling for floors at the thick end of their band. The rear notches slip over the corner ribs; glue them to the ribs. The front edge stays {PT["front_gap"]:g} mm clear of the closing walls. The {PT["door_width"]:g} x {dh:g} doorway sits {d0:g} mm from the front end, next to the opening walls; a PD1 leaf hangs in it on cotton tape.')
    raised_rear=brace_height(rear,0,gusset_dz[0])!=gusset_dz[0]
    if raised_rear:
        ground_outline=[[0,0],[d0,0],[d0,dh],[d1,dh],[d1,0],[Lp,0]]
        for dz in gusset_dz:
            gz=brace_height(rear,0,dz)
            ground_outline+=[[Lp,gz-.5],[Lp-notch,gz-.5],[Lp-notch,gz+GT+.5],[Lp,gz+GT+.5]]
        ground_outline+=[[Lp,clear],[0,clear]]
        PARTS['PT1']['note']=PARTS['PT1']['note'].replace('Three dividers, one per storey,','Two upper-storey dividers,')
        add('PT2','Room divider wall with raised rib clearance',wall,ground_outline,color='cream',category='Walls',note=PARTS['PT1']['note'].replace('Two upper-storey dividers,','One ground-floor divider,')+' The lower rear notch clears the rib raised above the veranda door.')
    for k in range(3):put('PT2' if raised_rear and k==0 else 'PT1',(xp-wall/2,yf,tops[k]),(0,1,0),(0,0,1))
    # Room doors: a 3 mm leaf in each doorway, flush with the divider's +X face, hung on a cotton-tape hinge at the
    # doorway's rear jamb. It swings 90 degrees into the +X room; no metal and no spring.
    lw,lh,lt=PT['door_width']-2,dh-2,T['detail'];hy=PT['door_y']+PT['door_width']
    add('PD1','Room door leaf',lt,rect(lw,lh),color='cream',category='Walls',note=f'Three leaves, one per divider doorway. Hinge each on two 15 mm cotton-tape strips glued to the leaf and the doorway\'s rear jamb (the tape folds round the 1 mm gap). It swings 90 degrees into the right-hand room; the figures are placed clear of its swing.')
    for k in range(3):
        leaf=put('PD1',(xp+wall/2,hy-1,tops[k]+1),(0,-1,0),(0,0,1),'RoomDoors')   # thickness toward -X, inside the doorway
        HARDWARE.append({'id':f'HG-Room-{k}','kind':'Room door hinge','group':'RoomDoors','position':[xp+wall/2,hy,tops[k]+1+lh/2],'height':lh,'width':15,'door':leaf['id'],'moves_with':[leaf['id']],'outward':[1,0],'note':'Two cotton-tape strips, 15 mm wide.'})
        DOOR_SWEEPS.append(([xp,hy-1-lw-1,tops[k]],[xp+wall/2+lw+1,hy,tops[k]+lh+1]))
    from architecture import entrances_and_veranda, dormer
    entrances_and_veranda(globals(),width,a,bt,pu,pv,pn,po,G)
    # Roof panels are planar triangles, not fake mesh sheets.
    FIN=CFG['finial'];finial_height=3+FIN['ball']   # R03 cap, then a smooth wooden ball
    roof_z=G+H;roof_peak=CFG['height']-CFG['fabrication']['base_lift']-finial_height;roof_h=roof_peak-roof_z
    roof_a=CFG['roof_diameter']/2*math.cos(math.pi/12)-3*roof_h/math.hypot(CFG['roof_diameter']/2*math.cos(math.pi/12),roof_h)
    slant=math.hypot(roof_a,roof_h);rw=2*roof_a*math.tan(math.pi/12)-2
    topcut=3*roof_a/roof_h;topwidth=rw*topcut/slant
    add('R01','Roof triangular panel',3,[[0,0],[rw,0],[rw/2+topwidth/2,slant-topcut],[rw/2-topwidth/2,slant-topcut]],color='red',category='Roof',note='Eleven standard panels plus special R06. Assemble over the roof-angle jig; glue interior cloth seam tapes, then fill and paint exterior seams.')
    from architecture import dormer_layout,dormer_angles
    cleat_r=q(170)
    roof={'z':roof_z,'h':roof_h,'a':roof_a,'slant':slant,'rw':rw,'scale':scale,'cleat_r':cleat_r}
    dormer_cut=dormer_layout(roof,CFG)['cut'];dcw=dormer_cut[1][0]-dormer_cut[0][0];dch=dormer_cut[2][1]-dormer_cut[0][1]
    dormer_panels={round((angle+75)/30)%12 for angle in dormer_angles(CFG)}
    over=' and '.join(CFG['dormer']['over'])
    add('R06','Roof panel with attic dormer opening',3,PARTS['R01']['outer'],[dormer_cut],color='red',category='Roof',note=f'{len(dormer_panels)} special panels, above {over}, each with a {dcw:g} x {dch:.1f} dormer opening just above the eave cleats. Cut while supported; the dormer sides stand on the skin beside it.')
    PARTS['R01']['note']=PARTS['R01']['note'].replace('Eleven standard panels plus special R06',f'{12-len(dormer_panels)} standard panels plus {len(dormer_panels)} special R06')
    for j in range(12):
        th=math.radians(-75+j*30);n=(math.cos(th),math.sin(th));u=(-n[1],n[0],0);v=(-n[0]*roof_a/slant,-n[1]*roof_a/slant,roof_h/slant)
        put('R06' if j in dormer_panels else 'R01',(n[0]*roof_a-u[0]*rw/2,n[1]*roof_a-u[1]*rw/2,roof_z),u,v,'Roof')
    dormer(globals(),roof)
    # Eave backing ring kept below the sloping skins, seated on short roof support blocks.
    ringr=q(182)
    add('R02','Roof eave reinforcement ring',3,poly(12,ringr,ringr,ringr),[poly(12,ringr-16,ringr,ringr)],color='red',category='Roof',note='Divided into three 120-degree sections. Glue to 12 padded internal cleats at the eave. Ring lifts off with roof; do not glue to fixed walls.')
    put('R02',(-ringr,-ringr,roof_z),group='Roof')
    add('R03','Roof top cap',3,poly(12,7,7,7),color='red',category='Roof');put('R03',(-7,-7,roof_peak),group='Roof')
    # A smooth ball, not a spire: nothing pointed at a toddler's eye height.
    br=FIN['ball']/2;fd,fl=FIN['dowel']
    add('FN01','White roof finial ball (turned wood)',FIN['ball'],poly(36,br,br,br),holes=[dict(hole(br,br,fd,fl/2,f'D{fd:g} dowel hole'),entry='bottom')],color='cream',category='Purchased wood',note=f'One D{FIN["ball"]:g} mm turned beech ball with a flat sanded on it; glue it on a D{fd:g} x {fl:g} dowel set into the cone apex through R03. Blunt by design: never replace it with a spire. Never lift the roof by it.')
    PARTS['FN01']['sphere']=br
    put('FN01',(-br,-br,roof_peak+3),group='Roof')
    cleat_z=roof_z+3;cleat_run=roof_a*(1-3/roof_h)-cleat_r;cleat_rise=roof_h*(1-cleat_r/roof_a)-3
    add('R04','Roof sloping support cleat',12,[[0,0],[cleat_run,0],[0,cleat_rise]],color='red',category='Purchased wood',note='Twelve triangular cleats cut from 12 mm solid wood. Glue bottom to roof ring and slope to roof skin. Wood grain along the sloping edge.')
    for j in range(12):
        th=math.radians(-75+j*30);n=(math.cos(th),math.sin(th));u=(n[0],n[1],0);v=(0,0,1);t=(n[1],-n[0],0)
        put('R04',(n[0]*cleat_r-t[0]*6,n[1]*cleat_r-t[1]*6,cleat_z),u,v,'Roof')
    # A temporary gauge needs no plywood: 2 mm greyboard, cut by hand on its 1:1 template.
    add('R05','Roof assembly angle jig (card)',2.0,[[0,0],[roof_a,0],[0,roof_h]],color='wood',category='Purchased packing',note='Two temporary jigs of 2 mm greyboard (bookbinding board): glue the printed 1:1 template on with removable adhesive and cut along the line with a sharp knife and a steel rule. Do not install in finished attic; use them to check roof slope before gluing.')
    # Chimney is attached to a roof panel above rear side (small, lightweight hollow box).
    def roofoutside(x,y):return roof_peak-(roof_h/roof_a)*(x+y)/math.sqrt(2)+3*slant/roof_a
    chimney_x,chimney_y,chimney_width=q(64),q(66),q(21)
    ctop=roofoutside(chimney_x,chimney_y)+q(53)
    for pid,x,y,length,axis,ref in [('CH01',chimney_x,chimney_y+3,chimney_width,'xz',chimney_y),('CH02',chimney_x,chimney_y+chimney_width,chimney_width,'xz',chimney_y+chimney_width-3),('CH03',chimney_x,chimney_y+3,chimney_width-6,'yz',chimney_x),('CH04',chimney_x+chimney_width-3,chimney_y+3,chimney_width-6,'yz',chimney_x+chimney_width-3)]:
        z0=roofoutside(x,ref) if axis=='xz' else roofoutside(ref,y)
        z1=roofoutside(x+length,ref) if axis=='xz' else roofoutside(ref,y+length)
        add(pid,'Chimney '+pid[-2:]+' sloped side',3,[[0,z0],[length,z1],[length,ctop],[0,ctop]],color='cream',category='Exterior',note='Short lower edge seats on roof. Sand across 3 mm thickness to match roof slope.')
        upright(pid,x,y,min(z0,z1),group='Roof',axis=axis)
    # 7 mm overhang all round: at 33.6 mm square the cap is too big to swallow if it ever came off.
    add('E07','Chimney cap',3,rect(chimney_width+14,chimney_width+14),color='red',category='Exterior')
    put('E07',(chimney_x-7,chimney_y-7,ctop),group='Roof')
    from architecture import battens_and_ladder,plinth_and_garden
    battens_and_ladder(globals(),G,roof_z)
    plinth_and_garden(globals(),G,bt)
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
    garden(G,bt)
    place_figures(tops,a-wall)
    # Brace plan outlines, in a frame whose x axis is the outer normal through the middle of the brace: along the
    # wall faces (`reach` from the end corners, through every corner held), then back along the inner edge RD inside.
    ai=a-wall;vr=ai/math.cos(math.pi/12);cos15=math.cos(math.pi/12)
    def brace_outline(n,reach):
        N=[math.radians(30*k-15*(n-1)) for k in range(n)];C=[x+math.pi/12 for x in N[:-1]]
        def at(angle,r):return [r*math.cos(angle),r*math.sin(angle)]
        def leg(k,corner):   # reach from the corner along facet k, toward its middle
            c,m=at(corner,vr),at(N[k],ai);l=math.hypot(m[0]-c[0],m[1]-c[1]);return [c[0]+(m[0]-c[0])*reach/l,c[1]+(m[1]-c[1])*reach/l]
        def inside(p,k):return [p[0]-RD*math.cos(N[k]),p[1]-RD*math.sin(N[k])]
        s,e=leg(0,C[0]),leg(n-1,C[-1])
        edge=[s]+[at(c,vr) for c in C]+[e]
        return edge,edge+[inside(e,n-1)]+[at(c,vr-RD/cos15) for c in C[::-1]]+[inside(s,0)]
    # A brace raised over a door keeps the short GS legs: at door height they pass beside the windows.
    placed=[(k,span,z,GS if z!=dz else GR) for k in range(3) for dz in gusset_dz for span,z in placed_braces(k,dz)]
    kinds=Counter((len(span),reach) for _,span,_,reach in placed);mid=2*ai*math.tan(math.pi/12)-1
    heights=f'Low braces start {gusset_dz[0]:.1f} mm above their floor, upper ones {pitch-base-gusset_dz[1]:.1f} mm below the ceiling. '
    BRACES={(3,GR):('J01','Three-wall corner rib',f'Each spans three facets of one shell: its outer edge glues along the whole middle facet ({mid:.0f} mm) and {GR-.5:.1f} mm onto both neighbours, so one rib holds two corners at 150 degrees. Dry-fit it first: it sets both corner angles, so glue all three walls to it in one go. Its inner edge runs {RD:.1f} mm inside the walls, clear of the rear pillars. '+heights),
            (2,GR):('J02','Two-wall corner bracket',f'For the corner no rib holds. Both long edges glue against the walls, {GR-.5:.1f} mm along each. '+heights),
            (3,GS):('J03','Three-wall corner rib with short legs',f'The J01 rib for the low position beside a ground-floor door, {door_h:.1f} mm up, just above the door opening: its legs reach only {GS-.5:.1f} mm onto the neighbours, clear of the windows beside the door.'),
            (2,GS):('J04','Two-wall corner bracket with short legs',f'The J02 bracket for the low position beside a ground-floor door, {door_h:.1f} mm up, just above the door opening: {GS-.5:.1f} mm along each wall, clear of the window beside it.')}
    for (n,reach),(pid,name,note) in BRACES.items():
        if kinds[(n,reach)]:add(pid,name,GT,brace_outline(n,reach)[1],color='blue',category='Walls',note=f'{kinds[(n,reach)]} pieces of {GT:g} mm plywood laid flat. '+note)
    for k,span,z,reach in placed:
        pid=BRACES[(len(span),reach)][0];edge,_=brace_outline(len(span),reach)
        group=WALLS[span[0]]['group'];z0=tops[k]+z+(SL if group!='Fixed' else 0)
        th=math.radians(facet_angle(f'W{span[1]+1:02}') if len(span)==3 else 30*corners_of(span)[0])
        c,s_=math.cos(th),math.sin(th);u=(c,s_,0);v=(-s_,c,0)
        def world(p):return (c*p[0]-s_*p[1],s_*p[0]+c*p[1])
        x0,y0=PARTS[pid]['origin_shift'];o=world((x0,y0))
        inst=put(pid,(o[0],o[1],z0),u,v,group)
        # One glued joint per wall face the brace touches; the walls stop 0.5 mm short of each corner.
        for f,(p,q_) in zip(span,zip(edge,edge[1:])):
            l=math.hypot(q_[0]-p[0],q_[1]-p[1]);d=((q_[0]-p[0])/l,(q_[1]-p[1])/l)
            if f!=span[0]:p=[p[0]+d[0]*.5,p[1]+d[1]*.5]
            if f!=span[-1]:q_=[q_[0]-d[0]*.5,q_[1]-d[1]*.5]
            (sx,sy),(tx,ty)=world(p),world(q_);na=math.radians(facet_angle(f'W{f+1:02}'))
            JOINTS.append({'id':f'J-Corner-{pid}-{span[1]}-{k}-{z:g}-{f}','type':'J2 corner rib joint','parts':[inst['id'],WALLS[f]['id']],'position':[(sx+tx)/2,(sy+ty)/2,z0+GT/2],'axis':[math.cos(na),math.sin(na),0],'outline':[[sx,sy,z0],[tx,ty,z0],[tx,ty,z0+GT],[sx,sy,z0+GT]],'glue':f'PVA on the {math.hypot(tx-sx,ty-sy):.1f} x {GT:g} mm edge face. Keep the corners at 150 degrees during cure.','contact_area_mm2':round(math.hypot(tx-sx,ty-sy)*GT,1)})
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
    # Window counts per wall level from the window openings (four panes each), plus the dormer windows.
    windows=[0,0,0]
    for pid,p in PARTS.items():
        if p['category']=='Walls' and pid.startswith('W'):
            for x,y,w,h in p.get('windows',[]):windows[int(y//pitch)]+=p['quantity']
    windows.append(len(PARTS['DM01']['windows'])*PARTS['DM01']['quantity'])
    # One table of display offsets shared by the STEP exports and the preview renders.
    # The veranda is permanent: it stays put when the walls open and only moves outward in the exploded view.
    travel=DR['travel']
    views={'open_angle':WS['angle'],'open':{'Roof':[0,0,300],'Drawer':[e_out[0]*travel,e_out[1]*travel,0]},'exploded':{'WallRight':[230,-40,0],'WallLeft':[-230,-40,0],'Roof':[0,0,420],'Porch':[pn[0]*150,pn[1]*150,0],'Furniture':[0,-80,0],'Figures':[0,-80,0],'Drawer':[e_out[0]*250,e_out[1]*250,0]}}
    # Dimension annotations for the 3D viewer: lines (a-b, optional extension lines), level marks and labels.
    total=roof_peak+finial_height;deck_top=G+T['structure'];dims=[]
    def dim(label,a,b,ext=(),group=None):dims.append({'kind':'line','label':label,'a':list(a),'b':list(b),'ext':[list(map(list,e)) for e in ext],'group':group})
    def mark(label,p,group=None):dims.append({'kind':'label','label':label,'p':list(p),'group':group})
    sx,sy=Ap+40,40
    dim(f'{total:g} total height',(-half-30,60,0),(-half-30,60,total))
    dim(f'D{2*half:g} green base',(-half,-half-40,0),(half,-half-40,0),[((-half,0,0),(-half,-half-40,0)),((half,0,0),(half,-half-40,0))])
    dim(f'Plinth {G:g} (base {bt:g} + stone {PL["height"]:g})',(0,-Ap-25,0),(0,-Ap-25,G))
    names=['Ground floor','Floor 1','Floor 2','Attic floor']
    for k in range(3):dim(f'{pitch:g}',(sx,sy,tops[k]),(sx,sy,tops[k+1]))
    for k,z in enumerate(tops):mark(f'{names[k]} Z{z:g}',(sx+10,sy,z))
    dim(f'Roof {roof_h:.0f} (about {math.degrees(math.atan(roof_h/roof_a)):.0f} degrees)',(sx,sy,roof_z),(sx,sy,roof_peak))
    dim(f'{finial_height:g} finial',(sx,sy,roof_peak),(sx,sy,total))
    mark(f'Eave Z{roof_z:g}',(sx+10,sy,roof_z));mark(f'Top Z{total:g}',(sx+10,sy,total))
    dim(f'Drawer pulls out {travel:g}',(*dpt(r0,hw+30),bt),(*dpt(r0+travel,hw+30),bt),[((*dpt(r0,0),bt),(*dpt(r0,hw+30),bt))])
    drawer_depth=rho_face(0)-back
    mark(f'Hidden drawer {2*hw:g} x {drawer_depth:.0f} x {dh_:g} (inside {2*hw-2*db:g} x {drawer_depth-db:.0f} x {dh_-4:g})',(*dpt((rho_face(0)+back)/2,0),bt+dh_+4),'Drawer')
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
    doorways=[{'name':f'Main entrance ({doors["main"]})','width':door_w,'height':door_h-sill},{'name':f'Veranda door ({doors["veranda"]})','width':door_w,'height':door_h-sill},{'name':f'Back door ({doors["back"]})','width':BD['width'],'height':door_h-sill},{'name':'Room divider doorway (PT1)','width':PT['door_width'],'height':PT['door_height']}]
    cw,chh=CFG['figures']['door_clearance'];fit=[]
    for f in FIGURES:
        st=clay.stats(f['key']);narrow=min(st['width'],st['length'])
        for dw in doorways:fit.append({'figure':f['name'],'doorway':dw['name'],'figure_width':round(narrow,1),'figure_height':round(st['height'],1),'spare_width':round(dw['width']-narrow,1),'spare_height':round(dw['height']-st['height'],1),'fits':dw['width']-narrow>=cw and dw['height']-st['height']>=chh})
    side=['right','back-right','back','back-left','left','front-left','front','front-right'][round(DR['direction']%360/45)%8]
    D=CFG['dormer'];dw_,dh2=D['window']
    changes=[f'Two attic dormers, over {" and ".join(D["over"])}: one beside the veranda next to the chimney, one on the opposite side above the main door. Each stands just above the eave cleats (about 70 mm lower than before), {D["front_width"]:g} mm wide with a {dw_:g} x {dh2:.0f} mm window (were 34 mm and 17 x 24), inside one roof panel',
      'Rope ladder from the veranda roof up to the eave beside the veranda-side dormer, one plywood piece glued on the corner batten',
      'Windows keep a solid cross in the wall between four panes, with a one-piece surround (frame, sill and pediment hood) and clear PET glazing: no thin glued bars to snap',
      'Nine 3 x 8 mm battens cover the outside corner seams that do not move (board-and-batten look)',
      f'Back door on {doors["back"]} with a lean-to canopy, stone steps and a woodpile shelter; room door leaves on cotton-tape hinges',
      'Snufkin, the Snork Maiden and Little My join the family in clay; no figure fits the small-parts cylinder and each passes every doorway',
      f'Toy safety: every magnet enclosed in solid wood behind a {CFG["magnets"]["skin"]:g} mm skin; a D{CFG["finial"]["ball"]:g} ball finial instead of the spire; divider front gap {PT["front_gap"]:g} mm (outside the 5-12 mm pinch range); recessed finger pulls instead of glued handles; a captive drawer stop',
      f'Strength: 9 mm roof turn-buttons (6 + 3 mm plies glued) between D12 fender washers; 2.0 x 10 door-hinge screws in 16 mm hardwood strips; 2.5 x {next(f["length"] for f in FASTENERS if f["type"]=="SC1"):g} wall-hinge wood screws into D1.8 pilots; stop posts on two dowels each',
      f'Stability: {CFG["stability"]["pads"]} rim pads under the base, steel ballast in the plinth and an anti-tip strap anchor in the rear shell; the opening shells hang {SL:g} mm above the plinth',
      f'CNC: finger joints with a fit clearance and cutter relief at every inside corner in both F01 and F02; {CFG["fabrication"]["floor_support"][0]:g} x {CFG["fabrication"]["floor_support"][1]:g} mm seam strips',
      'Optional LED lighting: a wire hole through every floor; faux cellar hatch on the plinth',
      'Display only: tiled stove, chandelier, bathtub, attic bed and desk, and a garden scene round the base']
    new={'DM06','GZ1','GZ2','WF1','RL1','E04','E11','GD03','GD04','PD1','DS1','HC1','WP1','WP2','WP3','BL2','AB1'}|{k for k in PARTS if k.startswith('BT')}
    changed={'R06','R01','DM01','DM02','DM04','DM05','FN01','E01','A02','A03','E07','MC1','GP1','DR1','F00','F01','F02','B01','PT1','PT2'}|{k for k in PARTS if k.startswith('W') and PARTS[k]['category']=='Walls'}
    for pid,p in PARTS.items():
        if pid in new:p['revision']='new'
        elif pid in changed:p['revision']='changed'
    derived={'views':views,'doorways':doorways,'figure_fit':fit,'dimensions':dims,'changes':changes,'figures':list(FIGURES),'drawer':{'direction':list(e_out),'side':side,'angle':DR['direction'],'travel':travel,'width':2*hw,'depth':drawer_depth,'height':dh_},'plinth_height':PL['height'],'ground_floor':G,'total_height':total,'wall_width':width,'floor_radius':floor_r,'roof_slant':slant,'roof_panel_width':rw,'floor_tops':tops,'clear_room_height':pitch-base,'hinge_axes':{'WallRight':[hinge_x,0],'WallLeft':[-hinge_x,0]},'roof_eave':roof_z,'windows_per_floor':windows,'veranda_size':[ver['width'],ver['depth']],'braces':[list(s) for s in braces],'veranda_facet':ver['facet'],'base_thickness':bt,'facets':[{'facet':k+1,'part':w['part'],'id':w['id'],'group':w['group']} for k,w in enumerate(WALLS)],'doors':doors,'reference_style':f'original/ photos: red hipped veranda on {ver["facet"]} ({facet_angle(ver["facet"])} degrees), white shaped columns and railings, gabled main entrance on {doors["main"]}'}
    data={'config':CFG,'parts':PARTS,'instances':INSTANCES,'hardware':HARDWARE,'fasteners':FASTENERS,'joints':JOINTS,'derived':derived,'clay':figs}
    from fabrication import redesign_panels
    redesign_panels(data)
    # Match the supplier cut file, after fabrication has split and consolidated the profiles.
    from dxf_r12 import COLOURS, ACI_RGB, thickness_layer
    for p in data['parts'].values():
        if p.get('render_only') or p['category'] in BOUGHT or (p.get('optional') and not CFG.get('supplier',{}).get('include_optional',False)):continue
        layer=thickness_layer(p['thickness']);aci=COLOURS[layer]
        p['dxf']={'layer':layer,'aci':aci,'color':ACI_RGB[aci]}
    return data

def fabrication_parts(data):
    """Only profiles that belong in CAD plans, cutting files and the build inventory."""
    return {pid:p for pid,p in data['parts'].items() if not p.get('render_only')}

def profile_variants(p):
    """Manufacturing signatures under in-plane quarter turns, with each frame's transform.

    Match full profiles, not bounding boxes. Winding, vertex start and drilling order
    do not change a part. Face-specific holes and countersink depths do.
    """
    stock=p['category'] if p['category'] in BOUGHT else 'Plywood'
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
FIGURE_CODES={'pappa':'FG1','mamma':'FG2','troll':'FG3','snufkin':'FG4','snorkmaiden':'FG5','littlemy':'FG6'}
def place_figures(tops,inner):
    """Stand the thermo-clay figures on their storeys (config figures.levels) in the front-most free spot, so
    they are seen when the walls open, turned a little toward the middle. Clear of furniture, posts, the
    divider, each other and the room doors' swing."""
    import clay
    fc=CFG['figures'];codes=FIGURE_CODES
    obstacles=[instance_box(i) for i in INSTANCES if i['group'] in ('Fixed','Furniture','RoofLocks','Drawer','RoomDoors') and (PARTS[i['part']]['category'] not in ('Walls','Exterior') or i['part'] in ('PT1','PT2')) and i['part'] not in ('F00','F01','F02')]
    obstacles+=[sweep for sweep in DOOR_SWEEPS]
    cands=sorted(((x,y) for x in range(-130,131,4) for y in range(-130,121,4)),key=lambda c:(c[1],abs(c[0])))
    for level,key in ((level,key) for level,keys in enumerate(fc['levels']) for key in keys):
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
        th=math.radians(yaw);pts=[(cx+x*math.cos(th)-y*math.sin(th),cy+x*math.sin(th)+y*math.cos(th)) for x,y in hull];xs,ys=zip(*pts)
        obstacles.append(([min(xs),min(ys),z],[max(xs),max(ys),z+h]))
        FIGURES.append({'id':f'{codes[key]}-01','code':codes[key],'key':key,'name':clay.NAMES[key],'level':level,'room':f'{ROOMS[level][0].capitalize()}, {ROOMS[level][1]}','where':f'in the {ROOMS[level][1]} on the {ROOMS[level][0]}','x':cx,'y':cy,'z':z,'yaw':yaw,'height':round(h,1),'top':[cx,cy,z+h],'revision':'new'})

def garden(G,bt):
    """Garden scene around the base for the renders and the viewer: a lantern on each stop post and, on the lawn
    beyond the base where the opening walls never reach, a well, a bathing hut, Snufkin's tent, a rowing boat, a
    small bridge and a mailbox. Display only, like the furniture; each is a few stacked solids."""
    def solid(pid,name,outline,t,color,o,ang,x,y,z,plane='xy'):
        # 'xy': outline in the item's plan, extruded up. 'yz': outline across the item (y, z), extruded along x.
        if pid not in PARTS:add(pid,name,t,outline,color=color,category='Furniture')
        c,s_=math.cos(math.radians(ang)),math.sin(math.radians(ang));X,Y=(c,s_,0),(-s_,c,0)
        at=(o[0]+c*x-s_*y,o[1]+s_*x+c*y,z)
        return put(pid,at,X,Y,'Garden') if plane=='xy' else put(pid,at,Y,(0,0,1),'Garden')
    # Lanterns: a small block on the centre of each post top, inside its footprint so the walls still meet the post.
    if 'GL01' not in PARTS:add('GL01','Post lantern',14,rect(10,10),color='ochre',category='Furniture')
    for inst in [i for i in INSTANCES if i['part']=='GP1']:
        o,u,w=inst['origin'],inst['u'],inst['w'];h=PARTS['GP1']['height'];sz=PARTS['GP1']['width']
        put('GL01',(o[0]+u[0]*sz/2+w[0]*sz/2-5,o[1]+u[1]*sz/2+w[1]*sz/2-5,o[2]+h),group='Furniture')
    o,a=(240,330),0   # well: stone ring, two posts, a little roof (clear of the drawer's path)
    solid('GW1','Well wall',poly(12,18,18,18),26,'stone',o,a,-18,-18,0)
    for dy in (-16,12):solid('GW2','Well post',rect(4,4),36,'wood',o,a,-2,dy,26)
    solid('GW3','Well roof',[[0,0],[44,0],[22,14]],30,'red',o,a,-15,-22,62,'yz')
    o,a=(120,370),-20   # bathing hut: body and roof
    solid('GH1','Bathing hut',rect(50,40),60,'blue',o,a,0,0,0)
    solid('GH2','Bathing hut roof',[[-3,0],[43,0],[20,16]],54,'red',o,a,-2,0,60,'yz')
    o,a=(-170,345),15   # Snufkin's tent
    solid('GT1',"Snufkin's tent",[[0,0],[44,0],[22,30]],60,'green',o,a,0,0,0,'yz')
    o,a=(-350,160),70   # rowing boat
    solid('GB1','Rowing boat',[[0,10],[12,0],[70,0],[86,10],[70,20],[12,20]],9,'blue',o,a,0,0,0)
    o,a=(-330,-60),100   # small bridge: abutments, deck, rails
    for x in (0,52):solid('GG1','Bridge abutment',rect(18,26),14,'stone',o,a,x,0,0)
    solid('GG2','Bridge deck',rect(70,26),4,'wood',o,a,0,0,14)
    for y in (0,23):solid('GG3','Bridge rail',[[0,0],[3,0],[3,10],[0,10]],70,'cream',o,a,0,y,18,'yz')
    o,a=(-80,-330),0   # mailbox
    solid('GX1','Mailbox post',rect(6,6),46,'wood',o,a,-3,-3,0)
    solid('GX2','Mailbox',rect(20,14),12,'red',o,a,-10,-7,46)

def furnish(tops):
    def part(pid,name,w,h,t=4,color='wood',note=''):
        if pid not in PARTS:add(pid,name,t,rect(w,h),color=color,category='Furniture',note=note)
    def box(prefix,name,x,y,z,w,d,h,color='cream',shelves=0,group='Furniture',has_back=True,has_shelves=True,has_top=True):
        part(prefix+'A',name+' side',d,h,color=color)
        if has_shelves:
            part(prefix+'B',name+' top / bottom / shelf',w-8,d-3,color=color)
            levels=[z]+([z+h-4] if has_top else [])+[z+(j+1)*(h-8)/(shelves+1) for j in range(shelves)]
            for zz in levels:put(prefix+'B',(x+4,y,zz),group=group)
        if has_back:
            part(prefix+'C',name+' back',w-8,h-8,3,color)
            upright(prefix+'C',x+4,y+d,z+4,group)
        upright(prefix+'A',x,y,z,group,axis='yz');upright(prefix+'A',x+w-4,y,z,group,axis='yz')

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
    # Room layouts per storey; the divider runs along X0 with its door opening at Y-107 to -69 swinging into +X.
    g,f1,f2,at=tops

    book_colors=['red','blue','ochre','sage','rose','ink']
    for c in book_colors:
        part(f'BK_{c}',f'Book block {c}',16,13,3,color=c)
    def wall_shelf(prefix,name,y,z,w,d,h,side='left',shelves=3,color='wood',books=True):
        """Bookshelf against the room divider along X=0 (design units, scaled with the furniture).
        The divider is 6 mm thick, so a back face at |X| = 4 design units (3.7 mm) leaves 0.7 mm clear.
        Two gables (4 thick) at the ends y..y+4 and y+w-4..y+w, the 3 mm back against the divider between them,
        and the shelves in front of the back. side='left' stands in the -X room, 'right' in the +X room.
        w runs along Y from y to y+w; d is the full depth from the divider; h is the height.
        """
        part(prefix+'A',name+' gable end',d,h,color=color)
        part(prefix+'B',name+' shelf / top / bottom',d-3,w-8,color=color)
        part(prefix+'C',name+' back panel',w-8,h-8,3,color=color)
        shelf_zs=[z]+[z+(j+1)*(h-8)/(shelves+1) for j in range(shelves)]
        if side=='left':
            upright(prefix+'A',-4-d,y+4,z,'Furniture',axis='xz')
            upright(prefix+'A',-4-d,y+w,z,'Furniture',axis='xz')
            upright(prefix+'C',-7,y+4,z+4,'Furniture',axis='yz')
            for zz in shelf_zs+[z+h-4]:
                put(prefix+'B',(-4-d,y+4,zz),group='Furniture')
            if books:
                bx=-4-d+3
                p_off=sum(ord(ch) for ch in prefix)
                for s_idx,sz in enumerate(shelf_zs):
                    n_books=max(3,min(6,int((w-16)/8)))
                    for k in range(n_books):
                        bc=book_colors[(k+s_idx*2+p_off)%len(book_colors)]
                        put(f'BK_{bc}',(bx,y+10+k*5,sz+4),(1,0,0),(0,0,1),group='Furniture')
        else:
            upright(prefix+'A',4,y+4,z,'Furniture',axis='xz')
            upright(prefix+'A',4,y+w,z,'Furniture',axis='xz')
            upright(prefix+'C',4,y+4,z+4,'Furniture',axis='yz')
            for zz in shelf_zs+[z+h-4]:
                put(prefix+'B',(7,y+4,zz),group='Furniture')
            if books:
                bx=9
                p_off=sum(ord(ch) for ch in prefix)
                for s_idx,sz in enumerate(shelf_zs):
                    n_books=max(3,min(6,int((w-16)/8)))
                    for k in range(n_books):
                        bc=book_colors[(k+s_idx*2+p_off)%len(book_colors)]
                        put(f'BK_{bc}',(bx,y+10+k*5,sz+4),(1,0,0),(0,0,1),group='Furniture')

    # Ground floor: Bookbindery & Reading Parlour along inner room wall
    box('K2','Cooker',-125,36,g,44,37,48,'cream',has_back=False)
    add('K7','Cooker burner discs',3,poly(12,5,5,5),color='ink',category='Furniture')
    for x,y in [(-118,43),(-100,43),(-118,61),(-100,61)]:put('K7',(x,y,g+48),group='Furniture')

    # Shelves along inner room wall (Ground floor)
    wall_shelf('GL1','Bookbindery tools and materials bookcase',-65,g,65,26,92,side='left',shelves=3,color='wood',books=False)
    wall_shelf('GL2','Card catalog shelving unit',10,g,55,26,88,side='left',shelves=3,color='ochre',books=False)

    wall_shelf('GR1','Tea parlour library bookcase',-60,g,75,24,100,side='right',shelves=4,color='wood',books=False)
    wall_shelf('GR2','Poetry and folio shelving',30,g,60,24,88,side='right',shelves=3,color='sage',books=False)

    # Floor 1: Grand Circular Library along inner room wall
    wall_shelf('L1L','Grand library west bookcase',-65,f1,80,26,110,side='left',shelves=4,color='wood')
    wall_shelf('L1M','Grand library north bookcase',30,f1,75,26,110,side='left',shelves=4,color='wood')

    wall_shelf('L1R','Reference collection bookcase',-60,f1,80,24,104,side='right',shelves=4,color='ochre')
    wall_shelf('L1S','Encyclopedic stacks bookcase',35,f1,70,24,104,side='right',shelves=4,color='cream')

    part('SS1A','Library step stringer',28,26,4,'wood');part('SS1B','Library step tread',18,14,4,'wood')
    upright('SS1A',-72,-50,f1,'Furniture',axis='yz');upright('SS1A',-50,-50,f1,'Furniture',axis='yz')
    put('SS1B',(-68,-50,f1+8),group='Furniture');put('SS1B',(-68,-36,f1+20),group='Furniture')

    part('LC1A','Lectern column',8,42,4,'wood');part('LC1B','Lectern base',24,24,4,'wood')
    part('LC1C','Lectern reading deck',32,24,3,'ochre')
    put('LC1B',(60,-30,f1),group='Furniture');upright('LC1A',68,-26,f1+4,'Furniture')
    put('LC1C',(56,-30,f1+46),group='Furniture')

    # Floor 2: Moominpappa’s Memoir Study & Scriptorium along inner room wall
    box('U4','Dresser',-95.5,-112.5,f2,48,28,44,'cream',1,has_back=False)   # clear of the W11 corner rib

    wall_shelf('L2L','Memoir manuscript bookcase',-65,f2,80,26,106,side='left',shelves=4,color='wood')
    wall_shelf('L2M','Autobiographical archives bookcase',30,f2,70,26,106,side='left',shelves=4,color='ochre')

    part('ST1A','Sorting tower gable',26,18,3,'sage');part('ST1B','Sorting tower shelf',19,16,3,'cream')
    upright('ST1A',-89.5,-111.5,f2+44,'Furniture',axis='yz');upright('ST1A',-67.5,-111.5,f2+44,'Furniture',axis='yz')
    for s_idx in range(3):put('ST1B',(-86.5,-111.5,f2+44+s_idx*7.5),group='Furniture')

    wall_shelf('L2R','Scholarly research bookcase',-60,f2,80,24,102,side='right',shelves=4,color='sage')
    wall_shelf('L2S','Cartographic journal bookcase',35,f2,70,24,102,side='right',shelves=4,color='wood')

    # Attic: Cartographer’s Garret
    box('AC1','Archival document chest',46,-42,at,46,26,30,'wood')
    part('AC1R','Curved chest lid rib',44,10,3,'ochre')
    upright('AC1R',47,-18,at+30,'Furniture')

    part('SB1A','Scroll bin wall',16,32,3,'ochre');part('SB1B','Scroll bin bottom',24,24,3,'wood');part('SB1C','Rolled scroll bundle',18,36,3,'cream')
    put('SB1B',(14,-26,at),group='Furniture');upright('SB1A',18,-23,at+3,'Furniture');upright('SB1A',18,-2,at+3,'Furniture');upright('SB1C',17,-11,at+3,'Furniture')

    # Living room (floor 1): a tiled stove (kakelugn) in the left room and a chandelier over the right room.
    part('KS1A','Tiled stove side',30,100,4,'cream');part('KS1B','Tiled stove front / back',22,100,4,'cream')
    part('KS1C','Tiled stove crown',36,36,4,'sage');part('KS1D','Tiled stove plinth',34,34,4,'ochre');part('KS1E','Tiled stove fire door',12,14,3,'ink')
    put('KS1D',(-97,55,f1),group='Furniture')
    upright('KS1A',-95,57,f1+4,'Furniture',axis='yz');upright('KS1A',-69,57,f1+4,'Furniture',axis='yz')
    upright('KS1B',-91,61,f1+4,'Furniture');upright('KS1B',-91,87,f1+4,'Furniture')
    put('KS1C',(-98,54,f1+104),group='Furniture');upright('KS1E',-86,57,f1+24,'Furniture')
    part('LG1','Chandelier ring',30,30,3,'ochre');part('LG2','Chandelier rod',3,22,3,'ink');part('LG3','Chandelier candle',4,8,4,'cream')
    lz=f1+(CFG['floor_pitch']-CFG['thickness']['floor'])*450/CFG['wall_height']-22   # rod top just under the ceiling
    upright('LG2',58,62,lz,'Furniture');put('LG1',(44,49,lz-3),group='Furniture')
    for cx,cy in ((46,51),(68,51),(46,73),(68,73)):put('LG3',(cx,cy,lz),group='Furniture')
    # Bedroom floor: a footed bathtub in the right room.
    part('BA1A','Bathtub side',54,20,4,'cream');part('BA1B','Bathtub end',18,24,4,'cream');part('BA1C','Bathtub bottom',46,18,4,'cream');part('BA1D','Bathtub foot',6,4,4,'ochre')
    upright('BA1A',40,44,f2+4,'Furniture');upright('BA1A',40,66,f2+4,'Furniture')
    upright('BA1B',40,44,f2,'Furniture',axis='yz');upright('BA1B',90,44,f2,'Furniture',axis='yz');put('BA1C',(44,44,f2+4),group='Furniture')
    for fx,fy in ((44,44),(84,44),(44,62),(84,62)):put('BA1D',(fx,fy,f2),group='Furniture')
    # Attic: a bed by the rear and a writing desk.
    bed('AB2','Attic bed',-30,18,at)
    table('AD1','Attic writing desk',30,40,at,40,22,30,'wood')
    box('N1','Attic chest',-61,-53,at,52,31,32,'wood',has_top=False)
    add('N3','Telescope silhouette',4,[[0,0],[42,0],[48,8],[42,16],[0,16]],color='ochre',category='Furniture',note='Decorative plywood telescope silhouette on a broad glued pedestal.')
    add('N4','Telescope pedestal',4,[[0,0],[32,0],[20,38],[12,38]],color='wood',category='Furniture')
    upright('N4',-55,0,at,'Furniture');upright('N3',-63,0,at+38,'Furniture')


if __name__=='__main__':
    data=build(); (ROOT/'output/parts.json').write_text(json.dumps(data,indent=2));print(f'{len(PARTS)} profiles, {len(INSTANCES)} instances')
