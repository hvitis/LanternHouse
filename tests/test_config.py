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
    'figure twice':        (lambda c:c['figures'].update(levels=[['elias','elias']]),'non-unique'),
    'figure on two floors':(lambda c:c['figures'].update(levels=[['elias'],['elias']]),'stands on storey 1 and storey 2'),
    'back door opens':     (lambda c:c['doors'].update(back='W02'),'fixed rear shell'),
    'dormer on chimney':   (lambda c:c['dormer'].update(over=['W05']),'chimney'),
    'colour name':         (lambda c:c['colors'].update(red='red'),'colors/red'),
    'one facet two doors': (lambda c:c['doors'].update(main=c['doors']['veranda']),'both on'),
    'door off the deck':   (lambda c:c['doors'].update(veranda='W06'),'veranda facet'),
    'roof inside walls':   (lambda c:c.update(roof_diameter=c['tower_diameter']),'roof_diameter'),
    'hinge off the wall':  (lambda c:c['wall_hinge'].update(centers=[40.0,c['wall_height']]),'does not fit'),
    'laser without stock': (lambda c:c['laser'].update(thickness=5.0),'laser/thickness'),
    'sheet below margins': (lambda c:c['stock']['main']['3'].update(primary=[20.0,297.0]),'margins'),
    # Only 3 and 6 mm plywood: every role, support strip and stock entry must use one of them.
    '8 mm pillars':        (lambda c:c['thickness'].update(structure=8.0),'thickness/structure'),
    '4 mm stock':          (lambda c:c['stock']['main'].update({'4':c['stock']['main']['3']}),"'4' is not one of"),
    '3 mm stock missing':  (lambda c:c['stock']['main'].pop('3'),'thickness/detail'),
    '4 mm base supports':  (lambda c:c['fabrication'].update(base_support=[4,20],base_lift=4),'fabrication/base_support'),
}

@pytest.mark.parametrize('name',BROKEN)
def test_broken_config_is_rejected(cfg,name):
    change,expected=BROKEN[name]
    bad=copy.deepcopy(cfg);change(bad)
    found=config_check.problems(bad)
    assert any(expected in line for line in found),found
