"""A3 fabrication sections, supported panel seams and continuous-pillar metadata."""
from __future__ import annotations
import copy
import re
from shapely.geometry import Polygon, box, MultiPoint, Point


def polygons(shape):
    if shape.is_empty:return []
    if shape.geom_type=='Polygon':return [shape]
    return [p for p in shape.geoms if p.geom_type=='Polygon' and p.area>0.01]


def finger_joint_regions(width, height, seam, tab_w=20.0, tab_h=10.0, margin=35.0):
    xmin, xmax = -10.0, width + 10.0
    path = [(xmin, seam), (margin, seam)]
    x = margin
    up = True
    while x + tab_w <= width - margin:
        ytab = seam + (tab_h / 2.0 if up else -tab_h / 2.0)
        path.extend([(x, ytab), (x + tab_w, ytab)])
        x += tab_w
        up = not up
    path.extend([(x, seam), (xmax, seam)])
    poly_lower = Polygon([(xmin, -10.0), (xmax, -10.0)] + list(reversed(path)))
    poly_upper = Polygon([(xmax, height + 10.0), (xmin, height + 10.0)] + path)
    return [poly_lower, poly_upper]


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
    for parent in ('B01','F00','F01','F02','R02'):
        original=copy.deepcopy(parts[parent]);copies=[i for i in instances if i['part']==parent]
        shape=Polygon(original['outer'],original['cuts'])
        # Quadrants use the base centre. Floor seams avoid the rear pillar slots.
        cx,cy=original['width']/2,original['height']/2
        if parent=='B01':
            # Offset the horizontal seam so the stop-post bores and their
            # countersinks remain wholly inside their fabrication sections.
            sy=cy+fab['base_seam_y']
            regions=[box(x0,y0,x1,y1) for x0,y0,x1,y1 in [(0,0,cx,sy),(cx,0,original['width'],sy),(0,sy,cx,original['height']),(cx,sy,original['width'],original['height'])]]
        elif parent=='F01':
            seam=cy+fab['seam_y']
            regions=finger_joint_regions(original['width'],original['height'],seam)
        else:
            seam=cy+(0 if parent=='R02' else fab['seam_y'])
            regions=[box(-1,-1,original['width']+1,seam),box(-1,seam,original['width']+1,original['height']+1)]
        sections=[p for region in regions for p in polygons(shape.intersection(region))]
        instances[:]=[i for i in instances if i['part']!=parent]
        del parts[parent];ids=[]
        for k,section in enumerate(sections):
            pid=parent if k==0 else f'{parent}{chr(65+k)}';ids.append(pid)
            note=('CNC interlocking puzzle / finger joint seam: interlock the CNC teeth and glue with PVA over the seam supports. Match the assembly positioning template. ' if parent=='F01' else 'Straight seam: glue over the supplied support pieces. Match the assembly positioning template. ')+original['note']
            m.add(pid,original['name']+f' / section {k+1}',original['thickness'],list(section.exterior.coords)[:-1],cuts=[list(r.coords)[:-1] for r in section.interiors],color='green' if parent=='B01' else 'red' if parent=='R02' else 'stone' if parent=='F00' else 'wood',note=note)
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
                o=inst['origin'];placed=m.put(pid,(o[0]+dx,o[1]+dy,o[2]),group=inst['group'],label=original['name']+f' / section {k+1}')
                placed['design_part']=parent
                replacements.setdefault(inst['id'],[]).append((section,placed['id'],o))
        panels[parent]={'sections':ids,'copies':len(copies),'thickness':original['thickness'],'outline':original['outer'],'cuts':original['cuts'],'origin':copies[0]['origin'],'seam_y':0 if parent=='R02' else fab['base_seam_y'] if parent=='B01' else fab['seam_y']}
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
    # Base: a coplanar cross of 4 mm supports and a centre pad, underneath.
    r=cfg['base_diameter']/2;t,width=fab['base_support'];half=width/2
    base_shape=Polygon(panels['B01']['outline']);base_shape=Polygon([(x-r,y-r) for x,y in base_shape.exterior.coords])
    sy=fab['base_seam_y']
    regions=[box(-half,sy-half,half,sy+half),box(-half,sy+half,half,r),box(-half,-r,half,sy-half),box(half,sy-half,r,sy+half),box(-r,sy-half,-half,sy+half)]
    for k,region in enumerate(regions,1):
        for shape in polygons(base_shape.intersection(region)):
            placed=sheet_part(f'BS{k:02}','Base seam support',shape,t,(0,0,-t),'Fixed','Glue underneath the base along its quarter seams. All supports lie in one plane; they raise the base by 4 mm. D8 access holes leave the garden-post screw heads accessible.','B01')
            support=parts[placed['part']]
            for fastener in data['fasteners']:
                x,y=fastener['origin'][:2]
                if any(pid.startswith('B01-') or pid.startswith(('B01B-','B01C-','B01D-')) for pid in fastener['parts']) and shape.contains(Point(x,y)):
                    support['holes'].append(dict(m.hole(x-placed['origin'][0],y-placed['origin'][1],8,None,'Stop-post screw access'),id=f'H{len(support["holes"])+1:02}'))
    # Floor seam supports: clip around existing upright supports to avoid overlap.
    support_t,support_w=fab['floor_support'];support_copies=[]
    for parent in ('F00','F01','F02'):
        panel=panels[parent];o=panel['origin'];world_shape=Polygon([(x+o[0],y+o[1]) for x,y in panel['outline']]);seam=fab['seam_y']
        if parent=='F00':
            strip=world_shape.intersection(box(-1000,seam-support_w/2,1000,seam+support_w/2))
            free=strip
            for inst in list(instances):
                p=parts[inst['part']]
                if inst['group']!='Fixed' or p.get('assembly_panel') or p.get('render_only'):continue
                pts=[[inst['origin'][n]+inst['u'][n]*x+inst['v'][n]*y+inst['w'][n]*depth for n in range(3)] for x,y in p['outer'] for depth in (0,p['thickness'])]
                if min(v[2] for v in pts)<o[2]-.001 and max(v[2] for v in pts)>o[2]-support_t+.001:
                    free=free.difference(MultiPoint([(v[0],v[1]) for v in pts]).convex_hull.buffer(.3))
            for shape in polygons(free):
                pid=f'FS{len(support_copies)+1:02}'
                inst=sheet_part(pid,'Floor seam support 4 x4 mm',shape,support_t,(0,0,o[2]-support_t),'Fixed','Centre on the seam: 2 mm bearing on each half. Leave gaps at existing supports. Make a glued joint sample before assembly.',parent)
                support_copies.append(inst['id'])
        else:
            zs=([data['derived']['floor_tops'][k]-panel['thickness'] for k in (1,2)] if parent=='F01' else [o[2]])
            for z in zs:
                for x in (40, 70, -40, -70):
                    shape=world_shape.intersection(box(x-support_w/2,-1000,x+support_w/2,1000))
                    pid=f'FS{len(support_copies)+1:02}'
                    inst=sheet_part(pid,'Floor seam support 4 x4 mm',shape,support_t,(0,0,z-support_t),'Fixed','Glue perpendicularly across the seam bridging both floor halves. Make a glued joint sample before assembly.',parent)
                    support_copies.append(inst['id'])
    # Ring seam bridges sit above the ring between the sloping cleats.
    panel=panels['R02'];o=panel['origin'];ring=Polygon([(x+o[0],y+o[1]) for x,y in panel['outline']],[[[x+o[0],y+o[1]] for x,y in cut] for cut in panel['cuts']])
    for k,side in enumerate((-1,1),1):
        region=box(-1000,-20,-.01,20) if side<0 else box(.01,-20,1000,20)
        for shape in polygons(ring.intersection(region)):
            sheet_part(f'RS{k:02}','Roof ring seam bridge',shape,4,(0,0,o[2]+panel['thickness']),'Roof','Glue above the ring across its seam, between the roof cleats.','R02')
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
    d['changes'][:]=['A3 plywood only; 420 /418 mm walls and 140 mm storeys.','Four continuous 8 mm P01 pillars pass through rectangular openings with CNC dogbone fillets (R2.0 mm corner relief) in both F01 levels.','F01 and F01B floor halves join with CNC interlocking puzzle/finger joints for rigid cantilever support during open play.','Wall butt hinges upgraded to 16 mm fasteners / M2.5 brass through-machine screws with decorative dome cap nuts on backing block A02.','Quartered base with 4 mm underside supports; divided floors and roof ring.']
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
