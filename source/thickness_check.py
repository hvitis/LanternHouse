"""Plywood thickness check: the house built from the nominal templates with real, measured sheets.

    make tolerance        (or: MOOMIN_HEADLESS=1 <FreeCAD python> source/thickness_check.py)

Bought plywood is rarely its nominal thickness; config thickness_tolerance gives the measured band per nominal
thickness. Every plywood part keeps its nominal outline and place but is rebuilt at the thinnest and then the
thickest end of its band, about its mid-plane, and the full CAD checks run again: overlaps, wall swing, door
sweep, drawer travel, roof lift and window clearance. Parts that touch at nominal size (glue faces, floors on
posts, walls on the plinth) just sit a little further apart or closer with real sheets, so an overlap between
them is counted as a shift. A failure is an overlap where the nominal design had a gap: a moving clearance, a
slot, or a door or drawer gap that the real thickness would close. Solid-wood strips and blocks keep their size.
"""
import json,sys,time
from pathlib import Path
import build_cad as bc   # sets up FreeCAD (headless with MOOMIN_HEADLESS=1)
from model import build

ROOT=Path(__file__).resolve().parents[1]
TOUCH=.05   # mm: parts closer than this at nominal size count as touching

def assemble(data,end):
    """World solids with every plywood part at the thin (0) or thick (1) end of its band; None is nominal."""
    band=data['config']['thickness_tolerance'];shapes={};delta={};world={}
    for pid,p in data['parts'].items():
        fixed=end is None or p['category'] in ('Purchased wood','Purchased packing')
        delta[pid]=0 if fixed else band.get(f'{p["thickness"]:g}',(0,0))[end]
        shapes[pid]=bc.profile_shape(dict(p,thickness=p['thickness']+delta[pid]))
    for i in data['instances']:
        d=delta[i['part']];world[i['id']]=bc.transformed(shapes[i['part']],dict(i,origin=[i['origin'][k]-i['w'][k]*d/2 for k in range(3)]))
    return shapes,world

def flagged(report):
    """(check, at, part, other part) for everything the CAD checks report."""
    for c in report['collisions']:yield 'overlap',None,c['a'],c['b']
    for w in report['wall_swing']:
        for h in w['collisions']:yield f'{w["group"]} swing',h['angle'],h['moving'],h['obstacle']
    for d in report['door_sweep']:
        for h in d['collisions']:yield f'door {d["door"]} sweep',h['angle'],h['moving'],h['obstacle']
    for h in report['drawer_travel']['collisions']:yield 'drawer travel',h['travel_mm'],h['part'],h['obstacle']
    for h in report['roof_lift_collisions']:yield 'roof lift',h['lift_mm'],h['roof'],h['obstacle']
    for h in report['window_occlusion']:yield 'window clearance',None,h['wall'],h['obstacle']

def main():
    started=time.time();data=build();band=data['config']['thickness_tolerance']
    figures=[];clay={}
    for f in data['derived']['figures']:
        clay[f['id']]=bc.clay_solid(f)[0];figures.append({'id':f['id'],'part':f['code'],'group':'Figures'})
    _,nominal=assemble(data,None);nominal.update(clay);gap={}
    def nominal_gap(a,b):
        key=tuple(sorted((a,b)))
        if key not in gap:gap[key]=nominal[a].distToShape(nominal[b])[0]
        return gap[key]
    result={'band_mm':band,'rule':'nominal outlines and placements, each plywood part at the measured thickness about its mid-plane','scenarios':{}}
    failures=[]
    for end,name in ((0,'thinnest'),(1,'thickest')):
        print(f'Checking the {name} plywood...',flush=True)
        shapes,world=assemble(data,end);world.update(clay)
        report=bc.validate(data,shapes,world,figures);shifts=0;lost=[]
        for check,at,a,b in flagged(report):
            g=nominal_gap(a,b)
            if g<TOUCH:shifts+=1
            else:lost.append({'check':check,'at':at,'part':a,'other':b,'nominal_gap_mm':round(g,2)})
        result['scenarios'][name]={'thickness_mm':{t:float(t)+v[end] for t,v in band.items()},'touching_pairs_that_shift':shifts,'lost_clearances':lost}
        failures+=[dict(x,scenario=name) for x in lost]
    result['all_pass']=not failures;result['runtime_seconds']=round(time.time()-started,1)
    out=ROOT/'output/reports';out.mkdir(parents=True,exist_ok=True);(out/'thickness-tolerance.json').write_text(json.dumps(result,indent=2))
    for name,s in result['scenarios'].items():print(f'{name}: {len(s["lost_clearances"])} lost clearances, {s["touching_pairs_that_shift"]} touching pairs that only shift',flush=True)
    if failures:
        print('THICKNESS CHECK FAILED:\n'+'\n'.join(f'  - {f["scenario"]}: {f["check"]}{" at "+str(f["at"]) if f["at"] is not None else ""}: {f["part"]} / {f["other"]} (nominal gap {f["nominal_gap_mm"]} mm)' for f in failures[:40]),flush=True);sys.exit(1)
    print('Thickness check passed: real sheets within the band close no clearance.',flush=True)

if __name__=='__main__':main()
