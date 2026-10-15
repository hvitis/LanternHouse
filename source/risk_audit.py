"""Toy-safety audit of the built model: tip-over, small parts, magnets, pinch gaps and points (RISKS.md).

    .venv/bin/python source/risk_audit.py     (reads output/parts.json, writes output/reports/risk-audit.json)

Tip-over: the mass and centre of gravity come from every placed part (plywood, hardwood, steel ballast, clay
figures), with both walls open at their stop angle. The house stands on the support cross and the rim pads under
the base; the force that tips it is weight x (distance from the centre of gravity to the nearest edge of that
footprint) / push height. Small parts: every fabricated piece is tested against the EN 71-1 small-parts cylinder by
its sizes; all of them are glued in, and the figures, the only loose pieces, must not fit at all.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from shapely.geometry import Polygon, MultiPoint

ROOT=Path(__file__).resolve().parents[1]
DENSITY={'Purchased wood':.70e-6,'Purchased metal':7.85e-6,'Purchased packing':1.35e-6}   # kg/mm3; plywood below
PLY=.68e-6;G_=9.81

def world(inst,x,y,z):return [inst['origin'][k]+inst['u'][k]*x+inst['v'][k]*y+inst['w'][k]*z for k in range(3)]

def mass_and_centre(data,open_walls=True):
    parts=data['parts'];der=data['derived'];total=0;moment=[0,0,0]
    for inst in data['instances']:
        p=parts[inst['part']]
        if p.get('render_only') or inst['group'] in ('Tools','Garden'):continue
        if p.get('sphere'):
            r=p['sphere'];vol=4/3*math.pi*r**3;c=(r,r,r)
        else:
            shape=Polygon(p['outer'],p['cuts']);vol=shape.area*p['thickness'];cx,cy=shape.centroid.coords[0];c=(cx,cy,p['thickness']/2)
        m=vol*DENSITY.get(p['category'],PLY);pt=world(inst,*c)
        if open_walls and inst['group'] in ('WallRight','WallLeft'):
            sign=1 if inst['group']=='WallRight' else -1;hx=der['hinge_axes'][inst['group']][0];a=math.radians(sign*der['views']['open_angle'])
            x,y=pt[0]-hx,pt[1];pt=[hx+x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),pt[2]]
        total+=m;moment=[moment[k]+m*pt[k] for k in range(3)]
    for f in der['figures']:
        m=data['clay'][f['key']]['grams']/1000;pt=[f['x'],f['y'],f['z']+f['height']*.4]
        total+=m;moment=[moment[k]+m*pt[k] for k in range(3)]
    return total,[v/total for v in moment]

def footprint(data):
    """Plan outline of everything under the base that touches the table."""
    parts=data['parts'];pts=[]
    for inst in data['instances']:
        p=parts[inst['part']]
        if p.get('assembly_panel')!='B01' or inst['design_part']=='B01':continue
        for x,y in p['outer']:
            q=world(inst,x,y,0)
            if abs(q[2])<1e-6:pts.append((q[0],q[1]))
    return MultiPoint(pts).convex_hull

def tip_force(hull,cg,mass,height):
    """Smallest horizontal push at `height` that tips the house over an edge of its footprint, and that edge."""
    ring=list(hull.exterior.coords)[:-1];best=None
    for a,b in zip(ring,ring[1:]+ring[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy)
        d=abs((cg[0]-a[0])*dy-(cg[1]-a[1])*dx)/l
        f=mass*G_*d/height
        if best is None or f<best[0]:best=(f,d)
    return best

def small_part(dims,cyl):
    a,b,c=sorted(dims);d,l=cyl
    return b<=d and c<=l

def audit(data):
    cfg=data['config'];parts=data['parts'];der=data['derived']
    mass,cg=mass_and_centre(data,True);mass_closed,cg_closed=mass_and_centre(data,False);hull=footprint(data)
    target=35.0;push=700.0;eave=der['roof_eave']
    f_eave,d_eave=tip_force(hull,cg,mass,eave);f_push,_=tip_force(hull,cg,mass,push)
    # Without the rim pads the base would stand only on its support cross.
    bs_pts=[tuple(world(inst,x,y,0)[:2]) for inst in data['instances'] if parts[inst['part']].get('assembly_panel')=='B01' and parts[inst['part']]['id'].startswith('BS') for x,y in parts[inst['part']]['outer']]
    if not bs_pts:
        r=cfg['base_diameter']/2;w=cfg['fabrication']['base_support'][1]/2
        bs_pts=[(-r,-w),(-r,w),(r,w),(r,-w),(-w,-r),(w,-r),(w,r),(-w,r)]
    bare=MultiPoint(bs_pts).convex_hull
    f_bare,_=tip_force(bare,cg,mass,push)
    tip={'mass_kg':round(mass,2),'centre_of_gravity_mm':[round(v,1) for v in cg],'centre_of_gravity_closed_mm':[round(v,1) for v in cg_closed],
         'footprint_min_edge_distance_mm':round(d_eave,1),'force_at_eave_N':round(f_eave,1),'eave_height_mm':round(eave,1),
         f'force_at_{push:g}_mm_N':round(f_push,1),'force_without_rim_pads_N':round(f_bare,1),'target_N':target,'target_height_mm':push,
         'meets_target_free_standing':f_push>=target,'anchor_fitted':'AB1' in parts,
         'note':'Walls open at the stop angle, roof on. Free standing the house tips at the forces above; the AT1 strap to the room wall (anchor AB1) takes any larger pull.'}
    cyl=cfg['figures']['small_parts'];small=[]
    for pid,p in parts.items():
        if p.get('render_only') or p['category'] in ('Tools',):continue
        dims=(p['width'],p['height'],p['thickness']) if not p.get('sphere') else (2*p['sphere'],)*3
        if small_part(dims,cyl):small.append({'part':pid,'name':p['name'],'size_mm':[round(v,1) for v in sorted(dims)],'quantity':p['quantity'],'fixing':'glued in, hidden' if p['category'] in ('Purchased packing','Purchased wood') else 'glued over its whole face'})
    import clay
    loose=[f['name'] for f in der['figures'] if clay.small_part(f['key'])]
    MG=cfg['magnets'];mags=[h for h in data['hardware'] if h['kind'] in ('Catch magnet','Stop magnet')]
    checks={'tip_over_anchor':tip['anchor_fitted'],'rim_pads_raise_tip_force':f_push>f_bare,'loose_figures_not_small_parts':not loose,
            'magnets_enclosed':all(h.get('enclosed',0)>=MG['skin'] for h in mags),'divider_gap_outside_pinch_range':not 5<=cfg['partition']['front_gap']<=12,
            'finial_blunt':parts['FN01'].get('sphere',0)*2>=35,'no_glued_handles':'E02' not in parts,'drawer_captive':'DS1' in parts}
    return {'all_pass':all(checks.values()),'checks':checks,'tip_over':tip,'small_parts':small,'loose_small_parts':loose,'magnets':len(mags)}

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());report=audit(data)
    out=ROOT/'output/reports';out.mkdir(parents=True,exist_ok=True);(out/'risk-audit.json').write_text(json.dumps(report,indent=2))
    t=report['tip_over'];print(json.dumps({k:v for k,v in report.items() if k!='small_parts'},indent=1));print(f'{len(report["small_parts"])} glued parts would fit the small-parts cylinder if pulled off')
    if not report['all_pass']:raise SystemExit('Risk audit fails: see output/reports/risk-audit.json')

if __name__=='__main__':main()
