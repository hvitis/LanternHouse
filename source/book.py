"""Dimensioned A4 building book, fabrication templates and colored paper decor."""
from __future__ import annotations
import argparse, json, math, random, textwrap
from pathlib import Path
from collections import Counter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit, ImageReader
from pypdf import PdfReader, PdfWriter
from model import fabrication_parts, BOUGHT
from specifications import book_rows
import assembly, naming

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'output/parts.json').read_text());P=DATA['parts'];CFG=DATA['config']
NEST=json.loads((ROOT/'output/nesting.json').read_text())
W,H=A4;M=40;INK=colors.HexColor('#284849');TEAL=colors.HexColor('#197F98');RUST=colors.HexColor('#B56535');LINE=colors.HexColor('#d6ded4')
OUT=ROOT/'output/pdf';OUT.mkdir(exist_ok=True)
DER=DATA['derived'];DOORS=CFG['doors'];VER=CFG['veranda'];VER_FACET=int(VER['facet'][1:])-1
TOPS=DER['floor_tops'];G0=TOPS[0];PITCH=CFG['floor_pitch'];EAVE=DER['roof_eave'];CLEAR=DER['clear_room_height']
GUSSETS=tuple(DER['brace_heights']);HINGES=[G0+c for c in CFG['wall_hinge']['centers']];DRAWER=CFG['plinth']['drawer']
MAG,CATCH,STOP=CFG['magnets'],CFG['wall_catch'],CFG['wall_stop'];OPEN=DER['views']['open_angle'];SIDE=DER['drawer']['side']
# Roof pivot: the bolt's washer stack (WS1 under the head plus the packing ones), the laminated turn-button and the pillar.
BL1=next((f for f in DATA['fasteners'] if f['type']=='BL1'),None);SC1=next(f for f in DATA['fasteners'] if f['type']=='SC1');WS1=(1+len(BL1['stack_mm'])-8) if BL1 else 0;LOCK=(P.get('E08',{}).get('thickness',0)+P.get('E09',{}).get('thickness',0));PT=P['P01']['thickness']
STOPWALLS=' and '.join(k for k,v in P.items() if any('garden stop' in h['purpose'] for h in v['holes']));CATCHHOLES=' and '.join(f'{pid}/{h["id"]}' for pid,p in P.items() if p.get('assembly_panel')=='F02' for h in p['holes'] if 'catch' in h['purpose'])
def zl(values):return ', '.join(f'Z{v:g}' for v in values[:-1])+f' and Z{values[-1]:g}'
# The book covers the house and clay family; furnishings only appear in the 3D view.
MAIN=fabrication_parts(DATA)
# Wall facets in order (facet 1 = front-right). Identical walls share one part ID, so a part can fill several facets.
FACETS=DER['facets']
PAGE_TITLES={}
def ids(names):
    names=list(names);c=Counter(names);out=[f'{k} x{v}' if v>1 else k for k,v in c.items()]
    return ', '.join(out[:-1])+' and '+out[-1] if len(out)>1 else out[0]
def facet_ref(i):
    """Part ID on facet i (0-based), with the facet number when that part also fills other facets."""
    f=FACETS[i];return f['part']+(f' (facet {i+1})' if sum(g['part']==f['part'] for g in FACETS)>1 else '')
def ribs_on():
    """Facets the J01 ribs lie across, e.g. 'W02, W05, W07 and W11'."""
    mids=[facet_ref(s[1]) for s in DER['braces'] if len(s)==3]
    return ', '.join(mids[:-1])+' and '+mids[-1] if len(mids)>1 else mids[0]
def window_walls(level):
    pitch=CFG['floor_pitch']
    return ids(f['part'] for f in FACETS if any(level*pitch<=min(v[1] for v in c)<(level+1)*pitch for c in P[f['part']]['cuts']))
def spans(nums):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'."""
    out=[];nums=sorted(nums)
    for n in nums:
        if out and n==out[-1][1]+1:out[-1][1]=n
        else:out.append([n,n])
    return ', '.join(f'{a}-{b}' if b>a else str(a) for a,b in out)
def shell(group):return [f['part'] for f in FACETS if f['group']==group]

class Book:
    def __init__(self,name,section):
        self.path=OUT/name;self.c=canvas.Canvas(str(self.path),pagesize=A4,pageCompression=1);self.c.setTitle(f'{naming.NAME} | '+section);self.c.setAuthor(f'{naming.NAME} CAD workshop');self.section=section;self.n=0
        PAGE_TITLES[name]=[]
    def page(self,title,kicker='',background=False):
        c=self.c
        PAGE_TITLES[self.path.name].append({'title':title,'page':c.getPageNumber()})
        if background:c.setFillColor(colors.white);c.rect(0,0,W,H,fill=1,stroke=0)
        c.setFillColor(INK);size=min(23,23*(W-2*M)/max(c.stringWidth(title,'Helvetica-Bold',23),1));c.setFont('Helvetica-Bold',size);c.drawString(M,H-66,title)
        c.setFont('Helvetica',9);c.setFillColor(TEAL);c.drawString(M,H-87,kicker.upper())
        c.setStrokeColor(colors.HexColor('#D6DED4'));c.setLineWidth(.5);c.line(M,H-103,W-M,H-103)
    def end(self):
        self.n+=1;c=self.c;c.setFillColor(INK);c.setFont('Helvetica',7.5);c.drawString(M,24,f'{naming.NAME.upper()}  /  {self.section.upper()}');c.drawRightString(W-M,24,str(self.n));c.showPage()
    def save(self):self.c.save();return self.path

def para(c,text,x,y,width=W-2*M,size=10,leading=15,color=INK):
    c.setFillColor(color);c.setFont('Helvetica',size)
    for paragraph in text.split('\n'):
        lines=simpleSplit(paragraph,'Helvetica',size,width)
        for line in lines:c.drawString(x,y,line);y-=leading
        y-=5
    return y
def label(c,text,x,y,size=10):c.setFillColor(INK);c.setFont('Helvetica-Bold',size);c.drawString(x,y,text)
def table(c,rows,x,y,widths,headers=None,size=8.5):
    available=W-M-x
    if sum(widths)>available:
        widths=[v*available/sum(widths) for v in widths]
    allrows=([headers] if headers else [])+rows
    for k,row in enumerate(allrows):
        cells=[simpleSplit(str(v),'Helvetica-Bold' if k==0 and headers else 'Helvetica',size,widths[i]-12) for i,v in enumerate(row)]
        height=max(len(v) for v in cells)*12+13
        c.setStrokeColor(colors.HexColor('#BCC6BD'));c.setLineWidth(.4)
        c.line(x,y-height,x+sum(widths),y-height)
        xx=x
        for i,cell in enumerate(cells):
            c.setFillColor(INK);c.setFont('Helvetica-Bold' if k==0 and headers else 'Helvetica',size)
            for j,line in enumerate(cell):c.drawString(xx+6,y-14-j*12,line)
            xx+=widths[i]
        y-=height
    return y
def imagebox(c,name,x,y,w,h):
    path=ROOT/'output/previews'/f'{name}.png'
    if path.exists():c.drawImage(str(path),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
def arrow(c,a,b,color=TEAL,dashed=False,width=1):
    c.saveState();c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(width)
    if dashed:c.setDash(4,3)
    c.line(*a,*b);c.setDash();angle=math.atan2(b[1]-a[1],b[0]-a[0]);s=5
    path=c.beginPath();path.moveTo(*b)
    for off in (-.55,.55):path.lineTo(b[0]-s*math.cos(angle+off),b[1]-s*math.sin(angle+off))
    path.close();c.drawPath(path,fill=1,stroke=0);c.restoreState()
def dimension(c,a,b,text,offset=12,size=8):
    c.saveState();c.setStrokeColor(TEAL);c.setFillColor(TEAL);c.setLineWidth(.5)
    if abs(a[1]-b[1])<.01:
        y=a[1]+offset;c.line(a[0],a[1],a[0],y+3);c.line(b[0],b[1],b[0],y+3);c.line(a[0],y,b[0],y)
        for x in (a[0],b[0]):c.line(x-2,y-2,x+2,y+2)
        c.setFont('Helvetica',size);c.drawCentredString((a[0]+b[0])/2,y+4,text)
    else:
        x=a[0]+offset;c.line(a[0],a[1],x+3,a[1]);c.line(b[0],b[1],x+3,b[1]);c.line(x,a[1],x,b[1])
        for y in (a[1],b[1]):c.line(x-2,y-2,x+2,y+2)
        c.setFont('Helvetica',size);c.saveState();c.translate(x+5,(a[1]+b[1])/2);c.rotate(90);c.drawCentredString(0,0,text);c.restoreState()
    c.restoreState()
def scale_bar(c,x,y):
    """100 mm reference bar for 1:1 printouts; (x, y) is its left end in points."""
    c.saveState();c.setStrokeColor(colors.black);c.setFillColor(colors.black);c.setLineWidth(.5)
    c.line(x,y,x+100*mm,y)
    for k in range(11):
        tick=3*mm if k in (0,5,10) else 1.6*mm;c.line(x+k*10*mm,y,x+k*10*mm,y+tick)
    for k in range(10):
        if k%2==0:c.rect(x+k*10*mm,y-1.2*mm,10*mm,1.2*mm,fill=1,stroke=0)
    c.rect(x,y-1.2*mm,100*mm,1.2*mm,fill=0,stroke=1)
    c.setFont('Helvetica',5.5);c.drawString(x,y+3.6*mm,'100 mm reference / measure after printing')
    c.drawRightString(x+100*mm,y+3.6*mm,'10 cm');c.restoreState()
def scale_bar_top(c):
    # Between the A4 header lines and a template tile that starts 273 mm up the page.
    scale_bar(c,98*mm,276.5*mm)
def scale_bar_bottom(c):
    # Above the page footer on titled pages.
    scale_bar(c,W-M-100*mm,40)
def image_frame(name,x,y,w,h):
    """Map world points (mm) and screen coordinates of a preview drawn by imagebox() to page points."""
    meta=json.loads((ROOT/'output/previews'/f'{name}.json').read_text())
    iw,ih=meta['size'];k=min(w/iw,h/ih);x0=x+(w-iw*k)/2;y0=y+(h-ih*k)/2;cam=meta['camera'];cx,cy=meta['center'];sc=meta['scale']
    def screen(sx,sy):return x0+((sx-cx)*sc+iw/2)*k,y0+(sy-cy)*sc*k+ih/2*k
    def project(p):return screen(sum(cam[0][i]*p[i] for i in range(3)),sum(cam[1][i]*p[i] for i in range(3)))
    return project,screen,meta
def aligned_dimension(c,a,b,text,offset=12,size=7.5):
    """Dimension parallel to segment a-b, offset to its left by `offset` points."""
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);nx,ny=-dy/l*offset,dx/l*offset
    c.saveState();c.setStrokeColor(TEAL);c.setFillColor(TEAL);c.setLineWidth(.5)
    for p in (a,b):c.line(p[0],p[1],p[0]+nx*1.15,p[1]+ny*1.15)
    c.line(a[0]+nx,a[1]+ny,b[0]+nx,b[1]+ny)
    c.setFont('Helvetica',size);c.translate((a[0]+b[0])/2+nx*1.35,(a[1]+b[1])/2+ny*1.35);c.rotate(math.degrees(math.atan2(dy,dx)));c.drawCentredString(0,-size/3,text);c.restoreState()
def mini_table(c,rows,x,y,widths,headers,size=6.5,row=9.5):
    """Compact single-line table for packed reference pages; returns the y below it."""
    c.setStrokeColor(colors.HexColor('#BCC6BD'));c.setLineWidth(.3)
    for k,cells in enumerate([headers]+rows):
        xx=x;c.setFillColor(INK);c.setFont('Helvetica-Bold' if k==0 else 'Helvetica',size)
        for w,v in zip(widths,cells):c.drawString(xx+2,y-row+2.8,str(v));xx+=w
        y-=row;c.line(x,y,x+sum(widths),y)
    return y
def loop(c,points,fill=None,stroke=INK,width=.7):
    path=c.beginPath();path.moveTo(*points[0])
    for pt in points[1:]:path.lineTo(*pt)
    path.close();c.setStrokeColor(stroke);c.setLineWidth(width)
    if fill:c.setFillColor(fill)
    c.drawPath(path,fill=int(fill is not None),stroke=1)

USE={'Structure':'base, floors, posts','Walls':'walls, corner ribs','Exterior':'doors, trim, veranda','Roof':'roof, dormer','Tools':'test coupons','Furniture':'furniture','Accessories':'accessories'}
def stock_rows(sheets):
    """One row per stock size, with its use taken from the parts actually nested on those sheets."""
    groups={}
    for s in sheets:
        key=(s['thickness'],s['width'],s['height'],bool(s.get('existing_stock')),bool(s.get('laser')))
        groups.setdefault(key,[]).append(s)
    rows=[]
    for (t,sw,sh,existing,laser),group in sorted(groups.items(),key=lambda kv:(-kv[0][0],-kv[0][1]*kv[0][2])):
        uses=[]
        for s in group:
            for item in s['items']:
                use=USE.get(P[item['part']]['category'],P[item['part']]['category'].lower())
                if use not in uses:uses.append(use)
        rows.append([f'{t:g} mm',f'{sw:g} x {sh:g} mm',len(group),'Existing supply' if existing else f'Birch grade {CFG["supplier"].get("grade","2/2")} / laser',', '.join(uses).capitalize()])
    return rows
def hardware_rows():
    return assembly.content(DATA)['hardware']

