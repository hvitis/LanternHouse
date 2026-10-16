"""Run with FreeCAD's Python, or exec from FreeCAD's Python console.

Creates actual Sketcher/Extrusion/Cut features and linked assembly instances.
Also performs solid-kernel checks and exports mesh geometry for illustrations.
"""
from __future__ import annotations
import json, math, os, sys, time, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
runtime_lib=Path(sys.executable).resolve().parent.parent/'lib'
if runtime_lib.exists():sys.path.insert(0,str(runtime_lib))
from model import build, CFG, fabrication_parts
import numpy as np
import clay
import FreeCAD as App
import Mesh
import Part
import Sketcher
try:
    if os.environ.get('LANTERNWOOD_HEADLESS')=='1':raise RuntimeError('headless')
    import FreeCADGui as Gui
    Gui.showMainWindow()
except Exception:
    Gui=None

def polygon(points):
    vs=[App.Vector(x,y,0) for x,y in points];return Part.makePolygon(vs+[vs[0]])
def profile_shape(p):
    if p.get('boxes'):
        boxes=[Part.makeBox(*box['size'],App.Vector(*box['origin'])) for box in p['boxes']]
        # Connected boards form one profile solid for CAD validation and collision checks.
        return boxes[0].multiFuse(boxes[1:]).removeSplitter() if len(boxes)>1 else boxes[0]
    if p.get('sphere'):   # a turned ball standing on its profile plane, with its dowel hole from below
        r=p['sphere'];shape=Part.makeSphere(r,App.Vector(r,r,r))
        for h in p['holes']:shape=shape.cut(Part.makeCylinder(h['diameter']/2,h['depth'] or 2*r,App.Vector(h['x'],h['y'],0)))
        return shape
    outer=Part.Wire(Part.makeCircle(p['outercircle'][2],App.Vector(p['outercircle'][0],p['outercircle'][1],0))) if p.get('outercircle') else polygon(p['outer'])
    shape=Part.Face(outer).extrude(App.Vector(0,0,p['thickness']))
    for c in p['cuts']:shape=shape.cut(Part.Face(polygon(c)).extrude(App.Vector(0,0,p['thickness'])))
    for h in p['holes']:
        depth=min(p['thickness'],h['depth'] or p['thickness'])
        z=0 if h.get('entry')=='bottom' else p['thickness']-depth
        shape=shape.cut(Part.makeCylinder(h['diameter']/2,depth,App.Vector(h['x'],h['y'],z)))
        if h.get('countersink'):
            shape=shape.cut(Part.makeCone(h['countersink']/2,h['diameter']/2,h['countersink_depth'],App.Vector(h['x'],h['y'],0)))
    return shape.removeSplitter()
def matrix(inst):
    m=App.Matrix()
    for c,key in enumerate(('u','v','w')):
        for r in range(3):setattr(m,f'A{r+1}{c+1}',inst[key][r])
    m.A14,m.A24,m.A34=inst['origin'];return m
def transformed(shape,inst):
    s=shape.copy()
    if 'scale' in inst:
        scale=App.Matrix();scale.A11,scale.A22,scale.A33=inst['scale']
        s=s.transformGeometry(scale)
    s.Placement=App.Placement(matrix(inst));return s
def color(hexval):return tuple(int(hexval[j:j+2],16)/255 for j in (1,3,5))
def thickness_alias(t):return 'Ply'+str(t).replace('.0','').replace('.','_')
def setcolor(obj,hexval,visible=True):
    if obj.ViewObject:
        obj.ViewObject.ShapeColor=color(hexval);obj.ViewObject.LineColor=(.15,.20,.20)
        obj.ViewObject.Visibility=visible
def figure_points(V,f):
    """Clay figure frame (snout +X) to its place in the house: turned by yaw, feet on its floor."""
    th=math.radians(f['yaw']);c,s=math.cos(th),math.sin(th)
    return np.stack([f['x']+V[:,0]*c-V[:,1]*s,f['y']+V[:,0]*s+V[:,1]*c,f['z']+V[:,2]],1)
