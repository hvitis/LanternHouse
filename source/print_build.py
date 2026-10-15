"""Generate the 3D-printable designs in source/prints/ as STL, 3MF and STEP files and check that each one prints.

    .venv/bin/python source/print_build.py              # publish every changed design to prints/
    .venv/bin/python source/print_build.py chair        # publish one design
    .venv/bin/python source/print_build.py --force      # rebuild every design, changed or not

This runs on the Mac: it needs build123d (requirements-print.txt), a CAD library on the OpenCASCADE kernel.
prints/ is committed, so the web page (source/viewer/prints.html) and CI read the published files and need no
CAD kernel. A design that fails a check is not published, and the command exits with an error.

A design is a Python file source/prints/<name>.py with:
    TITLE, NOTES, COLOR    a name, printing advice, and a colour from config.json "colors" (or #rrggbb)
    PARAMS                 {name: (default, min, max, step[, unit])}, the sliders in the live studio
    TOY = False            optional: skip the small-parts check for parts that are not toys
    build(**params)        returns a build123d solid; it is moved to stand centred on the bed at z=0
"""
import argparse, hashlib, importlib.util, json, shutil, time
from pathlib import Path
import print_mesh

ROOT=Path(__file__).resolve().parents[1]
DESIGNS=ROOT/'source/prints'
PUBLISHED=ROOT/'prints'
LIVE=ROOT/'output/prints/live'
STAGING=ROOT/'output/prints/staging'
TOLERANCE=(0.02,0.15)  # STL chord deviation (mm) and angle (rad): finer than a 0.4 mm nozzle prints

def designs():return sorted(p.stem for p in DESIGNS.glob('*.py') if not p.name.startswith('_'))

def source_hash(name):
    """What a published design depends on: its source, the printer, the small-parts rule and the mesh settings.
    The published hash goes stale (and CI fails) when any of them changes until the design is generated again."""
    h=hashlib.sha256()
    for path in (DESIGNS/f'{name}.py',print_mesh.PRINTER_FILE):h.update(path.read_bytes().replace(b'\r\n',b'\n'))
    h.update(json.dumps([print_mesh.small_parts(),TOLERANCE]).encode())
    return h.hexdigest()[:16]

def load(name):
    """The design module, read fresh from disk on every call so the live studio picks up each save."""
    spec=importlib.util.spec_from_file_location(f'print_design_{name}',DESIGNS/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def param_table(module,overrides=None):
    """PARAMS with the slider values: {name: {value, default, min, max, step, unit}}, values clamped to range."""
    table={}
    for key,spec in module.PARAMS.items():
        default,lo,hi,step,*unit=spec;value=(overrides or {}).get(key,default)
        kind=int if isinstance(default,int) and isinstance(step,int) else float
        value=min(max(kind(value),lo),hi)
        table[key]={'value':value,'default':default,'min':lo,'max':hi,'step':step,'unit':unit[0] if unit else 'mm'}
    return table

def colour(name):
    if name.startswith('#'):return name
    return json.loads((ROOT/'source/config.json').read_text())['colors'][name]

def build(name,overrides=None,out=LIVE):
    """Build one design into out/<name>.stl, .3mf and .step and return its manifest entry with the checks.
    Errors in the design (an exception, or no solid returned) propagate to the caller."""
    from build123d import Location, Shape, export_step, export_stl, __version__
    module=load(name);table=param_table(module,overrides)
    shape=module.build(**{k:v['value'] for k,v in table.items()})
    shape=getattr(shape,'part',shape)   # a BuildPart context hands back its part
    if not isinstance(shape,Shape) or not shape.volume>0:raise TypeError(f'{name}.build() must return a solid, not {type(shape).__name__}')
    box=shape.bounding_box()
    shape=shape.moved(Location((-(box.min.X+box.max.X)/2,-(box.min.Y+box.max.Y)/2,-box.min.Z)))
    out.mkdir(parents=True,exist_ok=True);files={k:out/f'{name}.{k}' for k in ('stl','3mf','step')}
    export_stl(shape,str(files['stl']),tolerance=TOLERANCE[0],angular_tolerance=TOLERANCE[1])
    V,F=print_mesh.read_stl(files['stl'])
    title=getattr(module,'TITLE',name.replace('_',' ').capitalize())
    print_mesh.write_3mf(files['3mf'],V,F,title)
    export_step(shape,str(files['step']))
    printer=print_mesh.printer()
    report=print_mesh.analyse(V,F,printer,toy=getattr(module,'TOY',True))
    return {'name':name,'title':title,'notes':getattr(module,'NOTES',''),'color':colour(getattr(module,'COLOR','cream')),
            'about':(module.__doc__ or '').strip(),'params':table,'hash':source_hash(name),'generator':f'build123d {__version__}',
            'files':{k:{'path':p.name,'bytes':p.stat().st_size} for k,p in files.items()},**report}

def manifest_path():return PUBLISHED/'manifest.json'
def read_manifest():
    path=manifest_path()
    return json.loads(path.read_text()) if path.exists() else {'parts':{}}

def write_manifest(parts):
    data={'printer':print_mesh.printer(),'small_parts':print_mesh.small_parts(),'parts':dict(sorted(parts.items()))}
    manifest_path().write_text(json.dumps(data,indent=1,ensure_ascii=False)+'\n')

def publish(names,force=False):
    """Build the named designs and copy the ones that pass into prints/. Returns the names that failed."""
    parts=read_manifest()['parts'];failed=[];PUBLISHED.mkdir(exist_ok=True)
    for gone in set(parts)-set(designs()):   # a deleted design leaves the site too
        for f in parts.pop(gone)['files'].values():(PUBLISHED/f['path']).unlink(missing_ok=True)
        print(f'  {gone}: removed (no source/prints/{gone}.py)')
    for name in names:
        old=parts.get(name)
        if not force and old and old['hash']==source_hash(name) and all((PUBLISHED/f['path']).exists() for f in old['files'].values()):
            print(f'  {name}: up to date');continue
        start=time.perf_counter()
        try:entry=build(name,out=STAGING)
        except Exception as error:
            print(f'  {name}: FAILED to build: {type(error).__name__}: {error}');failed.append(name);continue
        took=time.perf_counter()-start
        if entry['status']=='fail':
            print(f'  {name}: NOT published, {took:.1f} s')
            for c in entry['checks']:
                if c['status']=='fail':print(f'      {c["label"]}: {c["detail"]}')
            failed.append(name);continue
        for f in entry['files'].values():shutil.move(STAGING/f['path'],PUBLISHED/f['path'])
        parts[name]=entry
        warnings=[c['label'] for c in entry['checks'] if c['status']=='warn']
        print(f'  {name}: published, {took:.1f} s, {entry["grams"]["estimate"]:g} g'+(f' (warnings: {", ".join(warnings)})' if warnings else ''))
    write_manifest(parts)
    return failed

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('names',nargs='*',help='designs to build (default: all in source/prints/)')
    p.add_argument('--force',action='store_true',help='rebuild even when the published files are up to date')
    args=p.parse_args();names=args.names or designs()
    unknown=sorted(set(names)-set(designs()))
    if unknown:raise SystemExit(f'No such design: {", ".join(unknown)}. Designs: {", ".join(designs())}')
    print(f'Generating {len(names)} print design(s) into prints/ ...',flush=True)
    failed=publish(names,args.force)
    if failed:raise SystemExit(f'Not published: {", ".join(failed)}. Fix the checks above, or look at them in `make studio`.')

if __name__=='__main__':main()
