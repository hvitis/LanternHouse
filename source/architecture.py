"""Photo-reference entrances, permanent veranda on a fixed facet, and attic dormer."""
import math

def stair(api,ids,O,d_out,width,z_top,z_base,group,colors,name):
    """Straight stair: two stepped stringers and 3 mm treads, descending from z_top along d_out (plan unit)."""
    add,put,rect=[api[k] for k in ('add','put','rect')];cfg=api['CFG'];st=cfg['stairs'];T=cfg['thickness']
    n,t=st['risers'],st['tread'];rise=(z_top-z_base)/n;S=(n-1)*t;lat=(-d_out[1],d_out[0])
    h=[z_top-k*rise-T['detail']-z_base for k in range(1,n)]
    prof=[[0,0],[S,0],[S,h[-1]]]
    for k in range(n-1,1,-1):prof+=[[(k-1)*t,h[k-1]],[(k-1)*t,h[k-2]]]
    prof+=[[0,h[0]]]
    add(ids[0],name+' stringer',T['structure'],prof,color=colors[0],category='Exterior',note=f'Two stepped stringers: {n} risers of {rise:.1f}, treads {t:g} deep.')
    add(ids[1],name+' tread',T['detail'],rect(t,width),color=colors[1],category='Exterior',note=f'{n-1} per stair, glued on the stringers.')
    for w0 in (-width/2,width/2-T['structure']):
        o=(O[0]+lat[0]*(w0+T['structure']),O[1]+lat[1]*(w0+T['structure']))
        put(ids[0],(o[0],o[1],z_base),(d_out[0],d_out[1],0),(0,0,1),group)
    for k in range(1,n):
        o=(O[0]+d_out[0]*(k-1)*t-lat[0]*width/2,O[1]+d_out[1]*(k-1)*t-lat[1]*width/2)
        put(ids[1],(o[0],o[1],z_top-k*rise-T['detail']),(d_out[0],d_out[1],0),(lat[0],lat[1],0),group)

