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
from reportlab.lib.utils import simpleSplit, ImageReader
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

ROOT=Path(__file__).resolve().parents[1]
DEFAULTS={'revision':'SUP-002','material':'birch_plywood_raw','include_optional':False,'engraving':'none','maximum_sheet_mm':[297,420],'stock_sizes_mm':[[297,420]],'cutting_tolerance_mm':None,'thickness_tolerance_mm':None}
REGULAR='MoominSans';BOLD='MoominSans-Bold'

def fonts():
    for name,file in ((REGULAR,'DejaVuSans.ttf'),(BOLD,'DejaVuSans-Bold.ttf')):
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(ROOT/'source/fonts'/file)))

def house_bw_image():
    for p in (ROOT/'output/previews/house-closed-veranda.png',ROOT/'output/previews/house-closed.png',ROOT/'docs/images/house-closed.webp'):
        if p.exists():
            im=Image.open(p).convert('RGBA')
            r,g,b,a=im.split()
            gray=ImageOps.grayscale(Image.merge('RGB',(r,g,b)))
            return Image.merge('RGBA',(gray,gray,gray,a))
    return None

def languages():return tuple(sorted(p.stem for p in (ROOT/'source/locales').glob('*.json')))
def catalog(lang):
    if lang not in languages():raise ValueError(f'Unsupported language: {lang}')
    return json.loads((ROOT/'source/locales'/f'{lang}.json').read_text())
def settings(cfg):return dict(DEFAULTS,**cfg.get('supplier',{}))
def sheets_for(data,nest,options):
    sheets=list(nest['sheets'])
    if options['include_optional']:sheets+=nest.get('optional_sheets',[])
    if not sheets:raise ValueError('No plywood production sheets')
    for sheet in sheets:
        if any(data['parts'][item['part']].get('render_only') for item in sheet['items']):raise ValueError('View-only furniture cannot appear in supplier cutting sheets')
        if any(data['parts'][item['part']]['thickness']!=sheet['thickness'] for item in sheet['items']):raise ValueError('Mixed sheet thickness')
    expected=Counter({pid:p['quantity'] for pid,p in data['parts'].items() if not p.get('render_only') and p.get('category') not in ('Purchased wood','Purchased packing') and (options['include_optional'] or not p.get('optional'))})
    if Counter(item['part'] for sheet in sheets for item in sheet['items'])!=expected:raise ValueError('Supplier sheets omit or duplicate required parts')
    validate_one_piece(data,sheets,options)
    return sorted(sheets,key=lambda sheet:(sheet['thickness'],sheet['id']))

