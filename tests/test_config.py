import copy, json

import pytest
from jsonschema import Draft202012Validator

import config_check

def test_schema_is_a_valid_json_schema():
    Draft202012Validator.check_schema(json.loads(config_check.SCHEMA.read_text()))

def test_shipped_config_is_valid(cfg):
    assert config_check.problems(cfg)==[]

BROKEN={
    'misspelt key':        (lambda c:c.update(heigth=c.pop('height')),"'heigth' was unexpected"),
    'negative size':       (lambda c:c.update(height=-1),'height'),
    'unknown facet':       (lambda c:c['doors'].update(main='W13'),'doors/main'),
    'figure twice':        (lambda c:c['figures'].update(levels=['troll','troll']),'non-unique'),
    'colour name':         (lambda c:c['colors'].update(red='red'),'colors/red'),
    'one facet two doors': (lambda c:c['doors'].update(main=c['doors']['veranda']),'both on'),
    'door off the deck':   (lambda c:c['doors'].update(veranda='W06'),'veranda facet'),
    'roof inside walls':   (lambda c:c.update(roof_diameter=c['tower_diameter']),'roof_diameter'),
    'hinge off the wall':  (lambda c:c['wall_hinge'].update(centers=[40.0,c['wall_height']]),'does not fit'),
    'laser without stock': (lambda c:c['laser'].update(thickness=5.0),'laser/thickness'),
    'sheet below margins': (lambda c:c['stock']['main']['3'].update(primary=[20.0,297.0]),'margins'),
}

@pytest.mark.parametrize('name',BROKEN)
def test_broken_config_is_rejected(cfg,name):
    change,expected=BROKEN[name]
    bad=copy.deepcopy(cfg);change(bad)
    found=config_check.problems(bad)
    assert any(expected in line for line in found),found