def entrances_and_veranda(api,width,a,base,pu,pv,pn,po,G):
    add,put,rect,hole,cutrect=[api[k] for k in ('add','put','rect','hole','cutrect')]
    parts,instances,fasteners,hardware=[api[k] for k in ('PARTS','INSTANCES','FASTENERS','HARDWARE')]
    cfg=api['CFG'];DH=cfg['door_hinge'];doors=cfg['doors'];BD=cfg['back_door'];wall=cfg['thickness']['wall'];q=lambda v:v*cfg['wall_height']/450
    # Each door hangs 2 mm inside its notch on two HG2 hinges, on hardwood A03 strips glued behind the door and
    # behind the wall. Main and veranda doors hinge on the notch's counter-clockwise edge (the facet's +x end);
    # the narrow back door hinges on its clockwise edge, away from the wall-hinge blocks at the other end of its facet.
    # All three open outward and have a recessed finger pull instead of a glued-on handle.
    gap=2;sw=DH['backing_width'];hx=DH['hole_x'];sd,sl=DH['screw'];hole_ys=[c-DH['height']/2+dy for c in DH['centers'] for dy in DH['hole_y']]
    dt=cfg['thickness']['detail'];inset=wall-dt   # 3 mm doors, outer face flush with the wall's; the A03 strip glues to the inner face
    sill=cfg['thickness']['structure']   # threshold height: flush with the top of the veranda deck
    dh=q(96)-sill-4;pull=(5,14,q(47)-sill-2-7)   # finger slot width, height and bottom above the door's lower edge
    def door_part(pid,name,dw,hinge,note):
        # hinge +1: axis on the door's +x side; -1: on its -x side. Pilots sit hole_x from the axis.
        xh=dw+gap-hx if hinge>0 else hx-gap;xp=4 if hinge>0 else dw-4-pull[0]
        add(pid,name,dt,rect(dw,dh),[cutrect(xp,pull[2],pull[0],pull[1])],[hole(xh,y,DH['pilot_diameter'],dt,'Door hinge pilot') for y in hole_ys],color='ochre',category='Exterior',note=note)
    door_part('E01','Main / veranda door',q(50)-2*gap,1,f'Two doors. Lower edge {sill+2:g} mm above the floor keeps 2 mm over the threshold and the veranda deck. Two HG2 hinges per door into glued hardwood strips; the slot is the finger pull.')
    door_part('E04','Back door',BD['width']-2*gap,-1,'Narrow kitchen door, hinged on the other side from the main doors. Two HG2 hinges into glued hardwood strips; the slot is the finger pull.')
    add('A03','Door hinge backing strip',8,rect(sw,dh),holes=[hole(hx-gap,y,DH['block_pilot'],8,'Door backing pilot') for y in hole_ys],category='Purchased wood',note=f'Six 8 x {sw:g} x {dh:.0f} mm hardwood strips, two per door (on the door and behind the wall). Glue them, let them cure, then drill D{DH["block_pilot"]:g} pilots from the real hinge leaf.')
    add('E10','Door threshold',wall,rect(q(50),sill),color='cream',category='Exterior',note=f'Top {sill:g} mm above the floor, flush with the veranda deck; the door bottom keeps a 2 mm gap. As thick as the wall, so it fills the door notch.')
    add('E11','Back door threshold',wall,rect(BD['width'],sill),color='cream',category='Exterior')
    for pid in (doors['main'],doors['veranda'],doors['back']):
        wi=next(i for i in instances if i['part']==pid);u,n=wi['u'],wi['w'];group=wi['group'];z0=wi['origin'][2];z=z0+sill+2
        def point(x,y,r):return (wi['origin'][0]+u[0]*x+n[0]*r,wi['origin'][1]+u[1]*x+n[1]*r,y)
        back=pid==doors['back'];nw=BD['width'] if back else q(50);nx=BD['start'] if back else (width-nw)/2;dw=nw-2*gap;dx=nx+gap
        hinge=-1 if back else 1;axis=nx+nw if hinge>0 else nx
        door=put('E04' if back else 'E01',point(dx,z,inset),u,(0,0,1),group);moving=[door['id']]
        put('E11' if back else 'E10',point(nx,z0,0),u,(0,0,1),group)
        # Door strip on the hinge side of the door; frame strip behind the wall beside the notch.
        for target,ox in [('door',dx+dw-sw if hinge>0 else dx),('frame',axis if hinge>0 else axis-sw)]:
            strip=put('A03',point(ox,z,inset-8 if target=='door' else -8),u,(0,0,1),group)
            if target=='door':moving.append(strip['id'])
            xx=axis-hinge*hx if target=='door' else axis+hinge*hx
            for yy in hole_ys:
                fasteners.append({'id':f'FS-{pid}-{target}-{yy:g}','type':'SC2','diameter':sd,'length':sl,'head_diameter':2*sd,'head_height':1.0,'origin':point(xx,z+yy,wall+DH['leaf_thickness']),'axis':[-n[0],-n[1],0],'parts':[door['id'] if target=='door' else wi['id']],'pilot':DH['pilot_diameter'],'pilot_depth':DH['pilot_depth'],'note':f'D{sd:g} x {sl:g} countersunk wood screw (length includes the head) through the hinge leaf and a D{DH["pilot_diameter"]:g} pilot in the {"door" if target=="door" else "wall"} into the hardwood A03 strip.'})
                if target=='frame':parts[pid]['holes'].append(dict(hole(xx,z+yy-z0,DH['pilot_diameter'],wall,'Door frame hinge pilot'),id=f'H{len(parts[pid]["holes"])+1:02}'))
        for zz in (z+c for c in DH['centers']):hardware.append({'id':f'HG-{pid}-{zz:g}','kind':'Door butt hinge','group':group,'position':list(point(axis,zz,wall+DH['barrel_radius'])),'height':DH['height'],'width':DH['open_width'],'door':door['id'],'moves_with':moving,'outward':list(n[:2])})
        Ap=cfg['plinth']['apothem'];nn=(n[0],n[1])
        if pid==doors['main']:
            add('GD01','Main entrance gable',3,[[0,0],[q(60),0],[q(30),q(20)]],color='cream',category='Exterior')
            ps=math.hypot(q(30),q(20));co,si=q(30)/ps,q(20)/ps
            add('GD02','Main entrance canopy roof',3,rect(ps-2,q(20)),color='red',category='Exterior',note='Two small roof panels; tape and fill the square-edge ridge seam.')
            for r in (6,q(23)):put('GD01',point((width-q(60))/2,z0+q(100),r),u,(0,0,1),group)
            left=point((width-q(60))/2,z0+q(100),wall+q(20));uv=tuple(u[k]*co+(si if k==2 else 0) for k in range(3));vv=tuple(-v for v in n)
            put('GD02',left,uv,vv,group)
            uv2=tuple(u[k]*co-(si if k==2 else 0) for k in range(3));origin=point(width/2+2*co,z0+q(120)-2*si,wall+q(20))
            put('GD02',origin,uv2,vv,group)
            # Entrance steps from the base up to the stone ledge in front of the door.
            stair(api,('ES1','ET1'),(nn[0]*Ap,nn[1]*Ap),nn,cfg['stairs']['width'],G,base,'Fixed',('stone','stone'),'Main entrance step')
        if back:
            back_door_extras(api,wi,point,nx,nw,z0,G,base)
            mid=nx+nw/2-width/2;O=(nn[0]*Ap+u[0]*mid,nn[1]*Ap+u[1]*mid)
            stair(api,('ES1','ET1'),O,nn,cfg['stairs']['width'],G,base,'Fixed',('stone','stone'),'Main entrance step')
    veranda(api,a,base,pu,pv,po,G)

def back_door_extras(api,wi,point,nx,nw,z0,G,base):
    """Lean-to canopy over the back door: a sloping red roof on two triangular cream brackets."""
    add,put,rect=[api[k] for k in ('add','put','rect')];cfg=api['CFG'];wall=cfg['thickness']['wall'];q=lambda v:v*cfg['wall_height']/450
    u,n=wi['u'],wi['w'];cw,cd=cfg['back_door']['canopy'];x0=nx+nw/2-cw/2;zb=z0+q(96)+3;rise=cd*.6;h0=rise+6
    run=cd+2;slope=rise/run;sl=math.hypot(run,rise);co,si=run/sl,rise/sl
    # Knee brackets: the vertical edge on the wall, the top edge under the sloping roof.
    add('GD04','Back door canopy bracket',3,[[0,0],[cd,h0-slope*cd],[0,h0]],color='cream',category='Exterior',note='Two knee brackets glued edge-on to the wall above the back door.')
    for xx in (x0+6,x0+cw-3):
        put('GD04',point(xx,zb,wall),(n[0],n[1],0),(0,0,1),wi['group'])
    add('GD03','Back door canopy roof',3,rect(cw,sl),color='red',category='Exterior',note='Glue on the brackets and against the wall.')
    put('GD03',point(x0+cw,zb+h0,wall),(-u[0],-u[1],0),(n[0]*co,n[1]*co,-si),wi['group'])

