"""Physical stock limits, supported seams, continuous pillars and print coverage."""
import copy, math
from collections import Counter
import pytest
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import cnc
from hand_templates import layout
from model import BOUGHT


def test_every_fabrication_piece_fits_a3_and_two_a4(data):
    for pid,p in data['parts'].items():
        if p.get('render_only') or p['category'] in BOUGHT:continue
        assert min(p['width'],p['height'])<=297+1e-6,pid
        assert max(p['width'],p['height'])<=420+1e-6,pid
        spec=layout(p['width'],p['height'])
        assert spec['rows']*spec['columns']<=2,pid
    assert layout(80,420)['rows']==2
    assert layout(262,262)['paper'][0]>layout(80,420)['paper'][0]
    with pytest.raises(ValueError):layout(297,420)


def test_sections_reconstruct_panels_without_gaps(data):
    cnc=data['config']['cnc'];seam=data['config']['fabrication']['seam_y']
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
        if parent in ('F00','F01','F02'):
            # Finger and puzzle joints: only the fit clearance and the cutter relief at inside corners are missing,
            # all of it in the joint zones; nothing is added and nothing is lost elsewhere. F00 has a straight seam.
            y=original.bounds[3]/2+seam;split=panel['front_split'];pz=data['config']['fabrication']['front_split']
            reach=pz['reach']+pz['head']/2+1;puzzle=box(split['x']-reach,-1,split['x']+reach,y+10)
            finger=box(-1,y-10,original.bounds[2]+1,y+10) if parent!='F00' else box(0,0,0,0)
            assert assembled.difference(original).area<1e-6,parent
            missing=original.difference(assembled)
            assert missing.difference(puzzle.union(finger)).area<1e-6,parent
            assert missing.difference(finger).area<(y+len(split['knobs'])*(2*pz['reach']+math.pi*pz['head']))*cnc['joint_clearance']*1.5,parent
            assert missing.intersection(finger).area<original.bounds[2]*cnc['joint_clearance']*3+60*math.pi*(cnc['tool_diameter']/2)**2,parent
            continue
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
    fab=data['config']['fabrication'];supports=[p for p in data['parts'].values() if p['name'].startswith('Floor seam support')]
    assert supports
    for p in supports:
        t,w=fab['plinth_floor_support'] if p['assembly_panel']=='F00' else fab['floor_support']
        assert t==3 and p['dxf']['layer']=='CUT_3MM',p['id']
        assert p['thickness']==t and min(p['width'],p['height'])==pytest.approx(w),p['id']
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


def test_dimension_labels_include_the_base_support_height(data):
    import re
    dims=data['derived']['dimensions']
    assert dims[0]['label']==f'{data["config"]["height"]:g} total height'
    for dim in dims:
        match=re.search(r'\bZ(-?\d+(?:\.\d+)?)',dim['label'])
        if match:
            point=dim.get('p',dim.get('b'))
            assert float(match[1])==pytest.approx(point[2]),dim['label']


def test_dxf_files_are_strict_r12(tmp_path):
    ezdxf=pytest.importorskip('ezdxf')
    from ezdxf import recover
    from dxf_r12 import DXF
    d=DXF();d.polyline([[0,0],[80,0],[80,420],[0,420]],'CUT');d.circle(40,20,4.1,'pocket-top-d8.2-z3.5');d.polyline([[0,0],[10,0]],'CUT',closed=False)
    path=tmp_path/'sheet.dxf';d.save(path)
    doc,auditor=recover.readfile(path)
    assert doc.dxfversion=='AC1009' and not auditor.has_errors
    kinds=sorted(e.dxftype() for e in doc.modelspace())
    assert kinds==['CIRCLE','POLYLINE','POLYLINE']
    assert {l.dxf.name for l in doc.layers}>={'CUT','POCKET-TOP-D8_2-Z3_5'}
    assert doc.header['$INSUNITS']==4


def test_cnc_leaves_small_and_underside_features_to_the_builder():
    p={'outer':[[0,0],[100,0],[100,60],[0,60]],'cuts':[],'thickness':6,'holes':[
        {'id':'H01','x':10,'y':10,'diameter':3.2,'depth':None,'entry':'bottom','countersink':6,'countersink_depth':1.5,'purpose':'Screw clearance'},
        {'id':'H02','x':30,'y':10,'diameter':1.4,'depth':6,'entry':'top','purpose':'Hinge pilot'},
        {'id':'H03','x':50,'y':10,'diameter':10.2,'depth':1.2,'entry':'bottom','purpose':'Steel disc recess'}]}
    data={'config':{'cnc':{'two_sided':False,'min_drill':2.0}},'parts':{'P':p}}
    ops,hand=cnc.features(data,{'id':'S','items':[{'part':'P','copy':1,'x':0,'y':0,'angle':0}]})
    assert 'drill-top-d3.2-z6' in ops   # a through hole is drilled from the top whatever its screw's side
    assert not any(k.startswith(('countersink-bottom','pocket-bottom')) for k in ops)
    assert {(h['hole'],h['feature']) for h in hand}=={('H01','countersink'),('H02','drill'),('H03','pocket')}
