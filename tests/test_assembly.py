"""Build instructions must agree with the actual kit and survive model updates."""
from collections import Counter
import copy

import pytest
import assembly


def test_operations_install_every_physical_instance_once(data):
    guide=assembly.manifest(data)
    installed=[pid for step in guide['steps'] for pid in step['installs']]
    expected={i['id'] for i in data['instances'] if not data['parts'][i['part']].get('render_only')}
    assert set(installed)==expected
    assert all(count==1 for count in Counter(installed).values())
    assert guide['temporary']
    assert len({s['id'] for s in guide['steps']})==len(guide['steps'])
    by_id={i['id']:i for i in data['instances']}
    for step in guide['steps']:
        assert step['parts']==dict(Counter(by_id[pid]['part'] for pid in step['installs']))
        assert set(step['focus'])<=expected
        assert set(step['context'])<=expected
        assert step['repeat']>=1


def test_dependencies_and_supplies_are_resolved(data):
    guide=assembly.manifest(data);seen=set();supplies={s['id'] for s in guide['supplies']}
    for step in guide['steps']:
        assert step['prerequisite'] is None or step['prerequisite'] in seen
        assert set(step['supplies'])<=supplies
        for fastener in step['fasteners']:
            assert set(fastener['parts'])<=set(step['context'])|set(step['installs'])
        seen.add(step['id'])
    assert next(s for s in guide['supplies'] if s['id']=='floor-supports')['group']=='Hardware'


def test_repeat_batches_and_mirrored_shells(data):
    guide=assembly.manifest(data);steps={s['id']:s for s in guide['steps']}
    assert steps['windows-trim']['repeat']==steps['windows-trim']['parts']['WF1']
    assert steps['veranda-columns']['repeat']==steps['veranda-columns']['parts']['C01']//2
    by_id={i['id']:i for i in data['instances']}
    for side in ['right','left']:
        assert {by_id[pid]['group'] for pid in steps[f'opening-shells-{side}']['installs']}=={'Wall'+side.title()}


def test_no_required_roof_catches_when_absent(data):
    guide=assembly.manifest(data)
    assert not any(step['chapter']=='locks' for step in guide['steps'])
    chapter=assembly.content(data)['chapters']['locks']
    assert 'Magnets or a hinge-style' in chapter[2]


def test_revision_is_deterministic_and_changes_with_content(data,monkeypatch):
    guide=assembly.manifest(data)
    assert assembly.manifest(data)['revision']==guide['revision']
    operations=copy.deepcopy(assembly.OPERATIONS)
    suffix,title,text,pattern=operations['check'][0]
    operations['check'][0]=(suffix,title,text+' Check again.',pattern)
    monkeypatch.setattr(assembly,'OPERATIONS',operations)
    assert assembly.manifest(data)['revision']!=guide['revision']


def test_unknown_parts_fail_before_export(data):
    changed=copy.deepcopy(data)
    changed['instances'].append(dict(changed['instances'][0],id='unknown-instance',group='Unknown'))
    with pytest.raises(ValueError,match='coverage'):
        assembly.manifest(changed)