def veranda(api,a,base,pu,pv,po,G):
    """Permanent veranda on a fixed wall facet. Local x runs along the facet (0..width), local y from the
    outer deck edge (0) toward the wall (depth); z is absolute. Local (x, y, z) is a right-handed frame."""
    add,put,rect,hole=[api[k] for k in ('add','put','rect','hole')]
    parts=api['PARTS'];cfg=api['CFG'];ver=cfg['veranda'];T=cfg['thickness'];dt=T['detail'];q=lambda v:v*cfg['wall_height']/450   # dt: railing thickness
    W,D,g=ver['width'],ver['depth'],ver['wall_gap'];reach=a+g+D;mid=W/2;group='Porch'
    deck_top=G+T['structure'];col_h=ver['column_height'];head_top=deck_top+col_h+q(10)
    deck_t,skirt_t,column_ply,header_t,frame_t=3,3,3,3,3
    deck_bottom=deck_top-deck_t
    tanp=math.tan(math.radians(ver['pitch']));o=ver['overhang'];fx,rx=ver['front_column_x'],ver['rear_column_x']
    def P(x,y,z):return (po[0]+pu[0]*x+pv[0]*y,po[1]+pu[1]*x+pv[1]*y,z)
    def V(x,y,z):return (pu[0]*x+pv[0]*y,pu[1]*x+pv[1]*y,z)
    def at(pid,x,y,z,u=(1,0,0),v=(0,1,0)):return put(pid,P(x,y,z),V(*u),V(*v),group)
    def sub(p,q):return [p[k]-q[k] for k in range(3)]
    def dot(p,q):return sum(p[k]*q[k] for k in range(3))
    def cross(p,q):return [p[1]*q[2]-p[2]*q[1],p[2]*q[0]-p[0]*q[2],p[0]*q[1]-p[1]*q[0]]
    def unit(p):l=math.sqrt(dot(p,p));return [c/l for c in p]
    def mirror(p):return [W-p[0],p[1],p[2]]
    def plate(pid,name,t,pts,normal,color,note='',mirrored=False):
        """Planar part whose inner face holds the local 3D points; thickness grows along the outward normal.
        mirrored=True also places the same profile turned over at the mirror image (x -> width - x)."""
        u=unit(sub(pts[1],pts[0]));n=unit(normal);v=cross(n,u)
        flat=[[dot(sub(q,pts[0]),u),dot(sub(q,pts[0]),v)] for q in pts]
        add(pid,name,t,flat,color=color,category='Exterior',note=note)
        x0,y0=parts[pid]['origin_shift'];origin=[pts[0][k]+u[k]*x0+v[k]*y0 for k in range(3)]
        at(pid,*origin,u,v)
        if mirrored:
            mu=[-u[0],u[1],u[2]];mv=[-v[0],v[1],v[2]];mn=[-n[0],n[1],n[2]]
            at(pid,*[mirror(origin)[k]+mn[k]*t for k in range(3)],mu,mv)
    # Deck: rectangle in front; the rear edge follows the veranda facet and its two neighbours with the wall gap.
    c30=math.cos(math.radians(30));tv=(a+g)*math.tan(math.pi/12)
    def y_rear(x):return reach-((a+g)-abs(x-mid)*.5)/c30
    deck=[[0,0],[W,0],[W,y_rear(W)],[mid+tv,D],[mid-tv,D],[0,y_rear(0)]]
    add('E03','Veranda deck',deck_t,deck,color='wood',category='Exterior',note=f'{W:g} x {D:g} deck in {deck_t:g} mm plywood (top Z{deck_top:g}, flush with the door threshold). The rear edge follows the three tower facets. The deck sits on the skirt and joists.')
    at('E03',0,0,deck_bottom)
    # Skirt and joists carry the raised deck down to B01; they stop at the stone plinth faces.
    Ap=cfg['plinth']['apothem'];tvp=(Ap+g)*math.tan(math.pi/12);skirt=deck_bottom-base
    def y_plinth(x):return reach-(Ap+g) if abs(x-mid)<=tvp else reach-((Ap+g)-abs(x-mid)*.5)/c30
    add('VS1','Veranda front skirt',skirt_t,rect(W,skirt),color='blue',category='Exterior',note='Boarded skirt under the deck front; glue to B01 and under the deck.')
    at('VS1',0,skirt_t,base,(1,0,0),(0,0,1))
    side=min(y_plinth(0),y_plinth(skirt_t))-.5-skirt_t
    add('VS2','Veranda side skirt',skirt_t,rect(side,skirt),color='blue',category='Exterior',note='Two side skirts from the front skirt back to the stone plinth.')
    for x in (0,W-skirt_t):at('VS2',x,skirt_t,base,(0,1,0),(0,0,1))
    add('VJ1','Veranda deck joist',T['structure'],rect(y_plinth(mid)-.5-skirt_t,skirt),color='wood',category='Exterior',note='Two joists under the middle of the deck.')
    for x in (q(52),q(102)):at('VJ1',x,skirt_t,base,(0,1,0),(0,0,1))
    # Stairs down from the deck on its open local-x end, like the reference veranda.
    O=P(0,q(50),0);stair(api,('VS3','VT1'),(O[0],O[1]),(-pu[0],-pu[1]),cfg['stairs']['width'],deck_top,base,group,('blue','cream'),'Veranda step')
    # Shaped columns: two at the front corners, two on the veranda facet, clear of neighbouring windows.
    spindle=[[0,0],[14,0],[14,12],[11,16],[11,26],[10,32],[11,42],[12,50],[10,58],[10,64],[10,78],[11,86],[14,90],[14,104],[0,104],[0,90],[3,86],[4,78],[4,64],[4,58],[2,50],[3,42],[4,32],[3,26],[3,16],[0,12]]
    add('C01','Veranda shaped white column',column_ply,[[q(x),y*col_h/104] for x,y in spindle],color='cream',category='Exterior',note=f'Eight {column_ply:g} mm plies make four {2*column_ply:g} mm thick posts, {col_h:g} tall. Glue two identical C01 pieces face to face for each post. Align the profiles and clamp flat until the glue cures. Use a fine blade and file; clamp the blank to a larger carrier. Minimum neck width is 6 mm.')
    for x,y in [(fx,6),(W-fx-q(14),6),(rx,D),(W-rx-q(14),D)]:
        for ply in range(2):at('C01',x,y-ply*column_ply,deck_top,(1,0,0),(0,0,1))
    ztop=deck_top+col_h
    add('C10','Veranda rear wall header',header_t,rect(W-2*rx,q(10)),color='cream',category='Exterior',note='Sits on the two rear columns and is glued flat to the wall facet: it ties the veranda roof to the fixed shell.')
    at('C10',rx,D,ztop,(1,0,0),(0,0,1))
    # Side frame lines run from the front column corners to the rear column corners (a canted bay).
    d=unit([rx-fx,D,0]);nin=[d[1],-d[0],0];nout=[-d[1],d[0],0]
    s0=(6+header_t*d[0])/d[1];s1=(D-header_t)/d[1]
    # Front header ends are trimmed to the frame lines so they stay under the side roof panels.
    hx=fx+6*d[0]/d[1]
    add('C02','Veranda front header',header_t,rect(W-2*hx,q(10)),color='cream',category='Exterior')
    at('C02',hx,6,ztop,(1,0,0),(0,0,1))
    add('C03','Veranda side header',header_t,rect(s1-s0,q(10)),color='cream',category='Exterior',note='Two angled headers between the front header and the rear wall header; glue both end faces.')
    at('C03',fx+s0*d[0],s0*d[1],ztop,d,(0,0,1))
    rd=[-d[0],d[1],0];at('C03',W-fx+s1*rd[0],s1*rd[1],ztop,[-c for c in rd],(0,0,1))
    # Railings: front and the high local-x end; the other end is open above the steps.
    front_len=W-2*(fx+q(14))
    add('C06','Veranda front railing',dt,rect(front_len,q(6)),color='cream',category='Exterior')
    for z in (deck_top+q(18),deck_top+q(58)):at('C06',fx+q(14),6,z,(1,0,0),(0,0,1))
    rail_end=(D-2*column_ply)/d[1]   # rails stop at the columns, independently of the thinner headers
    r0=(6+dt*d[0])/d[1];side_len=rail_end-r0   # the side rails start against the end of the front rail
    add('C08','Veranda side railing',dt,rect(side_len,q(6)),color='cream',category='Exterior',note='Two angled rails on the closed end opposite the steps, glued between the front and rear columns.')
    rail=[W-fx+rail_end*rd[0],rail_end*rd[1]];ru=[-c for c in rd]
    for z in (deck_top+q(18),deck_top+q(58)):at('C08',*rail,z,ru,(0,0,1))
    bp=[[0,0],[10,0],[10,5],[7,8],[8,15],[10,18],[8,23],[7,27],[10,30],[10,34],[0,34],[0,30],[3,27],[2,23],[0,18],[2,15],[3,8],[0,5]]
    nf,ns=9,6
    add('C09','Veranda shaped baluster',dt,[[q(x),q(y)] for x,y in bp],color='cream',category='Exterior',note=f'{nf} front and {ns} side balusters. Glue both ends between the rails.')
    gap=(front_len-nf*q(10))/(nf+1)
    for k in range(nf):at('C09',fx+q(14)+gap+k*(q(10)+gap),6,deck_top+q(24),(1,0,0),(0,0,1))
    gap=(side_len-ns*q(10))/(ns+1)
    for k in range(ns):at('C09',rail[0]+ru[0]*(gap+k*(q(10)+gap)),rail[1]+ru[1]*(gap+k*(q(10)+gap)),deck_top+q(24),ru,(0,0,1))
    # Hipped roof over the canted plan: front triangle, two side panels meeting at a ridge that runs to the wall.
    ze=head_top-o*tanp;ae=[fx+o*nout[0],o*nout[1]]
    def dist(x,y):return (x-ae[0])*nin[0]+(y-ae[1])*nin[1]
    FL=[ae[0]+(-o-ae[1])/d[1]*d[0],-o];half=math.atan2(d[1],d[0])/2
    ya=-o+(mid-FL[0])*math.tan(half);yr=D-3
    RL=[ae[0]+(yr-ae[1])/d[1]*d[0],yr]
    fl=[FL[0],FL[1],ze];fr=mirror(fl);apex=[mid,ya,ze+(ya+o)*tanp];ridge=[mid,yr,ze+dist(mid,yr)*tanp];rl=[RL[0],RL[1],ze]
    nfront=[0,-tanp,1];nside=[-nin[0]*tanp,-nin[1]*tanp,1]
    roofnote='Glue along the hips over the C07 crossframe; then fit the hip caps. Paint red.'
    plate('C04','Veranda roof front panel',3,[fl,fr,apex],nfront,'red',roofnote)
    plate('C05','Veranda roof side panel',3,[fl,rl,ridge,apex],nside,'red','Two panels, the second turned over (mirror image). '+roofnote,mirrored=True)
    # Central crossframe: its top follows the front panel to the hips, then the side panels to the wall.
    frame_x=mid-frame_t/2;yh=-o+(frame_x-FL[0])*math.tan(half)
    frame=[[0,0],[yh,ze+(yh+o)*tanp-head_top],[D,ze+dist(frame_x,D)*tanp-head_top],[D,0]]
    add('C07','Veranda roof crossframe',frame_t,frame,color='cream',category='Exterior',note='Stands on the front and rear headers under the roof center line; carries the front panel and the ridge.')
    at('C07',frame_x,0,head_top,(0,1,0),(0,0,1))
    # Hip and ridge caps sit on the square panel edges and cover the V seams.
    def cap(pid,name,p,end,n1,n2,trim_start,trim_end):
        h=unit(sub(end,p));zp=unit([unit(n1)[k]+unit(n2)[k] for k in range(3)]);e=cross(zp,h);lift=3*dot(unit(n1),zp)
        length=math.sqrt(dot(sub(end,p),sub(end,p)))-trim_start-trim_end
        if pid not in parts:add(pid,name,3,rect(length,q(6)),color='cream',category='Exterior',note='Glue on top of the panel edges over the seam.')
        at(pid,*[p[k]+h[k]*trim_start+zp[k]*lift-e[k]*q(3) for k in range(3)],h,e)
    mside=[-nside[0],nside[1],nside[2]]
    cap('C11','Veranda hip cap',fl,apex,nfront,nside,1,6)
    cap('C11','Veranda hip cap',fr,apex,nfront,mside,1,6)
    cap('C12','Veranda ridge cap',apex,ridge,nside,mside,6,0)

