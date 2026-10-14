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
    add(ids[0],name+' stringer',T['wall'],prof,color=colors[0],category='Exterior',note=f'Two stepped stringers: {n} risers of {rise:.1f}, treads {t:g} deep.')
    add(ids[1],name+' tread',T['detail'],rect(t,width),color=colors[1],category='Exterior',note=f'{n-1} per stair, glued on the stringers.')
    for w0 in (-width/2,width/2-T['wall']):
        o=(O[0]+lat[0]*(w0+T['wall']),O[1]+lat[1]*(w0+T['wall']))
        put(ids[0],(o[0],o[1],z_base),(d_out[0],d_out[1],0),(0,0,1),group)
    for k in range(1,n):
        o=(O[0]+d_out[0]*(k-1)*t-lat[0]*width/2,O[1]+d_out[1]*(k-1)*t-lat[1]*width/2)
        put(ids[1],(o[0],o[1],z_top-k*rise-T['detail']),(d_out[0],d_out[1],0),(lat[0],lat[1],0),group)

def entrances_and_veranda(api,width,a,base,pu,pv,pn,po,G):
    add,put,rect,hole=[api[k] for k in ('add','put','rect','hole')]
    parts,instances,fasteners,hardware=[api[k] for k in ('PARTS','INSTANCES','FASTENERS','HARDWARE')]
    cfg=api['CFG'];DH=cfg['door_hinge'];doors=cfg['doors'];wall=cfg['thickness']['wall'];q=lambda v:v*cfg['wall_height']/450
    # Doors hinge on the counter-clockwise jamb (the facet's +x end): the axis sits on that notch edge,
    # 2 mm beside the door, and the pilots follow the HG2 leaf pattern in config. Both doors open outward.
    gap=2;dw=q(50)-2*gap;sw=12;hole_ys=[c-DH['height']/2+dy for c in DH['centers'] for dy in DH['hole_y']]
    hx_door=dw-(DH['hole_x']-gap);hx_strip=sw-(DH['hole_x']-gap)
    # Main entrance plus the door that opens onto the veranda.
    add('E01','Main / veranda door',4,rect(dw,q(96)-wall-4),holes=[hole(hx_door,y,DH['pilot_diameter'],4,'Door hinge pilot') for y in hole_ys],color='ochre',category='Exterior',note=f'Two doors. Lower edge Z{G+wall+2:g} keeps 2 mm over the Z{G+wall:g} threshold and the veranda deck. Two miniature hinges per door; inset backing wood is glued before drilling.')
    add('A03','Door hinge backing strip',8,rect(12,q(96)-wall-4),holes=[hole(hx_strip,y,DH['pilot_diameter'],DH['pilot_depth'],'Door backing pilot') for y in hole_ys],category='Purchased wood',note='Four 8 x12 x86 mm strips, two per door. Match pilot holes to actual hinge leaf.')
    add('E02','Door handle',3,rect(q(14),q(8)),color='cream',category='Exterior')
    add('E10','Door threshold',6,rect(q(50),wall),color='cream',category='Exterior',note=f'Top at Z{G+wall:g}, flush with the veranda deck; the door bottom at Z{G+wall+2:g} keeps a 2 mm gap.')
    for pid in (doors['main'],doors['veranda']):
        wi=next(i for i in instances if i['part']==pid);u,n=wi['u'],wi['w'];group=wi['group'];dx=(width-dw)/2;z=G+wall+2
        def point(x,y,r):return (wi['origin'][0]+u[0]*x+n[0]*r,wi['origin'][1]+u[1]*x+n[1]*r,y)
        door=put('E01',point(dx,z,2),u,(0,0,1),group)
        moving=[door['id'],put('E02',point(dx+2,G+q(47),6),u,(0,0,1),group)['id']]   # handle on the latch side
        put('E10',point(dx-2,G,0),u,(0,0,1),group)
        axis=dx+dw+gap
        for target,ox in [('door',dx+dw-sw),('frame',axis)]:
            strip=put('A03',point(ox,z,-6 if target=='door' else -8),u,(0,0,1),group)
            if target=='door':moving.append(strip['id'])
            for yy in hole_ys:
                xx=ox+hx_strip
                fasteners.append({'id':f'FS-{pid}-{target}-{yy:g}','type':'SC2','diameter':1.6,'length':8,'head_diameter':3.2,'head_height':.8,'origin':point(xx,z+yy,wall+DH['leaf_thickness']),'axis':[-n[0],-n[1],0],'parts':[door['id'] if target=='door' else wi['id']],'pilot':DH['pilot_diameter'],'pilot_depth':DH['pilot_depth'],'note':'D1.6 x8 countersunk screw; length includes head. Through door hinge into 8 mm solid backing.'})
                if target=='frame':parts[pid]['holes'].append(dict(hole(xx,z+yy-G,DH['pilot_diameter'],wall,'Door frame hinge pilot'),id=f'H{len(parts[pid]["holes"])+1:02}'))
        for zz in (z+c for c in DH['centers']):hardware.append({'id':f'HG-{pid}-{zz:g}','kind':'Door butt hinge','group':group,'position':list(point(axis,zz,wall+DH['barrel_radius'])),'height':DH['height'],'width':DH['open_width'],'door':door['id'],'moves_with':moving,'outward':list(n[:2])})
        if pid==doors['main']:
            add('GD01','Main entrance gable',3,[[0,0],[q(60),0],[q(30),q(20)]],color='cream',category='Exterior')
            ps=math.hypot(q(30),q(20));co,si=q(30)/ps,q(20)/ps
            add('GD02','Main entrance canopy roof',3,rect(ps-2,q(20)),color='red',category='Exterior',note='Two small roof panels; tape and fill the square-edge ridge seam.')
            for r in (6,q(23)):put('GD01',point((width-q(60))/2,G+q(100),r),u,(0,0,1),group)
            left=point((width-q(60))/2,G+q(100),wall+q(20));uv=tuple(u[k]*co+(si if k==2 else 0) for k in range(3));vv=tuple(-v for v in n)
            put('GD02',left,uv,vv,group)
            uv2=tuple(u[k]*co-(si if k==2 else 0) for k in range(3));origin=point(width/2+2*co,G+q(120)-2*si,wall+q(20))
            put('GD02',origin,uv2,vv,group)
            # Entrance steps from the base up to the stone ledge in front of the door.
            Ap=cfg['plinth']['apothem'];nn=(n[0],n[1])
            stair(api,('ES1','ET1'),(nn[0]*Ap,nn[1]*Ap),nn,cfg['stairs']['width'],G,base,'Fixed',('stone','stone'),'Main entrance step')
    veranda(api,a,base,pu,pv,po,G)

