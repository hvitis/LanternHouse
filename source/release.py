"""Publish a GitHub release with the generated PDFs, the supplier cut DXF and the build kit attached, using the GitHub CLI (gh).

    .venv/bin/python source/release.py v5 --dry-run    # check everything and print the release, upload nothing
    .venv/bin/python source/release.py v5 --draft      # create a draft release to review on GitHub
    .venv/bin/python source/release.py v5              # create and publish release v5 at the current commit

Generated files never go into git (about 100 MB per build); release assets are where builders download them.
Before uploading, this checks that the last build passed every release check, that it was built from the
source now on disk, and that this source is committed and pushed, so the files match the release tag.
"""
import argparse, hashlib, json, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
PDFS=['Complete','Instructions','Cutting-Templates','Dimensioned-Parts','Decor','Clay-Family','3mm-Hand-Templates','Supplier']
KIT=OUT/'Moomin-House-Build-Kit.zip'
CUT=OUT/'Moomin-House-Supplier-Cut.dxf'   # everything the supplier cuts, in one file

def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True).stdout.rstrip()

def repo_url():
    """https://github.com/<owner>/<repo> of the repository gh releases to, or None if gh cannot tell."""
    if not shutil.which('gh'):return None
    run=subprocess.run(['gh','repo','view','--json','url','--jq','.url'],cwd=ROOT,capture_output=True,text=True)
    return run.stdout.strip() or None

def sha256(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def assets():
    return [OUT/'pdf'/f'Moomin-House-{name}.pdf' for name in PDFS]+[CUT,KIT]

def problems():
    """Every reason the current output/ must not be released; empty when it is ready."""
    found=[];report=OUT/'reports/release-validation.json';manifest=OUT/'reports/build-manifest.json'
    if not report.exists():return ['there is no build: run source/rebuild.py first']
    checks=json.loads(report.read_text())
    found+=[f'release check failed: {c["check"]}' for c in checks['checks'] if not c['pass']]
    found+=[f'missing {p.relative_to(ROOT)}' for p in assets() if not p.exists()]
    if manifest.exists():
        # The manifest records the source the build ran from; any difference means output/ is stale.
        stale=[f['path'] for f in json.loads(manifest.read_text())['files'] if f['path'].startswith('source/')
               and (not (ROOT/f['path']).exists() or sha256(ROOT/f['path'])!=f['sha256'])]
        if stale:found.append(f'output/ was built from different source; rebuild first ({", ".join(stale[:4])}{" ..." if len(stale)>4 else ""} changed)')
    else:found.append('missing output/reports/build-manifest.json: run source/rebuild.py')
    if KIT.exists():
        with zipfile.ZipFile(KIT) as z:
            if any('/original/' in name for name in z.namelist()):found.append('the build kit contains the original/ reference photos: rebuild with the current package.py')
    dirty=git('status','--porcelain','--','source','requirements.txt')
    if dirty:found.append('source/ has uncommitted changes; commit them so the release tag matches the files:\n    '+dirty.replace('\n','\n    '))
    elif not git('branch','-r','--contains','HEAD'):found.append('the current commit is not on GitHub yet: push it first')
    if not shutil.which('gh'):found.append('the GitHub CLI (gh) is not installed: https://cli.github.com')
    return found

def notes(tag):
    """Release notes from the build reports."""
    checks=json.loads((OUT/'reports/release-validation.json').read_text())['checks']
    pages=json.loads((OUT/'reports/pdf-report.json').read_text())
    cad=json.loads((OUT/'reports/cad-validation.json').read_text())
    nest=json.loads((OUT/'nesting.json').read_text())
    sys.path.insert(0,str(ROOT/'source'));from package import stock_table
    pdf_pages={**pages['pdfs'],'Moomin-House-Complete.pdf':pages['complete_pages']}
    contents={CUT.name:'every cutting path for the supplier in one DXF R12 file: mm, one layer per plywood thickness, no frames or text',
              KIT.name:'everything: PDFs, STEP, FCStd, DXF, laser files, renders, reports and source'}
    rows=[f'| `{p.name}` | {f"{pdf_pages[p.name]} pages" if p.name in pdf_pages else contents[p.name]} | {p.stat().st_size/1024/1024:.1f} MB |' for p in assets()]
    url=repo_url();guide=f'[the build guide]({url}/blob/{tag}/docs/BUILD-GUIDE.md)' if url else 'the build guide (docs/BUILD-GUIDE.md)'
    return '\n'.join([
        f'Built from {git("rev-parse","--short","HEAD")} with FreeCAD {cad.get("freecad_version","?")}. All {len(checks)} release checks passed.','',
        '| File | Contents | Size |','| --- | --- | --- |',*rows,'',
        f'Print the cutting templates at **100 % / actual size** and measure the 100 mm calibration square before cutting. Read {guide} first.','',
        '**Plywood for the house**','',stock_table(nest['sheets']),'',
        'Furniture appears in the 3D viewer and renders only. The build kit contains no furniture CAD plans or cutting sheets.',
    ])

def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('tag',help='release tag, for example v5');p.add_argument('--title',help='default: "Moomin House <tag>"')
    p.add_argument('--draft',action='store_true',help='create a draft to review on GitHub before publishing')
    p.add_argument('--dry-run',action='store_true',help='check and print the release without uploading anything')
    args=p.parse_args();found=problems()
    if args.dry_run or found:
        if (OUT/'reports/release-validation.json').exists() and all(p.exists() for p in assets()):
            print(f'--- release notes for {args.tag} ---\n{notes(args.tag)}\n')
        print('Assets:\n'+'\n'.join(f'  {p.relative_to(ROOT)}' for p in assets()))
    if found:raise SystemExit('\nNot ready to release:\n'+'\n'.join('  - '+f for f in found))
    if args.dry_run:print('\nReady to release. Run again without --dry-run to upload.');return
    command=['gh','release','create',args.tag,*map(str,assets()),'--title',args.title or f'Moomin House {args.tag}',
             '--target',git('rev-parse','HEAD'),'--notes-file','-']+(['--draft'] if args.draft else [])
    subprocess.run(command,cwd=ROOT,input=notes(args.tag),text=True,check=True)

if __name__=='__main__':main()