def dormer_layout(roof,cfg):
    """Dormer geometry on a roof facet, derived from the actual roof pitch. r is the horizontal distance along the
    facet normal, q the distance along the facet. The front stands as low as the eave cleats under the skin allow."""
    D=cfg['dormer'];ra,rh,sl,rz=roof['a'],roof['h'],roof['slant'],roof['z'];tp=rh/ra;lift=3*sl/ra
    def z_out(r):return rz+(ra-r)*tp+lift   # outer roof surface over the facet
    def panel_y(r):return (ra-(r-3*rh/sl))*sl/ra   # R06 panel coordinate below an outer-surface point
    # Under an outer-surface point the skin's inner face lies 3*rh/sl further out: the opening's lower edge
    # stays cleat_clearance inside the R04 eave cleats.
    rf=roof['cleat_r']+3*rh/sl-D['cleat_clearance'];zf=z_out(rf);F=D['front_width']/2;hf,hg=D['height'],D['gable'];rb=rf-hf/tp
    x0,x1=roof['rw']/2-(F-3),roof['rw']/2+(F-3)
    return dict(rf=rf,zf=zf,F=F,hf=hf,hg=hg,rb=rb,tp=tp,z_out=z_out,panel_y=panel_y,cut=[[x0,panel_y(rf)],[x1,panel_y(rf)],[x1,panel_y(rb)],[x0,panel_y(rb)]])

