"""Physical stock limits, supported seams, continuous pillars and print coverage."""
import copy
from collections import Counter
import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union
import cnc
from hand_templates import layout


def test_every_fabrication_piece_fits_a3_and_two_a4(data):
    for pid,p in data['parts'].items():
        if p.get('render_only') or p['category'] in ('Purchased wood','Purchased packing'):continue
        assert min(p['width'],p['height'])<=297+1e-6,pid
        assert max(p['width'],p['height'])<=420+1e-6,pid
        spec=layout(p['width'],p['height'])
        assert spec['rows']*spec['columns']<=2,pid
    assert layout(80,420)['rows']==2
    assert layout(262,262)['paper'][0]>layout(80,420)['paper'][0]
    with pytest.raises(ValueError):layout(297,420)


def test_sections_reconstruct_panels_without_gaps(data):
    for parent,panel in data['derived']['panels'].items():
        original=Polygon(panel['outline'],panel['cuts']);o=panel['origin'];pieces=[]
        # Before base lift, panel origins describe the original assembly datum.
        ids=[i for i in data['instances'] if i['design_part']==parent]
        if parent=='F01':ids=sorted(ids,key=lambda i:i['origin'][2])[:len(panel['sections'])]
        for inst in ids:
            p=data['parts'][inst['part']]
            def world(loop):return [[inst['origin'][0]+inst['u'][0]*x+inst['v'][0]*y-o[0],inst['origin'][1]+inst['u'][1]*x+inst['v'][1]*y-o[1]] for x,y in loop]
            pieces.append(Polygon(world(p['outer']),[world(c) for c in p['cuts']]))
        assembled=unary_union(pieces)
        assert assembled.symmetric_difference(original).area<1e-6,parent
        assert sum(p.area for p in pieces)==pytest.approx(original.area),parent


def test_continuous_pillars_pass_through_both_floors(data):
    parts=data['parts'];pillars=[i for i in data['instances'] if i['part']=='P01']
    assert len(pillars)==4 and 'P02' not in parts
    assert parts['P01']['height']==pytest.approx(402)
    tops=data['derived']['floor_tops']
    for inst in pillars:
        assert inst['origin'][2]==pytest.approx(tops[0]+12)
        assert inst['origin'][2]+parts['P01']['height']==pytest.approx(tops[3]-6)
        x,y=inst['origin'][:2];w=parts['P01']['width'];t=parts['P01']['thickness']
        footprint=Polygon([[x,y],[x+w,y],[x+w,y-t],[x,y-t]])
        # Thickest 8 mm stock grows about its mid-plane by 0.2 mm each side.
        for z in tops[1:3]:
            cuts=[]
            for floor in data['instances']:
                if floor['design_part']!='F01' or abs(floor['origin'][2]-(z-6))>.001:continue
                p=parts[floor['part']];ox,oy=floor['origin'][:2]
                cuts += [Polygon([[ox+px,oy+py] for px,py in cut]) for cut in p['cuts']]
            assert any(c.contains(footprint.buffer(.2,join_style=2)) for c in cuts)


def test_floor_supports_keep_requested_cross_section(data):
    supports=[p for p in data['parts'].values() if p['name'].startswith('Floor seam support')]
    assert supports
    assert all(p['thickness']==4 and min(p['width'],p['height'])==pytest.approx(4) for p in supports)
    assert all(panel['thickness']==6 for parent,panel in data['derived']['panels'].items() if parent.startswith('F'))


def test_cnc_retained_edges_and_blind_pockets_are_distinct():
    p={'outer':[[0,0],[80,0],[80,420],[0,420]],'cuts':[],'holes':[{'x':30,'y':20,'diameter':8.2,'depth':3.5,'entry':'bottom','purpose':'Magnet pocket'}],'thickness':6,'retained_edges':[{'axis':'y','value':0},{'axis':'y','value':420}]}
    item={'part':'W','x':10,'y':0,'angle':0};ops=cnc.operations({'parts':{'W':p}},{'items':[item]})
    assert len(ops['cut'])==2
    assert all(kind=='line' and points[0][0]==points[1][0] for kind,points in ops['cut'])
    assert ops['pocket-bottom-d8.2-z3.5']==[('circle',(40,20,4.1))]


def test_panel_drilling_and_countersinks_do_not_cross_seams(data):
    from shapely.geometry import Point
    for p in data['parts'].values():
        if not p.get('assembly_panel') or p['name'].startswith(('Base seam support','Floor seam support','Roof ring seam bridge')):continue
        panel=Polygon(p['outer'],p['cuts'])
        for h in p['holes']:
            radius=max(h['diameter'],h.get('countersink',0))/2
            assert panel.buffer(1e-6).covers(Point(h['x'],h['y']).buffer(radius)),(p['id'],h['id'])


def test_roof_bolt_stack_retains_safe_thread_engagement(data):
    pivots=[f for f in data['fasteners'] if f['type']=='BL1']
    assert len(pivots)==2
    assert all(f['length']-sum(f['stack_mm'])==pytest.approx(3.5) for f in pivots)


def test_dimension_labels_include_the_base_support_height(data):
    import re
    dims=data['derived']['dimensions']
    assert dims[0]['label']==f'{data["config"]["height"]:g} total height'
    for dim in dims:
        match=re.search(r'\bZ(-?\d+(?:\.\d+)?)',dim['label'])
        if match:
            point=dim.get('p',dim.get('b'))
            assert float(match[1])==pytest.approx(point[2]),dim['label']
