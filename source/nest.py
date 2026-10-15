"""Polygon nesting on A3 stock: true-shape placement on a free-space grid, searched over several part orders with the
make stock packer (stock.py). Needs shapely and numpy only, so it runs in the project venv."""
from __future__ import annotations
import json, math, time
import numpy as np
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely import affinity
from shapely.prepared import prep
from shapely import contains_xy
from model import BOUGHT

ROOT=Path(__file__).resolve().parents[1]

def new_sheet(t,sw,sh,rules):
    """Empty sheet. Parts go inside its window (x0, y0, x1, y1); free space is tracked on a grid of `cell` mm."""
    window=rules['window'](sw,sh);cell=rules['cell']
    return {'thickness':t,'width':sw,'height':sh,'window':list(window),'spacing':rules['spacing'],'cell':cell,'laser':rules['laser'],'cnc':rules.get('cnc',False),'edge':rules.get('edge',10),'items':[],'placed':[],'buffer':None,
            'occupied':np.zeros((math.floor((window[3]-window[1])/cell),math.floor((window[2]-window[0])/cell)),dtype=bool)}

def sheet_rules(cfg,t):
    """Jigsaw sheets keep wide lanes and edges. Laser sheets (3 mm) pack tightly; an A4 laser sheet keeps its parts
    inside the printable window of one A4 page, so its 1:1 template prints on a single page."""
    if 'fabrication' in cfg:
        m=cfg['stock_margin']
        return cnc_rules(cfg['nest_spacing'],m)
    laser=cfg['laser']
    if t==laser['thickness']:
        m=laser['margin'];a4=laser['a4_window']
        return {'laser':True,'spacing':laser['spacing'],'cell':.5,'window':lambda w,h:tuple(a4) if (w,h)==(210,297) else (m,m,w-m,h-m)}
    m=cfg['stock_margin'];return {'laser':False,'spacing':cfg['nest_spacing'],'cell':2,'window':lambda w,h:(m,m,w-m,h-m)}

def try_place(pid,poly,s):
    # Roof triangles nest head-to-tail; everything else goes on the free-space grid (grid_place).
    if s.get('cnc'):
        # Clamp/lane margin at the sheet's short ends: 10 mm (or the sheet's 'edge'), less for parts nearly as long as the sheet (walls keep
        # the factory edges, battens and pillars get what is left); long parts are placed along the 420 mm side.
        h=max(poly.bounds[2]-poly.bounds[0],poly.bounds[3]-poly.bounds[1]);s['end_margin']=max(0,min(s.get('edge',10),math.floor((s['height']-h)/2/s['cell'])*s['cell']))   # on the placement grid
    return place(poly,s) if pid in ('R01','R06') else grid_place(poly,s)

def placement_order(unit):
    """Largest bounding box first, then the largest outline. Thin rings and long C-shaped sections have little area
    but span most of a sheet: placed early, smaller parts fill round them instead of each opening a sheet of its own
    (two fewer 6 mm sheets than ordering by outline area)."""
    a,b,c,d=unit[2].bounds;return (-(c-a)*(d-b),-unit[2].area)

RESTARTS=22   # perturbed part orders tried besides the planner's own two; the plan with the fewest sheets wins

def cnc_rules(spacing,margin):
    """CNC sheet rules: side margins on the long edges, up to `margin` at the short ends (see try_place)."""
    return {'laser':False,'cnc':True,'spacing':spacing,'cell':1,'edge':margin,'window':lambda w,h:(margin,0,w-margin,h)}

def orders(units):
    """The part orders to try: the planner's (largest box first; longest part first), then RESTARTS box orders with a
    seeded random weight, so near-equal parts swap places. Seeds are fixed, so every build nests the same."""
    import random, stock as planner
    out=[sorted(units,key=order) for order in planner.ORDERS.values()]
    for seed in range(RESTARTS):
        rng=random.Random(seed);weight={u[:2]:rng.uniform(.6,1.4) for u in units}
        out.append(sorted(units,key=lambda u:placement_order(u)[0]*weight[u[:2]]))
    return out

