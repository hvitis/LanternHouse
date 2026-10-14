"""Jigsaw-aware polygon nesting. Run with FreeCAD's bundled Python (Shapely)."""
from __future__ import annotations
import json, math, time
import numpy as np
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely import affinity
from shapely.prepared import prep
from shapely import contains_xy

ROOT=Path(__file__).resolve().parents[1]

def new_sheet(t,sw,sh,rules):
    """Empty sheet. Parts go inside its window (x0, y0, x1, y1); free space is tracked on a grid of `cell` mm."""
    window=rules['window'](sw,sh);cell=rules['cell']
    return {'thickness':t,'width':sw,'height':sh,'window':list(window),'spacing':rules['spacing'],'cell':cell,'laser':rules['laser'],'cnc':rules.get('cnc',False),'items':[],'placed':[],'buffer':None,
            'occupied':np.zeros((math.floor((window[3]-window[1])/cell),math.floor((window[2]-window[0])/cell)),dtype=bool)}

def sheet_rules(cfg,t):
    """Jigsaw sheets keep wide lanes and edges. Laser sheets (3 mm) pack tightly; an A4 laser sheet keeps its parts
    inside the printable window of one A4 page, so its 1:1 template prints on a single page."""
    if 'fabrication' in cfg:
        m=cfg['stock_margin']
        return {'laser':False,'cnc':True,'spacing':cfg['nest_spacing'],'cell':1,'window':lambda w,h:(m,0,w-m,h)}
    laser=cfg['laser']
    if t==laser['thickness']:
        m=laser['margin'];a4=laser['a4_window']
        return {'laser':True,'spacing':laser['spacing'],'cell':.5,'window':lambda w,h:tuple(a4) if (w,h)==(210,297) else (m,m,w-m,h-m)}
    m=cfg['stock_margin'];return {'laser':False,'spacing':cfg['nest_spacing'],'cell':2,'window':lambda w,h:(m,m,w-m,h-m)}

def try_place(pid,poly,s):
    # Roof triangles nest head-to-tail; everything else is placed by its bounding box on the free-space grid.
    if s.get('cnc'):
        s['end_margin']=(420-poly.bounds[3])/2 if pid.startswith('W') and poly.bounds[3]>400 else 5 if pid=='P01' else 10
    return place(poly,s) if pid in ('R01','R06') else grid_place(poly,s)

def nest_set(data,selected,prefix,stock):
    """Nest one part set: primary sheets first, then the smallest extra board that fits each overflow part."""
    cfg=data['config'];sheets=[]
    for t in (8,6,4,3):
        units=[];rules=sheet_rules(cfg,t)
        for pid,p in data['parts'].items():
            if p['thickness']!=t or p['category'] in ('Purchased wood','Purchased packing') or not selected(p):continue
            for q in range(p['quantity']):units.append((pid,q+1,Polygon(p['outer'])))
        if not units:continue
        spec=stock[str(t)];units.sort(key=lambda u:(-u[2].area,-max(u[2].bounds[2:])))
        ts=[]
        for n,(pid,q,poly) in enumerate(units):
            found=None
            for si,s in enumerate(ts):
                candidate=try_place(pid,poly,s)
                if candidate:found=(si,candidate);break
            if found is None:
                primary=sum(s['kind']=='primary' for s in ts)<spec['count']
                # Primary stock first while it lasts; parts too large for it fall back to the smallest extra board.
                options=([('primary',spec['primary'])] if primary else [])+[('extra',size) for size in sorted(spec['extra'],key=lambda v:v[0]*v[1])]
                for kind,(sw,sh) in options:
                    s=new_sheet(t,sw,sh,rules);candidate=try_place(pid,poly,s)
                    if candidate:s['kind']=kind;ts.append(s);found=(len(ts)-1,candidate);break
                if found is None:raise ValueError(f'{pid} fits none of the {t} mm stock options {options}')
            si,(angle,x,y,pp,bp)=found;s=ts[si]
            s['items'].append({'part':pid,'copy':q,'angle':angle,'x':x,'y':y,'outer':list(map(list,pp.exterior.coords[:-1]))})
            s['placed'].append(pp);s['buffer']=bp if s['buffer'] is None else s['buffer'].union(bp)
            update_grid(s,pp)
            if n%30==0:print(f'Nesting {prefix} {t} mm: {n+1}/{len(units)}, {len(ts)} sheets',flush=True)
        for j,s in enumerate(ts,1):
            s['id']=f'{prefix}{t}-{j:02}';s['existing_stock']=bool(spec.get('existing')) and s['kind']=='primary';s.pop('placed');s.pop('buffer');s.pop('occupied')
            area=sum(Polygon(item['outer']).area for item in s['items']);s['outer_profile_utilization_percent']=round(area/(s['width']*s['height'])*100,1)
            net=0
            for item in s['items']:
                p=data['parts'][item['part']];net+=Polygon(p['outer']).area-sum(Polygon(c).area for c in p['cuts'])
            s['finished_part_utilization_percent']=round(net/(s['width']*s['height'])*100,1)
            sheets.append(s)
    return sheets

