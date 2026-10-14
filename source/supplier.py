"""Localized supplier specification and exact, unannotated 3 mm vector sheets."""
from __future__ import annotations
import csv, hashlib, io, json, math
from collections import Counter
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

ROOT=Path(__file__).resolve().parents[1]
DEFAULTS={'revision':'SUP-001','material':'birch_plywood_raw','include_optional':False,'engraving':'none','maximum_sheet_mm':[1600,1000],'stock_sizes_mm':[[210,297],[297,420]],'cutting_tolerance_mm':None,'thickness_tolerance_mm':None}
REGULAR='MoominSans';BOLD='MoominSans-Bold'

def fonts():
    for name,file in ((REGULAR,'DejaVuSans.ttf'),(BOLD,'DejaVuSans-Bold.ttf')):
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(ROOT/'source/fonts'/file)))

def languages():return tuple(sorted(p.stem for p in (ROOT/'source/locales').glob('*.json')))
def catalog(lang):
    if lang not in languages():raise ValueError(f'Unsupported language: {lang}')
    return json.loads((ROOT/'source/locales'/f'{lang}.json').read_text())
def settings(cfg):return dict(DEFAULTS,**cfg.get('supplier',{}))
def sheets_for(data,nest,options):
    sheets=[s for s in nest['sheets'] if s['thickness']==3]
    if options['include_optional']:sheets += [s for s in nest.get('optional_sheets',[]) if s['thickness']==3]
    if not sheets:raise ValueError('No 3 mm production sheets')
    for s in sheets:
        if any(data['parts'][i['part']].get('render_only') for i in s['items']):raise ValueError('View-only furniture cannot appear in supplier cutting sheets; rebuild the nesting')
        if any(data['parts'][i['part']]['thickness']!=3 for i in s['items']):raise ValueError('Mixed sheet thickness')
    expected=Counter({pid:p['quantity'] for pid,p in data['parts'].items() if p['thickness']==3 and not p.get('render_only') and (options['include_optional'] or not p.get('optional'))})
    if Counter(i['part'] for s in sheets for i in s['items'])!=expected:raise ValueError('Supplier sheets omit or duplicate required parts')
    validate_one_piece(data,sheets,options)
    return sheets

def validate_one_piece(data,sheets,options):
    """Never clip, scale or divide a part to make it fit stock or the machine."""
    copies=set()
    for s in sheets:
        size=sorted([s['width'],s['height']])
        if any(a>b+1e-6 for a,b in zip(size,sorted(options['maximum_sheet_mm']))):raise ValueError(f'{s["id"]}: sheet exceeds laser envelope')
        if not any(all(abs(a-b)<1e-6 for a,b in zip(size,sorted(stock))) for stock in options['stock_sizes_mm']):raise ValueError(f'{s["id"]}: unsupported blank size')
        x0,y0,x1,y1=s.get('window',[0,0,s['width'],s['height']])
        if x0<0 or y0<0 or x1>s['width'] or y1>s['height']:raise ValueError('Invalid sheet window')
        for item in s['items']:
            key=(item['part'],item['copy'])
            if key in copies:raise ValueError(f'{key}: one part appears on multiple sheets or twice')
            copies.add(key);p=data['parts'][item['part']]
            pts=[transform(p,item,*v) for v in p['outer']]
            if p.get('outercircle'):
                xx,yy,r=p['outercircle'];xx,yy=transform(p,item,xx,yy);pts=[(xx-r,yy-r),(xx+r,yy+r)]
            if any(not x0-1e-6<=x<=x1+1e-6 or not y0-1e-6<=y<=y1+1e-6 for x,y in pts):raise ValueError(f'{key}: whole part does not fit a single sheet')

def transform(part,item,x,y):
    th=math.radians(item['angle']);co,si=math.cos(th),math.sin(th)
    corners=[(a*co-b*si,a*si+b*co) for a,b in part['outer']]
    return (x*co-y*si-min(a for a,b in corners)+item['x'],x*si+y*co-min(b for a,b in corners)+item['y'])

def contours(data,sheet):
    """Finished curves only. Starter holes and part labels never enter this interface."""
    for item in sheet['items']:
        p=data['parts'][item['part']]
        if p.get('outercircle'):
            x,y,r=p['outercircle'];x,y=transform(p,item,x,y);yield ('circle',(x,y,r))
        else:yield ('polygon',[transform(p,item,*v) for v in p['outer']])
        for cut in p['cuts']:yield ('polygon',[transform(p,item,*v) for v in cut])
        for h in p['holes']:
            if h.get('depth') is not None and h['depth']<p['thickness']:raise ValueError(f'{p["id"]}: a blind hole cannot be laser through-cut')
            x,y=transform(p,item,h['x'],h['y']);yield ('circle',(x,y,h['diameter']/2))