def pack_order(job):
    """One first-fit nest in a given part order with make stock's packer, then its merge pass (the emptiest sheets
    move into free space on the others) and its squeeze pass (the emptiest few sheets re-packed together)."""
    import stock as planner
    t,units,spacing,margin,primary,count,extra=job;rules=cnc_rules(spacing,margin);lookup={u[:2]:u for u in units}
    def repack(part_units):return planner.pack(t,part_units,[],rules,primary,count,fallback=extra)
    sheets=planner.squeeze(t,planner.merge(t,repack(units),lookup),lookup,repack)
    return [{k:v for k,v in s.items() if k in ('thickness','width','height','window','spacing','cell','laser','cnc','edge','items','size')} for s in sheets]

def best_plan(plans):
    """Fewest sheets; among those the most concentrated packing (full sheets and one emptiest sheet)."""
    def used(s):return sum(Polygon(i['outer']).area for i in s['items'])/(s['width']*s['height'])
    return min(plans,key=lambda plan:(len(plan),-round(sum(used(s)**2 for s in plan),6)))

def nest_set(data,selected,prefix,stock):
    """Nest one part set per thickness with the make stock packer (stock.pack, merge and squeeze) in several part
    orders, run in parallel, and keep the plan with the fewest sheets. Primary sheets first while their count lasts, then the
    smallest extra board that holds each overflow part."""
    import stock as planner
    cfg=data['config'];sheets=[];jobs=[]
    for t in sorted((float(k) for k in stock),reverse=True):
        units=[(pid,q+1,Polygon(p['outer'])) for pid,p in data['parts'].items() if p['thickness']==t and p['category'] not in BOUGHT and selected(p) for q in range(p['quantity'])]
        if not units:continue
        spec=stock[f'{t:g}'];primary=planner.skey(spec['primary']);extra=[planner.skey(size) for size in spec['extra']]
        jobs+=[(t,order,cfg['nest_spacing'],cfg['stock_margin'],primary,spec['count'],extra) for order in orders(units)]
    print(f'Nesting {prefix}: {len(jobs)} part orders over {len({j[0] for j in jobs})} thicknesses...',flush=True)
    try:
        from concurrent.futures import ProcessPoolExecutor
        import os
        with ProcessPoolExecutor(max(1,min(len(jobs),(os.cpu_count() or 2)-1))) as pool:plans=list(pool.map(pack_order,jobs))
    except (OSError,ImportError,RuntimeError):plans=[pack_order(j) for j in jobs]   # no process pool here: one by one
    for t in sorted({j[0] for j in jobs},reverse=True):
        mine=[plan for job,plan in zip(jobs,plans) if job[0]==t];spec=stock[f'{t:g}']
        chosen=best_plan(mine);print(f'Nesting {prefix} {t:g} mm: {len(chosen)} sheets (orders gave {sorted(len(p) for p in mine)})',flush=True)
        for j,s in enumerate(chosen,1):
            s['id']=f'{prefix}{t:g}-{j:02}';s['kind']='primary' if s.pop('size')==planner.skey(spec['primary']) else 'extra'
            s['existing_stock']=bool(spec.get('existing')) and s['kind']=='primary'
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
    result={'spacing_mm':cfg['nest_spacing'],'margin_mm':cfg['stock_margin'],'laser':laser,'sheets':sheets,'optional_sheets':optional,'validation':validate(sheets+optional),'existing_6mm_sheets':sum(s['existing_stock'] for s in sheets),'extra_6mm_sheets':sum(s['thickness']==6 and not s['existing_stock'] for s in sheets),'policy':f'A3 plywood only, 3 and 6 mm, grouped by thickness. Parts placed by their true shape; for each thickness the fewest sheets of {RESTARTS+2} part orders (make stock packer and merge). {cfg["nest_spacing"]:g} mm lanes, {cfg["stock_margin"]:g} mm edges; long parts get what is left of the end margin. Fixed walls retain the full 420 mm blank length. Confirm cutter and hold-down requirements with the supplier. No nesting inside openings; furniture is view-only.'}
    (ROOT/'output/nesting.json').write_text(json.dumps(result,indent=2))
    for s in sheets+optional:
        svg(s,data)
        if s['laser']:laser_files(s,data)
        if s.get('cnc'):
            import cnc
            s['operations']=cnc.export(data,s,ROOT/'output/dxf')
    (ROOT/'output/nesting.json').write_text(json.dumps(result,indent=2))
    print('Sheets:',{f'{t:g} mm':sum(s['thickness']==t for s in sheets) for t in sorted({s['thickness'] for s in sheets},reverse=True)},flush=True)