def validate(sheets):
    checks=[]
    for s in sheets:
        polygons=[Polygon(i['outer']) for i in s['items']];x0,y0,x1,y1=s['window']
        for i,p in enumerate(polygons):
            a,b,c,d=p.bounds
            assert a>=x0-.01 and b>=y0-.01 and c<=x1+.01 and d<=y1+.01,(s['id'],p.bounds)
            for q in polygons[i+1:]:assert p.distance(q)>=s['spacing']-.05, (s['id'],p.distance(q))
        checks.append({'sheet':s['id'],'parts':len(polygons),'spacing_mm':s['spacing'],'laser':s['laser'],'bounds_and_spacing':'PASS'})
    return checks

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());cfg=data['config']
    for pattern in ('PLY*-layout.svg','FUR*-layout.svg','PLY*-laser.*','FUR*-laser.*','PLY*-cnc-*'):
        for old in (ROOT/'output/dxf').glob(pattern):old.unlink()
    # Optional furniture never shares a sheet with the house, so it can be skipped entirely.
    sheets=nest_set(data,lambda p:not p.get('render_only') and not p.get('optional'),'PLY',cfg['stock']['main'])
    optional=[]
    laser=cfg['laser']
    result={'spacing_mm':cfg['nest_spacing'],'margin_mm':cfg['stock_margin'],'laser':laser,'sheets':sheets,'optional_sheets':optional,'validation':validate(sheets+optional),'existing_6mm_sheets':sum(s['existing_stock'] for s in sheets),'extra_6mm_sheets':sum(s['thickness']==6 and not s['existing_stock'] for s in sheets),'policy':'A3 plywood only, grouped by thickness. 12 mm nominal lanes, 10 mm edges; continuous pillars use 5 mm end margins. Fixed walls retain the full 420 mm blank length. Confirm cutter and hold-down requirements with the supplier. No nesting inside openings; furniture is view-only.'}
    (ROOT/'output/nesting.json').write_text(json.dumps(result,indent=2))
    for s in sheets+optional:
        svg(s,data)
        if s['laser']:laser_files(s,data)
        if s.get('cnc'):
            import cnc
            s['operations']=cnc.export(data,s,ROOT/'output/dxf')
    (ROOT/'output/nesting.json').write_text(json.dumps(result,indent=2))
    print('Sheets:',{t:sum(s['thickness']==t for s in sheets) for t in (8,6,4,3)},'optional:',{t:sum(s['thickness']==t for s in optional) for t in (4,3)},flush=True)