def paint_page(b):
    c=b.c;b.page('Toy-safe paint (EN 71-3)','Primer, paint and clear finish for a toy for ages 3-5')
    y=para(c,'Every coating on the house must be declared by its maker to meet EN 71-3, the European toy-safety standard that limits how much of 19 elements, such as lead, cadmium and chromium, can leach from a toy that is sucked or swallowed (current edition EN 71-3:2019+A2:2024). It applies to the primer and the clear finish as much as to the colours. Look for "EN 71-3" on the tin or in the technical data sheet: "non-toxic", "eco" or the American "AP" seal is not the same thing. DIN 53160 (fast to saliva and sweat) is a useful extra.',M,715,size=10)
    rows=[['Water-based acrylic furniture paint (recommended)','All solid colours: blue walls, red roof, cream trim, green base. Dries in 1-2 hours with little smell; thin coats keep the moving gaps.','Tikkurila Helmi; Rust-Oleum Furniture & Toy Paint, or its Matt / Satin Furniture Paint (not Chalky Finish); Earthborn eggshell; Helios Tessarol acrylic enamel'],
      ['Water-based primer','First coat on bare plywood, so two thin colour coats cover.','Bondex Isolier- & Allgrund; Helios Tessarol wood primer'],
      ['Hardwax oil (oil and wax)','Floors and furniture where the wood grain should show. Not opaque.','Osmo Dekorwachs (Transparent or Intensive); Bondex Holzöl'],
      ['Water-based stain','See-through colour, for example on the veranda deck.','Auro Nr. 160 Holzlasur Aqua; Luxdecor water-based lakierobejca'],
      ['Clear finish','Over the paint and the paper decor once both have cured.','Adler Aqua-Cryl CFB (water-based acrylic varnish)'],
      ['Avoid','Solvent alkyd ("oil") enamel and spray paint: strong solvent, days to cure, thick films that jam hinges, doors and the drawer. Old tins of unknown make. Craft acrylics without an EN 71-3 statement.','-']]
    y=table(c,rows,M,y-14,[120,205,190],['Type','Use it for','Examples whose makers state EN 71-3'],8.5)
    para(c,'The examples are products whose makers or sellers state EN 71-3 conformity on their data sheets or product pages, checked in October 2026; none was tested for this book. Formulations and shades change, so check the current tin, or ask the maker for the test report, before you buy. Let every coat cure fully (see the tin; often 3-7 days) before children play with the house. Keep coats thin in the hinge, door and drawer gaps and recheck the movement after each coat.',M,y-20,size=9.5,leading=14)
    b.end()

def screw_section(c,x,y,diameter,length,head,wood,scale=7,title='SC1'):
    label(c,title,x,y+42,12);top=y
    # x is screw axis; wood list is measured depth below the head plane.
    cursor=top
    palette=[colors.HexColor('#B7CED7'),colors.HexColor('#E0C49C'),colors.HexColor('#C49A6B')]
    for j,(thick,name) in enumerate(wood):
        h=thick*scale;c.setFillColor(palette[min(j,2)]);c.setStrokeColor(colors.HexColor('#9A8268'));c.rect(x-45,cursor-h,90,h,fill=1,stroke=1)
        c.setFillColor(INK);c.setFont('Helvetica',7.5);c.drawString(x+52,cursor-h/2,name);cursor-=h
    c.setStrokeColor(TEAL);c.setLineWidth(1.2);r=diameter*scale/2
    # Outer borders, countersunk head and pointed shank.
    head_depth=(head-diameter)/2
    outline=[(x-head*scale/2,top),(x-r,top-head_depth*scale),(x-r,top-(length-2)*scale),(x,top-length*scale),(x+r,top-(length-2)*scale),(x+r,top-head_depth*scale),(x+head*scale/2,top)]
    loop(c,outline,stroke=TEAL,width=1.2)
    for t in range(2,int(length)-2):c.line(x-r,top-t*scale,x+r,top-(t+.7)*scale)
    arrow(c,(x,top+25),(x,top-length*scale-20),TEAL,True)
    dimension(c,(x-45,top),(x-45,top-length*scale),f'L {length:g} mm',offset=-16)
    dimension(c,(x-r,top-20),(x+r,top-20),f'D{diameter:g}',offset=10)

def inst_points(i):
    p=P[i['part']];o,u,v,w=i['origin'],i['u'],i['v'],i['w']
    return [[o[k]+u[k]*x+v[k]*y+w[k]*t for k in range(3)] for x,y in p['outer'] for t in (0,p['thickness'])]
def overall_page(b):
    """Complete plan: two dimensioned CAD views and the key dimensions."""
    c=b.c;D=CFG['base_diameter'];r=D/2;top=CFG['height']
    b.page('Overall dimensions',f'Complete plan / all dimensions in millimetres / finished height {top:g}')
    deck=next(i for i in DATA['instances'] if i['part']=='E03');apex=max(q[2] for i in DATA['instances'] if i['group']=='Porch' for q in inst_points(i))
    for name,x,caption in [('house-closed',M,f'Front: main entrance {DOORS["main"]} and the opening walls'),('house-closed-veranda',M+262,f'Veranda side: veranda on {VER["facet"]} and chimney')]:
        w=253;h=w*4/3;y=714-24-h
        imagebox(c,name,x,y,w,h);project,screen,meta=image_frame(name,x,y,w,h);cam=meta['camera']
        ex=cam[0];toward=[cam[2][0],cam[2][1],0];tl=math.hypot(*toward[:2]);toward=[t/tl for t in toward]
        left=screen(meta['lo'][0],0)[0]
        base_y,top_y=project([0,0,0])[1],project([0,0,top])[1]
        dimension(c,(left+4,base_y),(left+4,top_y),f'{top:g} overall',-10,7.5)
        if name=='house-closed':
            pl,pr,pf=project([-r*ex[0],-r*ex[1],0]),project([r*ex[0],r*ex[1],0]),project([r*toward[0],r*toward[1],0])
            dimension(c,pl,pr,f'D{D:g} round base',pf[1]-pl[1]-12,7.5)
        else:
            o,u,wv=deck['origin'],deck['u'],deck['w']
            a=project([o[k]+wv[k]*6 for k in range(3)]);bb=project([o[k]+u[k]*VER['width']+wv[k]*6 for k in range(3)])
            aligned_dimension(c,a,bb,f'Veranda {VER["width"]:g}',-12,7)
        c.setFillColor(INK);c.setFont('Helvetica',8);c.drawCentredString(x+w/2,y-14,caption)
    rows=book_rows(DATA,apex,ids(shell("WallRight")),ids(shell("WallLeft")))
    mini_table(c,rows,M,y-36,[90,425],['Item','Dimension'],8,15.5)
    b.end()

FIG_ORDER=('elias','mira','ada','theo')
def clay_colours():
    """Clay colours any figure uses, in palette order."""
    cl=DATA['clay'];return [k for k in next(iter(cl.values()))['grams_by_colour'] if any(f['grams_by_colour'][k]>=.05 for f in cl.values())]
def clay_rows():
    """Per figure: floor, size, volume and clay to buy by colour; then the total and blocks."""
    cl=DATA['clay'];cc=CFG['figures']['clay'];figs={f['key']:f for f in DER['figures']}
    g=lambda v:'-' if v<.05 else '<1' if v<1 else f'{v:.0f}'
    rows=[];total={k:0 for k in clay_colours()}
    for key in FIG_ORDER:
        if key not in figs:continue
        s=cl[key];f=figs[key]
        for k in total:total[k]+=s['grams_by_colour'][k]
        rows.append([s['name'],f['room'].split(',')[0],f'{s["height"]:.0f}x{s["length"]:.0f}x{s["width"]:.0f}',*[g(s['grams_by_colour'][k]) for k in total],f'{s["grams"]:.0f}',f'{s["grams_with_core"]:.0f}'])
    rows.append(['All figures','','',*[g(v) for v in total.values()],f'{sum(total.values()):.0f}',f'{sum(cl[k]["grams_with_core"] for k in figs):.0f}'])
    rows.append([f'Blocks of {cc["block"]:g} g','','',*[str(math.ceil(v/cc['block'])) if v>=.05 else '-' for v in total.values()],'',''])
    return rows

def lump_text(key):
    """'body egg 35 x 34, legs D11 x 21 (x2), ...' for one figure, white lumps first."""
    import clay
    def size(d):
        if len(d)==1:return f'D{d[0]:.0f}'
        if len(d)==2:return f'D{d[0]:.0f} x {d[1]:.0f}'
        return f'D{sum(d)/3:.0f}' if max(d)-min(d)<1.5 else ' x '.join(f'{v:.0f}' for v in d)
    parts={}
    for label,dims,colour,n in clay.lumps(key):parts.setdefault(colour,[]).append(f'{label} {size(dims)}'+(' (x2)' if n==2 else ''))
    return '; '.join(f'{colour}: '+', '.join(items) for colour,items in parts.items())

def clay_steps():
    return ('Weigh out the clay from pages 3-4 of the instructions and knead each colour soft. Roll the lumps listed there and press them together, biggest first: body or coat, '
            'head, then legs and feet, arms and hands. Smooth every join with a fingertip until it looks like one piece; keep arms and accessories pressed against the body, nothing thin '
            'sticking out. Scrunch a foil ball first and wrap the body clay round it.\nPress in the black eyes. Elias wears his cap and holds a small lantern, Mira wears her coat with a hair bun '
            'and shoulder satchel, Ada wears her jacket and scarf with hair braids, and Theo wears his sweater and beanie holding a small toy boat. Flatten the underside on a ceramic tile, bake it fully on the tile as the packet '
            'says, and seal it with a clear varnish declared to EN 71-3. Use a phthalate-free clay whose maker states EN 71 conformity. Drop each baked figure five times from 85 cm onto a '
            'hard floor; discard any that chips. Every figure is too big for the small-parts test cylinder.')

def figures_page(b):
    """The thermo-clay figures from four sides at 1:2, two per page; the clay table and lump lists follow."""
    figs={f['key']:f for f in DER['figures']};keys=[key for key in FIG_ORDER if key in figs]
    for first in range(0,len(keys),2):figure_views(b,keys[first:first+2],first+2>=len(keys))

def figure_views(b,keys,last):
    c=b.c;cl=DATA['clay'];cc=CFG['figures']['clay'];figs={f['key']:f for f in DER['figures']};k=.5   # drawn at 1:2
    b.page('The Rowan family in thermo-clay' if keys[0]==FIG_ORDER[0] else 'Clay figures / continued','Example views at 1:2 (half size) / clay estimated from the 3D volume')
    views=[('front','Front'),('side','Side'),('back','Back'),('three-quarter','Three-quarter')]
    meta={(key,v):json.loads((ROOT/'output/previews'/f'clay-{key}-{v}.json').read_text()) for key in keys for v,_ in views}
    cols=[max(meta[key,v]['width_mm'] for key in keys)*k*mm for v,_ in views];info=M+sum(cols)+14;y=722
    for key in keys:
        s=cl[key];f=figs[key];ground=y-max(meta[key,v]['ground_from_top_mm'] for v,_ in views)*k*mm;x=M
        for (v,caption),w in zip(views,cols):
            m=meta[key,v];iw,ih=m['width_mm']*k*mm,m['height_mm']*k*mm;top=ground+m['ground_from_top_mm']*k*mm
            c.drawImage(str(ROOT/'output/previews'/f'clay-{key}-{v}.png'),x+(w-iw)/2,top-ih,width=iw,height=ih,mask='auto')
            c.setFont('Helvetica',6.5);c.setFillColor(TEAL);c.drawCentredString(x+w/2,ground-12,caption);x+=w
        dimension(c,(M+4,ground),(M+4,ground+s['height']*k*mm),f'{s["height"]:.0f} tall',-2,6.5)
        colours=', '.join(f'{name} {v:.0f} g' if v>=1 else f'{name} <1 g' for name,v in s['grams_by_colour'].items() if v>=.05)
        ty=ground+s['height']*k*mm-4;label(c,s['name'],info,ty,10)
        para(c,f'{f["room"]}, X{f["x"]:.0f} Y{f["y"]:.0f} in the 3D plan.\n{s["height"]:.0f} tall, {s["length"]:.0f} long, {s["width"]:.0f} wide. Volume {s["volume_mm3"]/1000:.1f} cm3.\nClay to buy: about {s["grams"]:.0f} g ({colours}). With a foil core of about D{s["core_ball_mm"]:.0f}: about {s["grams_with_core"]:.0f} g.',info,ty-14,width=W-M-info,size=7.5,leading=9.5)
        y=ground-26
    if not last:
        b.end();return
    b.end();b.page('How much clay','All figures / grams to buy by colour / lumps to roll')
    y=714
    cols=clay_colours();widths=[78,62,64]+[34]*len(cols)+[38,46]
    y=mini_table(c,clay_rows(),M,y,widths,['Figure','Floor','HxLxW mm']+[k.capitalize() for k in cols]+['Total g','Foil core g'],6.8,12)
    note=(f'Grams = 3D volume x {cc["density"]:g} g/cm3 (a typical oven-hardening polymer clay such as FIMO; weigh a block of your brand and scale if it differs) plus {cc["allowance"]*100:.0f} % for handling. '
          f'The foil core is a ball of scrunched kitchen foil inside the body, keeping at least {cc["foil_wall"]:g} mm of clay all round: it saves clay and helps the thick body bake through. '
          'Bake as the packet says (FIMO: 110 degrees C, about 30 minutes; thick figures need longer). Each figure stands loose on its flat underside, with no stand; '
          'the CAD check confirms the walls and room doors open and close clear of every figure.')
    y=para(c,note,M,y-12,size=8,leading=11)
    label(c,'Lumps to roll',M,y-10,10)
    y=para(c,'Sizes in mm (D = diameter; three sizes = an egg, longest first). Press them together and smooth every join; the 3D views show the result.',M,y-24,size=8,leading=11)
    names={f['key']:f['name'] for f in DER['figures']}
    for key in [key for key in FIG_ORDER if key in figs]:
        c.setFont('Helvetica-Bold',8);c.setFillColor(INK);c.drawString(M,y-2,names[key])
        y=para(c,lump_text(key)+'.',M+70,y-2,width=W-2*M-70,size=8,leading=10.5)
    b.end()