def dormer_angles(cfg):
    """Outer-normal angle of each dormer's roof panel: the panel above the configured wall facet."""
    return [-75+30*(int(f[1:])-1) for f in cfg['dormer']['over']]

def dormer(api,roof):
    add,put,rect,cutrect,parts=[api[k] for k in ('add','put','rect','cutrect','PARTS')]
    cfg=api['CFG'];D=cfg['dormer'];WN=cfg['windows'];q=lambda v:v*roof.get('scale',1);L=dormer_layout(roof,cfg)
    rf,zf,F,hf,hg,rb,tp=[L[k] for k in ('rf','zf','F','hf','hg','rb','tp')]
    ww,wh=D['window'];ws=D['sill'];bar=WN['bar'];pw,ph=(ww-bar)/2,(wh-bar)/2;fb=4.0;gz,gm=WN['glazing']
    def panes(x,y):return [cutrect(x+c*(pw+bar),y+r*(ph+bar),pw,ph) for r in (0,1) for c in (0,1)]
    # Front wall: bottom corners are notched where it would otherwise cut into the uncut roof skin. Its window
    # keeps a solid cross between four panes; a one-piece frame covers it outside, PET glazing inside.
    notch=3*tp+.3;W2=2*F
    add('DM01','Attic dormer front',3,[[0,notch],[3,notch],[3,0],[W2-3,0],[W2-3,notch],[W2,notch],[W2,hf],[0,hf]],panes(F-ww/2,ws),color='cream',category='Roof',note=f'One per dormer, {len(D["over"])} in all. Leave the cross between the panes solid. Each dormer is glued onto its R06 panel over the opening and lifts off with the roof.')
    parts['DM01']['windows']=[[F-ww/2,ws,ww,wh]]
    add('DM02','Attic dormer side',3,[[0,0],[0,hf-3*tp],[hf/tp-3,hf-3*tp]],color='cream',category='Roof',note='Two per dormer; the long edge is glued onto the roof skin beside the opening.')
    add('DM04','Attic dormer gable',3,[[0,0],[W2,0],[F,hg]],color='cream',category='Roof')
    add('DM06','Dormer window frame',3,rect(ww+2*fb,wh+2*fb),panes(fb,fb),color='cream',category='Roof',note='One per dormer, glued over the front so its cross lies on the solid cross of the front.')
    add('GZ2','Dormer glazing (clear PET)',gz,rect(ww+2*gm,wh+2*gm),color='cream',category='Purchased packing',note=f'Cut from {gz:g} mm clear PET sheet; glue inside the dormer front.')
    # Gable roof: front overhang and eaves ov beyond the walls, back edges lying on the main roof.
    ov=q(2);ze=zf+hf;zr=ze+hg;zee=ze-ov*hg/F
    def r_on_roof(z):return rf-(z-zf)/tp
    def sub(a,b):return [a[k]-b[k] for k in range(3)]
    def dot(a,b):return sum(a[k]*b[k] for k in range(3))
    def unit(a):l=math.sqrt(dot(a,a));return [c/l for c in a]
    def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    for angle in dormer_angles(cfg):
        th=math.radians(angle);n=(math.cos(th),math.sin(th),0);t=(-n[1],n[0],0);back=(-n[0],-n[1],0)
        def point(q_,r,z):return (t[0]*q_+n[0]*r,t[1]*q_+n[1]*r,z)
        put('DM01',point(-F,rf-3,zf),t,(0,0,1),'Roof')
        # Sides are right triangles whose long edge lies on the roof slope.
        for side in (F-3,-F):put('DM02',point(side,rf-3,zf+3*tp),back,(0,0,1),'Roof')
        put('DM04',point(-F,rf-3,zf+hf),t,(0,0,1),'Roof')
        put('DM06',point(-ww/2-fb,rf,zf+ws-fb),t,(0,0,1),'Roof')
        put('GZ2',point(-ww/2-gm,rf-3-gz,zf+ws-gm),t,(0,0,1),'Roof')
        pts=[point(F+ov,rf+ov,zee),point(0,rf+ov,zr),point(0,r_on_roof(zr),zr),point(F+ov,r_on_roof(zee),zee)]
        nrm=[t[k]*hg/F+(1 if k==2 else 0) for k in range(3)]
        u=unit(sub(pts[1],pts[0]));nu=unit(nrm);v=cross(nu,u)
        if 'DM05' not in parts:add('DM05','Attic dormer roof',3,[[dot(sub(p_,pts[0]),u),dot(sub(p_,pts[0]),v)] for p_ in pts],color='red',category='Roof',note='Two per dormer, the second turned over; their back edges lie on the main roof. Tape and fill the ridge seam.')
        x0,y0=parts['DM05']['origin_shift'];o=[pts[0][k]+u[k]*x0+v[k]*y0 for k in range(3)]
        put('DM05',tuple(o),tuple(u),tuple(v),'Roof')
        # Mirror image across the dormer's centre plane (q -> -q), turned over so its thickness stays outward.
        def m(a):d=dot(a,t);return [a[k]-2*d*t[k] for k in range(3)]
        mo=m(o);mn=m(nu);put('DM05',tuple(mo[k]+mn[k]*3 for k in range(3)),tuple(m(u)),tuple(m(v)),'Roof')

