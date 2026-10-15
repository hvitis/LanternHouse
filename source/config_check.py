"""Check a design config before building: the JSON Schema plus the cross-field rules a schema cannot express.

    .venv/bin/python source/config_check.py              # check source/config.json
    .venv/bin/python source/config_check.py other.json   # check another file

It takes a second, so rebuild.py, serve.py and export_viewer.py run it before they build, and a typo
fails here instead of minutes into the FreeCAD stage. The schema (config.schema.json) documents every key.
"""
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'source/config.json'
SCHEMA=ROOT/'source/config.schema.json'

def problems(cfg):
    """Every problem in cfg as a readable line; an empty list means the config is valid."""
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(json.loads(SCHEMA.read_text()))
    where=lambda e:'/'.join(map(str,e.absolute_path)) or '(top level)'
    found=[f'{where(e)}: {e.message}' for e in sorted(validator.iter_errors(cfg),key=lambda e:[str(p) for p in e.absolute_path])]
    if found:return found   # the rules below rely on the shapes the schema guarantees
    doors,ver=cfg['doors'],cfg['veranda']
    if doors['main']==doors['veranda']:found.append(f'doors: the main and veranda doors are both on {doors["main"]}')
    if doors['back'] in (doors['main'],doors['veranda']):found.append(f'doors: the back door shares {doors["back"]} with another door')
    facet=lambda f:int(f[1:])-1
    if not 3<=facet(doors['back'])<=8:found.append(f'doors/back: {doors["back"]} opens with a wall shell; the back door must be on the fixed rear shell (W04-W09)')
    if 'W05' in cfg['dormer']['over']:found.append('dormer/over: W05 carries the chimney; put the dormer on another panel')
    seen={}
    for level,keys in enumerate(cfg['figures']['levels']):
        for key in keys:
            if key in seen:found.append(f'figures/levels: {key} stands on storey {seen[key]+1} and storey {level+1}')
            seen[key]=level
    if doors['veranda']!=ver['facet']:found.append(f'doors/veranda: the veranda door ({doors["veranda"]}) must be on the veranda facet ({ver["facet"]}) so it opens onto the deck')
    if cfg['roof_diameter']<=cfg['tower_diameter']:found.append(f'roof_diameter: {cfg["roof_diameter"]:g} must exceed tower_diameter {cfg["tower_diameter"]:g} so the roof overhangs the walls')
    fab=cfg['fabrication']
    if fab['sheet_mm']!=[297,420]:found.append('fabrication/sheet_mm: this design requires A3 blanks, [297, 420] mm')
    if cfg['wall_height']>420:found.append('wall_height: a whole wall must not exceed the 420 mm A3 blank length')
    if abs(cfg['wall_height']-3*cfg['floor_pitch'])>1e-6:found.append('wall_height/floor_pitch: the wall must span three equal storeys')
    if fab['base_lift']!=fab['base_support'][0]:found.append('fabrication/base_lift: must equal the underside support thickness')
    pz=fab['front_split']
    if pz['head']<=pz['neck']:found.append('fabrication/front_split: the knob head must be wider than its neck, or the front pieces do not lock')
    if cfg['floor_pitch']<=cfg['thickness']['floor']+12:found.append('floor_pitch: insufficient height for the foot blocks and floor plate')
    for name,limit in (('wall_hinge',cfg['wall_height']),('door_hinge',None)):
        h=cfg[name]
        for c in h['centers']:
            if c-h['height']/2<0 or (limit and c+h['height']/2>limit):found.append(f'{name}/centers: a {h["height"]:g} mm hinge centred at {c:g} does not fit on the {"wall" if limit else "door"}')
        for y in h['hole_y']:
            if not 0<y<h['height']:found.append(f'{name}/hole_y: {y:g} is outside the {h["height"]:g} mm leaf')
    named={**{f'thickness/{k}':v for k,v in cfg['thickness'].items()},**{f'fabrication/{k}':fab[k][0] for k in ('base_support','floor_support','plinth_floor_support')}}
    for where,t in named.items():
        if f'{t:g}' not in cfg['stock']['main']:found.append(f'{where}: {t:g} mm plywood has no stock.main["{t:g}"]; the design uses 3 and 6 mm sheets only')
    laser=f'{cfg["laser"]["thickness"]:g}'
    if laser not in cfg['stock']['main']:found.append(f'laser/thickness: there is no stock.main["{laser}"] for the laser sheets')
    for group,stock in cfg['stock'].items():
        for t,spec in stock.items():
            for size in [spec['primary']]+spec.get('extra',[]):
                if min(size)<=2*cfg['stock_margin']:found.append(f'stock/{group}/{t}: a {size[0]:g} x {size[1]:g} sheet leaves no room inside the {cfg["stock_margin"]:g} mm margins')
                if size!=fab['sheet_mm']:found.append(f'stock/{group}/{t}: only A3 [297, 420] mm blanks are supported')
    return found

def check(path=CONFIG):
    """Load and validate a config; exit with a list of the problems if there are any."""
    cfg=json.loads(Path(path).read_text())
    found=problems(cfg)
    if found:raise SystemExit(f'{path} has {len(found)} problem(s):\n'+'\n'.join('  - '+p for p in found))
    return cfg

if __name__=='__main__':
    path=Path(sys.argv[1]) if len(sys.argv)>1 else CONFIG
    check(path);print(f'{path}: OK')