def lump_solid(spec):
    """One clay lump as an exact solid (mm, figure frame), matching clay.py's distance functions."""
    kind,*args=spec;V=lambda p:App.Vector(*p)
    if kind=='ellipsoid':
        c,r,R=args
        if max(r)-min(r)<1e-9:return Part.makeSphere(r[0],V(c))
        m=App.Matrix()
        for i in range(3):
            for j in range(3):setattr(m,f'A{i+1}{j+1}',R[i][j]*r[j])
        m.A14,m.A24,m.A34=c;return Part.makeSphere(1).transformGeometry(m)
    if kind=='capsule':
        a,b,ra,rb=args;axis=V(b)-V(a)
        rod=Part.makeCylinder(ra,axis.Length,V(a),axis) if abs(ra-rb)<1e-9 else Part.makeCone(ra,rb,axis.Length,V(a),axis)
        return rod.fuse([Part.makeSphere(ra,V(a)),Part.makeSphere(rb,V(b))])
    if kind=='cylinder':
        c,r,h,rr=args;cyl=Part.makeCylinder(r,2*h,V(c)-App.Vector(0,0,h))
        return cyl.makeFillet(rr,[e for e in cyl.Edges if e.Curve.TypeId=='Part::GeomCircle'])
    if kind=='box':
        c,half,rr=args;box=Part.makeBox(*(2*v for v in half),V([c[k]-half[k] for k in range(3)]));return box.makeFillet(rr,box.Edges)
    if kind=='handle':
        c,R,r=args;torus=Part.makeTorus(R,r,V(c),App.Vector(0,1,0))
        return torus.common(Part.makeBox(4*R,4*r,2*R,V(c)-App.Vector(2*R,2*r,0)))
    raise ValueError(kind)
def clay_solid(f):
    """Exact CAD solid of a clay figure: the plain union of its lumps (no smoothed joins or apron),
    flat underside on z=0, scaled to millimetres, turned by yaw and set on its floor."""
    lumps=[lump_solid(spec) for spec,_ in clay.lumps_spec(f['key'])]
    solid=lumps[0].multiFuse(lumps[1:]).common(Part.makeBox(400,400,400,App.Vector(-200,-200,0))).removeSplitter()
    solid=solid.Solids[0] if len(solid.Solids)==1 else solid
    solid.rotate(App.Vector(0,0,0),App.Vector(0,0,1),f['yaw']);solid.translate(App.Vector(f['x'],f['y'],f['z']))
    return solid,len(solid.Faces)
def dxf(p,dest):
    """One part's 1:1 profile as an R12 DXF: outer and inner cuts, finished holes and blade-entry starters on layers."""
    from dxf_r12 import DXF
    d=DXF()
    if p.get('outercircle'):d.circle(*p['outercircle'],'CUT_OUTER')
    else:d.polyline(p['outer'],'CUT_OUTER')
    for c in p['cuts']:d.polyline(c,'CUT_INNER')
    for h in p['holes']:d.circle(h['x'],h['y'],h['diameter']/2,'DRILL_FINISHED')
    for h in p['starters']:d.circle(h['x'],h['y'],h['diameter']/2,'DRILL_STARTER_WASTE')
    d.save(dest)