def printables_page(b):
    """3D-printable interior parts (stove, chandelier, bathtub, table, chair): rendering, measurements, print specs."""
    c=b.c
    b.page('3D-printable interior accessories','Optional accessories / no supports needed / STL, 3MF & STEP in prints/')
    y=718
    intro=('Five optional accessories can be 3D printed for the interior. Every model is a single watertight solid '
           'designed with self-supporting geometry (no overhang exceeds 45 degrees from vertical), so all pieces print upright '
           'without slicer supports or brim. Sized to exceed the EN 71-1 small-parts cylinder (D31.7 x 57.1 mm) for child play. '
           'Recommended slicing: 0.4 mm nozzle, 0.20 mm layer height, 20 % infill, 2 perimeters, standard PLA.')
    y=para(c,intro,M,y,size=8.5,leading=11.5)

    manifest_path=ROOT/'prints/manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    parts_meta=manifest.get('parts',{})

    items=[
        ('stove','PR-01','Kakelugn tiled stove','Ground floor kitchen','Traditional cylindrical kakelugn with arched firebox door, waist shelf, and flared crown cornice.'),
        ('chandelier','PR-02','Hanging chandelier','Floor 1 living room (ceiling)','4 candle holders with tapered candles, central fluted stem, and diamond suspension eyelet.'),
        ('bathtub','PR-03','Clawfoot bathtub','Floor 2 bathroom','Clawfoot plinth with four cone feet, smooth flared tub shell, and plug hole. Sized for the Rowan family.'),
        ('table','PR-04','Round pedestal table','Ground floor dining room','Single flared 45-degree conical pedestal column, wide stable foot, and rounded top edge.'),
        ('chair','PR-05','Dining chairs (x2)','Ground floor dining room','Arched backrest and 45-degree tunnel seat arches for 100 % support-free printing.'),
    ]

    top_w=(W-2*M-16)/2
    card_y=y-10
    card_h=135
    for idx,key in enumerate(['stove','chandelier']):
        it=next(item for item in items if item[0]==key)
        cx=M+idx*(top_w+16)
        c.setFillColor(colors.HexColor('#F8F9F8'));c.setStrokeColor(LINE);c.roundRect(cx,card_y-card_h,top_w,card_h,4,fill=1,stroke=1)
        img_p=ROOT/'output/previews'/f'print-{key}.png'
        if img_p.exists():
            c.drawImage(str(img_p),cx+6,card_y-card_h+8,width=100,height=card_h-16,preserveAspectRatio=True,anchor='c',mask='auto')
        info_x=cx+112;info_w=top_w-118;ty=card_y-16
        label(c,f'{it[1]}  {it[2]}',info_x,ty,9.5)
        meta=parts_meta.get(key,{})
        sz=meta.get('size',[0,0,0])
        wt=meta.get('grams',{}).get('estimate',0)
        c.setFont('Helvetica',7.5);c.setFillColor(TEAL)
        c.drawString(info_x,ty-13,f'Room: {it[3]}')
        c.drawString(info_x,ty-24,f'Size: {sz[0]:.0f} x {sz[1]:.0f} x {sz[2]:.0f} mm  |  Weight: ~{wt:.0f} g PLA')
        c.drawString(info_x,ty-35,f'Files: prints/{key}.stl / .3mf / .step')
        para(c,it[4],info_x,ty-48,width=info_w,size=7.2,leading=9.5,color=INK)

    bot_y=card_y-card_h-12
    bot_w=(W-2*M-20)/3
    bot_h=135
    for idx,key in enumerate(['bathtub','table','chair']):
        it=next(item for item in items if item[0]==key)
        cx=M+idx*(bot_w+10)
        c.setFillColor(colors.HexColor('#F8F9F8'));c.setStrokeColor(LINE);c.roundRect(cx,bot_y-bot_h,bot_w,bot_h,4,fill=1,stroke=1)
        img_p=ROOT/'output/previews'/f'print-{key}.png'
        if img_p.exists():
            c.drawImage(str(img_p),cx+(bot_w-72)/2,bot_y-68,width=72,height=60,preserveAspectRatio=True,anchor='c',mask='auto')
        ty=bot_y-78
        label(c,f'{it[1]} {it[2]}',cx+6,ty,8.5)
        meta=parts_meta.get(key,{})
        sz=meta.get('size',[0,0,0])
        wt=meta.get('grams',{}).get('estimate',0)
        c.setFont('Helvetica',7);c.setFillColor(TEAL)
        c.drawString(cx+6,ty-11,f'{sz[0]:.0f} x {sz[1]:.0f} x {sz[2]:.0f} mm  |  ~{wt:.0f} g PLA')
        c.drawString(cx+6,ty-21,f'{it[3]}')
        para(c,it[4],cx+6,ty-31,width=bot_w-12,size=6.8,leading=8.5,color=INK)

    tbl_y=bot_y-bot_h-14
    rows=[]
    for it in items:
        meta=parts_meta.get(it[0],{})
        sz=meta.get('size',[0,0,0])
        wt=meta.get('grams',{}).get('estimate',0)
        rows.append([it[1],it[2],it[3],f'{sz[0]:.0f} x {sz[1]:.0f} x {sz[2]:.0f}',f'{wt:.0f} g',f'prints/{it[0]}.stl'])
    table(c,rows,M,tbl_y,[44,115,145,80,45,86],['Part ID','Part Name','House Placement','Size (W x D x H mm)','PLA','Mesh file'],7.5)

    b.end()

def strip_rows():
    """No-laser option: 3 mm parts that are plain rectangles a few mm wide can be cut from bought strip wood."""
    groups={}
    for pid,p in MAIN.items():
        if p['thickness']!=3 or p['cuts'] or p['holes'] or len(p['outer'])!=4:continue
        w,h=sorted((p['width'],p['height']))
        if w>10:continue
        key=f'{3:g} x {w:g} mm'
        groups.setdefault(key,[]).append((pid,h,p['quantity']))
    rows=[]
    for key,items in sorted(groups.items()):
        total=sum(h*n for _,h,n in items)
        rows.append([key,', '.join(f'{pid} {n} x {h:.0f}' for pid,h,n in items),f'{total/1000*1.15:.1f} m'])
    WN=CFG['windows'];fb,sb=WN['frame'],WN['sill'];band,rise=WN['hood'];wins=sum(DER['windows_per_floor'][:3])
    rows.append([f'3 x {fb+.4:.0f} mm','WF1 surround as a mitred frame (two of each per window) plus the cross: '+f'{WN["width"]+2*fb:.0f} and {WN["height"]+2*fb:.0f} mm; cross bars {WN["width"]:.0f} and {WN["height"]:.0f} mm',f'{wins*2*(WN["width"]+WN["height"]+4*fb+ (WN["width"]+WN["height"])/2)/1000*1.15:.1f} m'])
    return rows

def dry_fit_rows():
    """Physical checks the CAD cannot make: done before glue and before the toy is given to a child."""
    MG=CFG['magnets'];tol=CFG['thickness_tolerance']
    return [['Plywood thickness','Measure every sheet at four edges. Each must be inside its band: '+', '.join(f'{t} mm {t_[0]:+g}/{t_[1]:+g}' for t,t_ in tol.items())+'. Outside it: update config thickness or the band, rebuild (make all).'],
      ['Floors and stack-up','Dry-fit the three pieces of F00, F01 and F02: puzzle and finger joints close by hand, the floors sit level on the pillars and their metal supports, every divider fits its storey with a little play (stack-up report).'],
      ['Cantilever press test','Walls open: press 40 N (4 kg) on the front edge of each floor. No crack, no sag you can see.'],
      ['F00 over the drawer bay','Press on the ground floor above the drawer: the drawer must still slide.'],
      ['Stop posts','Open each shell hard against its GP1 post (felt dot on the face). The post must not rock; recheck the dowels and the SC3 screw.'],
      ['Tip test','Both walls open, roof on: push sideways at the eave with 35 N (3.5 kg on a luggage scale). The house must not lift off any rim pad. Fit the anti-tip strap when it stands on the floor.'],
      ['Magnets',f'Every magnet is behind {MG["skin"]:g} mm of wood with a glued plug: none visible, none reachable. Pull each catch block and post with pliers after the epoxy cures: nothing moves.'],
      ['Small parts','Pull every glued trim piece, step and baluster with 90 N (9 kg) after the glue cures. Re-glue anything that moves; remove anything that breaks.'],
      ['Edges and finish','Round every exposed edge (R1 or more), no splinters, all paint and varnish cured (see the tin, often 3-7 days).'],
      ['Clay figures',f'Weigh a block of your clay and set figures.clay.density if it is not {CFG["figures"]["clay"]["density"]:g} g/cm3. Bake fully, drop each figure five times from 85 cm onto a hard floor: discard any that chips.']]