MASK_CELLS=200_000   # sheets up to this many grid cells (A3 has 116 000) place parts by their true footprint
CANDIDATES=40   # grid positions per orientation checked against the real outlines, lowest first
HALF_DIAGONAL=math.sqrt(2)/2
_footprints={}

def footprint(p,g):
    """The grid cells a part covers with its bounding box's lower-left corner on a cell corner: every cell whose centre
    lies within half a cell diagonal of the outline, so every point of the part is in one of them."""
    key=(p.wkb,g)
    if key not in _footprints:
        if len(_footprints)>4000:_footprints.clear()
        a,b,c,d=p.bounds;kw=max(1,math.ceil((c-a)/g-1e-9));kh=max(1,math.ceil((d-b)/g-1e-9))
        xx,yy=np.meshgrid(a+(np.arange(kw)+.5)*g,b+(np.arange(kh)+.5)*g)
        _footprints[key]=contains_xy(p.buffer(g*HALF_DIAGONAL,join_style=2),xx,yy)
    return _footprints[key]

def free_offsets(s,m):
    """Offsets (row, column) where footprint m covers no occupied cell, by FFT cross-correlation with the occupied
    grid. Offsets that would push m past the grid are left out, so the correlation never wraps round."""
    occ=s['occupied'];H,W=occ.shape;kh,kw=m.shape
    if kh>H or kw>W:return None
    if s.get('spectrum') is None:s['spectrum']=np.fft.rfft2(occ.astype(np.float32))
    overlap=np.fft.irfft2(s['spectrum']*np.conj(np.fft.rfft2(m.astype(np.float32),occ.shape)),occ.shape)
    return overlap[:H-kh+1,:W-kw+1]<.5

def grid_place(poly,s):
    """The lowest, then leftmost position on the free-space grid, over the quarter turns. On small sheets the part is
    matched by its true footprint, so it can sit in the hollow of a ring or beside a quarter circle; on large boards,
    where that search is slow, by its bounding box. Every candidate is then checked against the real outlines."""
    occupied=s['occupied'];g=s['cell'];x0,y0,x1,y1=s['window'];shape=bool(s.get('cnc')) and occupied.size<=MASK_CELLS
    integ=None if shape else np.pad(occupied.astype(np.int32).cumsum(0).cumsum(1),((1,0),(1,0)))
    best=None
    for angle,p in orientations(poly):
        _,_,w,h=p.bounds
        if angle>=180 and (not shape or p.area>.98*w*h):continue   # a half turn only helps a shape that is not a box
        if shape:
            ok=free_offsets(s,footprint(p,g))
            if ok is None:continue
            ys,xs=np.where(ok)
        else:
            # Laser sheets pack to the exact cell; jigsaw sheets keep one spare cell of slack.
            slack=0 if s['laser'] or s.get('cnc') else 1
            kw=math.ceil(w/g-1e-9)+slack;kh=math.ceil(h/g-1e-9)+slack
            if kw>occupied.shape[1] or kh>occupied.shape[0]:continue
            ys,xs=np.where(integ[kh:,kw:]-integ[:-kh,kw:]-integ[kh:,:-kw]+integ[:-kh,:-kw]==0)
        if s.get('cnc'):
            margin=s.get('end_margin',10)
            keep=(y0+ys*g>=margin-1e-6)&(y0+ys*g+h<=s['height']-margin+1e-6)
            ys,xs=ys[keep],xs[keep]
        for k in np.lexsort((xs,ys))[:CANDIDATES]:   # repeatable bottom-left order
            x,y=x0+int(xs[k])*g,y0+int(ys[k])*g;pp=affinity.translate(p,x,y)
            if pp.bounds[2]>x1+.01 or pp.bounds[3]>y1+.01:continue
            if any(pp.distance(old)<s['spacing']-.02 for old in s['placed']):continue
            score=(y+h,x+w)
            if best is None or score<best[0]:best=(score,(angle,x,y,pp,pp.buffer(s['spacing']/2,join_style=2)))
            break
    return best[1] if best else None