def top_surface_z(api,inst,x,y):
    """Height of a placed plate's upper face above plan point (x, y), or None if the point is off the plate."""
    p=api['PARTS'][inst['part']];o,u,v,w=inst['origin'],inst['u'],inst['v'],inst['w'];best=None
    for d in (0,p['thickness']):
        det=u[0]*v[1]-u[1]*v[0]
        if abs(det)<1e-6:return None   # a vertical plate: callers use its bounding box
        bx,by=x-o[0]-w[0]*d,y-o[1]-w[1]*d;s=(bx*v[1]-by*v[0])/det;t=(u[0]*by-u[1]*bx)/det
        if api['inside_polygon'](s,t,p['outer']):
            z=o[2]+u[2]*s+v[2]*t+w[2]*d;best=z if best is None else max(best,z)
    return best

def highest_below(api,footprint,instances,ceiling):
    """Top of the highest instance under a plan footprint (list of points), below `ceiling`."""
    from shapely.geometry import Polygon,MultiPoint
    area=Polygon(footprint).buffer(.5);top=None
    for inst in instances:
        lo,hi=api['instance_box'](inst)
        if hi[0]<area.bounds[0] or lo[0]>area.bounds[2] or hi[1]<area.bounds[1] or lo[1]>area.bounds[3] or lo[2]>ceiling:continue
        p=api['PARTS'][inst['part']];o,u,v,w=inst['origin'],inst['u'],inst['v'],inst['w']
        if abs(w[2])<.2:   # upright plate: its true plan outline
            pts=[(o[0]+u[0]*x+v[0]*y+w[0]*d,o[1]+u[1]*x+v[1]*y+w[1]*d) for x,y in p['outer'] for d in (0,p['thickness'])]
            if MultiPoint(pts).convex_hull.intersects(area):top=max(top or -1e9,hi[2])
        else:
            samples=list(area.exterior.coords)+[tuple(area.centroid.coords[0])]
            zs=[z for z in (top_surface_z(api,inst,x,y) for x,y in samples) if z is not None]
            if zs:top=max(top or -1e9,max(zs))
    return top