def main():
    started=time.time();data=build();build_parts=fabrication_parts(data)
    for d in ('cad/parts','dxf','reports','previews'):(ROOT/'output'/d).mkdir(parents=True,exist_ok=True)
    for folder,suffix in [('cad/parts','*.step'),('dxf','*.dxf')]:
        for old in (ROOT/'output'/folder).glob(suffix):
            if old.stem not in build_parts:old.unlink()
    for old in (ROOT/'output/cad').glob('*-furnished.step'):old.unlink()
    doc=App.newDocument('LanternwoodHouse');doc.Label='Lanternwood House | 700 mm | 3 floors + attic'
    params=doc.addObject('Spreadsheet::Sheet','Parameters');params.Label='Dimensions and plywood thickness (mm)'
    values=[('OverallHeight',CFG['height']),('TowerDiameter',CFG['tower_diameter']),('RoofDiameter',CFG['roof_diameter']),('FloorPitch',CFG['floor_pitch']),('WallHeight',CFG['wall_height'])]+[(thickness_alias(t),t) for t in sorted(set(p['thickness'] for p in data['parts'].values()))]
    for row,(alias,value) in enumerate(values,1):params.set(f'A{row}',alias);params.set(f'B{row}',f'{value} mm');params.setAlias(f'B{row}',alias)
    library=doc.addObject('App::DocumentObjectGroup','ProfileLibrary');library.Label='Editable local profiles (hidden)'
    groups={}
    for group in sorted({i['group'] for i in data['instances'] if i['part'] in build_parts}|{'Fasteners','JointGuides','Figures'}):
        groups[group]=doc.addObject('App::DocumentObjectGroup',group);groups[group].Label={'Furniture':'Optional furniture','Figures':'Thermo-clay figures','Accessories':'Optional accessories','Drawer':'Hidden plinth drawer','RoomDoors':'Room door leaves','Garden':'Garden scene (display only)'}.get(group,group)
    native,shapes={},{ }
    for pid,p in data['parts'].items():
        if p.get('render_only'):
            shapes[pid]=profile_shape(p)
            continue
        print('Profile',pid,flush=True)
        if p.get('sphere'):
            final=doc.addObject('Part::Feature',pid+'_Turned');final.Shape=profile_shape(p);library.addObject(final)
            final.Label=f'{pid} | {p["name"]} | D{2*p["sphere"]:g} | x{p["quantity"]}'
            final.addProperty('App::PropertyString','PartID','Fabrication');final.PartID=pid
            final.addProperty('App::PropertyInteger','RequiredQuantity','Fabrication');final.RequiredQuantity=p['quantity']
            final.addProperty('App::PropertyString','AssemblyNote','Fabrication');final.AssemblyNote=p['note']
            native[pid]=final;shapes[pid]=profile_shape(p);setcolor(final,p['color'],False)
            dxf(p,ROOT/'output/dxf'/f'{pid}.dxf');shapes[pid].exportStep(str(ROOT/'output/cad/parts'/f'{pid}.step'))
            continue
        sketch=doc.addObject('Sketcher::SketchObject',pid+'_Profile');sketch.Label=f'{pid} | {p["name"]} | editable outline'
        if p.get('outercircle'):
            x,y,r=p['outercircle'];idx=sketch.addGeometry(Part.Circle(App.Vector(x,y,0),App.Vector(0,0,1),r),False);sketch.addConstraint(Sketcher.Constraint('Block',idx))
        for loop in ([] if p.get('outercircle') else [p['outer']])+p['cuts']:
            for a,b in zip(loop,loop[1:]+loop[:1]):
                idx=sketch.addGeometry(Part.LineSegment(App.Vector(*a,0),App.Vector(*b,0)),False)
                sketch.addConstraint(Sketcher.Constraint('Block',idx))
        library.addObject(sketch)
        ex=doc.addObject('Part::Extrusion',pid+'_Plywood');ex.Base=sketch;ex.Dir=App.Vector(0,0,1);ex.LengthFwd=p['thickness'];ex.Solid=True
        ex.setExpression('LengthFwd',f'Parameters.{thickness_alias(p["thickness"])}')
        library.addObject(ex);final=ex
        if p['holes']:
            cylinders=[]
            for h in p['holes']:
                cyl=doc.addObject('Part::Cylinder',f'{pid}_{h["id"]}_Drill');cyl.Radius=h['diameter']/2;cyl.Height=min(p['thickness'],h['depth'] or p['thickness']);cyl.Placement.Base=App.Vector(h['x'],h['y'],0 if h.get('entry')=='bottom' else p['thickness']-cyl.Height.Value)
                cyl.Label=f'{pid} {h["id"]} | D{h["diameter"]} | depth {h["depth"] or "through"}'
                library.addObject(cyl);cylinders.append(cyl)
                if h.get('countersink'):
                    cs=doc.addObject('Part::Cone',f'{pid}_{h["id"]}_Countersink');cs.Radius1=h['countersink']/2;cs.Radius2=h['diameter']/2;cs.Height=h['countersink_depth'];cs.Placement.Base=App.Vector(h['x'],h['y'],0);library.addObject(cs);cylinders.append(cs)
            if len(cylinders)==1:tool=cylinders[0]
            else:tool=doc.addObject('Part::MultiFuse',pid+'_DrillUnion');tool.Shapes=cylinders;library.addObject(tool)
            final=doc.addObject('Part::Cut',pid+'_Finished');final.Base=ex;final.Tool=tool;library.addObject(final)
        final.Label=f'{pid} | {p["name"]} | {p["thickness"]:g} mm | x{p["quantity"]}'
        final.addProperty('App::PropertyString','PartID','Fabrication');final.PartID=pid
        final.addProperty('App::PropertyInteger','RequiredQuantity','Fabrication');final.RequiredQuantity=p['quantity']
        final.addProperty('App::PropertyString','AssemblyNote','Fabrication');final.AssemblyNote=p['note']
        native[pid]=final;shapes[pid]=profile_shape(p)
        setcolor(final,p['color'],False)
        dxf(p,ROOT/'output/dxf'/f'{pid}.dxf')
        shapes[pid].exportStep(str(ROOT/'output/cad/parts'/f'{pid}.step'))
    print('Recomputing profiles',flush=True);doc.recompute();print('Profiles recomputed',flush=True)
    mesh=[];world={};links=[]
    for inst in data['instances']:
        if len(mesh)%50==0:print('Assembly instance',len(mesh),flush=True)
        pid=inst['part']
        if pid in build_parts:
            ln=doc.addObject('Part::Compound',inst['id'].replace('-','_'));ln.Links=[native[pid]];ln.Placement=App.Placement(matrix(inst));ln.Label=f'{pid} | {inst["label"]}'
            ln.addProperty('App::PropertyString','PartID','Fabrication');ln.PartID=pid
            groups[inst['group']].addObject(ln);setcolor(ln,inst.get('color') or data['parts'][pid]['color'],inst['group'] not in ('Tools','Accessories'))
            links.append(ln)
        ws=transformed(shapes[pid],inst);world[inst['id']]=ws
        verts,faces=ws.tessellate(.8)
        mesh.append({'id':inst['id'],'part':pid,'design_part':inst['design_part'],'group':inst['group'],'color':inst.get('color') or data['parts'][pid]['color'],'vertices':[[v.x,v.y,v.z] for v in verts],'faces':faces})
    # Thermo-clay Rowan family: one exact solid per figure (its lumps, unsmoothed) for the native project and
    # every clearance check; the smoothed clay mesh is for the viewer and the renders.
    figures=[]
    DOMINANT_COLOR={'elias':clay.COLOURS['navy'],'mira':clay.COLOURS['sage'],'ada':clay.COLOURS['rust'],'theo':clay.COLOURS['mustard']}
    for f in data['derived']['figures']:
        print('Clay figure',f['id'],flush=True)
        solid,faces=clay_solid(f);name=f['id'].replace('-','_')
        obj=doc.addObject('Part::Feature',name);obj.Shape=solid;obj.Label=f'{f["id"]} | {f["name"]} | thermo-clay, {f["room"]}';groups['Figures'].addObject(obj);setcolor(obj,DOMINANT_COLOR.get(f['key'],clay.COLOURS['skin']))
        obj.addProperty('App::PropertyString','ClayNote','Fabrication');obj.ClayNote=f'{f["name"]}, {f["height"]:g} mm tall, about {clay.stats(f["key"])["volume_mm3"]/1000:.1f} cm3 of oven-hardening clay'
        world[f['id']]=solid;figures.append({'id':f['id'],'part':f['code'],'group':'Figures','faces':faces,'valid':solid.isValid(),'cad_volume_mm3':round(solid.Volume,1),
            'lumps_volume_mm3':round(clay.hard_volume(f['key']),1),'clay_volume_mm3':round(clay.stats(f['key'])['volume_mm3'],1)})
        V,F,_,C,_=clay.mesh(f['key'],1.5);palette=list(clay.COLOURS.values())
        c_faces=C[F]
        face=np.where(c_faces[:,0]==c_faces[:,1],c_faces[:,0],np.where(c_faces[:,1]==c_faces[:,2],c_faces[:,1],c_faces[:,0]))
        mesh.append({'id':f['id'],'part':f['code'],'group':'Figures','color':DOMINANT_COLOR.get(f['key'],palette[0]),'face_colors':[palette[k] for k in face],'vertices':np.round(figure_points(V,f),3).tolist(),'faces':F.tolist()})
    # Explicit screw / bolt reference solids, with real axes and tapered tips.
    for f in data['fasteners']:
        axis=App.Vector(*f['axis']);origin=App.Vector(*f['origin']);length=f['length'];tip=2 if f['type']!='BL1' else .3
        headdepth=0 if f['type']=='BL1' else f['head_height']
        shank=Part.makeCylinder(f['diameter']/2,length-tip-headdepth,origin+axis*headdepth,axis)
        tipshape=Part.makeCone(f['diameter']/2,0,tip,origin+axis*(length-tip),axis)
        head=Part.makeCylinder(f['head_diameter']/2,f['head_height'],origin,-axis) if f['type']=='BL1' else Part.makeCone(f['head_diameter']/2,f['diameter']/2,f['head_height'],origin,axis)
        shape=Part.makeCompound([shank,tipshape,head])
        obj=doc.addObject('Part::Feature',f['id'].replace('-','_'));obj.Shape=shape;obj.Label=f'{f["id"]} | {f["type"]} {f["diameter"]:g} x {length:g}';groups['Fasteners'].addObject(obj);setcolor(obj,'#C19A55',False)
        obj.addProperty('App::PropertyString','FasteningNote','Fabrication');obj.FasteningNote=f['note']
    # Hide construction library without disabling links to its objects.
    for obj in library.Group:
        if obj.ViewObject:obj.ViewObject.Visibility=False
    doc.recompute();doc.saveAs(str(ROOT/'output/cad/LanternwoodHouse.FCStd'))
    # Furniture exists only in the preview meshes and viewer data, never in CAD deliverables.
    house=[world[i['id']] for i in data['instances'] if i['group'] not in ('Tools','Accessories','Furniture','Figures','Garden')]
    Part.makeCompound(house).exportStep(str(ROOT/'output/cad/LanternwoodHouse.step'))
    # Alternative open assembly and exploded assembly as real solid CAD exports.
    open_shapes=[];exploded=[];views=data['derived']['views']
    for inst in data['instances']:
        if inst['group'] in ('Tools','Accessories','Furniture','Figures','Garden'):continue
        s=world[inst['id']].copy();e=s.copy();g=inst['group']
        if g in ('WallLeft','WallRight'):
            sign=1 if g=='WallRight' else -1;x=data['derived']['hinge_axes'][g][0]
            s.rotate(App.Vector(x,0,0),App.Vector(0,0,1),sign*views['open_angle'])
        if g in views['open']:s.translate(App.Vector(*views['open'][g]))
        if g in views['exploded']:e.translate(App.Vector(*views['exploded'][g]))
        open_shapes.append(s);exploded.append(e)
    Part.makeCompound(open_shapes).exportStep(str(ROOT/'output/cad/LanternwoodHouse-open.step'))
    Part.makeCompound(exploded).exportStep(str(ROOT/'output/cad/LanternwoodHouse-exploded.step'))
    add_contact_joints(data,world)
    for j in data['joints']:
        p=App.Vector(*j['position']);axis=App.Vector(*j['axis']);wire=Part.makeLine(p-axis*15,p+axis*15)
        if j.get('outline'):wire=Part.makeCompound([wire,Part.makePolygon([App.Vector(*v) for v in j['outline']+[j['outline'][0]]])])
        obj=doc.addObject('Part::Feature',j['id'].replace('-','_'));obj.Label=j['id']+' | '+j['type'];obj.Shape=wire;groups['JointGuides'].addObject(obj)
        obj.addProperty('App::PropertyString','JointNote','Fabrication');obj.JointNote=j['glue'];setcolor(obj,'#B56535',False)
    native_mismatches=[]
    for pid,obj in native.items():
        if not obj.Shape.isValid() or abs(obj.Shape.Volume-shapes[pid].Volume)>.05:native_mismatches.append(pid)
    doc.recompute();doc.saveAs(str(ROOT/'output/cad/LanternwoodHouse.FCStd'))
    (ROOT/'output/parts.json').write_text(json.dumps(data,indent=2))
    (ROOT/'output/previews/mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
    report=validate(data,shapes,world,figures)
    report['clay_figures']=figures;report['figure_door_fit']=data['derived']['figure_fit']
    report['native_profile_mismatches']=native_mismatches
    report['runtime_seconds']=round(time.time()-started,1);report['freecad_version']='.'.join(App.Version()[:3])
    (ROOT/'output/reports/cad-validation.json').write_text(json.dumps(report,indent=2))
    # Close and reopen the delivered native file, then re-read universal solids.
    App.closeDocument(doc.Name);reopened=App.openDocument(str(ROOT/'output/cad/LanternwoodHouse.FCStd'));reopened.recompute()
    report['native_reopen_objects']=len(reopened.Objects)
    step=Part.Shape();step.read(str(ROOT/'output/cad/LanternwoodHouse.step'));report['step_reopen_solids']=len(step.Solids)
    report['step_reopen_valid']=step.isValid();(ROOT/'output/reports/cad-validation.json').write_text(json.dumps(report,indent=2))
    # FreeCAD writes timestamped .FCBak copies when a document is saved over itself; they are not deliverables.
    for backup in (ROOT/'output/cad').glob('*.FCBak'):backup.unlink()
    print(json.dumps({k:v for k,v in report.items() if k!='collisions'},indent=2),flush=True)
    # Any failed check stops the build here, before nesting, renders and the book are made from a bad model.
    failed=failures(report,data)
    if failed:print(f'CAD CHECKS FAILED ({len(failed)}) - do not build:\n'+'\n'.join('  - '+f for f in failed[:40]),flush=True);sys.exit(1)

def failures(report,data):
    """Every failed CAD check as a readable line; an empty list means the house can be built."""
    out=[f'Invalid profile {p}' for p in report['invalid_profiles']]+[f'Native profile differs from its exported solid: {p}' for p in report.get('native_profile_mismatches',[])]
    out+=[f'Overlap {c["a"]} / {c["b"]}: {c["volume_mm3"]} mm3' for c in report['collisions']]
    out+=[f'{w["group"]} at {h["angle"]} degrees: {h["moving"]} hits {h["obstacle"]}' for w in report['wall_swing'] for h in w['collisions']]
    out+=[f'Door {d["door"]} at {h["angle"]} degrees: {h["moving"]} hits {h["obstacle"]}' for d in report['door_sweep'] for h in d['collisions']]
    out+=[f'Drawer at {h["travel_mm"]} mm: {h["part"]} hits {h["obstacle"]}' for h in report['drawer_travel']['collisions']]
    out+=[f'Roof lifted {h["lift_mm"]} mm: {h["roof"]} hits {h["obstacle"]}' for h in report['roof_lift_collisions']]
    out+=[f'{h["obstacle"]} stands within 10 mm of a window in {h["wall"]}' for h in report['window_occlusion']]
    out+=[f'Starter hole not in waste: {s}' for s in report['starter_hole_errors']]
    if 'step_reopen_valid' in report and not (report['step_reopen_valid'] and report['step_reopen_solids']==report['house_instances']):out.append('The house STEP does not reopen as valid solids')
    out+=[f'{f["figure"]} does not pass the {f["doorway"]}: {f["spare_width"]} mm spare width, {f["spare_height"]} mm spare height' for f in data['derived']['figure_fit'] if not f['fits']]
    return out

# Tessellated shapes report boxes up to ~0.1 mm small, so the collision pre-filter accepts near misses.
PREFILTER=-.5
def bbox_overlap(a,b,tol=.02):
    return all(min(getattr(a,hi),getattr(b,hi))-max(getattr(a,lo),getattr(b,lo))>tol for lo,hi in [('XMin','XMax'),('YMin','YMax'),('ZMin','ZMax')])
def add_contact_joints(data,world):
    items=[i for i in data['instances'] if not data['parts'][i['part']].get('render_only') and i['group'] in ('Fixed','Porch','Roof','Drawer')]
    axes=[('XMin','XMax'),('YMin','YMax'),('ZMin','ZMax')]
    for k,a in enumerate(items):
        for b in items[k+1:]:
            if a['group']!=b['group']:continue
            if a['group'] in ('Furniture','Figures') and a.get('design_part',a['part'])[:2]!=b.get('design_part',b['part'])[:2]:continue
            if a['group']=='Porch' and a['part'].startswith('PC')!=b['part'].startswith('PC'):continue
            sa,sb=world[a['id']],world[b['id']];ba,bb=sa.BoundBox,sb.BoundBox
            lo=[max(getattr(ba,v[0]),getattr(bb,v[0])) for v in axes];hi=[min(getattr(ba,v[1]),getattr(bb,v[1])) for v in axes];span=[hi[n]-lo[n] for n in range(3)]
            flat=[n for n,s in enumerate(span) if abs(s)<1e-6]
            if len(flat)!=1 or any(s<-1e-6 for s in span):continue
            normal=flat[0];other=[n for n in range(3) if n!=normal]
            if min(span[n] for n in other)<2.9:continue
            pos=[(lo[n]+hi[n])/2 for n in range(3)];p=App.Vector(*pos)
            if not sa.isInside(p,1e-6,True) or not sb.isInside(p,1e-6,True):continue
            axis=[0,0,0];axis[normal]=1
            outline=[]
            for x,y in [(lo[other[0]],lo[other[1]]),(hi[other[0]],lo[other[1]]),(hi[other[0]],hi[other[1]]),(lo[other[0]],hi[other[1]])]:
                v=pos.copy();v[other[0]]=x;v[other[1]]=y;outline.append(v)
            kind='J1 supported face joint' if a['group']=='Fixed' else 'J5 furniture / veranda glued joint'
            data['joints'].append({'id':f'J-Auto-{len(data["joints"])+1:03}','type':kind,'parts':[a['id'],b['id']],'position':pos,'axis':axis,'outline':outline,'glue':'PVA on the outlined mating face. Keep square during cure.','contact_area_mm2':round(span[other[0]]*span[other[1]],2)})
def validate(data,shapes,world,figures):
    bad=[pid for pid,s in shapes.items() if not s.isValid() or len(s.Solids)!=1]
    installed=[i for i in data['instances'] if i['group'] not in ('Tools','Accessories')]+figures
    collisions=[]
    for n,a in enumerate(installed):
        sa=world[a['id']]
        for b in installed[n+1:]:
            sb=world[b['id']]
            if not bbox_overlap(sa.BoundBox,sb.BoundBox,PREFILTER):continue
            common=sa.common(sb);volume=common.Volume
            if volume>.05:collisions.append({'a':a['id'],'b':b['id'],'volume_mm3':round(volume,3)})
    def hits_any(shape,obstacles,threshold=.2):
        return [ob['id'] for ob in obstacles if bbox_overlap(shape.BoundBox,world[ob['id']].BoundBox,PREFILTER) and shape.common(world[ob['id']]).Volume>threshold]
    swing=[];open_angle=data['derived']['views']['open_angle']
    # The permanent veranda and the optional furniture are obstacles: the walls must clear both.
    obstacles=[i for i in installed if i['group'] in ('Fixed','Furniture','Figures','RoofLocks','Roof','Porch')]
    for group,sign in [('WallRight',1),('WallLeft',-1)]:
        moving=[i for i in installed if i['group']==group];axis=App.Vector(data['derived']['hinge_axes'][group][0],0,0)
        hits=[]
        for angle in sorted(set(range(0,int(open_angle)+1,5))|{open_angle}):   # every 5 degrees and the stop itself
            for inst in moving:
                s=world[inst['id']].copy();s.rotate(axis,App.Vector(0,0,1),sign*angle)
                for ob in obstacles:
                    target=world[ob['id']]
                    if bbox_overlap(s.BoundBox,target.BoundBox,PREFILTER) and s.common(target).Volume>.2:
                        hits.append({'angle':angle,'moving':inst['id'],'obstacle':ob['id']})
        swing.append({'group':group,'range_degrees':[0,open_angle],'step_degrees':5,'collisions':hits})
    # Each door swings outward 0-90 degrees about its hinge axis with walls closed and everything installed.
    door_sweep=[]
    for door_id in sorted({h['door'] for h in data['hardware'] if h['kind'] in ('Door butt hinge','Room door hinge')}):
        hinge=next(h for h in data['hardware'] if h.get('door')==door_id);moving=hinge['moves_with']
        axis=App.Vector(hinge['position'][0],hinge['position'][1],0);out=App.Vector(*hinge['outward'],0)
        shapes_m=[world[m] for m in moving];centre=world[door_id].BoundBox.Center
        def turned(shape,deg):
            t=shape.copy();t.rotate(axis,App.Vector(0,0,1),deg);return t
        sign=1 if (turned(world[door_id],10).BoundBox.Center-centre).dot(out)>0 else -1
        others=[i for i in installed if i['id'] not in moving];hits=[]
        for angle in range(5,91,5):
            for m,shape in zip(moving,shapes_m):
                for ob in hits_any(turned(shape,sign*angle),others):hits.append({'angle':angle,'moving':m,'obstacle':ob})
        door_sweep.append({'door':door_id,'range_degrees':[0,90],'step_degrees':5,'collisions':hits})
    # The hidden drawer slides out along its direction in 10 mm steps without touching anything else.
    drawer=[i for i in installed if i['group']=='Drawer'];dd=data['derived']['drawer'];drawer_hits=[]
    others=[i for i in installed if i['group']!='Drawer']
    drawer_steps=sorted(set(range(0,int(dd['travel'])+1,10))|{dd['travel']})
    for step in drawer_steps:
        for i in drawer:
            moved=world[i['id']].copy();moved.translate(App.Vector(dd['direction'][0]*step,dd['direction'][1]*step,0))
            for ob in hits_any(moved,others):drawer_hits.append({'travel_mm':step,'part':i['id'],'obstacle':ob})
    # Nothing on the veranda may stand within 10 mm in front of a window opening.
    occlusion=[];porch=[i for i in installed if i['group']=='Porch']
    for inst in installed:
        p=data['parts'].get(inst['part'])
        if not p or p['category']!='Walls' or not inst['part'].startswith('W'):continue
        for c in p['cuts']:
            xs=[v[0] for v in c];ys=[v[1] for v in c]
            zone=Part.makeBox(max(xs)-min(xs),max(ys)-min(ys),10,App.Vector(min(xs),min(ys),p['thickness']))
            zone=transformed(zone,inst)
            for ob in hits_any(zone,porch,.05):occlusion.append({'wall':inst['id'],'window_at':[min(xs),min(ys)],'obstacle':ob})
    roof_lift=[]
    # Release both horizontal turn-buttons before lifting the complete roof.
    locked=[i for i in installed if i['group']=='RoofLocks'];released={}
    for inst in locked:
        s=world[inst['id']].copy();pivot=s.BoundBox.Center
        f=next(f for f in data['fasteners'] if inst['id'] in f['parts']);pivot=App.Vector(f['origin'][0],f['origin'][1],497)
        s.rotate(pivot,App.Vector(0,0,1),90);released[inst['id']]=s
    for dz in (0,1,3,10,50,200):
        for ri in [i for i in installed if i['group']=='Roof']:
            s=world[ri['id']].copy();s.translate(App.Vector(0,0,dz))
            for ob in [i for i in installed if i['group']!='Roof']:
                t=released.get(ob['id'],world[ob['id']])
                if bbox_overlap(s.BoundBox,t.BoundBox,PREFILTER) and s.common(t).Volume>.2:roof_lift.append({'lift_mm':dz,'roof':ri['id'],'obstacle':ob['id']})
    starter_errors=[]
    for pid,p in data['parts'].items():
        for sh in p['starters']:
            waste=Part.Face(polygon(p['cuts'][sh['cut']-1])).extrude(App.Vector(0,0,1));drill=Part.makeCylinder(sh['diameter']/2+2,1,App.Vector(sh['x'],sh['y'],0))
            if drill.cut(waste).Volume>.001:starter_errors.append(f'{pid}-{sh["id"]}')
    # Exact bounds: the default BoundBox follows the 0.8 mm display tessellation on curved faces.
    box=Part.makeCompound([world[i['id']] for i in installed if i.get('group')!='Garden']).optimalBoundingBox(False,False)
    return {'profile_count':len(fabrication_parts(data)),'render_only_profiles':len(shapes)-len(fabrication_parts(data)),'installed_instances':len(installed),'house_instances':sum(i['group'] not in ('Furniture','Figures','Garden') for i in installed),'optional_furniture_instances':sum(i['group'] in ('Furniture','Figures','Garden') for i in installed),'invalid_profiles':bad,'closed_assembly_bounds_mm':[box.XLength,box.YLength,box.ZLength],'collisions':collisions,'wall_swing':swing,'roof_lift_collisions':roof_lift,'door_sweep':door_sweep,'drawer_travel':{'travel_mm':dd['travel'],'checked_travel_mm':drawer_steps,'collisions':drawer_hits},'window_occlusion':occlusion,'starter_hole_errors':starter_errors,'windows_per_floor':data['derived']['windows_per_floor'],'wall_swing_configuration':'Permanent veranda, roof and optional furniture all installed while the walls swing.','physical_validation_required':['Measured plywood thickness','Actual hinge footprint and screw head seating','Continuous hinge movement between sampled angles','Glue bond strength, roof catches and tip resistance','Printer scale and test joints']}

if __name__=='__main__':main()