def veranda(api,a,base,pu,pv,po,G):
    """Permanent veranda on a fixed wall facet. Local x runs along the facet (0..width), local y from the
    outer deck edge (0) toward the wall (depth); z is absolute. Local (x, y, z) is a right-handed frame."""
    add,put,rect,hole=[api[k] for k in ('add','put','rect','hole')]
    parts=api['PARTS'];cfg=api['CFG'];ver=cfg['veranda'];T=cfg['thickness'];q=lambda v:v*cfg['wall_height']/450
    W,D,g=ver['width'],ver['depth'],ver['wall_gap'];reach=a+g+D;mid=W/2;group='Porch'
    deck_top=G+T['wall'];col_h=ver['column_height'];head_top=deck_top+col_h+q(10)
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
    add('E03','Veranda deck',T['wall'],deck,color='wood',category='Exterior',note=f'{W:g} x {D:g} deck at ground-floor level (top Z{deck_top:g}, flush with the door threshold). The rear edge follows the three tower facets and rests on the plinth rim; the rest sits on the skirt and joists.')
    at('E03',0,0,G)
    # Skirt and joists carry the raised deck down to B01; they stop at the stone plinth faces.
    Ap=cfg['plinth']['apothem'];tvp=(Ap+g)*math.tan(math.pi/12);skirt=G-base
    def y_plinth(x):return reach-(Ap+g) if abs(x-mid)<=tvp else reach-((Ap+g)-abs(x-mid)*.5)/c30
    add('VS1','Veranda front skirt',T['wall'],rect(W,skirt),color='blue',category='Exterior',note='Boarded skirt under the deck front; glue to B01 and under the deck.')
    at('VS1',0,6,base,(1,0,0),(0,0,1))
    side=min(y_plinth(0),y_plinth(T['wall']))-.5-6
    add('VS2','Veranda side skirt',T['wall'],rect(side,skirt),color='blue',category='Exterior',note='Two side skirts from the front skirt back to the stone plinth.')
    for x in (0,W-T['wall']):at('VS2',x,6,base,(0,1,0),(0,0,1))
    add('VJ1','Veranda deck joist',T['wall'],rect(y_plinth(mid)-.5-6,skirt),color='wood',category='Exterior',note='Two joists under the middle of the deck.')
    for x in (q(52),q(102)):at('VJ1',x,6,base,(0,1,0),(0,0,1))
    # Stairs down from the deck on its open local-x end, like the reference veranda.
    O=P(0,q(50),0);stair(api,('VS3','VT1'),(O[0],O[1]),(-pu[0],-pu[1]),cfg['stairs']['width'],deck_top,base,group,('blue','cream'),'Veranda step')
    # Shaped columns: two at the front corners, two on the veranda facet, clear of neighbouring windows.
    spindle=[[0,0],[14,0],[14,12],[11,16],[11,26],[10,32],[11,42],[12,50],[10,58],[10,64],[10,78],[11,86],[14,90],[14,104],[0,104],[0,90],[3,86],[4,78],[4,64],[4,58],[2,50],[3,42],[4,32],[3,26],[3,16],[0,12]]
    add('C01','Veranda shaped white column',6,[[q(x),y*col_h/104] for x,y in spindle],color='cream',category='Exterior',note=f'Four shaped posts, {col_h:g} tall. Use a fine blade and file; clamp the blank to a larger carrier. Minimum neck width is 6 mm.')
    for x,y in [(fx,6),(W-fx-q(14),6),(rx,D),(W-rx-q(14),D)]:at('C01',x,y,deck_top,(1,0,0),(0,0,1))
    ztop=deck_top+col_h
    add('C10','Veranda rear wall header',6,rect(W-2*rx,q(10)),color='cream',category='Exterior',note='Sits on the two rear columns and is glued flat to the wall facet: it ties the veranda roof to the fixed shell.')
    at('C10',rx,D,ztop,(1,0,0),(0,0,1))
    # Side frame lines run from the front column corners to the rear column corners (a canted bay).
    d=unit([rx-fx,D,0]);nin=[d[1],-d[0],0];nout=[-d[1],d[0],0]
    s0=(6+6*d[0])/d[1];s1=(D-6)/d[1]
    # Front header ends are trimmed to the frame lines so they stay under the side roof panels.
    hx=fx+6*d[0]/d[1]
    add('C02','Veranda front header',6,rect(W-2*hx,q(10)),color='cream',category='Exterior')
    at('C02',hx,6,ztop,(1,0,0),(0,0,1))
    add('C03','Veranda side header',6,rect(s1-s0,q(10)),color='cream',category='Exterior',note='Two angled headers between the front header and the rear wall header; glue both end faces.')
    at('C03',fx+s0*d[0],s0*d[1],ztop,d,(0,0,1))
    rd=[-d[0],d[1],0];at('C03',W-fx+s1*rd[0],s1*rd[1],ztop,[-c for c in rd],(0,0,1))
    # Railings: front and the high local-x end; the other end is open above the steps.
    front_len=W-2*(fx+q(14))
    add('C06','Veranda front railing',4,rect(front_len,q(6)),color='cream',category='Exterior')
    for z in (deck_top+q(18),deck_top+q(58)):at('C06',fx+q(14),6,z,(1,0,0),(0,0,1))
    r0=(6+4*d[0])/d[1];side_len=s1-r0
    add('C08','Veranda side railing',4,rect(side_len,q(6)),color='cream',category='Exterior',note='Two angled rails on the closed end opposite the steps, glued between the front and rear columns.')
    rail=[W-fx+s1*rd[0],s1*rd[1]];ru=[-c for c in rd]
    for z in (deck_top+q(18),deck_top+q(58)):at('C08',*rail,z,ru,(0,0,1))
    bp=[[0,0],[10,0],[10,5],[7,8],[8,15],[10,18],[8,23],[7,27],[10,30],[10,34],[0,34],[0,30],[3,27],[2,23],[0,18],[2,15],[3,8],[0,5]]
    nf,ns=9,6
    add('C09','Veranda shaped baluster',4,[[q(x),q(y)] for x,y in bp],color='cream',category='Exterior',note=f'{nf} front and {ns} side balusters. Glue both ends between the rails.')
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
    yh=-o+(mid-3-FL[0])*math.tan(half)
    frame=[[0,0],[yh,ze+(yh+o)*tanp-head_top],[D,ze+dist(mid-3,D)*tanp-head_top],[D,0]]
    add('C07','Veranda roof crossframe',6,frame,color='cream',category='Exterior',note='Stands on the front and rear headers under the roof center line; carries the front panel and the ridge.')
    at('C07',mid-3,0,head_top,(0,1,0),(0,0,1))
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
    # Optional furniture: the veranda chair stands clear of the door sweep.
    cx,cy=ver['chair']
    add('PC01','Veranda chair seat',q(4),rect(q(28),q(28)),color='cream',category='Furniture')
    add('PC02','Veranda chair side',q(4),rect(q(28),q(20)),color='cream',category='Furniture')
    add('PC03','Veranda chair back',q(4),rect(q(28),q(53)),color='cream',category='Furniture')
    put('PC01',P(cx,cy,deck_top+q(20)),pu,pv,'Furniture')
    for x in (cx,cx+q(24)):put('PC02',P(x,cy,deck_top),pv,(0,0,1),'Furniture')
    put('PC03',P(cx,cy+q(32),deck_top),pu,(0,0,1),'Furniture')