def battens_and_ladder(api,G,roof_z):
    """Board-and-batten seams and the rope ladder. A 3 x 8 batten covers the V-gap of every outside corner that
    does not move: between fixed facets and inside each opening shell, never across a hinge or the front seam.
    Each batten stops under the eave fascia and starts above anything built against the wall (the veranda) or
    met by an opened shell (the stop posts). The rope ladder is glued on the batten at the corner shared by a
    dormer panel and the veranda facet, from the veranda roof up to the eave: it is part of the house, so the
    roof lifts clear of it."""
    add,put,rect,cutrect=[api[k] for k in ('add','put','rect','cutrect')]
    cfg=api['CFG'];walls=api['WALLS'];instances=api['INSTANCES'];parts=api['PARTS']
    wall=cfg['thickness']['wall'];det=cfg['thickness']['detail'];WS=cfg['wall_stop']
    porch=[i for i in instances if i['group']=='Porch']
    stop_corners={330,210}   # the opened shells meet the GP1 posts just beside these corners
    vf=-75+30*(int(cfg['veranda']['facet'][1:])-1)
    ladder_corner=next(((a_+vf)/2%360 for a_ in dormer_angles(cfg) if abs(a_-vf)==30),None)
    lengths={};ladder=None
    for i in range(12):
        j=(i+1)%12;wi,wj=walls[i],walls[j]
        if wi['group']!=wj['group']:continue
        pi=parts[wi['part']];corner=(-60+30*i)%360
        # The batten's back face touches the outer edges of both facets.
        P1=[wi['origin'][k]+wi['u'][k]*pi['width']+wi['w'][k]*wall for k in range(2)]
        P2=[wj['origin'][k]+wj['w'][k]*wall for k in range(2)]
        dx,dy=P2[0]-P1[0],P2[1]-P1[1];l=math.hypot(dx,dy);t=(dx/l,dy/l);m=(t[1],-t[0])
        mid=((P1[0]+P2[0])/2,(P1[1]+P2[1])/2)
        z0=wi['origin'][2];top=z0+pi['height']-8-.5   # under the D03 fascia
        foot=[(mid[0]+t[0]*a_+m[0]*b_,mid[1]+t[1]*a_+m[1]*b_) for a_,b_ in ((-4,0),(4,0),(4,det),(-4,det))]
        under=highest_below(api,foot,porch,top);bottom=z0 if under is None else under+1
        if corner in stop_corners:bottom=max(bottom,G+WS['top']+2)
        L=round(top-bottom,1);pid=lengths.setdefault(L,f'BT{len(lengths)+1}')
        if pid not in parts:add(pid,'Seam batten',det,rect(8,L),color='blue',category='Exterior',note='3 x 8 mm batten glued over an outside corner seam: it bears on both facet edges; fill the hollow behind it with glue. Paint it like the walls.')
        put(pid,(mid[0]-t[0]*4,mid[1]-t[1]*4,bottom),(t[0],t[1],0),(0,0,1),wi['group'])
        if corner==ladder_corner:ladder=(mid,t,m,bottom)
    if ladder is None:return
    mid,t,m,bottom=ladder
    # One 3 mm piece, 24 wide, rails 5 and rungs 4 wide, glued flat on the batten's face.
    LW,rail,rung=24.0,5.0,4.0
    foot=[(mid[0]+t[0]*a_+m[0]*b_,mid[1]+t[1]*a_+m[1]*b_) for a_,b_ in ((-LW/2,det),(LW/2,det),(LW/2,2*det),(-LW/2,2*det))]
    under=highest_below(api,foot,porch,roof_z);lb=(bottom if under is None else under)+1;lt=roof_z-9;LL=lt-lb
    gaps=max(1,round((LL-rung)/16));pitch=(LL-rung)/gaps
    add('RL1','Rope ladder',det,rect(LW,LL),[cutrect(rail,rung+k*pitch,LW-2*rail,pitch-rung) for k in range(gaps)],color='ochre',category='Exterior',note='One piece, from the veranda roof up to the eave beside the dormer. Glue it flat on the seam batten at every rung; it belongs to the house, so the roof lifts off clear of it. Paint it rope-coloured: no cord and no loose rungs.')
    put('RL1',(mid[0]-t[0]*LW/2+m[0]*det,mid[1]-t[1]*LW/2+m[1]*det,lb),(t[0],t[1],0),(0,0,1),'Fixed')