def update_grid(s,p):
    g=s['cell'];x0,y0,_,_=s['window']
    # A cell is taken when its centre is closer than spacing + half its diagonal to a placed part: then a footprint
    # (or bounding box) that only covers free cells keeps the full spacing.
    buffered=p.buffer(s['spacing']+g*(.75 if s['laser'] else HALF_DIAGONAL),join_style=2);a,b,c,d=buffered.bounds
    nx,ny=s['occupied'].shape[1],s['occupied'].shape[0]
    ix=max(0,math.floor((a-x0)/g));iy=max(0,math.floor((b-y0)/g));jx=min(nx,math.ceil((c-x0)/g)+1);jy=min(ny,math.ceil((d-y0)/g)+1)
    if ix>=jx or iy>=jy:return
    xx,yy=np.meshgrid(x0+np.arange(ix,jx)*g+g/2,y0+np.arange(iy,jy)*g+g/2)
    s['occupied'][iy:jy,ix:jx] |= contains_xy(buffered,xx,yy);s['spectrum']=None

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
    and an R12 DXF with CUT and ENGRAVE_IDS layers."""
    from dxf_r12 import DXF
    w,h=sheet['width'],sheet['height'];d=DXF()
    text=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
          f'<!-- {sheet["id"]}: {w:g} x {h:g} x {sheet["thickness"]:g} mm plywood. Red = cut (hairline). Blue = part IDs, optional light engraving; delete if not wanted. -->',
          '<g id="cut" fill="none" stroke="#FF0000" stroke-width="0.01">'];labels=[]
    for item in sheet['items']:
        p=data['parts'][item['part']]
        for loop in [p['outer']]+p['cuts']:
            pts=[local_point(p,item,*v) for v in loop]
            text.append('<polygon points="'+' '.join(f'{x:.4f},{h-y:.4f}' for x,y in pts)+'"/>');d.polyline(pts,'CUT')
        for hh in p['holes']:
            x,y=local_point(p,item,hh['x'],hh['y']);r=hh['diameter']/2
            text.append(f'<circle cx="{x:.4f}" cy="{h-y:.4f}" r="{r}"/>');d.circle(x,y,r,'CUT')
        x,y=local_point(p,item,p['width']/2,p['height']/2);size=min(2.5,p['width']/4,p['height']/4)
        labels.append(f'<text x="{x:.3f}" y="{h-y+size/3:.3f}" text-anchor="middle" font-family="sans-serif" font-size="{size:.2f}">{item["part"]}</text>')
        d.text(x,y,size,item['part'])
    text+=['</g>','<g id="engrave-ids" fill="#0000FF" stroke="none">']+labels+['</g>','</svg>']
    (ROOT/'output/dxf'/f'{sheet["id"]}-laser.svg').write_text('\n'.join(text))
    d.save(ROOT/'output/dxf'/f'{sheet["id"]}-laser.dxf')

if __name__=='__main__':main()
