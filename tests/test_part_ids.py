"""Build IDs describe interchangeable pieces; copy IDs only track placements."""
import copy
from collections import Counter

import pytest

import model


def test_all_interchangeable_profiles_share_an_id(data):
    profiles=Counter(model.profile_key(p) for p in data['parts'].values())
    assert all(n==1 for n in profiles.values())
    assert len({i['id'] for i in data['instances']})==len(data['instances'])


def test_shared_build_quantities_and_design_roles(data):
    parts=data['parts']
    assert {pid:parts[pid]['quantity'] for pid in ('J01','P01','DM06','K2A')}=={
        'J01':54,'P01':4,'DM06':4,'K2A':2,
    }
    assert not {'DM07','K1A','K4A','K4B','K4C','K5A','K5B','PC01','PC02','PC03','V6A'} & parts.keys()


def test_floor_seam_supports_orientation_and_quantities(data):
    parts = data['parts']
    instances = data['instances']
    assert parts['FS04']['quantity'] == 6
    assert parts['FS05']['quantity'] == 6
    assert parts['FS04']['thickness'] == 4
    assert parts['FS05']['thickness'] == 4
    assert parts['FS04']['width'] == 4.0
    assert parts['FS05']['width'] == 4.0
    assert parts['FS04']['height'] > parts['FS05']['height']

    by_floor = {}
    seam_y = data['config']['fabrication']['seam_y']
    for inst in instances:
        if inst['part'] in ('FS04', 'FS05'):
            z = round(inst['origin'][2], 1)
            by_floor.setdefault(z, []).append(inst['part'])
            p = parts[inst['part']]
            ys = [inst['origin'][1] + inst['u'][1]*x + inst['v'][1]*y for x, y in p['outer']]
            assert min(ys) < seam_y < max(ys), "Must cross seam perpendicularly"

    assert len(by_floor) == 3
    for z, plist in by_floor.items():
        assert len(plist) == 4
        assert plist.count('FS04') == 2
        assert plist.count('FS05') == 2


@pytest.mark.parametrize('build_id,design_parts,size,quantity',[
    ('K2A',{'K2A'},(37,48,4),2),
    ('U4A',{'U4A','N1B'},(28,44,4),3),
])
def test_standard_furniture_blanks_have_shared_ids(data,build_id,design_parts,size,quantity):
    p=data['parts'][build_id]
    scale=data['config']['wall_height']/450
    assert (p['width'],p['height'],p['thickness'])==pytest.approx([value*scale for value in size])
    assert p['quantity']==quantity
    uses=[i for i in data['instances'] if i['part']==build_id]
    assert {i['design_part'] for i in uses}==design_parts
    assert all(i['part']==build_id for i in data['instances'] if i['design_part'] in design_parts)



def test_furniture_is_only_for_display(data):
    build_parts=model.fabrication_parts(data)
    decorations={pid for pid,p in data['parts'].items() if p['category'] in ('Furniture','Accessories')}
    assert decorations
    assert not decorations & build_parts.keys()
    assert all(data['parts'][pid]['render_only'] for pid in decorations)
    assert all(not p['render_only'] for p in build_parts.values())
    assert any(i['group']=='Furniture' for i in data['instances'])


@pytest.mark.parametrize('optional',[False,True])
def test_supplier_rejects_stale_furniture_cutting_sheets(data,optional):
    import supplier
    sheet={'thickness':4,'items':[{'part':'K2A'}]}
    nest={'sheets':[] if optional else [sheet],'optional_sheets':[sheet] if optional else []}
    with pytest.raises(ValueError,match='View-only furniture'):
        supplier.sheets_for(data,nest,dict(supplier.settings(data['config']),include_optional=True))