def plinth_and_garden(api,G,bt):
    """Faux cellar hatch on the plinth, the woodpile shelter beside the back door, the steel ballast inside the plinth
    and the anti-tip strap anchor inside the fixed rear shell. bt is the B01 base thickness."""
    add,put,rect,hole,poly=[api[k] for k in ('add','put','rect','hole','poly')]
    cfg=api['CFG'];PL=cfg['plinth'];Ap=PL['apothem'];det=cfg['thickness']['detail'];ph=G-bt-cfg['thickness']['floor']
    def facet(angle):th=math.radians(angle);n=(math.cos(th),math.sin(th));return n,(-n[1],n[0])
    # Cellar hatch: an arched door glued flat on the plinth panel beside the hidden drawer.
    dr=PL['drawer']['direction'];n,u=facet(dr-45)
    add('HC1','Faux cellar hatch',det,[[0,0],[36,0],[36,26],[33,33],[26,37.5],[10,37.5],[3,33],[0,26]],color='wood',category='Exterior',note='Glued flat on the stone plinth beside the hidden drawer; paint it as old planks with a black ring pull.')
    put('HC1',(n[0]*Ap-u[0]*18,n[1]*Ap-u[1]*18,bt+(ph-37.5)/2),(u[0],u[1],0),(0,0,1),'Fixed')
    # Woodpile shelter: an open box with a lean-to roof against the plinth facet beside the back door, shifted
    # toward the door so it stays clear of the veranda. Display only, like the garden scene: it stands around the
    # house, is not part of its construction, and is not cut or counted on plywood sheets.
    n,u=facet(-75+30*(int(cfg['doors']['back'][1:])-1)-30)
    wd,wh,wf,wb,off=30.0,40.0,34.0,44.0,19.0   # depth, back and front height, width, shift toward the back door
    k=(wh-wf)/wd   # roof slope; every top edge follows the roof's underside
    def at(lat,r,z):return (n[0]*(Ap+r)+u[0]*lat,n[1]*(Ap+r)+u[1]*lat,z)
    add('WP1','Woodpile shelter back',det,rect(wb,wh-det*k),color='wood',category='Furniture')
    add('WP2','Woodpile shelter side',det,[[0,0],[wd,0],[wd,wh-(det+wd)*k],[0,wh-det*k]],color='wood',category='Furniture')
    sl=math.hypot(wd+det+4,(wd+det+4)*k);add('WP3','Woodpile shelter roof',det,rect(wb+6,sl),color='red',category='Furniture')
    put('WP1',at(off-wb/2,0,bt),(u[0],u[1],0),(0,0,1),'Furniture')
    for lat in (off-wb/2+det,off+wb/2):put('WP2',at(lat,det,bt),(n[0],n[1],0),(0,0,1),'Furniture')   # thickness toward -lat
    co,si=1/math.hypot(1,k),k/math.hypot(1,k)
    put('WP3',at(off+wb/2+3,0,bt+wh),(-u[0],-u[1],0),(n[0]*co,n[1]*co,-si),'Furniture')
    # Firewood inside (display only): three rows of logs lying front to back.
    add('WL1','Firewood log',26.0,poly(10,4.2,4.2,4.2),color='wood',category='Furniture')
    for row,cols in enumerate((4,3,2)):
        for c_ in range(cols):
            lat=off-wb/2+det+4.5+c_*8.6+row*4.3;z=bt+row*7.4
            put('WL1',at(lat-4.2,det+2,z),(u[0],u[1],0),(0,0,1),'Furniture')
    # Steel ballast: flat bars screwed to B01 inside the plinth, either side of the drawer bay.
    count,(bl,bw,bth)=cfg['stability']['ballast'];th=math.radians(dr);e=(math.cos(th),math.sin(th));s_=(-e[1],e[0])
    if count:
        add('BL2','Steel ballast bar',bth,rect(bl,bw),holes=[hole(12,bw/2,3.5),hole(bl-12,bw/2,3.5)],color='gray',category='Purchased metal',note=f'{count} flat steel bars, {bl:g} x {bw:g} x {bth:g} mm (about {bl*bw*bth*7.85e-3:.0f} g each), screwed to B01 inside the plinth before F00 goes on. They lower the centre of gravity so the open house is harder to tip.')
        lat=PL['drawer']['half_width']+16+bw/2
        for sgn in (1,-1)[:count]:
            c=(s_[0]*sgn*lat,s_[1]*sgn*lat)
            put('BL2',(c[0]-e[0]*bl/2-s_[0]*bw/2,c[1]-e[1]*bl/2-s_[1]*bw/2,bt),(e[0],e[1],0),(s_[0],s_[1],0),'Fixed')
    # Anti-tip strap anchor: a hardwood block inside a fixed facet near the top; a screw eye through the wall
    # takes a furniture anti-tip strap to the room wall.
    AN=cfg['stability']['anchor'];wi=api['WALLS'][int(AN['facet'][1:])-1];wp=api['PARTS'][wi['part']];pw=wp['width']
    o,u2,n2=wi['origin'],wi['u'],wi['w'];zt=o[2]+AN['height']
    add('AB1','Anti-tip anchor block (solid wood)',12,rect(30,24),holes=[dict(hole(15,12,3.0,10,'Screw-eye pilot from the wall side'),entry='bottom')],category='Purchased wood',note='Glue inside the fixed shell, centred on its facet near the top; drive the anti-tip strap screw eye through the wall into it.')
    put('AB1',(o[0]+u2[0]*(pw/2-15),o[1]+u2[1]*(pw/2-15),zt),(u2[0],u2[1],0),(0,0,-1),'Fixed')   # thickness grows into the room
    wp['holes'].append(dict(hole(pw/2,AN['height']-12,3.0,None,'Anti-tip screw-eye hole'),id=f'H{len(wp["holes"])+1:02}'))
    api['HARDWARE'].append({'id':'AT-Anchor','kind':'Anti-tip strap','group':'Fixed','position':[o[0]+u2[0]*pw/2+n2[0]*6,o[1]+u2[1]*pw/2+n2[1]*6,zt-12],'height':12,'width':30,'note':'Furniture anti-tip strap kit: screw eye through the wall into AB1, strap to a plug in the room wall.'})
