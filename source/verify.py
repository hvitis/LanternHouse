"""Independent release checks for fabrication coverage, dimensions and PDF scale."""
import csv,json,math,struct,zipfile,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pypdf import PdfReader
from model import fabrication_parts
ROOT=Path(__file__).resolve().parents[1]

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());p=data['parts'];build_parts=fabrication_parts(data);nest=json.loads((ROOT/'output/nesting.json').read_text());cad=json.loads((ROOT/'output/reports/cad-validation.json').read_text());checks=[]
    def check(name,condition,detail=''):
        checks.append({'check':name,'pass':bool(condition),'detail':detail})
    check('Valid native profiles',not cad['invalid_profiles'] and not cad['native_profile_mismatches'])
    check('Closed assembly has no solid overlap',not cad['collisions'])
    check('Wall motion / roof removal (veranda and furniture installed)',not cad['roof_lift_collisions'] and all(not w['collisions'] for w in cad['wall_swing']))
    check('Both entrance doors swing 0-90 degrees clear',len(cad['door_sweep'])==2 and all(not d['collisions'] for d in cad['door_sweep']),str([d['collisions'][:3] for d in cad['door_sweep']]))
    check(f'Hidden drawer slides out {cad["drawer_travel"]["travel_mm"]:g} mm clear',not cad['drawer_travel']['collisions'],str(cad['drawer_travel']['collisions'][:3]))
    check('Veranda keeps 10 mm clear in front of every window',not cad['window_occlusion'],str(cad['window_occlusion'][:3]))
    check('Starter holes entirely inside waste',not cad['starter_hole_errors'])
    check('Native and universal CAD reopened',cad['native_reopen_objects']>0 and cad['step_reopen_valid'] and cad['step_reopen_solids']==cad['house_instances'])
    cfg=data['config'];size=[cfg['base_diameter'],cfg['base_diameter'],cfg['height']]
    check(f'{cfg["height"]:g} mm high / D{cfg["base_diameter"]:g} round base',all(abs(a-b)<.001 for a,b in zip(cad['closed_assembly_bounds_mm'],size)),str([round(v,3) for v in cad['closed_assembly_bounds_mm']]))
    check('Window openings per floor: 5 / 6 / 6 / 1 dormer (counted from cut-outs)',data['derived']['windows_per_floor']==[5,6,6,1],str(data['derived']['windows_per_floor']))
    counts=Counter(i['part'] for i in data['instances']);check('CAD instance quantities',all(counts[id]==v['quantity'] for id,v in p.items()))
    # Independent design-rule quantities (from config / window cut-outs), not from the instance list itself.
    tower_windows=sum(data['derived']['windows_per_floor'][:3]);hinges=3*2*2
    # Windows: two horizontal and two vertical frame bars, a middle vertical bar and a crossbar (D01 x3, D02 x3).
    expected={'F01':2,'F02':1,'R01':11,'R06':1,'J01':54,'A02':hinges,'A06':hinges,'A03':4,'E01':2,'E10':2,'D03':12,'D01':3*tower_windows,'D02':3*tower_windows,'C01':4,'E03':1,'F00':1,'PL1':10,'DR4':2,'DR2':2,'DG1':2,'PT1':2 if 'PT2' in p else 3,'VS2':2,'VJ1':2,'VS3':2,'ES1':2,'ET1':2*(data['config']['stairs']['risers']-1),'MC1':2,'GP1':2}
    if 'PT2' in p:expected['PT2']=1
    walls=sum(v['quantity'] for k,v in p.items() if k.startswith('W') and v['category']=='Walls')
    check('Design-rule part quantities (12 wall facets)',walls==12 and all(k in p and p[k]['quantity']==v for k,v in expected.items()) and not {'D04','D05','VT1','TC01'}&set(p),str({k:(p.get(k,{}).get('quantity'),v) for k,v in expected.items() if p.get(k,{}).get('quantity')!=v}|{'walls':walls}))
    # Shared IDs cover required parts and the optional furniture, including rotated strips.
    from model import profile_key
    profiles=Counter(profile_key(v) for v in p.values())
    facets=data['derived']['facets']
    check('Identical build parts share one ID',max(profiles.values())==1 and len(facets)==12 and all(Counter(f['part'] for f in facets)[k]==p[k]['quantity'] for k in {f['part'] for f in facets}),str([k for k,n in profiles.items() if n>1][:2]))
    # Thermo-clay figures: one per storey on its floor, closed meshes, CAD solids matching the clay volume.
    figs=data['derived']['figures'];tops=data['derived']['floor_tops']
    check('One thermo-clay Moomin on each floor',sorted(f['level'] for f in figs)==[0,1,2] and all(abs(f['z']-tops[f['level']])<1e-6 for f in figs) and sorted(f['key'] for f in figs)==['mamma','pappa','troll'] and not any(k.startswith('FG') for k in p),str([(f['name'],f['level']) for f in figs]))
    meshes_ok=True
    for key,c in data['clay'].items():
        import base64,numpy as np
        V=np.frombuffer(base64.b64decode(c['mesh']['positions']),'<f4').reshape(-1,3).astype(float);F=np.frombuffer(base64.b64decode(c['mesh']['index']),'<u2').reshape(-1,3)
        a,b,cc=V[F[:,0]],V[F[:,1]],V[F[:,2]];vol=np.einsum('ij,ij->i',a,np.cross(b,cc)).sum()/6
        meshes_ok=meshes_ok and c['closed'] and abs(vol-c['volume_mm3'])<.02*c['volume_mm3'] and V[:,2].min()>=-1e-6 and abs(V[:,2].max()-c['height'])<.5
    cadfigs=cad.get('clay_figures',[])
    # The CAD solid is the plain union of the lumps: it must match that volume, and the smoothed clay can only add to it.
    check('Clay meshes closed and match the estimate; CAD solids match their lumps',meshes_ok and len(cadfigs)==3 and all(f['valid'] and abs(f['cad_volume_mm3']-f['lumps_volume_mm3'])<.02*f['lumps_volume_mm3'] and f['clay_volume_mm3']>=f['lumps_volume_mm3'] for f in cadfigs),str([(f['id'],f['cad_volume_mm3'],f['lumps_volume_mm3'],f['clay_volume_mm3']) for f in cadfigs]))
    check('No stairs or floor openings',not any(v['category']=='Stairs' for v in p.values()) and 'L02' not in p and not p['F01']['cuts'] and not p['F02']['cuts'] and sum('pivot' in h['purpose'] for h in p['F02']['holes'])==2)
    coverage=Counter();copies=set();unique=True
    optional=nest.get('optional_sheets',[])
    mixed=[s['id'] for s in nest['sheets'] if any(p[i['part']].get('optional') for i in s['items'])]+[s['id'] for s in optional if any(not p[i['part']].get('optional') for i in s['items'])]
    rendered={pid for pid,v in p.items() if v.get('render_only')}
    cut_ids={i['part'] for s in nest['sheets']+optional for i in s['items']}
    check('View-only furniture has no cutting stock or templates',not mixed and not optional and not rendered & cut_ids,str(sorted(rendered & cut_ids)))
    for sheet in nest['sheets']+optional:
        for item in sheet['items']:
            coverage[item['part']]+=1;key=(item['part'],item['copy'])
            unique=unique and key not in copies;copies.add(key)
    for id,v in p.items():
        if v['category'] in ('Purchased wood','Purchased packing'):coverage[id]+=v['quantity']
    check('Every required part has cutting stock / template',all(coverage[id]==v['quantity'] for id,v in build_parts.items()),str({id:(coverage[id],v['quantity']) for id,v in build_parts.items() if coverage[id]!=v['quantity']}))
    check('Unique numbered copies across cutting layouts',unique)
    check('Sheet bounds and lanes (12 mm jigsaw, 2 mm laser)',all(c['bounds_and_spacing']=='PASS' for c in nest['validation']) and len(nest['validation'])==len(nest['sheets'])+len(optional))
    # Every 3 mm part is on a laser sheet (A4, or A3 for the roof panels) with its laser files; an A4 one fits one printed page.
    laser=data['config']['laser'];lsheets=[s for s in nest['sheets']+optional if s['thickness']==laser['thickness']]
    a4ok=all(s['window']==laser['a4_window'] for s in lsheets if (s['width'],s['height'])==(210,297))
    files=all((ROOT/'output/dxf'/f'{s["id"]}-laser.{ext}').exists() for s in lsheets for ext in ('dxf','svg'))
    check(f'{laser["thickness"]:g} mm parts on A4/A3 laser sheets with laser files',bool(lsheets) and all(s['laser'] and (s['width'],s['height']) in ((210,297),(297,420)) and s['spacing']==laser['spacing'] for s in lsheets) and a4ok and files and not any(s.get('laser') for s in nest['sheets']+optional if s['thickness']!=laser['thickness']),str([(s['id'],s['width'],s['height']) for s in lsheets]))
    existing=data['config']['stock']['main']['6']['count'];original=sum(bool(s.get('existing_stock')) for s in nest['sheets']);extra6=sum(s['thickness']==6 and not s.get('existing_stock') for s in nest['sheets'])
    check('Existing 6 mm sheets used before extra 6 mm stock',original<=existing and (extra6==0 or original==existing),f'{original} existing, {extra6} extra')
    fast=Counter(f['type'] for f in data['fasteners']);check('Installed hardware counts',fast=={'SC1':24,'SC2':16,'SC3':6,'BL1':2},str(dict(fast)))
    check('Both doors have two hinges',sum(h['kind']=='Door butt hinge' for h in data['hardware'])==4)
    kinds=Counter(h['kind'] for h in data['hardware']);stop=data['config']['wall_stop']['angle']
    check(f'Magnetic walls: 2 catch + 2 stop magnets, 4 steel discs, walls open to the {stop:g}-degree stop posts',kinds['Catch magnet']==2 and kinds['Stop magnet']==2 and kinds['Steel disc']==4 and data['derived']['views']['open_angle']==stop and all(w['range_degrees']==[0,stop] for w in cad['wall_swing']),str(dict(kinds)))
    misfit=[f'{f["figure"]} / {f["doorway"]}' for f in data['derived']['figure_fit'] if not f['fits']]
    check('Every clay figure passes upright through every doorway',bool(data['derived']['figure_fit']) and not misfit,str(misfit))
    connections=json.loads((ROOT/'output/reports/furniture-connections.json').read_text());check('Movable furniture has connected pieces',connections['all_pass'])
    dxfs=True
    for id,v in build_parts.items():
        step=ROOT/'output/cad/parts'/f'{id}.step';dxf=ROOT/'output/dxf'/f'{id}.dxf'
        dxfs=dxfs and step.exists() and dxf.exists() and '\n$INSUNITS\n70\n4\n' in dxf.read_text()
    check('All individual STEP / millimetre DXF files',dxfs)
    view_files=[str(path.relative_to(ROOT/'output')) for pid in rendered for path in (ROOT/'output/cad/parts'/f'{pid}.step',ROOT/'output/dxf'/f'{pid}.dxf') if path.exists()]
    check('View-only furniture has no CAD exports',not view_files and not (ROOT/'output/cad/MoominHouse-furnished.step').exists(),str(view_files))
    from pdf_checks import checks as pdf_checks
    for name,passed,detail in pdf_checks(ROOT):check(name,passed,detail)
    pdfs={p.name:len(PdfReader(p).pages) for p in (ROOT/'output/pdf').glob('*.pdf')}
    template=PdfReader(ROOT/'output/pdf/Moomin-House-Cutting-Templates.pdf');stream=template.pages[0].get_contents().get_data().decode('latin1')
    check('100 mm calibration square stored at true scale','283.4646 283.4646 re' in stream)
    # Every 1:1 printable page (tiles, carriers, solid wood, hinge templates, decor) carries the 100 mm bar.
    missing=[]
    for name in ('Cutting-Templates','Decor','Clay-Family','Dimensioned-Parts','3mm-Hand-Templates'):
        for n,page in enumerate(PdfReader(ROOT/f'output/pdf/Moomin-House-{name}.pdf').pages,1):
            text=page.extract_text()
            if any(k in text for k in ('ACTUAL SIZE 100%','100% ACTUAL SIZE','outline actual size','Actual size / compare','print 100%','actual-size'))and '100 mm reference' not in text:missing.append(f'{name} p{n}')
    check('100 mm reference bar on every 1:1 page',not missing,str(missing[:5]))
    index=json.loads((ROOT/'output/reports/template-index.json').read_text());check('Every sheet has all tiled printouts',len(index)==len(nest['sheets']) and all(i['last_tile_page']-i['first_tile_page']+1==i['rows']*i['columns']-len(i['skipped_tiles']) for i in index))
    with zipfile.ZipFile(ROOT/'output/cad/MoominHouse.FCStd') as z:
        gui=ET.fromstring(z.read('GuiDocument.xml'));views=gui.find('ViewProviderData');native=ET.fromstring(z.read('Document.xml'))
        colorok=len(views)==len(native.find('Objects').findall('Object'))
        native_names={o.attrib['name'] for o in native.find('Objects').findall('Object')}
        display_names={i['id'].replace('-','_') for i in data['instances'] if i['part'] in rendered}
        profile_names={pid+'_Profile' for pid in rendered}
        check('View-only furniture is absent from the native CAD project',not (display_names|profile_names) & native_names)
        for i in data['instances']:
            if i['part'] in rendered:continue
            name=i['id'].replace('-','_');material=z.read('MoominMaterial_'+name);wanted=int((i.get('color') or p[i['part']]['color'])[1:]+'ff',16)
            vp=next(v for v in views if v.attrib['name']==name);props=vp.find('Properties')
            legacy=next(prop for prop in props if prop.attrib['name']=='ShapeColor').find('PropertyColor')
            colorok=colorok and len(material)==40 and struct.unpack('<IIIIIffIII',material)[2]==wanted and int(legacy.attrib['value'])==wanted and vp.find('Extensions') is not None
    check('Native CAD colors and visibility saved',colorok)
    out=ROOT/'output/reports'
    with (out/'parts.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['ID','Name','Quantity','Thickness mm','Width mm','Height mm','Stock category','Notes'])
        for id,v in build_parts.items():w.writerow([id,v['name'],v['quantity'],v['thickness'],round(v['width'],3),round(v['height'],3),v['category'],v['note']])
    with (out/'hardware.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['Code','Specification','Installed quantity','Suggested purchase','Placement'])
        from book import hardware_rows
        w.writerows(hardware_rows())
    with (out/'stock.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['Sheet','Thickness mm','Width mm','Height mm','Parts','Profile utilization %'])
        for s in nest['sheets']:w.writerow([s['id'],s['thickness'],s['width'],s['height'],len(s['items']),s['outer_profile_utilization_percent']])
    report={'all_pass':all(c['pass'] for c in checks),'checks':checks,'pdf_pages':pdfs,'part_profiles':len(build_parts),'wood_pieces_including_tools':sum(v['quantity'] for v in build_parts.values()),'render_only_profiles':len(rendered)}
    (out/'release-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    if not report['all_pass']:raise RuntimeError('Release checks failed')
if __name__=='__main__':main()
