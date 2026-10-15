"""Geometry invariants of the pure-Python model: sizes, placements, profiles, stock and clay."""
import math
from collections import Counter

import pytest
from model import BOUGHT

LOOSE=('Tools','Accessories','Garden')   # beside the house in the CAD or on the lawn round the base, not part of it

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
    # nest.py lays out 6 and 3 mm sheets; purchased wood and packing are bought, not cut.
    missing=sorted({(pid,p['thickness']) for pid,p in data['parts'].items()
                    if not p.get('render_only') and p['category'] not in BOUGHT
                    and f'{p["thickness"]:g}' not in cfg['stock']['optional' if p.get('optional') else 'main']})
    assert not missing

def test_doors_and_veranda_follow_config(cfg,data):
    assert data['derived']['doors']==cfg['doors']
    groups={f['facet']:f['group'] for f in data['derived']['facets']}
    assert groups[int(cfg['veranda']['facet'][1:])]=='Fixed','the veranda must stand on a wall that does not open'


def test_veranda_thin_deck_and_skirts_meet_the_supports(data):
    parts=data['parts'];deck=next(i for i in data['instances'] if i['part']=='E03')
    assert all(parts[pid]['thickness']==3 and parts[pid]['dxf']['layer']=='CUT_3MM' for pid in ('E03','VS1','VS2'))
    assert deck['origin'][2]+parts['E03']['thickness']==pytest.approx(data['derived']['ground_floor']+data['config']['thickness']['structure'])
    for inst in data['instances']:
        if inst['part'] not in ('VS1','VS2','VJ1'):continue
        p=parts[inst['part']]
        top=max(inst['origin'][2]+x*inst['u'][2]+y*inst['v'][2]+z*inst['w'][2]
                for x,y in p['outer'] for z in (0,p['thickness']))
        assert top==pytest.approx(deck['origin'][2]),inst['id']


def test_veranda_columns_are_four_pairs_of_three_mm_plies(data):
    p=data['parts']['C01'];columns=[i for i in data['instances'] if i['part']=='C01']
    assert p['thickness']==3 and p['quantity']==len(columns)==8
    assert p['dxf']['layer']=='CUT_3MM'
    for first,second in zip(columns[::2],columns[1::2]):
        assert first['u']==second['u'] and first['v']==second['v'] and first['w']==second['w']
        assert second['origin']==pytest.approx([first['origin'][k]+3*first['w'][k] for k in range(3)])
        assert 2*p['thickness']==6


def test_veranda_headers_and_centered_crossframe_use_three_mm_plywood(data):
    for pid in ('C02','C03','C10','C07'):
        assert data['parts'][pid]['thickness']==3
        assert data['parts'][pid]['dxf']['layer']=='CUT_3MM'
    deck=next(i for i in data['instances'] if i['part']=='E03')
    frame=next(i for i in data['instances'] if i['part']=='C07')
    center=[frame['origin'][k]+frame['w'][k]*data['parts']['C07']['thickness']/2 for k in range(3)]
    across=sum((center[k]-deck['origin'][k])*deck['u'][k] for k in range(3))
    assert across==pytest.approx(data['config']['veranda']['width']/2)


def test_room_dividers_clear_the_installed_rear_braces(cfg,data):
    from model import inside_polygon
    def local(inst,point):
        delta=[point[k]-inst['origin'][k] for k in range(3)]
        return [sum(delta[k]*inst[axis][k] for k in range(3)) for axis in ('u','v','w')]
    checked=0
    for divider in data['instances']:
        if divider['design_part'] not in ('PT1','PT2'):continue
        panel=data['parts'][divider['part']]
        for brace in data['instances']:
            if brace['design_part'] not in ('J01','J02','J03','J04'):continue
            profile=data['parts'][brace['part']];z=brace['origin'][2]+profile['thickness']/2
            if not 0<local(divider,[cfg['partition']['x'],0,z])[1]<panel['height']:continue
            # Both faces and the mid-plane of the divider, across the rear corner the braces hold.
            samples=[[cfg['partition']['x']+dx*panel['thickness']/2,y/4,z] for dx in (-.99,0,.99) for y in range(400,700)]
            crossing=[p for p in samples if inside_polygon(*local(brace,p)[:2],profile['outer'])]
            if not crossing:continue
            checked+=1
            assert not [p for p in crossing if inside_polygon(*local(divider,p)[:2],panel['outer'])],(divider['id'],brace['id'])
    assert checked==6,'the rear brace at both heights of each of the three storeys must fit its divider notch'

def test_clay_figures_stand_on_their_configured_storeys(cfg,data):
    assert [(f['key'],f['level']) for f in data['derived']['figures']]==[(k,n) for n,keys in enumerate(cfg['figures']['levels']) for k in keys]