def validate_one_piece(data,sheets,options):
    """Never clip, scale or divide a part to make it fit stock or the machine."""
    copies=set()
    for s in sheets:
        size=sorted([s['width'],s['height']])
        if any(a>b+1e-6 for a,b in zip(size,sorted(options['maximum_sheet_mm']))):raise ValueError(f'{s["id"]}: sheet exceeds CNC envelope')
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
    """A4 reference pages and separate clean A3 pages for each machining operation."""
    import cnc
    fonts();tr=catalog(lang);options=settings(cfg);sheets=sheets_for(data,nest,options)
    parts=data['parts'];quantities=Counter(item['part'] for sheet in sheets for item in sheet['items'])
    path=Path(output) if output else ROOT/'output/pdf/Moomin-House-Supplier.pdf'
    path.parent.mkdir(parents=True,exist_ok=True)
    buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=A4,pageCompression=1);pages=[];width,height=A4
    def name(pid):return tr['parts'].get(pid,parts[pid]['name'])
    def text(value,x,y,size=10,bold=False):
        c.setFillColorRGB(0,0,0);c.setFont(BOLD if bold else REGULAR,size);c.drawString(x,y,str(value))
    def paragraph(value,y,size=10):
        for line in simpleSplit(value,REGULAR,size,width-80):text(line,40,y,size);y-=size*1.45
        return y-8
    def start(title,role):
        c.setPageSize(A4);text(title,40,height-55,17,True)
        text(tr['revision']+': '+options['revision'],40,height-76,9)
        pages.append({'page':len(pages)+1,'role':role,'title':title,'size_mm':[210,297]})
    def finish():
        text('Moomin House / '+options['revision'],40,24,8);text(len(pages),width-55,24,8);c.showPage()
    start(tr['title'],'specification')
    bw_house=house_bw_image()
    # Info about the license is preserved here but hidden for now:
    show_license=False
    if bw_house:
        img_w,img_h=(330,440) if show_license else (360,480)
        img_x=(width-img_w)/2;img_y=225 if show_license else (height-img_h)/2-15
        c.drawImage(ImageReader(bw_house),img_x,img_y,width=img_w,height=img_h,mask='auto')
    if show_license:
        c.setStrokeColorRGB(.78,.78,.78);c.setLineWidth(.6);c.line(40,205,width-40,205)
        text(tr['copyright_title'],40,190,8.5,bold=True);y_copy=176
        for block in tr['copyright_notice'].split('\n'):
            y_copy=paragraph(block,y_copy,7.5)+3
    finish()
    start(tr['summary_title'],'summary');y=paragraph(tr['summary_desc'],height-112)
    thicknesses=sorted(set(s['thickness'] for s in sheets))
    x0,w1,w2,w3=40,155,180,180
    x1,x2,x3=x0+w1,x0+w1+w2,x0+w1+w2+w3
    y-=14;y_top=y;h_head=26;h_row=24;h_tot=26
    c.setFillColorRGB(.93,.94,.95);c.rect(x0,y_top-h_head,w1+w2+w3,h_head,fill=1,stroke=0)
    c.setFillColorRGB(0,0,0);c.setFont(BOLD,9.5)
    c.drawString(x0+12,y_top-17,tr['col_thickness'])
    c.drawCentredString(x1+w2/2,y_top-17,tr['col_sheets'])
    c.drawCentredString(x2+w3/2,y_top-17,tr['col_elements'])
    curr_y=y_top-h_head
    for i,t in enumerate(thicknesses):
        t_sheets=[s for s in sheets if s['thickness']==t]
        s_count=len(t_sheets);e_count=sum(len(s['items']) for s in t_sheets)
        if i%2==1:
            c.setFillColorRGB(.98,.98,.98);c.rect(x0,curr_y-h_row,w1+w2+w3,h_row,fill=1,stroke=0)
        c.setFillColorRGB(0,0,0);c.setFont(REGULAR,9.5)
        c.drawString(x0+12,curr_y-16,f'{t:g} mm')
        c.drawCentredString(x1+w2/2,curr_y-16,str(s_count))
        c.drawCentredString(x2+w3/2,curr_y-16,str(e_count))
        c.setStrokeColorRGB(.82,.82,.82);c.setLineWidth(.5);c.line(x0,curr_y-h_row,x3,curr_y-h_row)
        curr_y-=h_row
    tot_sheets=len(sheets);tot_elements=sum(quantities.values())
    c.setFillColorRGB(.93,.94,.95);c.rect(x0,curr_y-h_tot,w1+w2+w3,h_tot,fill=1,stroke=0)
    c.setFillColorRGB(0,0,0);c.setFont(BOLD,10)
    c.drawString(x0+12,curr_y-17,tr['total'])
    c.drawCentredString(x1+w2/2,curr_y-17,str(tot_sheets))
    c.drawCentredString(x2+w3/2,curr_y-17,str(tot_elements))
    c.setStrokeColorRGB(0,0,0);c.setLineWidth(1)
    c.line(x0,curr_y,x3,curr_y);c.line(x0,curr_y-h_tot,x3,curr_y-h_tot)
    curr_y-=h_tot
    c.rect(x0,curr_y,w1+w2+w3,y_top-curr_y,fill=0,stroke=1)
    c.setStrokeColorRGB(.82,.82,.82);c.setLineWidth(.5)
    c.line(x1,curr_y,x1,y_top);c.line(x2,curr_y,x2,y_top)
    y_note=curr_y-24
    paragraph(tr['summary_footnote'].format(sheets=tot_sheets,parts=len(quantities),elements=tot_elements),y_note,8.5)
    finish()
    ordered=sorted(quantities,key=lambda pid:(parts[pid]['thickness'],pid))
    for first in range(0,len(ordered),20):
        start(tr['inventory'],'inventory');y=height-114
        text('ID / '+tr['name']+' / mm / '+tr['quantity'],40,y,9,True);y-=25
        for pid in ordered[first:first+20]:
            p=parts[pid];text(pid,40,y,8.5);text(name(pid),110,y,8.5)
            text(f'{p["width"]:.2f} × {p["height"]:.2f} × {p["thickness"]:g}',110,y-12,8)
            text(quantities[pid],width-60,y,9);y-=31
        finish()
    sheet_meta=[];operation_records=[]
    for sheet in sheets:
        start(tr['map']+' / '+sheet['id'],'reference');pages[-1]['sheet']=sheet['id']
        text(f'{sheet["width"]:g} × {sheet["height"]:g} mm / {sheet["thickness"]:g} mm',40,height-109)
        text(tr['reference_warning'],40,height-127,9)
        k=min((width-100)/sheet['width'],410/sheet['height']);ox=(width-sheet['width']*k)/2;oy=height-150-sheet['height']*k
        # Reference maps show finished boundaries, including retained blank edges.
        for item in sheet['items']:
            p=parts[item['part']]
            curves=[('polygon',[transform(p,item,*v) for v in p['outer']])]+[('polygon',[transform(p,item,*v) for v in cut]) for cut in p['cuts']]
            cnc.draw(c,curves,k,ox,oy)
            x,y=transform(p,item,p['width']/2,p['height']/2)
            c.saveState();c.translate(ox+x*k,oy+y*k)
            if p['height']>p['width'] and p['width']<20:c.rotate(90)
            c.setFont(REGULAR,5);c.drawCentredString(0,0,item['part']);c.restoreState()
        y=oy-24
        counts=sorted(Counter(item['part'] for item in sheet['items']).items())
        for first in range(0,len(counts),4):y=paragraph('   '.join(f'{pid} × {count}' for pid,count in counts[first:first+4]),y,8)
        reference_page=len(pages);finish()
        ops=cnc.operations(data,sheet);meta={'id':sheet['id'],'size_mm':[sheet['width'],sheet['height']],'thickness_mm':sheet['thickness'],'quantity':len(sheet['items']),'reference_page':reference_page,'production_pages':[],'optional':False}
        for operation,curves in ops.items():
            c.setPageSize((sheet['width']*mm,sheet['height']*mm));cnc.draw(c,curves,mm);c.showPage()
            page=len(pages)+1;stem=f'{sheet["id"]}-cnc-{operation}'
            pages.append({'page':page,'role':'production','sheet':sheet['id'],'operation':operation,'dxf':stem+'.dxf','title':f'{sheet["id"]} / {operation} / {sheet["thickness"]:g} mm','size_mm':meta['size_mm']})
            meta['production_pages'].append(page)
            operation_records.append({'sheet':sheet['id'],'thickness_mm':sheet['thickness'],'operation':operation,'page':page,'reference_page':reference_page,'dxf':stem+'.dxf'})
        meta['production_page']=meta['production_pages'][0];sheet_meta.append(meta)
    # A paginated operation schedule identifies text-free production pages.
    for first in range(0,len(operation_records),24):
        start(tr['index'],'index');y=height-112
        for record in operation_records[first:first+24]:
            text(f'{record["sheet"]} / {record["thickness_mm"]:g} mm / {record["operation"]}',40,y,8.5)
            text(f'{tr["reference"]} {record["reference_page"]} / {tr["production"]} {record["page"]}',width-210,y-12,8);y-=26
        finish()
    c.save();buf.seek(0);reader=PdfReader(buf);writer=PdfWriter()
    for page,meta in zip(reader.pages,pages):
        page[NameObject('/MoominPageRole')]=TextStringObject(meta['role'])
        if 'sheet' in meta:page[NameObject('/MoominSheetID')]=TextStringObject(meta['sheet'])
        if 'operation' in meta:page[NameObject('/MoominOperation')]=TextStringObject(meta['operation'])
        writer.add_page(page)
    for meta in pages:writer.add_outline_item(meta['title'],meta['page']-1)
    writer.add_metadata({'/Title':'Moomin House | '+tr['title'],'/Author':'Moomin House','/Revision':options['revision']})
    writer._root_object[NameObject('/Lang')]=TextStringObject(lang)
    with path.open('wb') as f:writer.write(f)
    csvpath=path.with_suffix('.csv')
    with csvpath.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(operation_records[0]));w.writeheader();w.writerows(operation_records)
    report={'language':lang,'revision':options['revision'],'title':tr['title'],'pdf':path.name,'csv':csvpath.name,'pages':pages,'sheets':sheet_meta,'operations':operation_records,'quantities':dict(quantities),'house_pieces':sum(quantities.values()),'optional_pieces':0,'status':'supplier_confirmation_required','engraving':'none','one_piece_check':True,'required_stock_sizes_mm':options['stock_sizes_mm'],'maximum_sheet_mm':options['maximum_sheet_mm'],'geometry_sha256':hashlib.sha256(json.dumps([cnc.operations(data,s) for s in sheets],sort_keys=True).encode()).hexdigest()}
    return path,report


def summary(report,output):
    """A4-only supplier appendix for the complete workshop book."""
    fonts();tr=catalog(report['language']);c=canvas.Canvas(str(output),pagesize=A4)
    for first in range(0,len(report['sheets']),20):
        c.setFont(BOLD,18);c.drawString(40,A4[1]-55,tr['title'])
        c.setFont(REGULAR,10);y=A4[1]-90
        for line in simpleSplit(tr['summary_note'],REGULAR,10,A4[0]-80):c.drawString(40,y,line);y-=15
        y-=20
        for s in report['sheets'][first:first+20]:
            c.drawString(40,y,f'{s["id"]} / {s["thickness_mm"]:g} mm / {s["quantity"]} / '+', '.join(map(str,s['production_pages'])));y-=25
        c.showPage()
    c.save();return Path(output)