def grid_place(poly,s):
    occupied=s['occupied'];g=s['cell'];x0,y0,x1,y1=s['window'];integ=np.pad(occupied.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
    best=None
    for angle,p in orientations(poly):
        if angle>=180:continue
        # Laser sheets pack to the exact cell; jigsaw sheets keep one spare cell of slack.
        slack=0 if s['laser'] or s.get('cnc') else 1
        _,_,w,h=p.bounds;kw=math.ceil(w/g-1e-9)+slack;kh=math.ceil(h/g-1e-9)+slack
        if kw>occupied.shape[1] or kh>occupied.shape[0]:continue
        sums=integ[kh:,kw:]-integ[:-kh,kw:]-integ[kh:,:-kw]+integ[:-kh,:-kw]
        ys,xs=np.where(sums==0)
        if s.get('cnc'):
            margin=s.get('end_margin',10)
            keep=(y0+ys*g>=margin-1e-6)&(y0+ys*g+h<=s['height']-margin+1e-6)
            ys,xs=ys[keep],xs[keep]
        if len(xs)==0:continue
        # Arrays are row-major, giving a repeatable bottom-left placement.
        x,y=x0+int(xs[0])*g,y0+int(ys[0])*g
        pp=affinity.translate(p,x,y)
        if pp.bounds[2]>x1+.01 or pp.bounds[3]>y1+.01:continue
        if any(pp.distance(old)<s['spacing']-.02 for old in s['placed']):continue
        score=(y+h,x+w)
        if best is None or score<best[0]:best=(score,(angle,x,y,pp,pp.buffer(s['spacing']/2,join_style=2)))
    return best[1] if best else None

def update_grid(s,p):
    g=s['cell'];x0,y0,_,_=s['window']
    # A cell is taken when its centre is closer than spacing + half its diagonal (plus margin) to a placed part.
    buffered=p.buffer(s['spacing']+g*(.75 if s['laser'] else math.sqrt(2)),join_style=2);a,b,c,d=buffered.bounds
    nx,ny=s['occupied'].shape[1],s['occupied'].shape[0]
    ix=max(0,math.floor((a-x0)/g));iy=max(0,math.floor((b-y0)/g));jx=min(nx,math.ceil((c-x0)/g)+1);jy=min(ny,math.ceil((d-y0)/g)+1)
    if ix>=jx or iy>=jy:return
    xx,yy=np.meshgrid(x0+np.arange(ix,jx)*g+g/2,y0+np.arange(iy,jy)*g+g/2)
    s['occupied'][iy:jy,ix:jx] |= contains_xy(buffered,xx,yy)

def orientations(poly):
    for angle in (0,90,180,270):
        p=affinity.rotate(poly,angle,origin=(0,0));a,b,c,d=p.bounds;p=affinity.translate(p,-a,-b)
        yield angle,p

def place(poly,s):
    prepared=prep(s['buffer']) if s['buffer'] is not None else None
    best=None;spacing=s['spacing'];x0,y0,x1,y1=s['window']
    # Search shelves and complementary triangle positions, then validate real polygon spacing.
    for angle,p in orientations(poly):
        _,_,w,h=p.bounds
        if w>x1-x0 or h>y1-y0:continue
        xs={x0};ys={max(y0,s.get('end_margin',0))}
        pv=list(p.exterior.coords)[:-1]
        for old in s['placed']:
            a,b,c,d=old.bounds;xs.update([a,c+spacing,c-w]);ys.update([b,d+spacing,d-h])
            if len(pv)<=4 and p.area<w*h*.9:
                for ox,oy in list(old.exterior.coords)[:-1]:
                    for nx,ny in pv:xs.update([ox-nx+spacing+1,ox-nx-spacing-1]);ys.update([oy-ny+spacing+1])
        xs=sorted(round(x,3) for x in xs if x0-.01<=x<=x1-w+.01)
        ys=sorted(round(y,3) for y in ys if y0-.01<=y<=y1-h+.01)
        for y in ys:
            if s.get('cnc') and (y<s.get('end_margin',10) or y+h>s['height']-s.get('end_margin',10)):continue
            if best and y+h>best[0][0]+.01:break
            for x in xs:
                pp=affinity.translate(p,x,y);bp=pp.buffer(spacing/2,join_style=2)
                if prepared and prepared.intersects(bp):continue
                score=(y+h,x+w,y,x,angle)
                if best is None or score<best[0]:best=(score,(angle,x,y,pp,bp))
    return best[1] if best else None

def local_point(p,item,x,y):
    angle=math.radians(item['angle']);c,s=math.cos(angle),math.sin(angle)
    corners=[(xx*c-yy*s,xx*s+yy*c) for xx,yy in p['outer']];a=min(v[0] for v in corners);b=min(v[1] for v in corners)
    return x*c-y*s-a+item['x'],x*s+y*c-b+item['y']

def svg(sheet,data):
    w,h=sheet['width'],sheet['height'];text=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>']
    for item in sheet['items']:
        p=data['parts'][item['part']]
        for loop,stroke in [(p['outer'],'black')]+[(c,'black') for c in p['cuts']]:
            pts=[local_point(p,item,*v) for v in loop];points=' '.join(f'{x:.4f},{h-y:.4f}' for x,y in pts);text.append(f'<polygon points="{points}" fill="none" stroke="{stroke}" stroke-width="0.3"/>')
        # A laser cuts openings directly, so laser sheets carry no blade-entry starter holes.
        for hh in p['holes']+([] if sheet['laser'] else p['starters']):
            x,y=local_point(p,item,hh['x'],hh['y']);text.append(f'<circle cx="{x:.4f}" cy="{h-y:.4f}" r="{hh["diameter"]/2}" fill="none" stroke="{("#2793aa" if hh["id"].startswith("S") else "#b84a30")}" stroke-width="0.25"/>')
        x,y=local_point(p,item,p['width']/2,p['height']/2);text.append(f'<text x="{x}" y="{h-y}" text-anchor="middle" font-family="sans-serif" font-size="3">{item["part"]}</text>')
    text.append('</svg>');(ROOT/'output/dxf'/f'{sheet["id"]}-layout.svg').write_text('\n'.join(text))

def laser_files(sheet,data):
    """Laser-ready layout of one sheet, in mm: SVG with red hairline cuts (blue part IDs are optional engraving)
    and a DXF (same minimal form as the part DXFs) with CUT and ENGRAVE_IDS layers."""
    w,h=sheet['width'],sheet['height']
    text=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
          f'<!-- {sheet["id"]}: {w:g} x {h:g} x {sheet["thickness"]:g} mm plywood. Red = cut (hairline). Blue = part IDs, optional light engraving; delete if not wanted. -->',
          '<g id="cut" fill="none" stroke="#FF0000" stroke-width="0.01">']
    dxf=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES'];labels=[]
    for item in sheet['items']:
        p=data['parts'][item['part']]
        for loop in [p['outer']]+p['cuts']:
            pts=[local_point(p,item,*v) for v in loop]
            text.append('<polygon points="'+' '.join(f'{x:.4f},{h-y:.4f}' for x,y in pts)+'"/>')
            dxf+=['0','LWPOLYLINE','100','AcDbEntity','8','CUT','62','1','100','AcDbPolyline','90',str(len(pts)),'70','1']
            for x,y in pts:dxf+=['10',f'{x:.4f}','20',f'{y:.4f}']
        for hh in p['holes']:
            x,y=local_point(p,item,hh['x'],hh['y']);r=hh['diameter']/2
            text.append(f'<circle cx="{x:.4f}" cy="{h-y:.4f}" r="{r}"/>');dxf+=['0','CIRCLE','100','AcDbEntity','8','CUT','62','1','100','AcDbCircle','10',f'{x:.4f}','20',f'{y:.4f}','30','0','40',str(r)]
        x,y=local_point(p,item,p['width']/2,p['height']/2);size=min(2.5,p['width']/4,p['height']/4)
        labels.append(f'<text x="{x:.3f}" y="{h-y+size/3:.3f}" text-anchor="middle" font-family="sans-serif" font-size="{size:.2f}">{item["part"]}</text>')
        dxf+=['0','TEXT','100','AcDbEntity','8','ENGRAVE_IDS','62','5','100','AcDbText','10',f'{x:.4f}','20',f'{y:.4f}','30','0','40',f'{size:.2f}','1',item['part'],'72','1','11',f'{x:.4f}','21',f'{y:.4f}','31','0','100','AcDbText']
    text+=['</g>','<g id="engrave-ids" fill="#0000FF" stroke="none">']+labels+['</g>','</svg>']
    dxf+=['0','ENDSEC','0','EOF']
    (ROOT/'output/dxf'/f'{sheet["id"]}-laser.svg').write_text('\n'.join(text))
    (ROOT/'output/dxf'/f'{sheet["id"]}-laser.dxf').write_text('\n'.join(dxf)+'\n')

if __name__=='__main__':main()