def test_no_clay_figure_fits_the_small_parts_cylinder(cfg,data):
    import clay
    assert not [f['key'] for f in data['derived']['figures'] if clay.small_part(f['key'])]

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

def test_every_magnet_is_enclosed_in_solid_wood(cfg,data):
    # RISK-01: a bore from the hidden face leaves a wood skin over the magnet's working face, then a plug closes it.
    MG=cfg['magnets'];parts=data['parts']
    magnets=[h for h in data['hardware'] if h['kind'] in ('Catch magnet','Stop magnet')]
    assert magnets and all(h.get('enclosed',0)>=MG['skin'] for h in magnets)
    for pid in ('MC1','GP1'):
        bores=[h for h in parts[pid]['holes'] if h['diameter']==MG['bore']]
        assert bores and all(h['depth']==pytest.approx(parts[pid]['thickness']-MG['skin']) for h in bores),pid
        assert parts[pid]['category']=='Purchased wood',pid
    assert not any(h['diameter']==MG['bore'] for p in parts.values() if p['category']!='Purchased wood' for h in p['holes'])

def test_dormers_sit_inside_one_roof_panel_above_the_cleats(cfg,data):
    from shapely.geometry import Polygon
    parts=data['parts'];r06=parts['R06']
    assert r06['quantity']==len(cfg['dormer']['over'])
    panel=Polygon(r06['outer']);opening=Polygon(r06['cuts'][0])
    assert panel.buffer(-6).contains(opening),'the opening keeps 6 mm of skin to every panel edge'
    assert parts['DM01']['quantity']==len(cfg['dormer']['over']) and len(parts['DM01']['cuts'])==4
    # Every dormer part lies over its own panel, between the two hips.
    for inst in data['instances']:
        if not inst['part'].startswith('DM'):continue
        angles={round(math.degrees(math.atan2(y,x))) for x,y,z in corners(inst,parts[inst['part']])}
        mid=sum(angles)/len(angles)
        assert max(abs((a-mid+180)%360-180) for a in angles)<15,inst['id']

def test_opening_shells_hang_clear_of_the_plinth(cfg,data):
    lift=cfg['shell_lift'];G=data['derived']['ground_floor']
    lows=[min(c[2] for c in corners(i,data['parts'][i['part']])) for i in data['instances'] if i['group'] in ('WallLeft','WallRight')]
    assert min(lows)==pytest.approx(G+lift)

def test_room_divider_front_gap_is_outside_the_pinch_range(cfg):
    gap=cfg['partition']['front_gap']
    assert gap<=3 or gap>=15,'EN 71-1 4.10: a gap of 5-12 mm traps fingers'

def test_finial_is_a_blunt_ball(cfg,data):
    fn=data['parts']['FN01']
    assert fn.get('sphere') and 2*fn['sphere']>=35


def test_plywood_is_3_or_6_mm_only(data):
    # Only two sheet thicknesses to buy: every cut plywood piece is 3 or 6 mm, including the view-only furniture's
    # drawer bottom and the supports under the base, floors and roof ring.
    odd=sorted({(pid,p['thickness']) for pid,p in data['parts'].items() if not p.get('render_only') and p['category'] not in BOUGHT and p['thickness'] not in (3,6)})
    assert not odd

def test_turn_buttons_are_two_glued_plies_on_one_bolt(data):
    # One 6 mm ply is too weak (stress test E08); 6 + 3 mm glued is 9 mm on the same M3 x 30 bolt.
    lower,upper=data['parts']['E08'],data['parts']['E09']
    assert (lower['thickness'],upper['thickness'])==(6,3) and lower['outer']==upper['outer'] and lower['holes'][0]['x']==upper['holes'][0]['x']
    for bolt in [f for f in data['fasteners'] if f['type']=='BL1']:
        tab,ply=[next(i for i in data['instances'] if i['id']==pid) for pid in bolt['parts'][1:]]
        assert (tab['part'],ply['part'])==('E08','E09') and ply['origin'][2]==pytest.approx(tab['origin'][2]+6) and ply['origin'][:2]==pytest.approx(tab['origin'][:2])

def test_pillar_slots_follow_the_pillar_thickness(data):
    pillar=data['derived']['pillars'];slot=pillar['thickness']+pillar['clearance']
    widths=[]
    for pid in data['derived']['panels']['F01']['sections']:
        for cut in data['parts'][pid]['cuts']:
            xs=[x for x,_ in cut];ys=[y for _,y in cut];widths.append(round(min(max(xs)-min(xs),max(ys)-min(ys)),3))
    # The opening is the pillar plus clearance; the R2 dogbone reliefs at its corners add 2 mm on each side.
    assert pillar['thickness']==6 and widths and all(w==pytest.approx(slot+2*2.0) for w in widths),widths