def manual():
    import steps as steplib
    b=Book(naming.PDF_INSTRUCTIONS,'Instructions');c=b.c
    c.drawImage(str(ROOT/'output/previews/cover.png'),0,0,width=W,height=H)
    c.setFillColor(INK);c.rect(0,0,W,65,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica-Bold',11);c.drawCentredString(W/2,39,f'{CFG["height"]:g} mm tall  /  Three floors + attic  /  Round D{CFG["base_diameter"]:g} base');c.setFont('Helvetica',9);c.drawCentredString(W/2,21,'Real CAD  -  Jigsaw templates  -  Illustrated assembly');b.n=1;c.showPage()
    overall_page(b);figures_page(b);printables_page(b)
    rows=hardware_rows()
    b.page('Buy the hardware first','Exact installed quantities + sensible spare packs')
    para(c,'Every fastener has a drawing code. D means diameter. Countersunk screw length includes the head. Pan-head bolt length starts below the head. Wood screws bite into timber through a pilot hole. M3 bolts need matching nuts.',M,715,size=10)
    y=table(c,rows[:6],M,638,[42,255,43,45,130],['Code','Type / example search wording','Used','Buy','Placement'],8)
    para(c,f'Example shop searches: "wood screw 2.5 x {SC1["length"]:g} countersunk"; "small butt hinge 25 mm"; "M3 x 30 pan head screw". Select a matching driver bit and countersunk hinge holes. Hinge footprints vary: compare your actual hardware with the printed checking page before drilling.',M,y-23,size=9,leading=14)
    b.end()
    b.page('Packing, magnets and supplies','Hardware and finishing materials')
    y=table(c,rows[6:14],M,716,[42,255,43,45,130],['Code','Specification','Used','Buy','Placement'],8)
    para(c,'Also buy: about 500 ml PVA wood glue; about 5 m of 15-20 mm cotton seam tape; removable paper-template adhesive; slow-setting 2-part epoxy for the magnets, plugs and steel discs; clear craft glue for the PET; and primer, water-based paints and a clear finish that are all declared to EN 71-3 (two pages on).',M,y-26,size=10)
    b.end()
    b.page('Dowels, glazing and safety kit','Bought items that make the house safer to play with')
    y=table(c,rows[14:],M,716,[42,255,43,45,130],['Code','Specification','Used','Buy','Placement'],8)
    para(c,f'Solid wood: A02 hinge blocks (8 x 16 mm hardwood strip), A03 door strips (8 x {CFG["door_hinge"]["backing_width"]:g} mm), A04 foot blocks, R04 roof cleats, MC1 catch blocks and AB1 anchor (12 mm hardwood board), GP1 stop posts (20 x 20 mm hardwood strip), DS1 and the plugs (dowel rod) and the FN01 ball. Exact cut quantities and lengths are in the part inventory.',M,y-20,size=10)
    b.end()
    paint_page(b)
    b.page('Read a screw drawing','Outer borders and the axis through the wood')
    sd,sl=CFG['door_hinge']['screw']
    wh_,wall_=CFG['wall_hinge'],CFG['thickness']['wall']
    screw_section(c,145,650,SC1['diameter'],SC1['length'],SC1['head_diameter'],[(wh_['leaf_thickness'],f'Hinge leaf: {wh_["leaf_thickness"]:g}'),(wh_['packing_thickness'],f'A06 shim: {wh_["packing_thickness"]:g}'),(wall_,f'Wall: {wall_:g}'),(8,'A02 hardwood: 8')],6.5,f'SC1 / {Counter(f["type"] for f in DATA["fasteners"])["SC1"]} screws')
    screw_section(c,145,470,sd,sl,2*sd,[(.8,'Door hinge: 0.8'),(4,'Door: 4'),(8,'A03 hardwood: 8')],7,f'SC2 / {Counter(f["type"] for f in DATA["fasteners"])["SC2"]} screws')
    screw_section(c,145,300,3,16,6,[(6,'F00 plate: 6'),(12,'Foot block: 12')],6,'SC3 / 4 foot-block screws')
    screw_section(c,400,300,3,16,6,[(6,'B01 base: 6'),(14,'GP1 post end grain')],6,'SC3 / 2 stop-post screws')
    para(c,'Blue outlines show the complete fastener; the dashed arrow is its drilling and insertion axis. Nominal mm, enlarged; not cutting templates. The stop-post screw goes into end grain, which holds only about half as well: the two D4 dowels beside it take the side load and the glue holds the foot. Tighten by hand after pilot drilling; stop when the head seats.',M,140,size=9,leading=13)
    b.end()
    if BL1:
        b.page('Build the captive roof pivots','BL1 x 2 / actual section / no exposed thread')
        x=190;y=690;s_=7.2
        st=BL1['stack_mm'];packing=sum(st[8:])
        stack=[(st[0],'WS1 steel washer / under head'),(st[1],'F02 attic floor'),(st[2],'SP1 nylon spacer'),(st[3],'WS3 D12 fender washer'),(st[4],f'E08 turn-button ply, {st[4]:g} mm'),(st[5],f'E09 ply glued on top, {st[5]:g} mm'),(st[6],'WS3 D12 fender washer'),(st[7],'WS2 nylon washer'),(packing,f'WS1 steel washer{"s" if WS1>2 else ""} x{WS1-1}; {packing:g} mm')]
        cursor=y;previous_label=y+20
        for j,(thick,text) in enumerate(stack):
            h=thick*s_;c.setFillColor(colors.HexColor('#DCC19D') if j in (1,4,5) else colors.HexColor('#DCE8E8'));c.setStrokeColor(INK);c.rect(x-40,cursor-h,80,h,fill=1,stroke=1)
            center=cursor-h/2;ly=min(center,previous_label-15);previous_label=ly
            c.setStrokeColor(TEAL);c.setLineWidth(.4);c.line(x+40,center,x+52,ly);label(c,text,x+56,ly-3,9);cursor-=h
        c.setFillColor(colors.HexColor('#B9C7C6'));c.setStrokeColor(INK);c.roundRect(x-24,cursor-6*s_,48,6*s_,10,fill=1,stroke=1);label(c,'NT1 cap nut',x+56,min(cursor-20,previous_label-17),9)
        c.setStrokeColor(TEAL);c.setLineWidth(1.1);c.rect(x-3*s_/2,y-30*s_,3*s_,30*s_,fill=0,stroke=1);c.rect(x-3*s_,y,6*s_,2*s_,fill=0,stroke=1)
        arrow(c,(x,y+35),(x,y-30*s_-25),TEAL,True);dimension(c,(x-55,y),(x-55,y-30*s_),'30 mm below head',-15)
        para(c,f'Stack {sum(st):g} mm, so {BL1["length"]-sum(st):g} mm of thread is left for the cap nut. Check that its cavity is at least 3.8 mm deep and that it seats on the washer, not on the screw tip.',M,355,size=10)
        para(c,f'Set light pivot friction, then lock the cap nut with permanent threadlocker: the washers and nut can then never come loose as small parts. Do not glue the moving tab. Roof ring top is Z{EAVE+6:g}; tab underside is Z{EAVE+9:g}: a 3 mm retaining gap. The {LOCK:g} mm tab is a {st[4]:g} mm E08 ply and a {st[5]:g} mm E09 ply glued face to face (line the holes up with an M3 screw while the glue sets), with a 22 mm neck round the pivot and a fender washer on each face. A single 3 mm tab broke when the house was lifted by its roof, and a single 6 mm tab falls short of the safety margin.',M,300,size=10)
        para(c,'Locked: tab points outward and overlaps the roof ring. Unlocked: rotate each tab 90 degrees toward the center, then lift the roof vertically. The tapered tip keeps the turned tab inside the ring.',M,200,size=10)
        b.end()
    b.page('Joints used in this house','Orange marks identify glue joints in the diagrams')
    joint_rows=[['J1','Supported edge-to-face butt joint','Floor rests on its supports and posts. Glue both support faces; do not depend on a thin plywood edge alone.'],['J2','150-degree faceted corner + ribs','Adjacent square-edged panels meet with a small seam. A flat J01 rib glues along three inner wall faces and holds two corners at once; outside, a batten covers the seam. One leftover fixed-shell corner stays open.'],['J3','Reinforced screwed hinge joint','Glue hardwood backing first, let it cure, then drill pilots through the hinge leaf and wall into the backing.']]
    if BL1:joint_rows.append(['J4','Captive machine-screw pivot','BL1 passes through F02, washers, spacer and E08; NT1 covers its threaded end.'])
    joint_rows.append([f'J{len(joint_rows)+1}','Glued trim and veranda joint','Dry-fit trim, headers and rails on a flat board. Apply thin PVA over the whole face, clamp gently and wipe squeeze-out.'])
    y=table(c,joint_rows,M,714,[35,175,305],['Code','Joint','How it works'],9)
    y=para(c,'Clamping hints: use scrap pads to avoid dents; check square with a small square; keep all pieces flat until the glue cures. Painted or paper-covered surfaces must not lie inside structural glue joints.',M,y-25,size=10)
    cx=180;cy=y-110;r=90
    a=(cx+r,cy);d=(cx+r*math.cos(math.radians(150)),cy+r*math.sin(math.radians(150)))
    c.setStrokeColor(INK);c.setLineWidth(8);c.line(cx,cy,*a);c.line(cx,cy,*d)
    loop(c,[(cx+15,cy+4),(cx+52,cy+4),(cx-38,cy+27)],colors.HexColor('#B8C9B5'),RUST,1)
    arrow(c,(cx+43,cy-28),(cx+43,cy+22),RUST,True);arrow(c,(cx-48,cy+60),(cx-25,cy+17),RUST,True)
    label(c,'150 degrees',cx+12,cy+56,10);label(c,f'J01 rib / {P["J01"]["thickness"]:g} mm',cx+140,cy+5,10);b.end()
    b.page('Plywood and parts','Measured thickness comes before cutting')
    rows=stock_rows(NEST['sheets'])
    y=table(c,rows,M,714,[55,105,50,145,160],['Ply','Sheet size','Qty','Existing supply','Use'],9)
    y=para(c,f'All cutting stock is A3, 297 x 420 mm, grouped by thickness: 3 and 6 mm only. Fixed walls use the full 420 mm blank length (factory end edges: check they are square), opening walls are 418 mm. Long strips get what is left of the 10 mm end margins. Confirm workholding and cutters with the company. Inspect actual sheet thickness and flatness.',M,y-24,size=10)
    para(c,'Measure thickness at several edges. Cut T01/T02 and check the printed 100 mm length, blade entry, and joint fits. If stock differs materially, update source/config.json and regenerate the CAD and book. Sand to a supported glue fit; do not force slots or rely on friction alone.',M,y-8,size=10)
    imagebox(c,'house-open',M,58,W-2*M,300);b.end()
    b.page('Print, join and glue templates','Print actual size / 100% / A4 / single-sided')
    para(c,'1. Print the calibration page first. Turn off Fit, Shrink, Scale to page and borderless enlargement. Measure the 100 mm square in both directions. Do not cut structural parts if either dimension differs by more than 0.5 mm.\n2. Join each individual part template using its row/column labels. Trim only the RIGHT and TOP overlap edges where needed. Overlap matching crosshairs by 10 mm; match long profile lines across seams.\n3. Tape joins on the back. Glue the completed part template to the correct plywood thickness using removable adhesive. Mark the part ID and keep the cutting-order page nearby.\n4. Use the cutting templates, not the small reference drawings. Decorations go onto finished wood later.',M,712,size=11,leading=17)
    label(c,'Line legend',M,391,12)
    c.setStrokeColor(INK);c.line(M,365,M+90,365);label(c,'Black: final cut boundary',M+112,361,10)
    c.setStrokeColor(RUST);c.circle(M+45,331,8);c.line(M+34,331,M+56,331);c.line(M+45,320,M+45,342);label(c,'H: finished or pilot hole',M+112,327,10)
    c.setStrokeColor(TEAL);c.setDash(3,2);c.circle(M+45,292,9);c.setDash();label(c,'S: temporary hole in waste',M+112,288,10)
    arrow(c,(M,252),(M+90,252),TEAL,True);label(c,'Dashed blue: fastener / drill axis',M+112,248,10)
    c.setStrokeColor(RUST);c.rect(M,202,90,15,fill=0,stroke=1);label(c,'Orange: glue or supported joint',M+112,205,10)
    b.end()
    b.page('Cut an inside opening','Starter holes keep the blade inside waste')
    outer=[(85,425),(355,425),(355,655),(85,655)];inner=[(145,465),(305,465),(305,615),(145,615)]
    loop(c,outer,colors.HexColor('#E6CBA2'));loop(c,inner,colors.white)
    c.setStrokeColor(TEAL);c.setDash(3,2);c.circle(178,498,17);c.setDash();arrow(c,(178,498),(158,476));arrow(c,(158,476),(289,476));arrow(c,(289,476),(289,601));label(c,'S01 / D10 / in waste',M,692,11)
    dimension(c,(145,465),(305,465),'Finished opening width',-22);dimension(c,(305,465),(305,615),'Finished height',22)
    para(c,'Clamp the sheet with sacrificial wood underneath. Drill the indicated S hole, disconnect the saw while inserting its blade, then bring the blade to the waste side of the cut line. Follow the arrows and cut straight sides in stages. Keep the saw shoe supported. Each window has four panes: leave the cross between them standing.',M,358,size=11,leading=17)
    para(c,'A starter hole is not a finished feature. Its whole circumference stays in waste. Use the T01 test to confirm your blade fits D10. For a narrow opening, use the smaller specified drill and finish with a precise file. Drill relief holes only inside waste; do not overrun a corner into finished wood.',M,232,size=10)
    para(c,'For clean edges, use a fine wood blade, modest feed pressure and a supported backer. Test orbital action and cut-face splintering on scrap. Leave about 0.5 mm on the waste side for filing, then finish to the line. Use eye protection and follow your saw manual.',M,141,size=10)
    b.end()
    b.page('Cutting order and useful offcuts','Keep the work clamped until the last exterior cut')
    para(c,'For sheets you cut yourself:\n1. Drill finished holes and pilots using a depth stop for blind holes. Confirm the entry face: TOP or UNDERSIDE.\n2. Drill S holes and cut enclosed openings while the surrounding sheet is intact.\n3. Break the sheet into manageable groups through the blank lanes.\n4. Cut large exterior contours first, then small parts. Retain temporary bridges or extra surrounding stock until each part can be clamped safely.\n5. File to size, round exposed edges, remove template paper and label the back of each part.',M,714,size=11,leading=17)
    para(c,f'The laser layout reserves {CFG["nest_spacing"]:g} mm between independent contours and {CFG["stock_margin"]:g} mm at sheet sides. All sheets use grade {CFG["supplier"].get("grade","2/2")} birch plywood. Router or jigsaw cutting requires wider lanes and a new layout. Long parts retain the end allowances shown on their reference maps.',M,378,size=10)
    para(c,'Save window rectangles, roof-ring centers and large corner offcuts. They can become clamping pads, painting samples, future miniature decorations or spare parts. Clamp tiny blanks to a larger sacrificial carrier; never hold a small loose piece beside a moving blade.',M,273,size=10)
    para(c,f'Both plywood thicknesses have A3 laser layouts. Use the individual A4 cutting templates for DIY work; large parts take two pages. For laser cutting, send {naming.PDF_SUPPLIER} and {naming.SUPPLIER_CUT_DXF}. Drill blind features separately. Read docs/SUPPLIER-READINESS.md first. No engraving is requested.',M,154,size=10)
    b.end()
    b.page('No laser? Bought strip wood for the 3 mm trim','Cut to length with a knife and a mitre box')
    y=para(c,'Every thin 3 mm part that is a plain strip can be cut from bought basswood or birch strip instead of the 3 mm sheets. Lengths below are finished sizes; the totals include 15 % for waste. The window surround can be made the same way as a mitred frame with its cross, glued straight onto the wall\'s own solid cross.',M,712,size=10,leading=14)
    table(c,strip_rows(),M,y-10,[80,330,70],['Strip','Parts and lengths','Buy'],8.5)
    b.end()
    b.page('Inspect supplied parts','For parts supplied by a cutting company')
    para(c,'Compare the supplied parts with the supplier inventory and reference maps. Inspect the narrow strips and battens, check the pivot holes and the depth of every pocket before assembly. Sort the supplied house parts by their shared build IDs.',M,710,size=11,leading=17)
    para(c,'Skip cutting, starter-hole drilling and waste-side filing for finished supplied parts. Drill by hand any underside or small pilot holes the supplier left out (the supplier index lists them). Remove loose residue, round exposed edges and lightly clean mating edges before gluing. Dry-fit the finger and puzzle joints first: they have a 0.1 mm gap per side and rounded or relieved corners.',M,553,size=11,leading=17)
    para(c,'The supplier specification awaits confirmation of the actual 3 and 6 mm plywood, cutting tolerances, cutters, hold-down and two-sided machining. Keep textures in the decor PDF and apply them after assembly. Furniture appears only in the 3D view and uses no supplied plywood.',M,365,size=11,leading=17)
    b.end()
    b.page('Dry-fit and safety checks','Physical checks before glue-up and before a child plays')
    y=table(c,dry_fit_rows(),M,714,[120,395],['Check','How'],8.5)
    para(c,'The CAD proves clearances, not strength or durability. Keep this page and repeat the magnet, small-part and tip checks every few months of play.',M,y-14,size=9.5,leading=13)
    b.end()
    b.page('Redesign from your photos',f'Veranda on {VER["facet"]} / dormers over {" and ".join(CFG["dormer"]["over"])} / round base')
    imagebox(c,'house-closed-veranda',M,284,W-2*M,430)
    wpf=DER['windows_per_floor'];dmr=CFG['dormer']
    para(c,f'Your uploaded photos define the exterior arrangement. The red hipped veranda sits on the fixed facet {VER["facet"]}, so it stays in place while the front walls open. Shaped white columns, a front railing and an angled side railing surround it; side steps lead onto its deck. A rope ladder runs from its roof up to the eave beside the dormer over {dmr["over"][0]}, next to the chimney. A red gabled canopy covers the main entrance on {DOORS["main"]}, and a second dormer sits on the opposite side of the roof above it.',M,244,size=10)
    para(c,f'Windows: {wpf[0]} on the ground floor, {wpf[1]} on the middle floor, {wpf[2]} on the bedroom floor, and {wpf[3]} attic dormers. The house stands on a round D{CFG["base_diameter"]:g} landscaped base, with a back door, a woodpile and a faux cellar hatch round the plinth.',M,133,size=10)
    b.end()
    b.page('Wall map and rib heights','Plan view / front is at the bottom / dimensions in mm')
    s=.8;cx=W/2;cy=470
    deck=next(i for i in DATA['instances'] if i['part']=='E03')
    loop(c,[(cx+s*(deck['origin'][0]+deck['u'][0]*x+deck['v'][0]*y),cy+s*(deck['origin'][1]+deck['u'][1]*x+deck['v'][1]*y)) for x,y in P['E03']['outer']],colors.HexColor('#E8C9A6'),RUST)
    label(c,'Veranda',cx+s*(deck['origin'][0]+deck['u'][0]*VER['width']/2-deck['v'][0]*18)-20,cy+s*(deck['origin'][1]+deck['u'][1]*VER['width']/2-deck['v'][1]*18),9)
    for i in range(12):
        theta=math.radians(-75+i*30);n=(math.cos(theta),math.sin(theta));u=(-n[1],n[0]);a=175*math.cos(math.pi/12);half=DATA['derived']['wall_width']/2
        aa=(cx+s*(n[0]*a-u[0]*half),cy+s*(n[1]*a-u[1]*half));bb=(cx+s*(n[0]*a+u[0]*half),cy+s*(n[1]*a+u[1]*half))
        c.setStrokeColor(colors.HexColor('#4A94BC'));c.setLineWidth(6);c.line(*aa,*bb);label(c,FACETS[i]['part'],cx+n[0]*202*s-10,cy+n[1]*202*s-3,8)
        c.setFillColor(colors.HexColor('#8A9A91'));c.setFont('Helvetica',6);c.drawCentredString(cx+n[0]*150*s,cy+n[1]*150*s-2,str(i+1))
        if P[FACETS[i]['part']].get('windows'):c.setFillColor(colors.HexColor('#FFF3DB'));c.circle(cx+n[0]*a*s,cy+n[1]*a*s,5,fill=1,stroke=0)
    label(c,'Fixed rear shell',cx-45,cy+60,10);label(c,'Opening left',cx-105,cy-45,10);label(c,'Opening right',cx+35,cy-45,10)
    para(c,f'{DOORS["veranda"]} is the veranda door, {DOORS["main"]} the main entrance and {DOORS["back"]} the back door; all three are ground-floor notches. Ground-floor windows: {window_walls(0)}. Upper windows: {window_walls(1)}. The veranda deck is glued to B01 and against {facet_ref((VER_FACET-1)%12)}, {facet_ref(VER_FACET)} and {facet_ref((VER_FACET+1)%12)}. Small grey numbers are the facet numbers; identical walls share one ID.',M,239,size=10)
    reach=DER['brace_reach'];depth=DER['brace_depth']
    band=', '.join(f'{z:.1f}' for z in GUSSETS)
    para(c,f'J01 ribs only (no two-wall brackets): two bands per storey at {band} mm above each floor top — low below the windows, and high just under the floor above (under F01B on the ground floor). Each {P["J01"]["thickness"]:g} mm rib lies across a whole facet and reaches about {reach-.5:.0f} mm (~75 %) onto both neighbours, only {depth:.0f} mm into the room; they lie across {ribs_on()}. One fixed-shell corner stays open. Beside the doors the ground-floor low braces sit at Z{G0+96*CFG["wall_height"]/450:g}, just above the door openings, with short legs that clear the windows when a raised rib would not cross a window middle; there are none at the front seam and the hinge corners. Opening-shell braces sit {CFG["shell_lift"]:g} mm higher, like their walls. Dividers are plain PT1 panels with no rear rib notches.',M,146,size=10)
    b.end()
    b.page('Frame placement coordinates','Plan view / house center is X0, Y0 / front is -Y')
    cx=W/2;cy=505;s=.78
    def plan(x,y):return cx+x*s,cy+y*s
    c.setStrokeColor(colors.HexColor('#ACB9AB'));c.setLineWidth(.7);c.circle(cx,cy,CFG['base_diameter']/2*s,fill=0,stroke=1)
    floor=P['F01'];r=DATA['derived']['floor_radius']
    outline=DER['panels']['F01']['outline'];loop(c,[plan(x-r,y-r) for x,y in outline],stroke=INK)
    feet=[i for i in DATA['instances'] if i['part']=='A04'];posts=[i for i in DATA['instances'] if i['part']=='P01']
    for i in feet+posts:
        x,y,z=i['origin'];w=P[i['part']]['width'];d=24 if i['part']=='A04' else PT
        if i['part']=='P01':y-=PT
        loop(c,[plan(x,y),plan(x+w,y),plan(x+w,y+d),plan(x,y+d)],colors.HexColor('#E8C9A6') if i['part']=='A04' else colors.HexColor('#7C9B84'),RUST)
        if i['part']=='P01':label(c,i['part'],*plan(x-13,y-14),size=7)
    wx,wy=CFG['lighting']['at'];c.setStrokeColor(TEAL);c.circle(*plan(wx,wy),CFG['lighting']['wire_hole']/2*s+1);label(c,'LED wire',*plan(wx-14,wy+6),size=6)
    arrow(c,plan(0,0),plan(50,0),TEAL);arrow(c,plan(0,0),plan(0,50),TEAL);label(c,'X',*plan(56,0),size=8);label(c,'Y',*plan(0,55),size=8)
    rows=[[str(k+1),f'{f["origin"][0]:.0f}, {f["origin"][1]:.0f}',f'{p_["origin"][0]:.0f}, {p_["origin"][1]-PT:.0f}'] for k,(f,p_) in enumerate(zip(feet,posts))]
    y=table(c,rows,M,284,[45,235,235],['Pair','A04 left/front corner X,Y','Post left/front corner X,Y'],9)
    para(c,f'Feet: 24 x24 x12, screwed to F00 from below, bottom Z{G0:g}. P01 pillars: {DER["pillars"]["width"]:g} x{PT:g} footprint, {DER["pillars"]["length"]:g} long, bottom Z{G0+12:g}, top Z{TOPS[3]-6:g}. Both F01 levels have four matching through-openings. No floor ledges are cut: support both F01 levels and F02 on small metal angle brackets fitted after production, with their tops at the floor undersides {zl([t-6 for t in TOPS[1:]])}. The optional LED wire passes up through D{CFG["lighting"]["wire_hole"]:g} holes behind the left rear pillar.',M,y-18,size=9,leading=13)
    b.end()
    dmr=CFG['dormer']
    texts=assembly.content(DATA)['chapters']
    assert set(texts)==set(steplib.KEYS),set(texts)^set(steplib.KEYS)
    per,_,_=steplib.assign(DATA)
    for index,key in enumerate(steplib.KEYS,1):
        title,img,text,hint=texts[key];number=f'{index:02}'
        b.page(title,'Assembly step '+number);imagebox(c,img,M,289,W-2*M,422)
        y=para(c,text,M,262,size=10.5,leading=15)
        y=para(c,hint,M,y-6,size=9.5,leading=13,color=TEAL)
        if per[key]:para(c,'Parts: '+steplib.listing(per[key]),M,y-4,size=8,leading=11)
        b.end()
    b.page('Roof ring and cleats from below','R02 (3 mm) + R04 x12 / cone bearing faces / retaining gap')
    imagebox(c,'roof-underside',M,280,W-2*M,431)
    para(c,f'R02 ring: underside Z{EAVE:g}, thickness 3, outer vertex radius {182*CFG["wall_height"]/450:g}. Three 120-degree sections (R02, R02B, R02C), centered on the cone. R04 cleats start at radial {170*CFG["wall_height"]/450:g}, bottom Z{EAVE+3:g}. Place one cleat in the center of each cone facet. Glue its level bottom to the ring and its slope to the roof skin. The dormer openings stop {dmr["cleat_clearance"]:g} mm short of their cleats.',M,244,size=10,leading=15)
    para(c,f'Use R05 angle gauges to hold the cone while its taped seams cure. Make the ring and all twelve cleats part of the removable roof. The finial ball top is Z{DER["total_height"]:g}.',M,152,size=10,leading=15)
    b.end()
    b.page('Validation and workshop checks','CAD checks do not replace a physical dry fit')
    r=json.loads((ROOT/'output/reports/cad-validation.json').read_text())
    ok=lambda v:'Clear' if not v else f'{len(v)} problems - DO NOT BUILD'
    rows=[['Native solid model',f'{r["profile_count"]} profiles / {r["house_instances"]} house parts. Furniture and garden appear only in the 3D view'],['Closed assembly','No overlaps' if not r['collisions'] else f'{len(r["collisions"])} collisions - DO NOT BUILD'],['Opening walls',f'0-{OPEN:g} degrees every 5 degrees, veranda and furniture in place: '+ok([h for w in r['wall_swing'] for h in w['collisions']])],['Doors',f'{len(r["door_sweep"])} doors, 0-90 degrees every 5 degrees: '+ok([h for d in r['door_sweep'] for h in d['collisions']])],['Roof lift','Turn-buttons released, lifted 0-200 mm: '+ok(r['roof_lift_collisions'])],['Windows','Veranda keeps 10 mm clear: '+ok(r['window_occlusion'])],['Finished size',f'D{CFG["base_diameter"]:g} x {CFG["height"]:g} mm'],['STEP reopen','Valid solid export' if r['step_reopen_valid'] else 'FAILED'],['Sheet layouts','Stock boundaries and minimum profile spacing checked']]
    fit=DER['figure_fit'];kinds=Counter(h['kind'] for h in DATA['hardware'])
    rows+=[['Figures through doorways',f'{len(fit)} figure / doorway pairs, at least {min(f["spare_width"] for f in fit):g} mm to spare in width'+('' if all(f['fits'] for f in fit) else ' - DO NOT BUILD')],['Magnets',f'{kinds["Catch magnet"]} catch + {kinds["Stop magnet"]} stop magnets, each enclosed behind {MAG["skin"]:g} mm of wood; walls stop at {OPEN:g} degrees']]
    stack=ROOT/'output/reports/stackup.json'
    if stack.exists():
        sr=json.loads(stack.read_text());rows.append(['Plywood stack-up',f'{len(sr["chains"])} joint chains at the thinnest and thickest sheets: '+('all hold' if sr['all_pass'] else 'FAILS - see the stack-up report')])
    risk=ROOT/'output/reports/risk-audit.json'
    if risk.exists():
        ra=json.loads(risk.read_text());tip=ra['tip_over']
        rows.append(['Tip-over',f'Walls open: {tip["force_at_eave_N"]:.0f} N at the eave tips the house (target {tip["target_N"]:g} N); anchored with the strap'])
    y=table(c,rows,M,713,[170,345],['Check','Result'],9.5)
    para(c,'Before glue-up, work through the dry-fit and safety checks page. This is a CAD-verified fabrication design, not a physically load-tested or certified toy. For ages 3-5, supervise play, keep hands clear of hinge gaps, and recheck magnets, small parts and the anti-tip strap regularly.',M,y-22,size=10,leading=15)
    b.end()
    b.page('Files and reference sources','Rebuild from the included source files')
    para(c,f'{naming.PDF_COMPLETE}: this A4 instruction book, contents, dimensioned references, individual cutting templates, decor, clay figures and A4 supplier summary. Native A3 machining pages are in the separate supplier PDF.\n{naming.PDF_CUTTING_TEMPLATES}: all house templates. Print at 100%. Use {naming.PDF_3MM_HAND_TEMPLATES} for the thin parts only.\n{naming.PDF_DIMENSIONED_PARTS}: measurements and drilling schedule.\n{naming.PDF_DECOR}: paint palette, stone plinth panels and roof shingle strips.\n{naming.PDF_CLAY_FAMILY}: modelling the clay figures.\n{naming.PDF_SUPPLIER}: Polish by default; specification, reference maps and clean full-size cutting pages.\n{naming.CAD_DOCUMENT}: native editable FreeCAD project. {naming.CAD_STEM}.step is the house. Furniture and garden appear only in the 3D viewer and renders. DXF and sheet SVG files provide 1:1 profiles.',M,713,size=11,leading=17)
    para(c,'To change stock or hinges, edit source/config.json and regenerate all outputs together. Read README.md before changing CAD sketches: editable geometry changes do not automatically update already-exported PDF files.',M,423,size=10)
    sources=[('FreeCAD official releases','https://github.com/FreeCAD/FreeCAD/releases'),('Bossard cap-nut specification examples','https://www.bossard.com/global-en/eshop/hex-nuts/hex-domed-cap-nuts-acorn-nuts/p/513/'),('Bosch jigsaw operating guidance','https://www.bosch-professional.com/binary/manualsmedia/o606338v21_160992AD26_202509.pdf')]
    y=324
    for title,url in sources:
        label(c,title,M,y,9);c.linkURL(url,(M,y-4,W-M,y+12),relative=0);y=para(c,url,M,y-17,size=7.5,leading=11)-12
    para(c,'Cover: a summer scene painted by source/cover.py around the CAD render of the house, with the title in Chalkboard SE. All technical diagrams and cutting profiles are derived from the CAD model.',M,84,size=8.5,leading=12)
    b.end();return b.save()

def profile_reference(c,p,x,y,w,h,max_scale=5):
    # Reference drawing area; lower-left datum marked at (0,0).
    scale=min((w-100)/max(p['width'],1),(h-68)/max(p['height'],1),max_scale)
    ox=x+(w-p['width']*scale)/2;oy=y+(h-p['height']*scale)/2
    def xy(a,b):return ox+a*scale,oy+b*scale
    loop(c,[xy(*v) for v in p['outer']],colors.HexColor('#F0DEBD'))
    for cut in p['cuts']:
        loop(c,[xy(*v) for v in cut],colors.white)
        a,b,d,e=min(v[0] for v in cut),min(v[1] for v in cut),max(v[0] for v in cut),max(v[1] for v in cut)
        if d-a>20:dimension(c,xy(a,b),xy(d,b),f'{d-a:.1f}',-11,7)
        if e-b>25:dimension(c,xy(d,b),xy(d,e),f'{e-b:.1f}',11,7)
    for hh in p['holes']+p['starters']:
        a,b=xy(hh['x'],hh['y']);c.setStrokeColor(TEAL if hh['id'].startswith('S') else RUST);c.setLineWidth(.6)
        if hh['id'].startswith('S'):c.setDash(2,2)
        c.circle(a,b,hh['diameter']*scale/2);c.setDash();c.line(a-4,b,a+4,b);c.line(a,b-4,a,b+4)
        c.setFont('Helvetica',7);c.setFillColor(TEAL if hh['id'].startswith('S') else RUST);c.drawString(a+5,b+4,hh['id'])
    dimension(c,xy(0,0),xy(p['width'],0),f'{p["width"]:.2f}',-18)
    dimension(c,xy(0,0),xy(0,p['height']),f'{p["height"]:.2f}',-26)
    if p['id'] in CFG['doors'].values():
        dimension(c,xy(*p['outer'][2]),xy(*p['outer'][3]),f'{DER["doorways"][0]["width"]:.1f} door notch',11,7)
        dimension(c,xy(*p['outer'][4]),xy(*p['outer'][3]),f'{DER["doorways"][0]["height"]+CFG["thickness"]["wall"]:.1f}',9,7)
    arrow(c,xy(0,0),xy(min(p['width'],25),0),TEAL);arrow(c,xy(0,0),xy(0,min(p['height'],25)),TEAL)
    c.setFont('Helvetica',7);c.setFillColor(TEAL);c.drawString(ox-6,oy-9,'0,0')

def references():
    b=Book(naming.PDF_DIMENSIONED_PARTS,'Dimensioned parts');c=b.c
    part_pages(b,MAIN,'All house wood parts / including temporary jigs')
    assembly_maps(b)
    hinge_templates(b);return b.save()

def assembly_maps(b):
    """Dimensioned positioning maps, in the original panel lower-left datum."""
    c=b.c;lift=CFG['fabrication']['base_lift']
    for parent,panel in DER['panels'].items():
        b.page(parent+' / section and support positioning','Scaled assembly map / coordinates in mm / not a cutting template')
        outline=panel['outline'];ww=max(x for x,y in outline);hh=max(y for x,y in outline)
        k=min((W-2*M)/ww,340/hh);ox=(W-ww*k)/2;oy=340
        def xy(x,y):return ox+x*k,oy+y*k
        loop(c,[xy(x,y) for x,y in outline],stroke=colors.black)
        for cut in panel['cuts']:loop(c,[xy(x,y) for x,y in cut],stroke=colors.black)
        datum=panel['origin'];panel_z=datum[2]+lift
        sections=[i for i in DATA['instances'] if i['design_part']==parent and abs(i['origin'][2]-panel_z)<.001]
        supports=[i for i in DATA['instances'] if P[i['part']].get('assembly_panel')==parent and i['design_part']!=parent and (abs(i['origin'][2]+P[i['part']]['thickness']-panel_z)<.001 or parent=='R02' and abs(i['origin'][2]-panel_z-panel['thickness'])<.001)]
        for inst in sections+supports:
            part=P[inst['part']]
            pts=[[inst['origin'][0]+inst['u'][0]*x+inst['v'][0]*y-datum[0],inst['origin'][1]+inst['u'][1]*x+inst['v'][1]*y-datum[1]] for x,y in part['outer']]
            c.setDash(3,2) if inst in supports else c.setDash()
            loop(c,[xy(x,y) for x,y in pts],stroke=RUST if inst in supports else TEAL)
            xx,yy=xy(sum(x for x,y in pts)/len(pts),sum(y for x,y in pts)/len(pts));label(c,inst['part'],xx,yy,7)
        c.setDash();dimension(c,xy(0,0),xy(ww,0),f'{ww:.2f} mm',-18,8)
        dimension(c,xy(0,0),xy(0,hh),f'{hh:.2f} mm',-18,8)
        rows=[]
        for inst in supports:
            angle=math.degrees(math.atan2(inst['u'][1],inst['u'][0]))
            rows.append([inst['part'],f'{inst["origin"][0]-datum[0]:.2f}',f'{inst["origin"][1]-datum[1]:.2f}',f'{angle:.0f} deg'])
        y=table(c,rows,M,300,[95,120,120,180],['Support','Origin X','Origin Y','Orientation'],8)
        para(c,'Coordinates refer to the lower-left corner of the complete panel outline. Blue lines identify fabrication sections. Dashed brown lines identify support pieces. Place each support using its template origin and orientation. Centre floor supports on the seam for 2 mm bearing per half.',M,y-18,size=9,leading=13)
        para(c,'Join panels on a flat board. Keep upper faces flush. Glue base supports below the base and ring bridges above the roof ring. Make a physical sample of the narrow floor joint before assembly.',M,y-92,size=9,leading=13)
        b.end()

HALF=(W-2*M-12)/2;REF_SCALE=2.5
def block_spec(p):
    """Packed reference block: full width for wide or hole-heavy parts, otherwise half width."""
    rows=len(p['holes'])+len(p['starters']);full=p['width']>200 or rows>8;w=W-2*M if full else HALF
    natural=68+p['height']*min((w-100)/max(p['width'],1),REF_SCALE)
    return full,w,max(90,min(300 if full else 250,natural))
def hole_rows(p):
    return [[hh['id'],f'{hh["diameter"]:g}',f'{hh["x"]:.2f}',f'{hh["y"]:.2f}','Through' if hh.get('depth') is None else f'{hh["depth"]:g} mm',('UNDERSIDE' if hh.get('entry')=='bottom' else 'TOP') if not hh['id'].startswith('S') else 'Waste'] for hh in p['holes']+p['starters']]
def block_height(p,w,draw_h):
    rows=len(p['holes'])+len(p['starters'])
    return 22+draw_h+((rows+1)*9.5+6 if rows else 0)+(len(simpleSplit(p['note'],'Helvetica',7,w))*9+4 if p['note'] else 0)+6
def draw_block(c,p,x,top,w,draw_h):
    c.setFillColor(INK);c.setFont('Helvetica-Bold',9);name=f'{p["id"]}  {p["name"]}'
    while c.stringWidth(name,'Helvetica-Bold',9)>w:name=name[:-2]
    c.drawString(x,top-9,name)
    c.setFont('Helvetica',7);c.setFillColor(TEAL);c.drawString(x,top-18,f'{p["quantity"]} required / {p["thickness"]:g} mm / outline {p["width"]:.1f} x {p["height"]:.1f}')
    profile_reference(c,p,x,top-22-draw_h,w,draw_h,REF_SCALE);y=top-22-draw_h-2
    rows=hole_rows(p)
    if rows:y=mini_table(c,rows,x,y,[v*w/251.5 for v in (26,24,40,40,44,77)] if w<300 else [40,40,70,70,80,120],['Hole','D mm','X mm','Y mm','Depth','Entry / type'])-4
    if p['note']:para(c,p['note'],x,y-8,width=w,size=7,leading=9)

def part_pages(b,parts,kicker):
    """Inventory with page references, then dimensioned references packed several per page (not 1:1)."""
    c=b.c;blocks=[(pid,p,*block_spec(p)) for pid,p in parts.items()]
    # First fit: each row goes on the first page that still has room for it.
    pages=[];space=[]
    def place(items):
        height=max(block_height(p,w,dh) for _,p,_,w,dh in items)
        n=next((n for n,y in enumerate(space) if y-height>=52),None)
        if n is None:pages.append([]);space.append(714);n=len(pages)-1
        for k,item in enumerate(items):pages[n].append((item,M+k*(HALF+12),space[n]))
        space[n]-=height+8
    pending=None
    for item in blocks:
        if item[2]:place([item])
        elif pending:place([pending,item]);pending=None
        else:pending=item
    if pending:place([pending])
    inventory_pages=math.ceil(len(parts)/22);first=b.n+1+inventory_pages
    page_of={item[0]:first+n for n,page in enumerate(pages) for item,_,_ in page}
    rows=[[p['id'],p['name'],p['quantity'],f'{p["width"]:.1f} x{p["height"]:.1f}',f'{p["thickness"]:g}',page_of[pid]] for pid,p in parts.items()]
    for start in range(0,len(rows),22):
        b.page('Part inventory' if not start else 'Part inventory / continued',kicker if not start else 'Cut quantities are totals for this part set')
        table(c,rows[start:start+22],M,714,[38,210,34,140,45,48],['ID','Part','Qty','Outline W xH mm','Thick.','Page'],8)
        b.end()
    for page in pages:
        b.page('Dimensioned parts','Scaled reference drawings, not 1:1 templates / hole positions from the 0,0 datum')
        for (pid,p,full,w,dh),x,top in page:draw_block(c,p,x,top,w,dh)
        b.end()

def hinge_templates(b):
    c=b.c;b.page('Hinge checking templates','Actual size / compare metal hardware before drilling')
    for y,key,title in [(600,'wall_hinge','HG1 wall hinge / x6'),(365,'door_hinge',f'HG2 door hinge / x{sum(h["kind"]=="Door butt hinge" for h in DATA["hardware"])}')]:
        hh=CFG[key];x=140;scale=mm;ww=hh['open_width']*scale;hhgt=hh['height']*scale
        label(c,title,M,y+85,13);c.setStrokeColor(INK);c.rect(x,y,ww,hhgt,fill=0,stroke=1);c.setDash(4,3);c.line(x+ww/2,y-20,x+ww/2,y+hhgt+20);c.setDash()
        for leaf in (-1,1):
            xx=x+ww/2+leaf*hh['hole_x']*scale
            for yy in hh['hole_y']:
                c.circle(xx,y+yy*scale,(1 if key=='wall_hinge' else .8)*scale);c.line(xx-4,y+yy*scale,xx+4,y+yy*scale)
        dimension(c,(x,y),(x+ww,y),f'{hh["open_width"]:g} open width',-17)
        dimension(c,(x,y),(x,y+hhgt),f'{hh["height"]:g} height',-25)
        para(c,'Compare height, leaf width, barrel diameter and every hole center. The metal hole pattern must match this template and its mounted wall/door pilots. If it differs, update config and regenerate; do not enlarge wood holes to compensate.',M,y-61,size=9,leading=13)
    scale_bar_bottom(c);b.end()

def transform_point(p,item,x,y):
    th=math.radians(item['angle']);co,si=math.cos(th),math.sin(th);vs=[(a*co-b*si,a*si+b*co) for a,b in p['outer']];a=min(v[0] for v in vs);b=min(v[1] for v in vs)
    return x*co-y*si-a+item['x'],x*si+y*co-b+item['y']
def draw_sheet(c,sheet,scale=mm,ox=0,oy=0,labels=True):
    def xy(x,y):return ox+x*scale,oy+y*scale
    laser=sheet.get('laser')
    for item in sheet['items']:
        p=P[item['part']]
        for contour in [p['outer']]+p['cuts']:
            loop(c,[xy(*transform_point(p,item,*v)) for v in contour],stroke=colors.black,width=.4 if laser else .5)
        # A laser (or a knife) cuts openings directly: laser sheets have no blade-entry starter holes.
        for hh in p['holes']+([] if laser else p['starters']):
            x,y=xy(*transform_point(p,item,hh['x'],hh['y']));c.setStrokeColor(TEAL if hh['id'].startswith('S') else RUST);c.setLineWidth(.4)
            if hh['id'].startswith('S'):c.setDash(2,1.5)
            c.circle(x,y,hh['diameter']*scale/2);c.setDash();c.line(x-3,y,x+3,y);c.line(x,y-3,x,y+3)
            if labels and scale>=1 and not laser:c.setFont('Helvetica',5.5);c.setFillColor(INK);c.drawString(x+3,y+3,f'{hh["id"]} D{hh["diameter"]:g}')
        x,y=xy(*transform_point(p,item,p['width']/2,p['height']/2));c.setFillColor(INK)
        if laser and scale>=1:
            # Laser parts sit 2 mm apart: print just the part ID, along the length of thin strips.
            w,h=(p['width'],p['height']) if item['angle'] in (0,180) else (p['height'],p['width'])
            c.saveState();c.translate(x,y)
            if h>w and w<12:c.rotate(90)
            c.setFont('Helvetica-Bold',5 if min(w,h)>=5 else 4);c.drawCentredString(0,-1.6,item['part']);c.restoreState()
            continue
        c.setFont('Helvetica-Bold',6 if scale>=1 else 4.5);c.drawCentredString(x,y,item['part'])
        if p['width']>35 and p['height']>30 and scale>=1:
            c.setFont('Helvetica',5.5);c.drawCentredString(x,y-8,f'{p["thickness"]:g} mm / {p["width"]:.1f} x{p["height"]:.1f}')

def calibration(b):
    c=b.c;b.page('Printer calibration','A4 / 100% actual size / no Fit or Shrink',False)
    para(c,'Print only this page first. Measure both sides of the square and the 100 mm line. Each must be 100 mm within 0.5 mm. If not, correct printer settings and repeat before printing any cutting template.',M,710,size=11,leading=17)
    x=100;y=285;c.setStrokeColor(colors.black);c.setLineWidth(.6);c.rect(x,y,100*mm,100*mm,fill=0,stroke=1)
    dimension(c,(x,y),(x+100*mm,y),'100 mm',-23);dimension(c,(x,y),(x,y+100*mm),'100 mm',-28)
    c.line(x,210,x+100*mm,210)
    for j in range(11):c.line(x+j*10*mm,205,x+j*10*mm,215)
    label(c,'100 mm / check both printer directions',M,167,11);scale_bar_bottom(c);b.end()

def templates():
    from hand_templates import pages
    b=Book(naming.PDF_CUTTING_TEMPLATES,'Individual cutting templates')
    index=pages(b,MAIN,draw_sheet,scale_bar,calibration)
    return b.save(),[dict(i,pdf=b.path.name) for i in index]

def hand_templates(selected):
    from hand_templates import pages
    b=Book(naming.PDF_3MM_HAND_TEMPLATES,'3 mm hand-cutting templates')
    thin={pid:p for pid,p in MAIN.items() if p['thickness']==3 and p['category'] not in BOUGHT}
    index=pages(b,thin,draw_sheet,scale_bar,calibration)
    return b.save(),[dict(i,pdf=b.path.name) for i in index]

def segment_hits_rect(a,b,x0,y0,x1,y1):
    """Liang-Barsky: does segment a-b touch the rectangle?"""
    t0,t1=0,1;dx,dy=b[0]-a[0],b[1]-a[1]
    for pp,q in ((-dx,a[0]-x0),(dx,x1-a[0]),(-dy,a[1]-y0),(dy,y1-a[1])):
        if pp==0:
            if q<0:return False
        else:
            t=q/pp
            if pp<0:t0=max(t0,t)
            else:t1=min(t1,t)
            if t0>t1:return False
    return True
def tile_has_content(sheet,x0,y0,x1,y1):
    for item in sheet['items']:
        p=P[item['part']]
        for contour in [p['outer']]+p['cuts']:
            pts=[transform_point(p,item,*v) for v in contour]
            if any(segment_hits_rect(a,q,x0,y0,x1,y1) for a,q in zip(pts,pts[1:]+pts[:1])):return True
        for hh in p['holes']+p['starters']:
            x,y=transform_point(p,item,hh['x'],hh['y']);r=hh['diameter']/2
            if x0-r<=x<=x1+r and y0-r<=y<=y1+r:return True
    return False
def laser_band(c,sheet,height,lines):
    """Unfilled header for human-use 3 mm templates; never used on supplier production pages."""
    c.setFillColor(colors.black);c.setFont('Helvetica-Bold',11);c.drawString(10*mm,H-8*mm,f'3 mm HAND TEMPLATE  /  {sheet["id"]}  /  {sheet["thickness"]:g} mm plywood')
    c.setFont('Helvetica',7)
    for k,text in enumerate(lines):c.drawString(10*mm,H-12.5*mm-k*3.4*mm,text)
def template_pages(b,sheets,purchased):
    """Calibration page, tiled 1:1 sheet templates and purchased-wood outlines. Thin hand templates get an unfilled header;
    an A4 thin sheet is its own single 1:1 page (its parts stay inside the printable window)."""
    c=b.c;calibration(b)
    tilew,tileh,overlap=190,260,10;stepx,stepy=tilew-overlap,tileh-overlap
    template_index=[]
    for sheet in sheets:
        laser=sheet.get('laser')
        if laser and (sheet['width'],sheet['height'])==(210,297):
            # The page is the sheet: lay the print flush with the plywood edges.
            c.setFillColor(colors.white);c.rect(0,0,W,H,fill=1,stroke=0)
            draw_sheet(c,sheet,mm,0,0)
            laser_band(c,sheet,H-275*mm,['ACTUAL SIZE 100%: lay the print flush with the sheet edges.',f'Laser file: output/dxf/{sheet["id"]}-laser.dxf (or .svg)'])
            c.setStrokeColor(colors.HexColor('#CCCCCC'));c.setLineWidth(.3);x0,y0,x1,y1=sheet['window'];c.rect(x0*mm-1,y0*mm-1,(x1-x0)*mm+2,(y1-y0)*mm+2,fill=0,stroke=1)
            c.setFont('Helvetica',6.5);c.setFillColor(INK);c.drawString(10*mm,7*mm,f'{len(sheet["items"])} parts, {sheet["spacing"]:g} mm apart. Cut only the black outlines; the grey frame is not a cut.')
            scale_bar(c,98*mm,276.5*mm);b.n+=1;c.showPage()
            template_index.append({'sheet':sheet['id'],'overview_page':None,'first_tile_page':b.n,'last_tile_page':b.n,'columns':1,'rows':1,'skipped_tiles':[],'laser':True})
            continue
        nx=max(1,math.ceil((sheet['width']-tilew)/stepx)+1);ny=max(1,math.ceil((sheet['height']-tileh)/stepy)+1)
        skipped=[[col,row] for row in range(ny) for col in range(nx) if not tile_has_content(sheet,col*stepx,row*stepy,col*stepx+tilew,row*stepy+tileh)]
        if laser:laser_band(c,sheet,15*mm,[f'Hand-cutting reference only. Use the separate supplier PDF for machine cutting. A3 sheet; print the following A4 tiles at 100%.'])
        b.page(sheet['id']+' / sheet overview',f'{sheet["width"]:g} x {sheet["height"]:g} x {sheet["thickness"]:g} mm / {nx} columns x {ny} rows')
        scale=min((W-2*M)/(sheet['width']*mm),480/(sheet['height']*mm))*mm
        ox=(W-sheet['width']*scale)/2;oy=190;c.setStrokeColor(colors.HexColor('#BBBBBB'));c.rect(ox,oy,sheet['width']*scale,sheet['height']*scale,fill=0,stroke=1)
        # Tile map: dashed tile outlines with column,row labels; grey tiles have no cut lines and are not printed.
        for row in range(ny):
            for col in range(nx):
                tx,ty=col*stepx,row*stepy;tw,th=min(tilew,sheet['width']-tx),min(tileh,sheet['height']-ty)
                if [col,row] in skipped:c.setFillColor(colors.HexColor('#E3E3E3'));c.rect(ox+tx*scale,oy+ty*scale,tw*scale,th*scale,fill=1,stroke=0)
                c.setStrokeColor(TEAL);c.setLineWidth(.4);c.setDash(2,2);c.rect(ox+tx*scale,oy+ty*scale,tw*scale,th*scale,fill=0,stroke=1);c.setDash()
                c.setFillColor(TEAL);c.setFont('Helvetica',6);c.drawString(ox+tx*scale+2,oy+ty*scale+2,f'{col+1},{row+1}'+(' not printed' if [col,row] in skipped else ''))
        draw_sheet(c,sheet,scale,ox,oy,False)
        printed=nx*ny-len(skipped)
        para(c,f'Overview only - not full size. Print the {printed} tile pages for this sheet at 100%'+(f'; the {len(skipped)} grey tiles carry no cut lines and are skipped' if skipped else '')+'. Black contours are cut edges; H holes remain in the finished part'+(f'. Parts are {sheet["spacing"]:g} mm apart for a laser; without one, glue the tiles on and cut with a sharp knife.' if laser else '; S holes are temporary blade-entry holes in waste.'),M,142,size=9,leading=13)
        label(c,f'Outer-profile utilization: {sheet["outer_profile_utilization_percent"]}%'+('' if laser else ' / preserve large offcuts'),M,72,9)
        b.end();first=b.n+1
        # Row 1 is the bottom of the sheet, matching the local Y datum.
        for row in range(ny):
            for col in range(nx):
                if [col,row] in skipped:continue
                c.setFillColor(colors.white);c.rect(0,0,W,H,fill=1,stroke=0)
                c.setFillColor(INK);c.setFont('Helvetica-Bold',10);c.drawString(10*mm,H-10*mm,('HAND TEMPLATE / ' if laser else '')+f'{sheet["id"]} / column {col+1}/{nx} / row {row+1}/{ny} / {sheet["thickness"]:g} mm')
                c.setFont('Helvetica',7);c.drawString(10*mm,H-15*mm,'ACTUAL SIZE 100%   |   10 mm overlap   |   Match crosshairs; row 1 is bottom')
                x0,y0=col*stepx,row*stepy;ox=10*mm;oy=13*mm
                c.saveState();clip=c.beginPath();clip.rect(ox,oy,tilew*mm,tileh*mm);c.clipPath(clip,stroke=0,fill=0)
                draw_sheet(c,sheet,mm,ox-x0*mm,oy-y0*mm)
                # Repeated crosses at overlap midlines use global sheet coordinates.
                c.setStrokeColor(colors.HexColor('#999999'));c.setLineWidth(.35)
                for gx in range(5,int(sheet['width'])+1,stepx):
                    for gy in range(5,int(sheet['height'])+1,stepy):
                        xx=ox+(gx-x0)*mm;yy=oy+(gy-y0)*mm;c.line(xx-4,yy,xx+4,yy);c.line(xx,yy-4,xx,yy+4)
                c.restoreState();c.setStrokeColor(colors.HexColor('#CCCCCC'));c.rect(ox,oy,tilew*mm,tileh*mm,fill=0,stroke=1)
                c.setFont('Helvetica',7);c.setFillColor(INK);c.drawString(10*mm,7*mm,f'Local tile origin X{x0:g}, Y{y0:g} mm | Cut only solid black profile boundaries')
                scale_bar_top(c);b.n+=1;c.showPage()
        template_index.append({'sheet':sheet['id'],'overview_page':first-1,'first_tile_page':first,'last_tile_page':b.n,'columns':nx,'rows':ny,'skipped_tiles':skipped,'laser':bool(laser)})
    # Purchased wood: actual-size cutting outlines, not plywood sheet nesting.
    for p in purchased:
        b.page(p['id']+' / purchased solid wood',f'{p["quantity"]} required / outline actual size / stock thickness {p["thickness"]:g} mm',False)
        ox=M+30;oy=H-160-p['height']*mm
        loop(c,[(ox+x*mm,oy+y*mm) for x,y in p['outer']],stroke=colors.black)
        for hh in p['holes']:
            x,y=ox+hh['x']*mm,oy+hh['y']*mm;c.setStrokeColor(RUST);c.circle(x,y,hh['diameter']*mm/2);c.line(x-4,y,x+4,y);c.line(x,y-4,x,y+4);label(c,f'{hh["id"]} D{hh["diameter"]:g}',x+10,y+6,8)
        dimension(c,(ox,oy),(ox+p['width']*mm,oy),f'{p["width"]:.2f} mm',-20)
        dimension(c,(ox,oy),(ox,oy+p['height']*mm),f'{p["height"]:.2f} mm',-28)
        para(c,p['note'],M,oy-68,size=10)
        if p.get('outercircle'):para(c,'This is purchased round dowel stock: cut to the 8 mm LENGTH. Do not saw a circular plywood replacement.',M,oy-130,size=10)
        scale_bar_bottom(c);b.end()
    return template_index

def stone_rect(c,x,y,w,h,seed=0):
    """Printable stone courses: rounded grey stones in mortar, deterministic per seed."""
    rnd=random.Random(seed);c.saveState();path=c.beginPath();path.rect(x,y,w,h);c.clipPath(path,stroke=0,fill=0)
    c.setFillColor(colors.HexColor('#8E8C84'));c.rect(x,y,w,h,fill=1,stroke=0)
    yy=y
    while yy<y+h:
        rh=rnd.uniform(5.5,8)*mm;xx=x-rnd.uniform(0,8)*mm
        while xx<x+w:
            sw=rnd.uniform(7,15)*mm;tone=rnd.choice(['#C9C5B9','#BDB8AB','#D3CFC4','#B2AEA2','#C4BFB2'])
            c.setFillColor(colors.HexColor(tone));c.roundRect(xx+.6,yy+.6,sw-1.2,rh-1.2,2.2,fill=1,stroke=0);xx+=sw
        yy+=rh
    c.restoreState();c.setStrokeColor(INK);c.setLineWidth(.4);c.rect(x,y,w,h,fill=0,stroke=1)

import shingles
def draw_strip(c,roof,s,X,Y,angle=0):
    """One shingle strip at 1:1, turned by angle about its development origin (the cone apex), which lands at page point X, Y (mm)."""
    cs=s['course'];m=s['m'];k=cs['k'];r,y0,yt=cs['r'],cs['y0'],cs['yt'];rw=roof.rw
    rnd=random.Random(1000*k+s['start']);c.saveState();c.translate(X*mm,Y*mm);c.rotate(angle);c.scale(mm,mm)
    labelled=False
    for fa in s['facets']:
        c.saveState();c.rotate(math.degrees((fa['t']-(m-1)/2)*roof.alpha));c.translate(-rw/2,-roof.apex)
        path=c.beginPath();o=cs['outline'];path.moveTo(*o[0])
        for q in o[1:]:path.lineTo(*q)
        path.close();c.clipPath(path,stroke=0,fill=0)
        c.saveState()
        if fa['holes']:
            hp=c.beginPath();hp.rect(-5,y0-5,rw+10,yt-y0+10)
            for _,poly in fa['holes']:
                hp.moveTo(*poly[0])
                for q in poly[1:]:hp.lineTo(*q)
                hp.close()
            c.clipPath(hp,stroke=0,fill=0,fillMode=0)
        for cx in cs['centres']:
            c.setFillColor(colors.HexColor(rnd.choice(shingles.TONES)));c.rect(cx-r,y0+r,2*r,yt-y0-r+1,fill=1,stroke=0);c.circle(cx,y0+r,r,fill=1,stroke=0)
        # The glue band lies under the next course: shaded, and its lower edge is where the next tips sit.
        c.setFillColor(colors.Color(.32,.08,.06,alpha=.22));c.rect(-5,y0+shingles.VIS,rw+10,yt-y0,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#6E2520'));c.setLineWidth(.18);c.line(-5,y0+shingles.VIS,rw+10,y0+shingles.VIS)
        c.setStrokeColor(colors.HexColor('#8E3530'));c.setLineWidth(.12)
        for cx in cs['centres']:c.arc(cx-r,y0,cx+r,y0+2*r,180,180)
        # Course and panel number in the hidden top band.
        wt=roof.width(yt-1.2)
        if wt>=6:
            c.setFillColor(colors.HexColor('#4A1814'));c.setFont('Helvetica-Bold',1.7);c.drawCentredString(rw/2,yt-1.9,f'{k+1}\u00b7{fa["facet"]+1}');labelled=True
        elif not labelled and fa['t']==m//2:
            c.setFillColor(colors.HexColor('#4A1814'));c.setFont('Helvetica-Bold',1.3);c.drawCentredString(rw/2,yt-1.6,str(k+1));labelled=True
        c.restoreState()
        c.setStrokeColor(colors.HexColor('#2B1513'));c.setLineWidth(.15)
        for name,poly in fa['holes']:
            loop(c,poly,stroke=colors.HexColor('#2B1513'),width=.15)
            hx=sum(x for x,_ in poly)/len(poly);hy=min(max(sum(y for _,y in poly)/len(poly),y0+2),yt-3)
            c.setFillColor(colors.HexColor('#2B1513'));c.setFont('Helvetica',1.6);c.drawCentredString(hx,hy,'cut out: '+name)
        c.restoreState()
    # Cut outline and the creases on the hips between panels, left out inside the dormer and chimney holes.
    holes=[[roof.to_dev(fa['t'],m,q) for q in poly] for fa in s['facets'] for _,poly in fa['holes']]
    c.saveState()
    if holes:
        bx0,by0,bx1,by1=s['bbox'];path=c.beginPath();path.rect(bx0-5,by0-5,bx1-bx0+10,by1-by0+10)
        for poly in holes:
            path.moveTo(*poly[0])
            for q in poly[1:]:path.lineTo(*q)
            path.close()
        c.clipPath(path,stroke=0,fill=0,fillMode=0)
    loop(c,s['poly'],stroke=colors.HexColor('#2B1513'),width=.15)
    c.setStrokeColor(colors.HexColor('#F0C9C2'));c.setLineWidth(.12);c.setDash(.7,.7)
    for t in range(1,m):
        a=roof.to_dev(t,m,cs['top'][0]);b=roof.to_dev(t,m,cs['lower'][0]);c.line(*a,*b)
    c.setDash();c.restoreState();c.restoreState()

def shingle_pages(b):
    """Intro page, then the strips packed tightly on 1:1 pages."""
    c=b.c;roof,items=shingles.strips(DATA);area=(12,16,186,262)
    pages=shingles.best_pack(items,area[2],area[3])
    chimney=next((f+1 for f,hs in roof.holes.items() for name,_ in hs if name=='chimney'),None)
    per=Counter(s['m'] for s in items);rows=len(roof.rows)
    b.page('Roof shingle strips','Optional / one strip per course, unrolled so it wraps the round roof',False)
    y=para(c,f'The roof is a cone of 12 flat panels, so a level course of tiles turns a little at every hip and a straight strip cannot follow it. Each strip on the next {len(pages)} pages is one course of the roof unrolled flat: it bends at the hips, where you crease it on the dotted line, and its ends are cut along the hips. The {rows} courses take {len(items)} strips: '+', '.join(f'{per[m]} of {m} panel'+('s' if m>1 else '') for m in sorted(per))+'. Low courses are long, so they are split; near the top one strip wraps the whole roof.',M,712,size=10,leading=14)
    steps=['Paint the roof red first so any gaps stay red. Number the roof panels 1-12 in pencil: the dormer panel R06 is 1, then count to the right as you face the roof (anticlockwise seen from above)'+(f'. The chimney stands on panel {chimney}.' if chimney else '.'),
      'Print at 100% and check the 100 mm bar. Cut each strip on its dark outline: the straight top, the scalloped bottom and the two ends. Cut out the marked dormer and chimney holes.',
      'Crease each strip on its dotted lines: they sit on the roof hips.',
      f'Start with course 1 at the eave. The mark in the top band, for example 7\u00b73, means course 7 on panel 3. Glue only the top {shingles.GLUE:g} mm band. Each next course goes {shingles.VIS:g} mm higher, with its tile tips on the dark line of the course below.',
      f'The R03 top cap covers the cone tip above course {rows}. Seal the finished roof with a compatible clear finish.']
    for n,text in enumerate(steps,1):y=para(c,f'{n}. {text}',M,y-6,size=10,leading=14)
    # A sample strip at full size, with its parts named.
    s=next(s for s in items if s['m']>=3 and s['bbox'][2]-s['bbox'][0]<150 and not any(f['holes'] for f in s['facets']))
    x0,y0_,x1,y1=s['bbox'];X=(W/mm-(x1-x0))/2-x0;Y=108-y1
    draw_strip(c,roof,s,X,Y)
    cs=s['course'];t=s['m']//2
    def pt(q,tt=t):a=roof.to_dev(tt,s['m'],q);return ((a[0]+X)*mm,(a[1]+Y)*mm)
    callouts=[(pt((roof.rw*.45,cs['yt']-2)),'Glue only this top band: the next course covers it',M,122*mm,'l'),
      (pt((roof.xl(cs['yt']-3),cs['yt']-3),t),'Crease on the hip (dotted line)',W-M,122*mm,'r'),
      (pt((roof.rw*.3,cs['y0']+shingles.VIS),0),'The next course\'s tile tips sit on this dark line',M,52*mm,'l'),
      (pt((roof.rw*.55,cs['y0']+.3),s['m']-1),'Cut on the dark outline: scallops, straight top, ends on the hips',W-M,52*mm,'r')]
    for (px,py),text,lx,ly,side in callouts:
        c.setFont('Helvetica',8);tw=c.stringWidth(text,'Helvetica',8);ex=lx+tw/2 if side=='l' else lx-tw/2
        c.setStrokeColor(TEAL);c.setLineWidth(.5);c.line(px,py,ex,ly+(9 if ly<py else -3));c.circle(px,py,1.2,fill=0,stroke=1)
        c.setFillColor(TEAL);(c.drawString if side=='l' else c.drawRightString)(lx,ly,text)
    c.setFillColor(INK);c.setFont('Helvetica',8);c.drawString(M,26*mm,f'Course {s["row"]} on panels '+', '.join(str(f["facet"]+1) for f in s['facets'])+' at full size (also on the strip pages).')
    scale_bar_bottom(c);b.end()
    for n,page in enumerate(pages,1):
        c.setFillColor(colors.white);c.rect(0,0,W,H,fill=1,stroke=0)
        label(c,f'Roof shingle strips / page {n}/{len(pages)}',10*mm,H-11*mm,10);c.setFont('Helvetica',7)
        courses=sorted({s['row'] for s,*_ in page})
        c.drawString(10*mm,H-16*mm,f'Print 100% / {len(page)} strips, courses {spans(courses)} / cut on the dark outline, crease the dotted hips / mark = course\u00b7panel')
        for s,x,y,angle in page:draw_strip(c,roof,s,area[0]+x,area[1]+y,angle)
        scale_bar(c,98*mm,8*mm);b.n+=1;c.showPage()

def decor():
    b=Book(naming.PDF_DECOR,'Colored decor');c=b.c
    b.page('Paint and texture palette','Paint references / print the stone and shingle pages at 100%')
    y=692
    for name,key,where in [('Lanternwood blue','blue','Exterior wall panels'),('Roof red','red','Roof and chimney cap'),('Warm cream','cream','Window trim, veranda columns and railings'),('Garden green','green','Base and landscape'),('Honey ochre','ochre','Doors'),('Warm wood','wood','Floors and veranda deck')]:
        c.setFillColor(colors.HexColor(CFG['colors'][key]));c.roundRect(M,y-35,70,35,5,fill=1,stroke=0);label(c,name,M+90,y-10,11);para(c,CFG['colors'][key]+' / '+where,M+90,y-28,size=9);y-=61
    para(c,'These HEX values are visual references, not a guarantee of a paint match. Paint the walls, floors and trim. The printed stone plinth panels and roof shingle strips that follow are optional finishing details: test the glue and a compatible clear finish on a scrap first.',M,132,size=10)
    b.end()
    # Stone plinth textures, one per plinth facet (including the two hidden-drawer fronts).
    pw,ph=P['PL1']['width'],P['PL1']['height'];panels=['PL1']*P['PL1']['quantity']+['DR4 drawer front']*P['DR4']['quantity']
    for page in range(0,len(panels),8):
        b.page('Stone plinth panels' if not page else 'Stone plinth panels / continued',f'Actual size {pw:.1f} x {ph:g} mm / glue onto the plinth facets after painting',False)
        for j,name in enumerate(panels[page:page+8]):
            x=M+(j%2)*(pw*mm+18);y=700-ph*mm-(j//2)*(ph*mm+26)
            stone_rect(c,x,y,pw*mm,ph*mm,seed=page+j);label(c,name,x,y+ph*mm+5,7)
        para(c,'Paint the plinth stone grey, or glue these printed stones on. Use the same print on the two drawer fronts so the drawer stays hidden; cut their 14 x 5 mm finger notches with a knife.',M,96,size=9)
        scale_bar_bottom(c);b.end()
    shingle_pages(b)
    return b.save()

def appendix():
    """Clay family instructions; furniture has no printout or fabrication plans."""
    b=Book(naming.PDF_CLAY_FAMILY,'Clay family');c=b.c
    b.page('Model the family in thermo-clay','Thermo-clay figures');imagebox(c,'clay-family',M,269,W-2*M,442)
    y=para(c,clay_steps(),M,235,size=11,leading=16)
    para(c,'Clay amounts and lump sizes are in the instructions. Where they stand: '+', '.join(f'{f["name"]} {f["where"]}' for f in DER['figures'])+'. They stand loose and need no glue.',M,y-8,size=9.5,leading=14,color=TEAL);b.end()
    return b.save()

def main(lang='pl'):
    import config_check,supplier
    from pdf_assembly import combine
    cfg=config_check.check()
    (template_path,main_index),appendix_path=templates(),appendix()
    selected=supplier.sheets_for(DATA,NEST,supplier.settings(cfg))
    hand_path,hand_index=hand_templates(selected)
    supplier_path,supplier_report=supplier.build(DATA,NEST,cfg,lang)
    summary_path=supplier.summary(supplier_report,OUT/naming.PDF_SUPPLIER_SUMMARY)
    paths=[manual(),references(),template_path,decor(),appendix_path,summary_path]
    (ROOT/'output/reports/template-index.json').write_text(json.dumps(main_index,indent=2))
    titles=['Instructions and hardware','Dimensioned parts','Full-size cutting templates','Color and decor','Appendix: clay family',supplier_report['title']]
    sections=[{'path':p,'title':t,'entries':[]} for p,t in zip(paths,titles)]
    sections[0]['entries']=PAGE_TITLES[paths[0].name]
    sections[2]['entries']=[{'title':i['sheet'],'page':i['overview_page'] or i['first_tile_page']} for i in main_index]
    sections[-1]['entries']=[]
    contents=combine(sections,OUT/naming.PDF_COMPLETE)
    report={'pdfs':{p.name:len(PdfReader(p).pages) for p in paths+[hand_path,supplier_path]},'complete_pages':contents['complete_pages'],'paper':'A4 complete workshop book; separate supplier PDF has native A3 machining pages','template_scale':'1 mm = 72/25.4 PDF points','print_background':'White interior pages, transparent CAD diagram backgrounds, unfilled tables; original cover and textures preserved','starter_holes':sum(len(p['starters'])*p['quantity'] for p in MAIN.values()),'fasteners':dict(Counter(f['type'] for f in DATA['fasteners'])),'windows_per_floor':DATA['derived']['windows_per_floor'],'veranda':f'Permanent {VER["width"]:g} x {VER["depth"]:g} veranda on fixed facet {VER["facet"]}: hipped red roof with caps, shaped white columns, front and side railings, side steps','furniture':'3D view only; no CAD plans, templates or stock','cnc_sheets':[s['id'] for s in NEST['sheets'] if s.get('cnc')],'supplier_language':lang}
    for name,data in [('supplier-index.json',supplier_report),('hand-template-index.json',hand_index),('contents-index.json',contents)]:
        (ROOT/'output/reports'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    (ROOT/'output/reports/pdf-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
    import supplier
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lang',choices=supplier.languages(),default='pl',help='Supplier appendix language only (default: pl)')
    main(parser.parse_args().lang)
