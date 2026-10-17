"""Serve the interactive 3D viewer for the Lanternwood House model.

    .venv/bin/python source/serve.py              # http://127.0.0.1:8765/ (or the next free port)
    .venv/bin/python source/serve.py --open       # also opens the browser
    .venv/bin/python source/serve.py --rebuild    # refresh the model data after editing config.json

The viewer builds every solid in the browser from output/parts.json, the same profiles and
placements the CAD export uses. If that file is missing (a fresh clone), or with --rebuild, it is
generated from source/model.py, which needs numpy and shapely, not FreeCAD. The DXF uses matching production
nesting when available, otherwise computes the layout. Only viewer assets, model data, DXF and label positions,
and the published 3D prints in prints/ (for prints.html) are served, on the local machine unless --host says otherwise.
"""
import argparse, errno, http.server, json, mimetypes, shutil, sys, time, webbrowser
from pathlib import Path
import naming

ROOT=Path(__file__).resolve().parents[1]
VIEWER=(ROOT/'source/viewer').resolve()
DATA={'/data/assembly.json':ROOT/'output/viewer/assembly.json','/data/parts.json':ROOT/'output/parts.json','/data/house.dxf':ROOT/'output/viewer/house.dxf','/data/dxf-labels.json':ROOT/'output/viewer/dxf-labels.json','/data/checklist-pl.pdf':ROOT/'output/viewer/checklist-pl.pdf','/data/checklist-en.pdf':ROOT/'output/viewer/checklist-en.pdf'}
PRINTS=(ROOT/'prints').resolve()   # the published 3D prints, for prints.html
mimetypes.add_type('text/javascript','.js')

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self,path):
        clean=path.split('?',1)[0].split('#',1)[0]
        if clean in DATA:return str(DATA[clean])
        if clean.startswith('/prints/'):
            target=(PRINTS/clean[len('/prints/'):]).resolve()
            return str(target) if PRINTS in target.parents else str(VIEWER/'missing')
        target=(VIEWER/(clean.lstrip('/') or 'index.html')).resolve()
        # Never serve anything outside the viewer folder.
        return str(target) if target==VIEWER or VIEWER in target.parents else str(VIEWER/'missing')
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
    def log_message(self,fmt,*args):pass

def model_data():
    """The viewer data, built from source/model.py without FreeCAD (about 10 s) after checking the config.
    The full CAD build (source/rebuild.py) writes the same data with extra glue-face joints the viewer does not use."""
    sys.path.insert(0,str(ROOT/'source'))
    import config_check;config_check.check()
    import model
    start=time.time();data=model.build()
    print(f'  {len(data["parts"])} profiles, {len(data["instances"])} instances in {time.time()-start:.0f} s',flush=True)
    return data

def build_data(path):
    print('Building output/parts.json from source/model.py (no FreeCAD needed)...',flush=True)
    data=model_data();path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2))

def bind(host,port,tries=50,handler=Handler):
    """Start on the requested port and step up to the next free one if it is taken."""
    for candidate in range(port,port+tries):
        try:return http.server.ThreadingHTTPServer((host,candidate),handler),candidate
        except OSError as error:
            if error.errno!=errno.EADDRINUSE:raise
    raise SystemExit(f'No free port between {port} and {port+tries-1}.')

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8765);p.add_argument('--open',action='store_true')
    p.add_argument('--rebuild',action='store_true',help='regenerate output/parts.json from source/model.py before serving (run source/rebuild.py again before making PDFs)')
    args=p.parse_args()
    parts_path=DATA['/data/parts.json']
    sources=[ROOT/'source/model.py',ROOT/'source/config.json',ROOT/'source/fabrication.py']
    site_parts=ROOT/'_site/data/parts.json'
    stale=not parts_path.exists() or any(s.exists() and s.stat().st_mtime>parts_path.stat().st_mtime for s in sources)
    if args.rebuild or stale:
        if not args.rebuild and site_parts.is_file() and all(site_parts.stat().st_mtime>=s.stat().st_mtime for s in sources if s.exists()):
            parts_path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(site_parts,parts_path)
        else:
            build_data(parts_path)
    import assembly
    assembly_path=DATA['/data/assembly.json'];assembly_path.parent.mkdir(parents=True,exist_ok=True)
    assembly_path.write_text(json.dumps(assembly.manifest(json.loads(DATA['/data/parts.json'].read_text()))),encoding='utf-8')
    from viewer_dxf import preview
    drawing=preview(json.loads(DATA['/data/parts.json'].read_text()))
    cut=DATA['/data/house.dxf'];cut.parent.mkdir(parents=True,exist_ok=True)
    cut.write_text(drawing['dxf'],encoding='utf-8')
    DATA['/data/dxf-labels.json'].write_text(json.dumps(drawing['labels']),encoding='utf-8')
    server,port=bind(args.host,args.port);url=f'http://{args.host}:{port}/'
    if port!=args.port:print(f'Port {args.port} is busy; using the next free port {port}.')
    print(f'{naming.NAME} 3D viewer: {url}  (Ctrl+C to stop)',flush=True)
    if args.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:print()
    finally:server.server_close()

if __name__=='__main__':main()