def test_joint_and_hardware_references_survive_merging(data):
    ids={i['id'] for i in data['instances']}
    refs=[pid for item in data['joints']+data['fasteners'] for pid in item['parts']]
    refs+=[h['door'] for h in data['hardware'] if 'door' in h]
    refs+=[pid for h in data['hardware'] for pid in h.get('moves_with',[])]
    assert set(refs)<=ids
    assert all(f['id'] in ids for f in data['derived']['facets'])


def test_merging_rotated_profiles_preserves_world_geometry(monkeypatch):
    for name,value in (('PARTS',{}),('INSTANCES',[]),('JOINTS',[]),('FASTENERS',[]),('HARDWARE',[])):
        monkeypatch.setattr(model,name,value)
    # Same asymmetric profile, turned 90 degrees, with a face-specific blind hole.
    a=[[0,0],[30,0],[24,20],[0,20]]
    b=[[20-y,x] for x,y in a]
    model.add('Q1','Horizontal support',4,a,holes=[dict(model.hole(7,8,2,3),entry='bottom')])
    model.add('Q2','Vertical support',4,b,holes=[dict(model.hole(12,7,2,3),entry='bottom')])
    model.put('Q1',(2,3,4))
    inst=model.put('Q2',(50,60,70),(0,1,0),(0,0,1))
    model.JOINTS.append({'parts':[inst['id']]})
    model.HARDWARE.append({'door':inst['id'],'moves_with':[inst['id']]})

    def world(i,points):
        return sorted(tuple(round(i['origin'][k]+x*i['u'][k]+y*i['v'][k]+z*i['w'][k],6) for k in range(3)) for x,y,z in points)
    def geometry(i,p):
        return world(i,[(x,y,z) for x,y in p['outer'] for z in (0,p['thickness'])]),world(i,[(h['x'],h['y'],0) for h in p['holes']])

    before=[geometry(i,model.PARTS[i['part']]) for i in model.INSTANCES]
    model.merge_identical()
    assert list(model.PARTS)==['Q1']
    assert model.PARTS['Q1']['quantity']==2
    assert [geometry(i,model.PARTS[i['part']]) for i in model.INSTANCES]==before
    assert model.JOINTS[0]['parts']==['Q1-02']
    assert model.HARDWARE[0]=={'door':'Q1-02','moves_with':['Q1-02']}


@pytest.mark.parametrize('change',[
    {'thickness':6}, {'outer':model.rect(20,30)[:-1]+[[2,30]]},
    {'cuts':[model.cutrect(2,2,5,5)]},
    {'holes':[{'x':4,'y':6,'diameter':3,'depth':2,'entry':'bottom','countersink':5,'countersink_depth':1}]},
    {'holes':[{'x':4,'y':6,'diameter':3,'depth':3,'entry':'top','countersink':5,'countersink_depth':1}]},
    {'holes':[{'x':4,'y':6,'diameter':3,'depth':2,'entry':'top','countersink':5,'countersink_depth':2}]},
    {'category':'Purchased wood'}, {'category':'Purchased packing'}, {'category':'Furniture'},
])
def test_same_size_does_not_merge_different_manufacturing_details(change):
    p={'thickness':4,'category':'Structure','outer':model.rect(20,30),'cuts':[],
       'holes':[{'x':4,'y':6,'diameter':3,'depth':2,'entry':'top','countersink':5,'countersink_depth':1}]}
    different=copy.deepcopy(p);different.update(change)
    assert model.profile_key(p)!=model.profile_key(different)


def test_vertex_and_drilling_order_do_not_change_the_build_id():
    p={'thickness':4,'category':'Structure','outer':model.rect(20,30),
       'cuts':[model.cutrect(2,2,5,5),model.cutrect(12,12,5,5)],
       'holes':[model.hole(4,24,2),model.hole(14,24,2)]}
    reordered=copy.deepcopy(p)
    reordered['outer']=reordered['outer'][2:]+reordered['outer'][:2]
    reordered['cuts']=[c[::-1] for c in reordered['cuts'][::-1]]
    reordered['holes'].reverse()
    assert model.profile_key(p)==model.profile_key(reordered)
