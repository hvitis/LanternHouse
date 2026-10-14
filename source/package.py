"""Create the reviewable build kit, excluding local runtimes, CAD backups and the third-party reference photos."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GUIDE=ROOT/'docs/BUILD-GUIDE.md'   # holds the generated stock tables
def stock_table(sheets):
    groups={}
    for s in sheets:
        key=(s['thickness'],s['width'],s['height'],bool(s.get('existing_stock')))
        groups[key]=groups.get(key,0)+1
    rows=['| Thickness | Sheet size | Quantity |','| --- | --- | --- |']
    for (t,w,h,existing),q in sorted(groups.items(),key=lambda kv:(-kv[0][0],-kv[0][1]*kv[0][2])):
        rows.append(f'| {t:g} mm | {w:g} × {h:g} | {q}{" existing" if existing else ""} |')
    return '\n'.join(rows)
def update_stock_tables(path=GUIDE):
    """Refresh the generated stock tables in the build guide from the current nesting."""
    if not path.exists():return
    nest=json.loads((ROOT/'output/nesting.json').read_text());text=path.read_text()
    for key,sheets in (('main',nest['sheets']),('optional',nest.get('optional_sheets',[]))):
        start,end=f'<!-- stock:{key}:start -->',f'<!-- stock:{key}:end -->'
        if start in text and end in text:
            text=text[:text.index(start)+len(start)]+'\n'+stock_table(sheets)+'\n'+text[text.index(end):]
    path.write_text(text)
def main():
    report=json.loads((ROOT/'output/reports/release-validation.json').read_text())
    if not report['all_pass']:raise RuntimeError('Package blocked: resolve failed release checks')
    update_stock_tables()
    dest=ROOT/'output/Moomin-House-Build-Kit.zip';files=[]
    # original/ is deliberately left out: it holds other people's copyrighted reference photos.
    for folder in ('source','docs','tests','output'):
        for p in (ROOT/folder).rglob('*'):
            if not p.is_file() or p==dest or '__pycache__' in p.parts or p.name=='.DS_Store' or p.suffix in ('.FCBak','.FCStd1','.zip'):continue
            if p.name=='build-manifest.json':continue
            files.append(p)
    files.extend(ROOT/name for name in ('README.md','README.pl.md','TODO.md','LICENSE','Makefile','requirements.txt','requirements-dev.txt','package.json','package-lock.json','pytest.ini','.gitignore') if (ROOT/name).exists())
    manifest={'validation':'output/reports/release-validation.json','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
    mp=ROOT/'output/reports/build-manifest.json';mp.write_text(json.dumps(manifest,indent=2));files.append(mp)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in files:z.write(p,'Moomin-House/'+str(p.relative_to(ROOT)))
    print(f'Packaged {len(files)} files / {dest.stat().st_size/1024/1024:.1f} MB / {dest}')
if __name__=='__main__':main()
