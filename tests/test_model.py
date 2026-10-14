"""Geometry invariants of the pure-Python model: sizes, placements, profiles, stock and clay."""
import math
from collections import Counter

import pytest

LOOSE=('Tools','Accessories')   # laid out beside the house in the CAD, not part of it

def corners(inst,part):
    """World coordinates of a placed profile's outline, on both faces of the plywood."""
    o,u,v,w=inst['origin'],inst['u'],inst['v'],inst['w']
    for x,y in part['outer']:
        for z in (0,part['thickness']):yield [o[k]+u[k]*x+v[k]*y+w[k]*z for k in range(3)]

def house(data):
    for i in data['instances']:
        if i['group'] not in LOOSE:yield i,data['parts'][i['part']]

def is_simple(points):
    """True if no two non-adjacent edges of the closed polygon cross."""
    def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    edges=[(points[k],points[(k+1)%len(points)]) for k in range(len(points))];n=len(edges)
    for i in range(n):
        for j in range(i+2,n):
            if i==0 and j==n-1:continue
            (a,b),(c,d)=edges[i],edges[j]
            if turn(c,d,a)*turn(c,d,b)<0 and turn(a,b,c)*turn(a,b,d)<0:return False
    return True

def test_height_matches_config(cfg,data):
    assert data['derived']['total_height']==pytest.approx(cfg['height'])
    assert max(c[2] for i,p in house(data) for c in corners(i,p))==pytest.approx(cfg['height'],abs=.01)

def test_floors_follow_plinth_and_pitch(cfg,data):
    ground=cfg['fabrication']['base_lift']+cfg['thickness']['base']+cfg['plinth']['height']
    assert data['derived']['floor_tops']==pytest.approx([ground+k*cfg['floor_pitch'] for k in range(4)])

def test_everything_stands_on_the_base(cfg,data):
    r=cfg['base_diameter']/2
    outside=sorted({i['id'] for i,p in house(data) for x,y,z in corners(i,p) if math.hypot(x,y)>r+.01 or z<-.01})
    assert not outside

def test_instances_match_part_quantities(data):
    placed=Counter(i['part'] for i in data['instances'])
    assert set(placed)<=set(data['parts'])
    assert {pid:p['quantity'] for pid,p in data['parts'].items()}=={pid:placed[pid] for pid in data['parts']}

def test_instance_frames_are_orthonormal(data):
    dot=lambda a,b:sum(x*y for x,y in zip(a,b))
    for i in data['instances']:
        u,v,w=i['u'],i['v'],i['w']
        assert (dot(u,u),dot(v,v),dot(u,v))==pytest.approx((1,1,0),abs=1e-9),i['id']
        assert w==pytest.approx([u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]),i['id']

def test_profiles_are_simple_polygons(data):
    bad=[pid for pid,p in data['parts'].items() if len(p['outer'])<3 or not is_simple(p['outer']) or not all(map(is_simple,p['cuts']))]
    assert not bad

def test_holes_and_openings_lie_on_their_part(data):
    off=[]
    for pid,p in data['parts'].items():
        inside=lambda x,y:-1e-6<=x<=p['width']+1e-6 and -1e-6<=y<=p['height']+1e-6
        off+=[(pid,h['id']) for h in p['holes']+p['starters'] if not inside(h['x'],h['y'])]
        off+=[(pid,'cut') for c in p['cuts'] for x,y in c if not inside(x,y)]
    assert not off

def test_every_sheet_part_has_plywood_stock(cfg,data):
    # nest.py lays out 8, 6, 4 and 3 mm sheets; purchased wood and packing are bought, not cut.
    missing=sorted({(pid,p['thickness']) for pid,p in data['parts'].items()
                    if not p.get('render_only') and p['category'] not in ('Purchased wood','Purchased packing')
                    and f'{p["thickness"]:g}' not in cfg['stock']['optional' if p.get('optional') else 'main']})
    assert not missing

def test_doors_and_veranda_follow_config(cfg,data):
    assert data['derived']['doors']==cfg['doors']
    groups={f['facet']:f['group'] for f in data['derived']['facets']}
    assert groups[int(cfg['veranda']['facet'][1:])]=='Fixed','the veranda must stand on a wall that does not open'

def test_room_dividers_clear_the_installed_rear_gussets(cfg,data):
    from model import inside_polygon
    def local(inst,point):
        delta=[point[k]-inst['origin'][k] for k in range(3)]
        return [sum(delta[k]*inst[axis][k] for k in range(3)) for axis in ('u','v','w')]
    checked=0
    for divider in data['instances']:
        if divider['design_part'] not in ('PT1','PT2'):continue
        panel=data['parts'][divider['part']]
        for gusset in data['instances']:
            if gusset['design_part']!='J01':continue
            profile=data['parts'][gusset['part']]
            pts=list(corners(gusset,profile))
            point=[cfg['partition']['x'],(min(p[1] for p in pts)+max(p[1] for p in pts))/2,gusset['origin'][2]+profile['thickness']/2]
            gx,gy,gz=local(gusset,point);x,y,z=local(divider,point)
            if not (point[1]>100 and 0<x<panel['width'] and 0<y<panel['height'] and inside_polygon(gx,gy,profile['outer'])):continue
            checked+=1
            assert not inside_polygon(x,y,panel['outer']),(divider['id'],gusset['id'])
    assert checked==6,'both rear gussets on each of the three storeys must fit their divider notches'

def test_one_clay_figure_per_configured_storey(cfg,data):
    assert [(f['key'],f['level']) for f in data['derived']['figures']]==[(k,n) for n,k in enumerate(cfg['figures']['levels'])]

def test_clay_estimate_is_consistent(cfg,data):
    clay=cfg['figures']['clay']
    for key,fig in data['clay'].items():
        assert fig['closed'],key
        assert fig['grams']==pytest.approx(fig['volume_mm3']/1000*clay['density']*(1+clay['allowance'])),key
        assert sum(fig['grams_by_colour'].values())==pytest.approx(fig['grams']),key

def test_figures_pass_every_doorway(data):
    misfit=[(f['figure'],f['doorway']) for f in data['derived']['figure_fit'] if not f['fits']]
    assert data['derived']['figure_fit'] and not misfit

def test_magnets_pair_catches_and_stops(cfg,data):
    kinds=Counter(h['kind'] for h in data['hardware'])
    assert (kinds['Catch magnet'],kinds['Stop magnet'],kinds['Steel disc'])==(2,2,4)
    assert data['derived']['views']['open_angle']==cfg['wall_stop']['angle']