def draw_paths(c,data,sheet,scale=mm,ox=0,oy=0):
    c.setStrokeColorRGB(0,0,0);c.setLineWidth(.01*mm)
    for kind,curve in contours(data,sheet):
        if kind=='circle':
            x,y,r=curve;c.circle(ox+x*scale,oy+y*scale,r*scale,stroke=1,fill=0)
        else:
            p=c.beginPath();p.moveTo(ox+curve[0][0]*scale,oy+curve[0][1]*scale)
            for x,y in curve[1:]:p.lineTo(ox+x*scale,oy+y*scale)
            p.close();c.drawPath(p,stroke=1,fill=0)

def build(data,nest,cfg,lang='pl',output=None):
    """Return path + page metadata. Production pages stay text-free in every language."""
    fonts();tr=catalog(lang);options=settings(cfg);sheets=sheets_for(data,nest,options)
    parts=data['parts'];quantities=Counter(i['part'] for s in sheets for i in s['items'])
    for pid in quantities:
        if pid not in tr['parts']:raise ValueError(f'{lang}: missing supplier translation for {pid}')
        if quantities[pid]!=parts[pid]['quantity']:raise ValueError(f'{pid}: incomplete supplier quantity')
    inventory=[]
    for optional in (False,True):
        ids=sorted(pid for pid in quantities if bool(parts[pid].get('optional'))==optional)
        for start in range(0,len(ids),22):inventory.append((optional,ids[start:start+22]))
    roof_sheets=[s for s in sheets if any(i['part'] in ('R01','R06') for i in s['items'])]
    reference_start=3+len(inventory)+bool(roof_sheets);production_start=reference_start+len(sheets)
    path=Path(output) if output else ROOT/'output/pdf/Moomin-House-Supplier.pdf'
    path.parent.mkdir(parents=True,exist_ok=True);buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=A4,pageCompression=1)
    c.setTitle('Moomin House | '+tr['title']);c.setAuthor('Moomin House');width,height=A4
    pages=[]
    def text(value,x,y,size=10,bold=False):
        c.setFillColorRGB(0,0,0);c.setFont(BOLD if bold else REGULAR,size);c.drawString(x,y,value)
    def paragraph(value,y,size=10):
        for line in simpleSplit(value,REGULAR,size,width-80):text(line,40,y,size);y-=size*1.5
        return y-8
    def start(title,role):
        c.setPageSize(A4);text(title,40,height-55,17,True)
        text(f'{tr["revision"]}: {options["revision"]}',40,height-76,9)
        pages.append({'page':len(pages)+1,'role':role,'title':title,'size_mm':[210,297]})
    def finish():
        text(f'Moomin House / {options["revision"]}',40,24,8);c.setFont(REGULAR,8);c.drawRightString(width-40,24,f'{tr["page"]} {len(pages)}');c.showPage()
    def row(values,y,widths,bold=False):
        x=40
        for value,w in zip(values,widths):text(str(value),x+3,y,8.5,bold);x+=w
        c.setStrokeColorRGB(.7,.7,.7);c.setLineWidth(.3);c.line(40,y-7,width-40,y-7)
        return y-23
    start(tr['title'],'specification');y=paragraph(tr['status'],height-112,10)
    fields=[('material',tr[options['material']]),('supply',tr['supplier_material']),('thickness','3.0 mm'),('process',tr['laser']),('engraving',tr['no_engraving'])]
    for key,value in fields:y=paragraph(tr[key]+': '+value,y)
    for key,setting in [('cut_tolerance','cutting_tolerance_mm'),('thickness_tolerance','thickness_tolerance_mm')]:
        value=tr['pending'] if options[setting] is None else f'±{options[setting]:g} mm — '+tr['proposed']
        y=paragraph(tr[key]+': '+value,y)
    for key in ('kerf','spacing','one_piece','packing','no_substitution','production_only'):y=paragraph(tr[key],y,9.5)
    if y<50:raise ValueError('Supplier specification exceeds one page')
    finish()
    start(tr['index'],'index');y=height-117
    y=row([tr['sheet'],tr['group'],tr['size'],tr['quantity'],tr['reference'],tr['production']],y,[83,90,100,66,80,96],True)
    sheet_meta=[]
    for j,s in enumerate(sheets):
        optional=all(parts[i['part']].get('optional') for i in s['items']);group=tr['optional'] if optional else tr['house']
        y=row([s['id'],group,f'{s["width"]:g} × {s["height"]:g}',len(s['items']),reference_start+j,production_start+j],y,[83,90,100,66,80,96])
        sheet_meta.append({'id':s['id'],'size_mm':[s['width'],s['height']],'quantity':len(s['items']),'reference_page':reference_start+j,'production_page':production_start+j,'optional':optional})
    y=paragraph(tr['page_note'],y-22,10)
    house=sum(m['quantity'] for m in sheet_meta if not m['optional']);optional_count=sum(m['quantity'] for m in sheet_meta if m['optional'])
    paragraph(tr['totals' if optional_count else 'house_totals'].format(house=house,optional=optional_count,total=house+optional_count),y,11);finish()
    if roof_sheets:
        start(tr['capacity'],'capacity');y=height-112
        sources=json.loads((ROOT/'source/supplier_sources.json').read_text())
        roof=next(parts[k] for k in ('R01','R06') if k in quantities)
        y=paragraph(tr['roof_fit'].format(width=roof['width'],height=roof['height']),y,10)
        y=paragraph(tr['capacity_note'],y,10)
        low=min(r['price_pln'][0] for r in sources['retail_a3_3mm']);high=max(r['price_pln'][1] for r in sources['retail_a3_3mm'])
        y=paragraph(tr['cost_note'].format(date=sources['checked_local_date'],count=len(roof_sheets),low=low,high=high,total_low=low*len(roof_sheets),total_high=high*len(roof_sheets)),y,10)
        y=paragraph(tr['fallback'],y,10)
        text(tr['sources'],40,y-7,10,True);y-=29
        for source in sources['vendors']+sources['retail_a3_3mm']:
            text(source['name'],40,y,9);c.linkURL(source['url'],(40,y-3,width-40,y+11),relative=0);y-=23
        finish()
    for optional,ids in inventory:
        start(tr['inventory']+' / '+(tr['optional'] if optional else tr['house']),'inventory');y=height-117
        y=row(['ID',tr['name'],tr['size'],tr['quantity']],y,[61,280,105,69],True)
        for pid in ids:
            p=parts[pid];y=row([pid,tr['parts'][pid],f'{p["width"]:.2f} × {p["height"]:.2f}',quantities[pid]],y,[61,280,105,69])
        finish()
    for j,s in enumerate(sheets):
        start(tr['map']+' / '+s['id'],'reference');pages[-1]['sheet']=s['id']
        paragraph(tr['reference_only'].format(page=production_start+j),height-110,9)
        scale=min((width-100)/s['width'],420/s['height']);ox=(width-s['width']*scale)/2;oy=250
        draw_paths(c,data,s,scale,ox,oy)
        for item in s['items']:
            p=parts[item['part']];x,y=transform(p,item,p['width']/2,p['height']/2)
            c.saveState();c.translate(ox+x*scale,oy+y*scale)
            w,h=(p['width'],p['height']) if item['angle']%180==0 else (p['height'],p['width'])
            if h>w and w<12:c.rotate(90)
            c.setFillColorRGB(.05,.15,.25);c.setFont(REGULAR,4.5);c.drawCentredString(0,-1.5,item['part']);c.restoreState()
        counts=sorted(Counter(i['part'] for i in s['items']).items())
        text(tr['quantity_by_id'],40,216,10,True)
        for k,(pid,count) in enumerate(counts):text(f'{pid} × {count}',40+(k%3)*172,196-(k//3)*17,9)
        finish()
    for s in sheets:
        c.setPageSize((s['width']*mm,s['height']*mm));draw_paths(c,data,s);c.showPage()
        pages.append({'page':len(pages)+1,'role':'production','sheet':s['id'],'title':tr['production']+' / '+s['id'],'size_mm':[s['width'],s['height']]})
    c.save();buf.seek(0);reader=PdfReader(buf);writer=PdfWriter()
    for page,meta in zip(reader.pages,pages):
        page[NameObject('/MoominPageRole')]=TextStringObject(meta['role'])
        if 'sheet' in meta:page[NameObject('/MoominSheetID')]=TextStringObject(meta['sheet'])
        writer.add_page(page)
    for meta in pages:writer.add_outline_item(meta['title'],meta['page']-1)
    writer.add_metadata({'/Title':'Moomin House | '+tr['title'],'/Author':'Moomin House','/Subject':tr['status'],'/Revision':options['revision']})
    writer.root_object[NameObject('/Lang')]=TextStringObject(lang)
    with path.open('wb') as f:writer.write(f)
    csvpath=path.with_suffix('.csv')
    with csvpath.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['ID',tr['name'],tr['group'],tr['quantity'],tr['thickness'],tr['width'],tr['height']])
        for pid,count in sorted(quantities.items()):
            p=parts[pid];w.writerow([pid,tr['parts'][pid],tr['optional'] if p.get('optional') else tr['house'],count,3,round(p['width'],4),round(p['height'],4)])
    report={'language':lang,'revision':options['revision'],'title':tr['title'],'pdf':path.name,'csv':csvpath.name,'pages':pages,'sheets':sheet_meta,'quantities':dict(quantities),'house_pieces':house,'optional_pieces':optional_count,'status':'supplier_confirmation_required','engraving':'none','one_piece_check':True,'required_stock_sizes_mm':options['stock_sizes_mm'],'maximum_sheet_mm':options['maximum_sheet_mm'],'geometry_sha256':hashlib.sha256(json.dumps([list(contours(data,s)) for s in sheets],sort_keys=True).encode()).hexdigest()}
    return path,report
