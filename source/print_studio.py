"""Live 3D-print studio: change a design in source/prints/, or move its sliders, and the browser shows the new
part, its printability checks and its downloads about a second later.

    .venv/bin/python source/print_studio.py --open     # http://127.0.0.1:8766/ (or the next free port)
    make studio

Each save of source/prints/<name>.py rebuilds that design into output/prints/live/, with the slider values set
in the page; a save of printer.json or source/print_mesh.py (the checks) rebuilds them all. The page is source/viewer/prints.html, the same page the
published site shows from prints/. Nothing in prints/ changes here: publish with `make prints`. Every build is
also logged in this terminal. The server listens on this machine only, unless --host says otherwise.
"""
import argparse, http.server, importlib, json, queue, threading, time, traceback, webbrowser
from pathlib import Path
import print_build, print_mesh
from serve import VIEWER, bind

ADDRESS=print_build.ROOT/'output/prints/studio-url.txt'

def design_error(error):
    """The error as a designer needs it: where in the design file it happened, then the message."""
    tb=traceback.TracebackException.from_exception(error)
    where=[f'{Path(f.filename).relative_to(print_build.ROOT)}, line {f.lineno}, in {f.name}()' for f in tb.stack if Path(f.filename).parent==print_build.DESIGNS]
    return '\n'.join(where+[''.join(tb.format_exception_only()).strip()])

def log(entry):
    stamp=time.strftime('%H:%M:%S');name=entry['name']
    if 'error' in entry:print(f'{stamp}  {name}: ERROR  {entry["error"].splitlines()[-1]}',flush=True);return
    print(f'{stamp}  {name}: {entry["status"]}  {entry["build_ms"]} ms  {entry["grams"]["estimate"]:g} g  '
          f'{" × ".join(f"{s:g}" for s in entry["size"])} mm',flush=True)
    for c in entry['checks']:
        if c['status']!='pass':print(f'          {c["status"]}: {c["label"]}: {c["detail"]}',flush=True)

class Studio:
    """The latest build of each design, the slider values from the page, and the pages listening for builds."""
    def __init__(self):
        self.lock=threading.Lock();self.parts={};self.overrides={};self.listeners=set();self.version=0

    def manifest(self):
        with self.lock:parts=dict(sorted(self.parts.items()))
        return {'live':True,'printer':print_mesh.printer(),'small_parts':print_mesh.small_parts(),'parts':parts}

    def send(self,message):
        for q in list(self.listeners):q.put(message)

    def build(self,name):
        self.send({'event':'building','part':name})
        with self.lock:
            start=time.perf_counter()
            try:entry=print_build.build(name,self.overrides.get(name),out=print_build.LIVE)
            except Exception as error:   # keep showing the last good build under the error
                entry={**self.parts.get(name,{'name':name,'title':name,'checks':[],'files':{},'params':{}}),'error':design_error(error)}
            self.version+=1
            entry.update(version=self.version,build_ms=round((time.perf_counter()-start)*1000),overrides=self.overrides.get(name,{}))
            self.parts[name]=entry
        log(entry);self.send({'event':'built','part':name,'version':entry['version']})
        return entry

    def watch(self):
        """Rebuild a design when its file is saved, and every design when printer.json or the checks are."""
        seen={}
        while True:
            try:
                stamps={p.stem:p.stat().st_mtime_ns for p in print_build.DESIGNS.glob('*.py') if not p.name.startswith('_')}
                shared=(print_mesh.PRINTER_FILE.stat().st_mtime_ns,Path(print_mesh.__file__).stat().st_mtime_ns)
            except FileNotFoundError:time.sleep(.25);continue   # a file vanished mid-save
            changed=[n for n,s in stamps.items() if seen.get(n)!=s]
            if seen and seen.get('shared')!=shared:
                if seen['shared'][1]!=shared[1]:importlib.reload(print_mesh)   # print_build uses the same module
                changed=list(stamps)
            for gone in set(self.parts)-set(stamps):
                with self.lock:self.parts.pop(gone,None)
                self.send({'event':'removed','part':gone})
            seen={**stamps,'shared':shared}
            for name in changed:self.build(name)
            time.sleep(.25)

class Handler(http.server.SimpleHTTPRequestHandler):
    """The page and three.js from source/viewer/, the live files from output/prints/live/, and a small API."""
    studio=None
    def translate_path(self,path):
        clean=path.split('?',1)[0].split('#',1)[0]
        base,rel=(print_build.LIVE,clean[len('/prints/'):]) if clean.startswith('/prints/') else (VIEWER,clean.lstrip('/') or 'prints.html')
        target=(base/rel).resolve()
        return str(target) if base.resolve() in target.parents else str(VIEWER/'missing')
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
    def log_message(self,fmt,*args):pass
    def send_json(self,data):
        body=json.dumps(data).encode();self.send_response(200)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

    def do_GET(self):
        clean=self.path.split('?',1)[0]
        if clean=='/prints/manifest.json':return self.send_json(self.studio.manifest())
        if clean=='/api/events':return self.events()
        super().do_GET()

    def do_POST(self):
        """{"part": name, "values": {param: value}} sets sliders and rebuilds; {"part": name, "reset": true} clears them."""
        if self.path.split('?',1)[0]!='/api/params':return self.send_error(404)
        # JSON only: a cross-site page cannot send it without a preflight, which this server never answers.
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send_error(415)
        body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}');name=body.get('part')
        if name not in print_build.designs():return self.send_error(404,'No such design')
        if body.get('reset'):self.studio.overrides.pop(name,None)
        else:self.studio.overrides[name]={**self.studio.overrides.get(name,{}),**{k:float(v) for k,v in body.get('values',{}).items()}}
        self.send_json(self.studio.build(name))

    def events(self):
        """Server-sent events: 'building', 'built' and 'removed' for every design, for as long as the page is open."""
        self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
        q=queue.Queue();self.studio.listeners.add(q)
        try:
            while True:
                try:self.wfile.write(f'data: {json.dumps(q.get(timeout=15))}\n\n'.encode())
                except queue.Empty:self.wfile.write(b': still here\n\n')
                self.wfile.flush()
        except OSError:pass   # the page closed
        finally:self.studio.listeners.discard(q)

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8766);p.add_argument('--open',action='store_true')
    args=p.parse_args()
    Handler.studio=studio=Studio()
    threading.Thread(target=studio.watch,daemon=True).start()
    server,port=bind(args.host,args.port,handler=Handler);url=f'http://{args.host}:{port}/'
    if port!=args.port:print(f'Port {args.port} is busy; using the next free port {port}.')
    ADDRESS.parent.mkdir(parents=True,exist_ok=True);ADDRESS.write_text(url+'\n')   # for source/print_shot.mjs
    print(f'Moomin House print studio: {url}  (Ctrl+C to stop)\n'
          f'Edit source/prints/*.py and the page follows. Publish to prints/ with `make prints`.',flush=True)
    if args.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:print()
    finally:server.server_close();ADDRESS.unlink(missing_ok=True)

if __name__=='__main__':main()
