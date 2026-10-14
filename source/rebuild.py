"""Rebuild all deliverables with a FreeCAD Python runtime and this Python."""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def clean():
    """Empty output/, so no file from an earlier build (a removed part's DXF, an old sheet or render) survives."""
    out=ROOT/'output';out.mkdir(exist_ok=True)
    for p in out.iterdir():shutil.rmtree(p) if p.is_dir() else p.unlink()
def main():
    p=argparse.ArgumentParser();p.add_argument('--freecad-python',help='FreeCAD bundled Python executable, with FreeCAD/Part/Sketcher importable')
    from supplier import languages
    p.add_argument('--lang',choices=languages(),default='pl',help='Supplier appendix language only (default: pl)')
    p.add_argument('--clean-only',action='store_true',help='only empty output/');args=p.parse_args()
    if args.clean_only:clean();print('output/ emptied');return
    if not args.freecad_python:p.error('--freecad-python is required')
    sys.path.insert(0,str(ROOT/'source'));import config_check;config_check.check()   # fail in a second, not minutes into FreeCAD
    clean();env=dict(os.environ,MOOMIN_HEADLESS='1',QT_QPA_PLATFORM='offscreen')
    for script in ('build_cad.py','nest.py','audit_connections.py'):
        subprocess.run([args.freecad_python,str(ROOT/'source'/script)],cwd=ROOT,env=env,check=True)
    for script in ('render.py','cover.py','decorate_cad.py','book.py','verify.py','package.py'):
        subprocess.run([sys.executable,str(ROOT/'source'/script)]+(['--lang',args.lang] if script=='book.py' else []),cwd=ROOT,check=True)
if __name__=='__main__':main()
