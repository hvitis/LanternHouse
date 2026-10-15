"""Independent release checks for fabrication coverage, dimensions and PDF scale."""
import csv,json,math,struct,zipfile,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pypdf import PdfReader
from model import fabrication_parts, BOUGHT
ROOT=Path(__file__).resolve().parents[1]

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());p=data['parts'];build_parts=fabrication_parts(data);nest=json.loads((ROOT/'output/nesting.json').read_text());cad=json.loads((ROOT/'output/reports/cad-validation.json').read_text());checks=[]
    def check(name,condition,detail=''):
        checks.append({'check':name,'pass':bool(condition),'detail':detail})
    check('Valid native profiles',not cad['invalid_profiles'] and not cad['native_profile_mismatches'])
    check('Closed assembly has no solid overlap',not cad['collisions'])
    check('Wall motion / roof removal (veranda and furniture installed)',not cad['roof_lift_collisions'] and all(not w['collisions'] for w in cad['wall_swing']))
    doors=sum(h['kind']=='Door butt hinge' for h in data['hardware'])//2+sum(h['kind']=='Room door hinge' for h in data['hardware'])
    check(f'All {doors} doors (three entrances, three room doors) swing 0-90 degrees clear',len(cad['door_sweep'])==doors==6 and all(not d['collisions'] for d in cad['door_sweep']),str([d['collisions'][:3] for d in cad['door_sweep']]))
    check(f'Hidden drawer slides out {cad["drawer_travel"]["travel_mm"]:g} mm clear',not cad['drawer_travel']['collisions'],str(cad['drawer_travel']['collisions'][:3]))
    check('Veranda keeps 10 mm clear in front of every window',not cad['window_occlusion'],str(cad['window_occlusion'][:3]))
    check('Starter holes entirely inside waste',not cad['starter_hole_errors'])
    check('Native and universal CAD reopened',cad['native_reopen_objects']>0 and cad['step_reopen_valid'] and cad['step_reopen_solids']==cad['house_instances'])
    cfg=data['config'];size=[cfg['base_diameter'],cfg['base_diameter'],cfg['height']]
    check(f'{cfg["height"]:g} mm high / D{cfg["base_diameter"]:g} round base',all(abs(a-b)<.001 for a,b in zip(cad['closed_assembly_bounds_mm'],size)),str([round(v,3) for v in cad['closed_assembly_bounds_mm']]))
    dormers=len(cfg['dormer']['over'])
    check(f'Window openings per floor: 5 / 6 / 6 / {dormers} dormers (from the window openings)',data['derived']['windows_per_floor']==[5,6,6,dormers],str(data['derived']['windows_per_floor']))
    counts=Counter(i['part'] for i in data['instances']);check('CAD instance quantities',all(counts[id]==v['quantity'] for id,v in p.items()))
    # Independent design-rule quantities (from config / window cut-outs), not from the instance list itself.
    tower_windows=sum(data['derived']['windows_per_floor'][:3]);hinges=3*2*2
    # Windows: one surround and one PET pane each; the cross between the panes is the wall itself.
    treads=data['config']['stairs']['risers']-1
    # Corner braces: nine corners per height (no hinge or front-seam corner), six heights; a rib holds two corners
    # and the fixed shell's fifth corner takes a bracket.
    ribs,brackets=6*4,6*1
    expected={'R01':12-dormers,'R06':dormers,'DM01':dormers,'DM06':dormers,'GZ2':dormers,'A02':hinges,'A06':hinges,'A03':6,'E01':2,'E04':1,'E10':2,'E11':1,'D03':12,'WF1':tower_windows,'GZ1':tower_windows,'C01':8,'E03':1,'PL1':10,'DR4':2,'DR2':2,'DG1':2,'PT1':2 if 'PT2' in p else 3,'PD1':3,'VS2':2,'VJ1':2,'VS3':2,'ES1':4,'ET1':3*treads,'MC1':2,'GP1':2,'DS1':1,'RL1':1,'BP1':cfg['stability']['pads'],'BL2':cfg['stability']['ballast'][0],'AB1':1}
    if 'PT2' in p:expected['PT2']=1
    braces=(sum(p.get(k,{}).get('quantity',0) for k in ('J01','J03')),sum(p.get(k,{}).get('quantity',0) for k in ('J02','J04')))
    walls=sum(v['quantity'] for k,v in p.items() if k.startswith('W') and v['category']=='Walls')
    battens=sum(v['quantity'] for k,v in p.items() if k.startswith('BT'))
    check('Design-rule part quantities (12 wall facets, 9 seam battens, 24 ribs and 6 brackets)',walls==12 and battens==9 and braces==(ribs,brackets) and all(k in p and p[k]['quantity']==v for k,v in expected.items()) and not {'D01','D02','D04','D05','DM07','E02','VT1','TC01'}&set(p),str({k:(p.get(k,{}).get('quantity'),v) for k,v in expected.items() if p.get(k,{}).get('quantity')!=v}|{'walls':walls,'battens':battens,'ribs, brackets':braces}))
    # Shared IDs cover required parts and the optional furniture, including rotated strips.
    from model import profile_key
    profiles=Counter(profile_key(v) for v in p.values())
    facets=data['derived']['facets']
    check('Identical build parts share one ID',max(profiles.values())==1 and len(facets)==12 and all(Counter(f['part'] for f in facets)[k]==p[k]['quantity'] for k in {f['part'] for f in facets}),str([k for k,n in profiles.items() if n>1][:2]))
    # Thermo-clay figures: one per storey on its floor, closed meshes, CAD solids matching the clay volume.
    figs=data['derived']['figures'];tops=data['derived']['floor_tops']
    placed=[(f['key'],f['level']) for f in figs];wanted=[(k,n) for n,keys in enumerate(cfg['figures']['levels']) for k in keys]
    check('Every clay figure stands on its configured storey',placed==wanted and all(abs(f['z']-tops[f['level']])<1e-6 for f in figs) and not any(k.startswith('FG') for k in p),str([(f['name'],f['level']) for f in figs]))
    meshes_ok=True
    for key,c in data['clay'].items():
        import base64,numpy as np
        V=np.frombuffer(base64.b64decode(c['mesh']['positions']),'<f4').reshape(-1,3).astype(float);F=np.frombuffer(base64.b64decode(c['mesh']['index']),'<u2').reshape(-1,3)
        a,b,cc=V[F[:,0]],V[F[:,1]],V[F[:,2]];vol=np.einsum('ij,ij->i',a,np.cross(b,cc)).sum()/6
        meshes_ok=meshes_ok and c['closed'] and abs(vol-c['volume_mm3'])<.02*c['volume_mm3'] and V[:,2].min()>=-1e-6 and abs(V[:,2].max()-c['height'])<.5
    cadfigs=cad.get('clay_figures',[])
    # The CAD solid is the plain union of the lumps: it must match that volume, and the smoothed clay can only add to it.
    check('Clay meshes closed and match the estimate; CAD solids match their lumps',meshes_ok and len(cadfigs)==len(figs) and all(f['valid'] and abs(f['cad_volume_mm3']-f['lumps_volume_mm3'])<.02*f['lumps_volume_mm3'] and f['clay_volume_mm3']>=f['lumps_volume_mm3'] for f in cadfigs),str([(f['id'],f['cad_volume_mm3'],f['lumps_volume_mm3'],f['clay_volume_mm3']) for f in cadfigs]))
    panels=data['derived']['panels'];pillars=data['derived']['pillars']
    check('Four continuous pillars and four through-openings per F01',p['P01']['quantity']==4 and 'P02' not in p and abs(p['P01']['height']-402)<.001 and sum(len(p[k]['cuts'])*p[k]['quantity'] for k in panels['F01']['sections'])==8 and not any(p[k]['cuts'] for k in panels['F02']['sections']))
    check('All floor plates use 6 mm plywood',all(p[k]['thickness']==6 for parent in ('F00','F01','F02') for k in panels[parent]['sections']))

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
        if v['category'] in BOUGHT:coverage[id]+=v['quantity']
    check('Every required part has cutting stock / template',all(coverage[id]==v['quantity'] for id,v in build_parts.items()),str({id:(coverage[id],v['quantity']) for id,v in build_parts.items() if coverage[id]!=v['quantity']}))
    check('Unique numbered copies across cutting layouts',unique)
    check(f'A3 sheet bounds and {cfg["nest_spacing"]:g} mm lanes',all(c['bounds_and_spacing']=='PASS' and c['spacing_mm']==cfg['nest_spacing'] for c in nest['validation']) and len(nest['validation'])==len(nest['sheets'])+len(optional))
    check('All plywood uses native A3 CNC stock',all((s['width'],s['height'])==(297,420) and s.get('cnc') for s in nest['sheets']) and all((ROOT/'output/dxf'/op['dxf']).exists() and (ROOT/'output/dxf'/op['svg']).exists() for s in nest['sheets'] for op in s['operations']))
    check('No larger-stock fallback',all(spec['primary']==[297,420] and not spec['extra'] for spec in cfg['stock']['main'].values()))
    fast=Counter(f['type'] for f in data['fasteners']);check('Installed hardware counts',fast=={'SC1':24,'SC2':24,'SC3':6},str(dict(fast)))
    check('Every entrance door has two hinges',sum(h['kind']=='Door butt hinge' for h in data['hardware'])==6)
    kinds=Counter(h['kind'] for h in data['hardware']);stop=data['config']['wall_stop']['angle']
    check(f'Magnetic walls: 2 catch + 2 stop magnets, 4 steel discs, walls open to the {stop:g}-degree stop posts',kinds['Catch magnet']==2 and kinds['Stop magnet']==2 and kinds['Steel disc']==4 and data['derived']['views']['open_angle']==stop and all(w['range_degrees']==[0,stop] for w in cad['wall_swing']),str(dict(kinds)))
    MG=cfg['magnets'];magnets=[h for h in data['hardware'] if h['kind'] in ('Catch magnet','Stop magnet')]
    check(f'Every magnet enclosed in solid wood ({MG["skin"]:g} mm skin, plugged bore)',all(h.get('enclosed',0)>=MG['skin'] for h in magnets) and all(h['depth']==p[k]['thickness']-MG['skin'] for k in ('MC1','GP1') for h in p[k]['holes'] if h['diameter']==MG['bore']))
    import clay
    small=[f['name'] for f in data['derived']['figures'] if clay.small_part(f['key'])]
    check('No clay figure fits the EN 71-1 small-parts cylinder',not small,str(small))
    check('Blunt finial (ball of 35 mm or more) and a divider gap outside 5-12 mm',p['FN01'].get('sphere',0)*2>=35 and not 5<=cfg['partition']['front_gap']<=12)
    import steps
    _,missing,double=steps.assign(data)
    check('Every house piece belongs to exactly one assembly step',not missing and not double,str(missing[:5]+double[:5]))
    for name,path in (('Plywood stack-up holds at both ends of the thickness band','stackup.json'),('Risk audit: tip-over, small parts, magnets','risk-audit.json')):
        report_=ROOT/'output/reports'/path
        check(name,report_.exists() and json.loads(report_.read_text())['all_pass'],path)
    misfit=[f'{f["figure"]} / {f["doorway"]}' for f in data['derived']['figure_fit'] if not f['fits']]
    check('Every clay figure passes upright through every doorway',bool(data['derived']['figure_fit']) and not misfit,str(misfit))
    connections=json.loads((ROOT/'output/reports/furniture-connections.json').read_text());check('Movable furniture has connected pieces',connections['all_pass'])
    dxfs=True
    for id,v in build_parts.items():
        step=ROOT/'output/cad/parts'/f'{id}.step';dxf=ROOT/'output/dxf'/f'{id}.dxf'
        dxfs=dxfs and step.exists() and dxf.exists() and '\n$INSUNITS\n70\n4\n' in dxf.read_text()
    check('All individual STEP / millimetre DXF files',dxfs)
    # The single supplier cut file: closed polylines and circles only, one layer per thickness, and exactly the
    # outlines, openings and through holes of every nested copy (counted here from the parts, not from cnc.py).
    cut=ROOT/'output/Moomin-House-Supplier-Cut.dxf';entities=[]
    if cut.exists():
        text=cut.read_text();pairs=list(zip(*[iter(text.splitlines())]*2))
        body=pairs[pairs.index(('2','ENTITIES'))+1:]
        for code,value in body:
            if code=='0':entities.append({'type':value})
            elif entities:entities[-1].setdefault(code,value)
    min_drill=cfg.get('cnc',{}).get('min_drill',0);wanted=Counter();found=Counter()
    for sheet in nest['sheets']:
        for item in sheet['items']:
            v=p[item['part']];layer=f'CUT_{v["thickness"]:g}MM'
            wanted[(layer,'CIRCLE' if v.get('outercircle') else 'POLYLINE')]+=1;wanted[(layer,'POLYLINE')]+=len(v['cuts'])
            wanted[(layer,'CIRCLE')]+=sum(min(h.get('depth') or v['thickness'],v['thickness'])>=v['thickness'] and h['diameter']>=min_drill for h in v['holes'])
    for e in entities:
        if e['type'] in ('POLYLINE','CIRCLE'):found[(e['8'],e['type'])]+=1
    kinds={e['type'] for e in entities}-{'VERTEX','SEQEND','EOF','ENDSEC'}
    check('Single supplier cut DXF: R12 in mm, only closed cutting paths, one layer per thickness, every nested copy',
          cut.exists() and '\nAC1009\n' in text and '\n$INSUNITS\n70\n4\n' in text and kinds<={'POLYLINE','CIRCLE'} and found==wanted and all(e.get('70')=='1' for e in entities if e['type']=='POLYLINE'),
          str({'missing':not cut.exists(),'entity types':sorted(kinds),'differences':{f'{k[0]} {k[1]}':(found[k],wanted[k]) for k in set(found)|set(wanted) if found[k]!=wanted[k]}}))
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
    index=json.loads((ROOT/'output/reports/template-index.json').read_text());check('Every required part has one or two A4 template pages',{i['part'] for i in index}==set(build_parts) and all(1<=i['last_tile_page']-i['first_tile_page']+1<=2 for i in index))
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
