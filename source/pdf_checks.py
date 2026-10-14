"""Independent PDF geometry checks against existing laser DXFs and book indices."""
import json,math
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

# ReportLab rounds the largest A3 coordinates to 0.001 PDF point.
# The resulting half-unit rounding is at most 0.000177 mm.
# This encoding allowance is unrelated to the supplier's manufacturing tolerance.
PDF_COORDINATE_EPS_MM = .0002

def pdf_paths(page):
    result=[];points=[];curves=False
    for args,op in page.get_contents().operations:
        if op==b'm':points=[tuple(map(float,args))];curves=False
        elif op==b'l':points.append(tuple(map(float,args)))
        elif op==b'c':points.append(tuple(map(float,args[-2:])));curves=True
        elif op==b'S':
            scale=25.4/72
            if curves:
                xs,ys=zip(*points);result.append(('circle',[(min(xs)+max(xs))/2*scale,(min(ys)+max(ys))/2*scale,(max(xs)-min(xs))/2*scale]))
            else:result.append(('polygon',[v*scale for point in points for v in point]))
            points=[]
    return result

def dxf_paths(path):
    lines=path.read_text().splitlines();pairs=list(zip(lines[::2],lines[1::2]));entities=[];entry=[]
    for code,value in pairs:
        if code=='0':
            if entry:entities.append(entry)
            entry=[]
        entry.append((code,value))
    if entry:entities.append(entry)
    result=[]
    for e in entities:
        tags=dict(e)
        if tags.get('8')!='CUT':continue
        if e[0][1]=='LWPOLYLINE':
            xs=[float(v) for c,v in e if c=='10'];ys=[float(v) for c,v in e if c=='20']
            result.append(('polygon',[v for point in zip(xs,ys) for v in point]))
        elif e[0][1]=='CIRCLE':result.append(('circle',[float(tags[k]) for k in ('10','20','40')]))
    return result

def checks(root):
    root=Path(root);out=root/'output';result=[]
    def check(name,ok,detail=''):result.append((name,bool(ok),detail))
    metadata=json.loads((out/'reports/pdf-report.json').read_text());supplier=json.loads((out/'reports/supplier-index.json').read_text());contents=json.loads((out/'reports/contents-index.json').read_text())
    book=PdfReader(out/'pdf/Moomin-House-Complete.pdf');vendor=PdfReader(out/'pdf'/supplier['pdf'])
    expected=set(metadata['pdfs'])|{'Moomin-House-Complete.pdf'};actual={p.name for p in (out/'pdf').glob('*.pdf')}
    check('Expected PDF files, including supplier and hand templates',actual==expected,str(sorted(actual)))
    size_ok=True;clean_ok=True;geometry_ok=True
    for name in actual:
        reader=PdfReader(out/'pdf'/name)
        for n,p in enumerate(reader.pages):
            width,height=float(p.mediabox.width)*25.4/72,float(p.mediabox.height)*25.4/72
            if p.get('/MoominPageRole')=='production':
                s=next((s for s in supplier['sheets'] if s['id']==p.get('/MoominSheetID')),None)
                size_ok=size_ok and s is not None and all(abs(a-b)<.001 for a,b in zip((width,height),s['size_mm']))
                clean_ok=clean_ok and not p.extract_text().strip() and not p.get('/Annots') and not p.images
                ops=p.get_contents().operations
                clean_ok=clean_ok and not any(op in (b'Tj',b'TJ',b"'",b'"',b'Do',b'f',b'f*',b'B',b'B*',b'W',b'W*') for _,op in ops)
                if name==supplier['pdf']:
                    native=pdf_paths(p);dxf=dxf_paths(out/'dxf'/f'{s["id"]}-laser.dxf')
                    geometry_ok=geometry_ok and len(native)==len(dxf) and all(a[0]==b[0] and len(a[1])==len(b[1]) and all(abs(x-y)<PDF_COORDINATE_EPS_MM for x,y in zip(a[1],b[1])) for a,b in zip(native,dxf))
            else:size_ok=size_ok and abs(width-210)<.001 and abs(height-297)<.001
    check('A4 workshop/reference pages and exact native-size production pages',size_ok)
    check('Production pages have only unannotated vector cutting paths',clean_ok)
    check('Supplier production geometry matches independent laser DXFs within 0.0002 mm (PDF encoding)',geometry_ok)
    supplier_start=contents['sections'][-1]['first_page']-1
    check('Supplier appendix is last and preserves every original page',len(book.pages)-supplier_start==len(vendor.pages) and all(book.pages[supplier_start+j].get_contents().get_data()==p.get_contents().get_data() for j,p in enumerate(vendor.pages)))
    link_count=sum(len(book.pages[p].get('/Annots',[])) for p in range(1,1+contents['contents_pages']))
    check('Printed contents links cover every indexed entry',link_count==len(contents['entries']) and all(1<=e['complete_page']<=len(book.pages) for e in contents['entries']))
    destinations=[]
    def walk(items):
        for i in items:
            if isinstance(i,list):walk(i)
            else:destinations.append((i.title,book.get_destination_page_number(i)+1))
    walk(book.outline)
    check('All contents bookmarks resolve to their indexed pages',all((e['title'],e['complete_page']) in destinations for e in contents['entries']))
    import supplier as exporter
    cfg=json.loads((root/'source/config.json').read_text());data=json.loads((out/'parts.json').read_text());nest=json.loads((out/'nesting.json').read_text())
    try:exporter.sheets_for(data,nest,exporter.settings(cfg));one_piece=True
    except ValueError:one_piece=False
    check('Every supplier part fits one blank and laser envelope without splitting',one_piece and supplier['one_piece_check'])
    check('Supplier appendix excludes furniture and engraving',supplier['optional_pieces']==0 and supplier['engraving']=='none' and not any(s['optional'] for s in supplier['sheets']))
    check('Supplier language and revision recorded',vendor.trailer['/Root'].get('/Lang')==supplier['language'] and vendor.metadata.get('/Revision')==supplier['revision'])
    hand=json.loads((out/'reports/hand-template-index.json').read_text())
    check('Hand templates cover the same complete sheets',{i['sheet'] for i in hand}=={s['id'] for s in supplier['sheets']})
    return result