def dormer_layout(roof):
    """Dormer on the front-right roof facet (normal -45 degrees), derived from the actual roof pitch.
    r is the horizontal distance along the facet normal, q the distance along the facet."""
    ra,rh,sl,rz=roof['a'],roof['h'],roof['slant'],roof['z'];tp=rh/ra;lift=3*sl/ra
    def z_out(r):return rz+(ra-r)*tp+lift   # outer roof surface over the facet
    def panel_y(r):return (ra-(r-3*rh/sl))*sl/ra   # R06 panel coordinate below an outer-surface point
    q=lambda v:v*roof.get('scale',1);rf=.62*ra;zf=z_out(rf);hf,hg=q(39),q(14);rb=rf-hf/tp
    x0,x1=roof['rw']/2-(q(18)-3),roof['rw']/2+(q(18)-3)
    return dict(rf=rf,zf=zf,hf=hf,hg=hg,rb=rb,tp=tp,z_out=z_out,cut=[[x0,panel_y(rf)],[x1,panel_y(rf)],[x1,panel_y(rb)],[x0,panel_y(rb)]])

def dormer(api,roof):
    add,put,rect,cutrect,parts=[api[k] for k in ('add','put','rect','cutrect','PARTS')]
    q=lambda v:v*roof.get('scale',1);L=dormer_layout(roof);rf,zf,hf,hg,rb,tp=[L[k] for k in ('rf','zf','hf','hg','rb','tp')]
    th=math.radians(-45);n=(math.cos(th),math.sin(th),0);t=(-n[1],n[0],0);back=(-n[0],-n[1],0)
    def point(q,r,z):return (t[0]*q+n[0]*r,t[1]*q+n[1]*r,z)
    # Front wall: bottom corners are notched where it would otherwise cut into the uncut roof skin.
    notch=3*tp+.3
    add('DM01','Attic dormer front',3,[[0,notch],[3,notch],[3,0],[q(36)-3,0],[q(36)-3,notch],[q(36),notch],[q(36),hf],[0,hf]],[cutrect(q(9),q(8),q(18),q(26))],color='cream',category='Roof',note='One attic window. The dormer is glued onto R06 over its opening and lifts off with the roof.')
    put('DM01',point(-q(18),rf-3,zf),t,(0,0,1),'Roof')
    # Sides are right triangles whose long edge lies on the roof slope.
    add('DM02','Attic dormer side',3,[[0,0],[0,hf-3*tp],[hf/tp-3,hf-3*tp]],color='cream',category='Roof',note='Two sides; the long edge is glued onto the roof skin beside the opening.')
    for side in (q(18)-3,-q(18)):put('DM02',point(side,rf-3,zf+3*tp),back,(0,0,1),'Roof')
    add('DM04','Attic dormer gable',3,[[0,0],[q(36),0],[q(18),hg]],color='cream',category='Roof')
    put('DM04',point(-q(18),rf-3,zf+hf),t,(0,0,1),'Roof')
    add('DM06','Dormer horizontal frame',3,rect(q(26),q(4)),color='cream',category='Roof')
    add('DM07','Dormer vertical frame',3,rect(q(4),q(26)),color='cream',category='Roof')
    for z in (zf+q(4),zf+q(34)):put('DM06',point(-q(13),rf,z),t,(0,0,1),'Roof')
    for side in (-q(13),q(9)):put('DM07',point(side,rf,zf+q(8)),t,(0,0,1),'Roof')
    # Gable roof: front overhang 2, eaves 2 beyond the sides, back edges lying on the main roof.
    ze=zf+hf;zr=ze+hg;zee=ze-q(2)*hg/q(18)
    def r_on_roof(z):return rf-(z-zf)/tp
    pts=[point(q(20),rf+q(2),zee),point(0,rf+q(2),zr),point(0,r_on_roof(zr),zr),point(q(20),r_on_roof(zee),zee)]
    nrm=[t[k]*hg/q(18)+(1 if k==2 else 0) for k in range(3)]
    def sub(a,b):return [a[k]-b[k] for k in range(3)]
    def dot(a,b):return sum(a[k]*b[k] for k in range(3))
    def unit(a):l=math.sqrt(dot(a,a));return [c/l for c in a]
    def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    u=unit(sub(pts[1],pts[0]));nu=unit(nrm);v=cross(nu,u)
    add('DM05','Attic dormer roof',3,[[dot(sub(p,pts[0]),u),dot(sub(p,pts[0]),v)] for p in pts],color='red',category='Roof',note='Two panels, the second turned over; their back edges lie on the main roof. Tape and fill the ridge seam.')
    x0,y0=parts['DM05']['origin_shift'];o=[pts[0][k]+u[k]*x0+v[k]*y0 for k in range(3)]
    put('DM05',tuple(o),tuple(u),tuple(v),'Roof')
    # Mirror image across the dormer's centre plane (q -> -q), turned over so its thickness stays outward.
    def m(a):d=dot(a,t);return [a[k]-2*d*t[k] for k in range(3)]
    mo=m(o);mn=m(nu);put('DM05',tuple(mo[k]+mn[k]*3 for k in range(3)),tuple(m(u)),tuple(m(v)),'Roof')
