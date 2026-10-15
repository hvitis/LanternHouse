"""A3 fabrication sections, supported panel seams and continuous-pillar metadata."""
from __future__ import annotations
import copy
import math
import re
from shapely.geometry import Polygon, box, MultiPoint, Point


def polygons(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [shape]
    return [p for p in shape.geoms if p.geom_type=='Polygon' and p.area>0.01]


def relieve_inside_corners(shape, near, radius):
    """Dogbone relief: a router leaves a radius in every inside corner, so a square tab of the mating part could not
    seat. Cut a circle of the cutter radius at each concave corner that lies inside `near` (the joint zone)."""
    from shapely.ops import unary_union
    ring=list(shape.exterior.coords)[:-1];ccw=shape.exterior.is_ccw;holes=[]
    for k,v in enumerate(ring):
        a,c=ring[k-1],ring[(k+1)%len(ring)]
        turn=(v[0]-a[0])*(c[1]-v[1])-(v[1]-a[1])*(c[0]-v[0])
        if (turn<-1e-9 if ccw else turn>1e-9) and near.contains(Point(v)):holes.append(Point(v).buffer(radius,quad_segs=8))
    return shape.difference(unary_union(holes)) if holes else shape


def finger_joint_regions(width, height, seam, tab_w=20.0, tab_h=10.0, margin=35.0, flat=0.0):
    """Split a panel at y=seam with square teeth. With `flat`, the teeth run outward from a flat stretch that wide in
    the middle, mirrored on both sides, so a second seam along the middle can meet this one square."""
    xmin, xmax = -10.0, width + 10.0
    if flat:
        c = width / 2.0
        right = [(c + flat / 2.0 + k * tab_w, k % 2 == 0) for k in range(int((c - flat / 2.0 - margin) // tab_w))]
        tabs = sorted([(2 * c - x - tab_w, up) for x, up in right] + right)
    else:
        tabs, x, up = [], margin, True
        while x + tab_w <= width - margin:
            tabs.append((x, up));x += tab_w;up = not up
    path, end = [(xmin, seam)], None
    for x, up in tabs:
        if end is None or abs(x - end) > 1e-9:
            if end is not None:path.append((end, seam))
            path.append((x, seam))
        ytab = seam + (tab_h / 2.0 if up else -tab_h / 2.0)
        path.extend([(x, ytab), (x + tab_w, ytab)]);end = x + tab_w
    path.extend([(end if tabs else margin, seam), (xmax, seam)])
    poly_lower = Polygon([(xmin, -10.0), (xmax, -10.0)] + list(reversed(path)))
    poly_upper = Polygon([(xmax, height + 10.0), (xmin, height + 10.0)] + path)
    return [poly_lower, poly_upper]


def puzzle_regions(x, extent, knobs, neck, head, reach, fillet):
    """Split the box `extent` (x0, y0, x1, y1) at x=`x` with jigsaw knobs and return (left, right). Each knob is
    (y, side): side 1 grows from the left part into the right, -1 the other way. A knob is a `neck` wide stem ending
    in a D`head` disc `reach` from the seam, so the parts lock against pulling apart. Every inside corner of both parts
    is rounded to at least `fillet`, so a router cuts them exactly."""
    from shapely.ops import unary_union
    x0, y0, x1, y1 = extent
    def knob(y, side):
        tip = x + side * reach
        return unary_union([box(min(x - side, tip), y - neck / 2, max(x - side, tip), y + neck / 2), Point(tip, y).buffer(head / 2, quad_segs=16)])
    def closing(shape):return shape.buffer(fillet, quad_segs=8).buffer(-fillet, quad_segs=8)
    lbox, rbox = box(x0, y0, x, y1), box(x, y0, x1, y1)
    # Each side with its own knobs, filleted where they leave the seam; the other side keeps the rest.
    grown_left = closing(unary_union([lbox] + [knob(y, 1) for y, side in knobs if side > 0]))
    grown_right = closing(unary_union([rbox] + [knob(y, -1) for y, side in knobs if side < 0]))
    # Buffering re-tessellates every arc; 0.01 mm keeps the curves and drops the redundant points.
    left = unary_union([grown_left.intersection(rbox), lbox.difference(grown_right)]).simplify(0.01)
    return left, box(*extent).difference(left)


def redesign_panels(data):
    import model as m
    cfg=data['config'];parts=data['parts'];instances=data['instances'];fab=cfg['fabrication']
    panels={};replacements={}
    def sheet_part(pid,name,shape,t,origin,group,note,parent=None):
        points=list(shape.exterior.coords)[:-1]
        m.add(pid,name,t,points,cuts=[list(r.coords)[:-1] for r in shape.interiors],category='Structure',note=note)
        p=parts[pid];dx,dy=p['origin_shift'];p['assembly_panel']=parent
        p['optional']=False;p['render_only']=False
        return m.put(pid,(origin[0]+dx,origin[1]+dy,origin[2]),group=group)
    CN=cfg['cnc'];PZ=fab['front_split']
    for parent in ('B01','F00','F01','F02','R02'):
        original=copy.deepcopy(parts[parent]);copies=[i for i in instances if i['part']==parent]
        shape=Polygon(original['outer'],original['cuts'])
        # Quadrants use the base centre. Floor seams avoid the rear pillar slots.
        cx,cy=original['width']/2,original['height']/2;roles=None
        if parent=='B01':
            # Offset the horizontal seam so the stop-post bores and their
            # countersinks remain wholly inside their fabrication sections.
            sy=cy+fab['base_seam_y']
            R=max(original['width'],original['height'])*2
            quad_angles=[(180,225),(225,270),(270,315),(315,360),(90,135),(135,180),(0,45),(45,90)]
            regions=[Polygon([(cx,sy)]+[(cx+R*math.cos(math.radians(a1+(a2-a1)*step/8)),sy+R*math.sin(math.radians(a1+(a2-a1)*step/8))) for step in range(9)]+[(cx,sy)]) for a1,a2 in quad_angles]
        elif parent in ('F01','F02'):
            # CNC finger joint: each half stops clearance/2 short of the shared path, and the inside corners are
            # relieved for the cutter, so the tabs seat fully. The teeth leave the middle flat for the puzzle seam.
            seam=cy+fab['seam_y']
            regions=[r.buffer(-CN['joint_clearance']/2,join_style=2) for r in finger_joint_regions(original['width'],original['height'],seam,flat=PZ['flat'])]
            zone=box(-1,seam-10,original['width']+1,seam+10)
        elif parent=='R02':
            t_ring=cfg['thickness']['detail']
            R=max(original['width'],original['height'])*2
            def ring_wedge(a1,a2):
                pts=[(cx,cy)]
                for a in range(int(a1),int(a2)+1,15):
                    rad=math.radians(a)
                    pts.append((cx+R*math.cos(rad),cy+R*math.sin(rad)))
                return Polygon(pts)
            regions=[ring_wedge(0,120),ring_wedge(120,240),ring_wedge(240,360)]
            roles=['section 1','section 2','section 3']
        else:
            seam=cy+fab['seam_y']
            regions=[box(-1,-1,original['width']+1,seam),box(-1,seam,original['width']+1,original['height']+1)]
        if parent in ('F00','F01','F02'):
            # The front of each floor, on show when the house opens, is two pieces joined on the house axis by a
            # puzzle joint: smaller pieces nest on A3, and the knobs lock the halves against pulling apart. Knobs
            # alternate sides, end_margin clear of the front point and of the cross seam.
            front=min(y for x,y in original['outer']);n=PZ['knobs'];a,b=front+PZ['end_margin'],seam-PZ['end_margin']
            knobs=[(a+(b-a)*k/(n-1) if n>1 else (a+b)/2,1 if k%2==0 else -1) for k in range(n)]
            halves=[r.buffer(-CN['joint_clearance']/2,join_style=2) for r in puzzle_regions(cx,(-10,-10,original['width']+10,original['height']+10),knobs,PZ['neck'],PZ['head'],PZ['reach'],CN['tool_diameter']/2+.5)]
            regions=[regions[0].intersection(halves[0]),regions[1],regions[0].intersection(halves[1])];roles=['front left','rear','front right']
        sections=[(p,role,0) for idx,(region,role) in enumerate(zip(regions,roles or [None]*len(regions))) for p in polygons(shape.intersection(region))]
        if parent in ('F01','F02'):sections=[(q,role,dz) for p,role,dz in sections for q in polygons(relieve_inside_corners(p,zone,CN['tool_diameter']/2))]
        instances[:]=[i for i in instances if i['part']!=parent]
        del parts[parent];ids=[]
        for k,(section,role,dz) in enumerate(sections):
            pid=parent if k==0 else f'{parent}{chr(65+k)}';ids.append(pid)
            cross='CNC finger joint' if parent!='F00' else 'straight seam'
            t_part=t_ring if parent=='R02' else original['thickness']
            if role and role.startswith('front'):note=f'Front piece, on show when the house is open. A puzzle joint on the house axis joins it to the other front piece and a {cross} to the rear piece: dry-fit, then press the knobs in from above and glue with PVA over the seam supports. Match the assembly positioning template. '
            elif parent in ('F01','F02'):note='CNC finger joint seam with relieved inside corners: interlock the teeth and glue with PVA over the seam supports. Match the assembly positioning template. '
            elif parent=='B01':note='Straight seam: glue over underside seam supports (cut from leftover material). Match the assembly positioning template. '
            elif parent=='R02':note=f'3 mm plywood ring section ({role}). Glue to internal cleats into a reinforcement ring. '
            else:note='Straight seam: glue over the supplied support pieces. Match the assembly positioning template. '
            part_name=original['name']+f' ({role})' if parent=='R02' else original['name']+' / '+(role or f'section {k+1}')
            m.add(pid,part_name,t_part,list(section.exterior.coords)[:-1],cuts=[list(r.coords)[:-1] for r in section.interiors],color='green' if parent=='B01' else 'red' if parent=='R02' else 'stone' if parent=='F00' else 'wood',note=note+original['note'])
            p=parts[pid]=m.PARTS[pid];dx,dy=p['origin_shift'];p['assembly_panel']=parent;p['optional']=False;p['render_only']=False
            p['holes']=[]
            for h in original['holes']:
                centre=Point(h['x'],h['y'])
                if not section.covers(centre):continue
                radius=max(h['diameter'],h.get('countersink',0))/2
                if not section.buffer(1e-6).covers(centre.buffer(radius)):
                    raise ValueError(f'{parent}: a drilling feature crosses a section seam; adjust the seam before fabrication')
                p['holes'].append(dict(h,x=h['x']-dx,y=h['y']-dy))
            for j,h in enumerate(p['holes']):h['id']=f'H{j+1:02}'
            for inst in copies:
                o=inst['origin'];placed=m.put(pid,(o[0]+dx,o[1]+dy,o[2]+dz),group=inst['group'],label=part_name)
                placed['design_part']=parent
                replacements.setdefault(inst['id'],[]).append((section,placed['id'],o))
        panels[parent]={'sections':ids,'copies':len(copies),'thickness':t_ring if parent=='R02' else original['thickness'],'outline':original['outer'],'cuts':original['cuts'],'origin':copies[0]['origin'],'seam_y':0 if parent=='R02' else fab['base_seam_y'] if parent=='B01' else fab['seam_y']}
        if roles:panels[parent]['front_split']={'x':cx,'knobs':[list(k) for k in knobs]}
    # Keep fastening references attached to the section carrying the screw/pivot.
    for item in data['fasteners']+data['joints']:
        changed=[]
        for old in item['parts']:
            if old not in replacements:changed.append(old);continue
            point=item.get('origin',item.get('position'))
            choices=replacements[old]
            hit=next((pid for shape,pid,o in choices if shape.buffer(.01).covers(MultiPoint([(point[0]-o[0],point[1]-o[1])]))),choices[0][1])
            changed.append(hit)
        item['parts']=changed
    # Underside base lift and rim pads. Base seam supports are cut by user from leftover materials.
    r=cfg['base_diameter']/2;t,width=fab['base_support'];t_base=t
    # Floor seam supports, clipped around anything already standing where they go. The plinth floor F00 sits on the
    # plinth walls, so a thin strip suffices there (and the drawer passes under it); the upper floors cantilever
    # over the open front, so they get wider strips across the seam.
    support_copies=[]
    def clipped(strip,z_top,depth):
        free=strip
        for inst in list(instances):
            p=parts[inst['part']]
            if p.get('assembly_panel') or p.get('render_only') or inst['group'] in ('Tools','Drawer'):continue
            pts=[[inst['origin'][n]+inst['u'][n]*x+inst['v'][n]*y+inst['w'][n]*d for n in range(3)] for x,y in p['outer'] for d in (0,p['thickness'])]
            if min(v[2] for v in pts)<z_top-.001 and max(v[2] for v in pts)>z_top-depth+.001:
                free=free.difference(MultiPoint([(v[0],v[1]) for v in pts]).convex_hull.buffer(.3))
        return polygons(free)
    for parent in ('F00','F01','F02'):
        panel=panels[parent];o=panel['origin'];world_shape=Polygon([(x+o[0],y+o[1]) for x,y in panel['outline']]);seam=fab['seam_y']
        if parent=='F00':
            # One strip under the straight seam and one under the puzzle seam between the front pieces, up to it.
            support_t,support_w=fab['plinth_floor_support'];x=o[0]+panel['front_split']['x']
            for strip in (box(-1000,seam-support_w/2,1000,seam+support_w/2),box(x-support_w/2,-1000,x+support_w/2,seam-support_w/2)):
                for shape in clipped(world_shape.intersection(strip),o[2],support_t):
                    pid=f'FS{len(support_copies)+1:02}'
                    inst=sheet_part(pid,f'Floor seam support {support_t:g} x {support_w:g} mm',shape,support_t,(0,0,o[2]-support_t),'Fixed','Centre on the seam: half its width bears on each half. Leave gaps at existing supports. Make a glued joint sample before assembly.',parent)
                    support_copies.append(inst['id'])
        else:
            support_t,support_w=fab['floor_support']
            zs=([data['derived']['floor_tops'][k]-panel['thickness'] for k in (1,2)] if parent=='F01' else [o[2]])
            for z in zs:
                # 60 mm either side of the seam: enough to splice the halves, and clear of the catch blocks that
                # swing under the front edge of the attic floor.
                for x in (40, 70, -40, -70):
                    for shape in clipped(world_shape.intersection(box(x-support_w/2,seam-60,x+support_w/2,seam+60)),z,support_t):
                        pid=f'FS{len(support_copies)+1:02}'
                        inst=sheet_part(pid,f'Floor seam support {support_t:g} x {support_w:g} mm',shape,support_t,(0,0,z-support_t),'Fixed','Glue across the finger-joint seam under both floor halves, on edge-grain-free faces. Make a glued joint sample before assembly.',parent)
                        support_copies.append(inst['id'])
    # Rim pads under the base, between the support cross: with only the cross touching the table the base would
    # tip about the lines joining its arm ends (0.71 of the radius); with pads it stands on nearly its full circle.
    ST=cfg['stability'];pw,pd=ST['pad'];np_=ST['pads']
    m.add('BP1','Base rim pad',t_base,m.rect(pd,pw),category='Structure',note=f'{np_} pads glued under B01 at its rim; stick a felt dot under each. All pads lie in one plane with the underside supports.')
    parts['BP1']['assembly_panel']='B01';parts['BP1']['optional']=False;parts['BP1']['render_only']=False
    for k in range(np_):
        a=math.radians(180/np_+k*360/np_);rr=r-pd/2-3;e=(math.cos(a),math.sin(a));t=(-e[1],e[0])
        m.put('BP1',(rr*e[0]-e[0]*pd/2-t[0]*pw/2,rr*e[1]-e[1]*pd/2-t[1]*pw/2,-t_base),(e[0],e[1],0),(t[0],t[1],0),'Fixed')
    # Raise the entire assembly to account for the underside base supports.
    lift=fab['base_lift']
    for inst in instances:inst['origin'][2]+=lift
    for item in data['hardware']:item['position'][2]+=lift
    for item in data['fasteners']:item['origin']=[*item['origin'][:2],item['origin'][2]+lift]
    for item in data['joints']:
        item['position'][2]+=lift
        item['outline']=[[*point[:2],point[2]+lift] for point in item['outline']]
    d=data['derived']
    for key in ('ground_floor','roof_eave','total_height'):d[key]+=lift
    d['floor_tops']=[z+lift for z in d['floor_tops']]
    for f in d['figures']:f['z']+=lift;f['top'][2]+=lift
    for dim in d['dimensions']:
        dim['label']=re.sub(r'\bZ(-?\d+(?:\.\d+)?)',lambda match:f'Z{float(match[1])+lift:g}',dim['label'])
        for key in ('a','b','p'):
            if key in dim:dim[key][2]+=lift
        for line in dim.get('ext',[]):
            for point in line:point[2]+=lift
    d['dimensions'][0]['a'][2]=0
    d['dimensions'][0]['label']=f'{d["total_height"]:g} total height'
    d['panels']=panels
    d['pillars']={'part':'P01','quantity':4,'length':parts['P01']['height'],'width':parts['P01']['width'],'thickness':parts['P01']['thickness'],'clearance':fab['pillar_clearance'],'floor_slots':4,'passes_through':['F01'],'seats_under':'F02'}
    for p in parts.values():
        p['note']=re.sub(r'\bZ(-?\d+(?:\.\d+)?)',lambda match:f'Z{float(match[1])+lift:g}',p['note'])
        p['quantity']=sum(i['part']==p['id'] for i in instances)
        if p['category']=='Walls' and p['id'].startswith('W'):
            p['retained_edges']=[{'axis':'y','value':0},{'axis':'y','value':p['height']}] if p['height']==420 else []
    # Merge repeated section/support geometry, while retaining design_part and panel maps.
    m.merge_identical()
    for parent,panel in panels.items():panel['sections']=sorted({i['part'] for i in instances if i.get('design_part')==parent})
