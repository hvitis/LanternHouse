"""Plywood purchase optimizer: which sheet sizes to buy, how many, and what they cost.

Nests every plywood piece the house needs on the sheet sizes a supplier sells and prices the purchase. A supplier
profile (ops/suppliers/*.json) lists its offers per thickness (size, price, pieces per pack, grade), the minimum
distance between parts and edge margin of whoever cuts the parts, and the supplier's saw kerf. A board offer may list
the supplier's cutting tiers ("cut into up to 4 pieces" for a price); every even a x b split of the board the tiers
allow then becomes an offer too, each piece the board less the kerfs, so the search also finds the best custom format.
Only the house's construction counts: no furniture, figures, garden scene or woodpile (display only), and no bought
hardware, screws or solid wood strips.

Search, per thickness: one size only (in two part orders), a size that holds every part paired with a smaller one,
all sizes, and the first N sheets of one size; each is a first-fit nest with the project's placement (nest.py), after
which parts of the emptiest sheets move into free space on the others. The cheapest plans are then priced per grade, and every sheet whose parts fit
on cheaper sheets is replaced by them. Packs are bought whole: n sheets cost the cheapest mix of singles and packs.

    plan = optimize(model.build(), load_profile('ops/suppliers/sklejka-krakow.json'))
"""
from __future__ import annotations
import itertools, json, math, os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from shapely.geometry import Polygon
import nest
from model import BOUGHT

ROOT=Path(__file__).resolve().parents[1]
DISPLAY=('Furniture','Accessories','Figures')   # view-only; the garden scene and the woodpile are Furniture
TOP=12   # plans per thickness carried into the price-aware repacking
MIN_FORMAT=100   # narrowest format cut from a board worth offering, mm

def tkey(t):return f'{float(t):g}'
def skey(size):a,b=sorted(size,reverse=True);return f'{a:g}x{b:g}'
def ssize(key):return tuple(sorted((float(v) for v in key.split('x')),reverse=True))
def area(key):a,b=ssize(key);return a*b

# --- supplier profile -------------------------------------------------------------------------------------------

def load_profile(path):
    p=json.loads(Path(path).read_text());check_profile(p);return p

def check_profile(p):
    for k in ('name','spacing_mm','margin_mm','offers'):
        if k not in p:raise ValueError(f'Supplier profile needs "{k}"')
    if p['spacing_mm']<0 or p['margin_mm']<0 or p.get('kerf_mm',0)<0:raise ValueError('Spacing, margin and kerf must not be negative')
    for o in p['offers']:
        if len(o['size'])!=2 or min(o['size'])<=0 or o['price']<0 or o.get('pack',1)<1:raise ValueError(f'Bad offer: {o}')
        if any(c['pieces']<2 or c['price']<0 for c in o.get('cutting',[])):raise ValueError(f'Bad cutting tier: {o}')

def label(o):
    """An offer's name, or one made from its thickness and size."""
    return o.get('name') or f'Sklejka {float(o["thickness"]):g} mm {max(o["size"]):g}x{min(o["size"]):g}'+(f' ({o["pack"]} szt.)' if o.get('pack',1)>1 else '')

def board_formats(p):
    """Formats the supplier saws from its boards: every a x b grid a cutting tier allows, each piece the board less
    (a-1) and (b-1) kerfs, split evenly and rounded down to whole mm, priced per board (one pack of a*b pieces)."""
    k=p.get('kerf_mm',0);out=[]
    for o in p['offers']:
        tiers=sorted(o.get('cutting',[]),key=lambda c:c['pieces'])
        if not tiers:continue
        L,W=sorted(o['size'],reverse=True);seen=set()
        for a in range(1,tiers[-1]['pieces']+1):
            for b in range(1,tiers[-1]['pieces']//a+1):
                n=a*b;size=sorted((math.floor((L-(a-1)*k)/a),math.floor((W-(b-1)*k)/b)),reverse=True)
                if n<2 or size[1]<MIN_FORMAT or tuple(size) in seen:continue
                seen.add(tuple(size));tier=next(c for c in tiers if c['pieces']>=n)
                out.append({'thickness':o['thickness'],'size':size,'price':tier['price'],'pack':n,'grade':o.get('grade'),
                            'name':f'{label(o)}, cięcie na {n} formatek {size[0]}x{size[1]}','url':tier.get('url',o.get('url')),
                            'cut':{'board':[L,W],'grid':[a,b],'kerf':k,'tier':tier.get('name','')}})
    return out

def save_profile(p,path):
    """One offer per line, so a profile stays easy to edit by hand."""
    head={k:v for k,v in p.items() if k!='offers'}
    text=json.dumps(head,ensure_ascii=False,indent=1)[:-2]+',\n "offers": [\n'
    text+=',\n'.join('  '+json.dumps(o,ensure_ascii=False) for o in p['offers'])+'\n ]\n}\n'
    Path(path).write_text(text)

def grades(p):
    """Grades to price, in the profile's order; offers without a grade belong to every grade."""
    found=[o['grade'] for o in p['offers'] if o.get('grade')]
    return list(p.get('grades') or dict.fromkeys(found)) or ['']

def offers(p,grade):
    """{thickness: {size: [(pack, price, offer)]}} for one grade, without sizes beyond the machine's bed."""
    bed=sorted(p['max_sheet_mm'],reverse=True) if p.get('max_sheet_mm') else None
    out={}
    for o in p['offers']+board_formats(p):
        if o.get('grade') and grade and o['grade']!=grade:continue
        size=sorted(o['size'],reverse=True)
        if bed and (size[0]>bed[0] or size[1]>bed[1]):continue
        out.setdefault(tkey(o['thickness']),{}).setdefault(skey(size),[]).append((int(o.get('pack',1)),float(o['price']),dict(o,name=label(o))))
    return out

def buy(n,options):
    """Cheapest way to get at least n sheets from (pack, price, offer) options: (cost, [(offer, units bought)])."""
    best=[(0.0,())]+[None]*n
    for i in range(1,n+1):
        best[i]=min(((price+best[max(0,i-pack)][0],best[max(0,i-pack)][1]+(k,)) for k,(pack,price,_) in enumerate(options)),key=lambda c:c[0])
    cost,picks=best[n];return round(cost,2),[(options[k][2],c) for k,c in sorted(Counter(picks).items())]

def dominated(options,most=60):
    """Sizes no plan needs: a size is dropped when a size at least as large in both directions costs no more for
    every number of sheets up to `most`."""
    cost={k:[buy(n,v)[0] for n in range(1,most+1)] for k,v in options.items()}
    def covers(b,a):return b!=a and all(x>=y for x,y in zip(ssize(b),ssize(a))) and all(x<=y+1e-9 for x,y in zip(cost[b],cost[a]))
    return {a for a in options if any(covers(b,a) for b in options)}

# --- parts ------------------------------------------------------------------------------------------------------

def house_parts(data,thickness_map=None,tools=True):
    """The house's plywood pieces as {thickness: [(part id, copy, outline)]} and the pieces left out, by reason.

    `thickness_map` ({"4": 3}) moves a thickness the supplier lacks onto one it sells (outlines stay as drawn)."""
    tmap={tkey(k):tkey(v) for k,v in (thickness_map or {}).items()}
    units={};left=Counter()
    for pid,p in sorted(data['parts'].items()):
        q=p['quantity']
        if p.get('render_only') or p['category'] in DISPLAY:left['display']+=q;continue
        if p['category'] in BOUGHT:left['bought']+=q;continue
        if p['category']=='Tools' and not tools:left['tools']+=q;continue
        t=tmap.get(tkey(p['thickness']),tkey(p['thickness']))
        units.setdefault(t,[]).extend((pid,k+1,Polygon(p['outer'])) for k in range(q))
    left['hardware']=len(data.get('hardware',[]));left['fasteners']=len(data.get('fasteners',[]))
    return units,dict(left)

# --- nesting ----------------------------------------------------------------------------------------------------

def rules(spacing,margin):
    """CNC sheet rules of nest.py with the supplier's spacing and margin: side margins on the long edges, and up to
    `margin` at the short ends (less for parts as long as the sheet, which keep the factory ends)."""
    return {'laser':False,'cnc':True,'spacing':spacing,'cell':1,'edge':margin,'window':lambda w,h:(margin,0,w-margin,h)}

def new(t,key,r):a,b=ssize(key);s=nest.new_sheet(float(t),b,a,r);s['size']=key;return s

CROWDED=20   # placed parts after which roof triangles are placed like any other part

def place(s,pid,q,poly):
    """nest.try_place on one sheet. Sheets with fewer free grid cells than the part's area are skipped at once (its
    area, not its box: a ring half fits in far fewer cells than its box), and the head-to-tail roof triangle search
    (R01, R06) only runs on sheets with few parts: its candidate grid grows with every placed part, and on a full sheet
    one call can take minutes."""
    if s.get('free') is not None and poly.area/s['cell']**2>s['free']:return False
    found=nest.try_place(pid if len(s['placed'])<CROWDED else '',poly,s)
    if not found:return False
    angle,x,y,pp,bp=found
    s['items'].append({'part':pid,'copy':q,'angle':angle,'x':x,'y':y,'outer':[list(v) for v in pp.exterior.coords[:-1]]})
    s['placed'].append(pp);s['buffer']=bp if s['buffer'] is None else s['buffer'].union(bp);nest.update_grid(s,pp)
    s['free']=int(s['occupied'].size-s['occupied'].sum())
    return True

def fits(poly,key,r):
    """Whether an empty sheet holds the part, in either quarter turn: the same whole-millimetre grid test as
    nest.grid_place (side margins on the long edges; the end margin shrinks for parts as long as the sheet)."""
    a,b,c,d=poly.bounds;w,h=c-a,d-b;L,S=ssize(key);across=math.floor(S-2*r['edge'])
    return any(math.ceil(x-1e-9)<=across and math.ceil(y-1e-9)<=math.floor(L) for x,y in ((w,h),(h,w)))

def pack(t,units,sizes,r,first=None,count=0,fallback=()):
    """First-fit nest. A part goes on the first open sheet with room; else a new sheet: `first` while fewer than
    `count` of it are open, otherwise the smallest of `sizes` that holds the part, otherwise the smallest of `fallback`."""
    sheets=[]
    for pid,q,poly in units:
        if any(place(s,pid,q,poly) for s in sheets):continue
        opened=sum(s['size']==first for s in sheets)
        for key in ([first] if first and opened<count else [])+sorted(sizes,key=area)+sorted(fallback,key=area):
            s=new(t,key,r) if fits(poly,key,r) else None
            if s and place(s,pid,q,poly):sheets.append(s);break
        else:raise ValueError(f'{pid} ({t} mm) fits none of the sheet sizes {sorted(set(sizes)|set(fallback))}')
    return sheets

def used(s):return sum(Polygon(i['outer']).area for i in s['items'])/area(s['size'])

def clone(s):
    c=dict(s);c['items']=list(s['items']);c['placed']=list(s['placed']);c['occupied']=s['occupied'].copy();return c

def merge(t,sheets,lookup):
    """Empty the least used sheets into free space on the others, as long as every one of their parts finds room."""
    changed=True
    while changed and len(sheets)>1:
        changed=False
        for j in sorted(range(len(sheets)),key=lambda j:used(sheets[j])):
            rest=[clone(s) for k,s in enumerate(sheets) if k!=j]
            items=sorted(sheets[j]['items'],key=lambda i:nest.placement_order(lookup[(i['part'],i['copy'])]))
            if all(any(place(s,*lookup[(i['part'],i['copy'])]) for s in rest) for i in items):sheets=rest;changed=True;break
    return sheets

def squeeze(t,sheets,lookup,repack):
    """Re-pack the parts of the 2, 3 or 4 least used sheets together on fresh sheets, in both part orders, and keep it
    when they need fewer sheets; repeat while that saves one. merge() empties one sheet into the others; this joins
    sheets whose free space is too fragmented for that (a few strips on one, balusters on another).
    repack(units) -> sheets nests a part list on new sheets."""
    improved=True
    while improved:
        improved=False
        for k in (2,3,4):
            if len(sheets)<k:break
            worst=sorted(range(len(sheets)),key=lambda j:used(sheets[j]))[:k]
            units=[lookup[(i['part'],i['copy'])] for j in worst for i in sheets[j]['items']]
            for order in ORDERS.values():
                new=repack(sorted(units,key=order))
                if len(new)<k:sheets=[s for j,s in enumerate(sheets) if j not in worst]+new;improved=True;break
            if improved:break
    return sheets

ORDERS={'box':nest.placement_order,'long':lambda u:(-max(u[2].bounds[2]-u[2].bounds[0],u[2].bounds[3]-u[2].bounds[1]),)+nest.placement_order(u)}

def strip(s):
    return {'thickness':s['thickness'],'size':s['size'],'width':s['width'],'height':s['height'],'window':s['window'],'spacing':s['spacing'],'edge':s['edge'],'items':s['items']}

def alone(t,sizes,holds):
    """One size only, in each part order: (thickness, order, label, sizes, first, count)."""
    return [(t,order,f'tylko {k}',[k],None,0) for order in ORDERS for k in sizes if holds([k])]

def candidates(t,sizes,singles,holds):
    """The other price-independent nesting jobs for one thickness, given the sheet counts of `alone`: pairs of a size
    that holds every part with one that does not (a new sheet is the smallest that holds the part), all sizes, and
    1 .. n-1 sheets (at most 4) of a size that needs n sheets alone, followed by the smallest of any size. Two sizes
    that each hold every part nest almost as the smaller one alone, so that pair is left to the repacking."""
    jobs=[(t,'box',f'{a} + {b}',[a,b],None,0) for a,b in itertools.combinations(sizes,2) if holds([a,b]) and not (holds([a]) and holds([b]))]
    if len(sizes)>2 and holds(sizes):jobs.append((t,'box','wszystkie rozmiary',list(sizes),None,0))
    for k,n in singles.items():
        jobs+=[(t,'box',f'{c}× {k} najpierw',list(sizes),k,c) for c in range(1,min(n,5))]
    return jobs

UNITS={};RULES={}
def _init(units,spacing,margin):UNITS.update(units);RULES['r']=rules(spacing,margin)

def _nest(job):
    t,order,label,sizes,first,count=job;r=RULES['r']
    units=sorted(UNITS[t],key=ORDERS[order]);lookup={(pid,q):(pid,q,poly) for pid,q,poly in units}
    try:sheets=pack(t,units,[] if first else sizes,r,first,count,fallback=sizes)
    except ValueError as e:return {'job':job,'error':str(e)}
    sheets=merge(t,sheets,lookup)
    return {'job':job,'label':label,'sheets':[strip(s) for s in sheets]}

def _repack(args):
    """Replace each sheet, emptiest first, by cheaper sheets of one size (or of the smallest that fits each part)
    when they hold all its parts and cost less."""
    t,plan,price=args;r=RULES['r'];lookup={(pid,q):(pid,q,poly) for pid,q,poly in UNITS[t]};out=[]
    for s in plan['sheets']:
        items=sorted((lookup[(i['part'],i['copy'])] for i in s['items']),key=nest.placement_order)
        base=price[s['size']];cheaper=[k for k in price if price[k]<base-1e-9];best=(base,[s])
        for option in [[k] for k in cheaper]+([cheaper] if len(cheaper)>1 else []):
            try:sub=pack(t,items,option,r)
            except ValueError:continue
            cost=sum(price[x['size']] for x in sub)
            if cost<best[0]-1e-9:best=(cost,[strip(x) for x in sub])
        out+=best[1]
    return dict(plan,sheets=out,label=plan['label']+(' + przepakowanie' if len(out)!=len(plan['sheets']) or any(a['size']!=b['size'] for a,b in zip(out,plan['sheets'])) else ''))

# --- plans ------------------------------------------------------------------------------------------------------

def price_plan(plan,options,part_area):
    counts=Counter(s['size'] for s in plan['sheets']);lines=[];cost=0
    for key,n in sorted(counts.items(),key=lambda kv:-area(kv[0])):
        c,picks=buy(n,options[key]);cost+=c
        lines.append({'size':key,'sheets':n,'cost':c,'buy':[{'offer':o,'units':u} for o,u in picks]})
    bought=sum(area(s['size']) for s in plan['sheets'])
    return dict(plan,counts=dict(counts),cost=round(cost,2),lines=lines,bought_m2=bought/1e6,part_m2=part_area/1e6,used=part_area/bought)

def signature(plan):return tuple(sorted(plan['counts'].items()))

def check(plan,units):
    """Every piece placed once, inside its sheet with the edge margin rules, and at least `spacing` from the others."""
    problems=[];want=Counter((pid,q) for pid,q,_ in units);got=Counter((i['part'],i['copy']) for s in plan['sheets'] for i in s['items'])
    if want!=got:problems.append(f'pieces placed {sum(got.values())}, needed {sum(want.values())}')
    for n,s in enumerate(plan['sheets'],1):
        x0,_,x1,_=s['window'];polys=[Polygon(i['outer']) for i in s['items']]
        for p in polys:
            a,b,c,d=p.bounds
            if a<x0-.01 or c>x1+.01 or b<-.01 or d>s['height']+.01:problems.append(f'sheet {n}: a part leaves the sheet')
        for i,p in enumerate(polys):
            for q in polys[i+1:]:
                if p.distance(q)<s['spacing']-.05:problems.append(f'sheet {n}: parts {p.distance(q):.1f} mm apart')
    return problems

def summary(res):
    """The result without the layouts of the variants that lost: settings, recommendations with their sheets, and
    every variant's sheet counts, cost and covered area."""
    def short(p):return {'label':p['label'],'counts':p['counts'],'sheets':len(p['sheets']),'cost':p['cost'],'bought_m2':p['bought_m2'],'used':p['used']}
    def full(p):return dict(short(p),lines=p['lines'],layout=p['sheets'])
    return {k:v for k,v in res.items() if k not in ('grades','offers')}|{'grades':{g:{k:v for k,v in G.items() if k!='thickness'}|{'thickness':{t:{
        'best':full(T['best']),'simple':full(T['simple']),'densest':short(T['densest']),'single':{k:short(p) for k,p in T['single'].items()},'variants':[short(p) for p in T['plans']]}
        for t,T in G['thickness'].items()}} for g,G in res['grades'].items()}}

def optimize(data,profile,workers=None,progress=print):
    """Every plan per grade and thickness, cheapest first; see the module docstring."""
    check_profile(profile)
    units,left=house_parts(data,profile.get('thickness_map'),profile.get('include_tools',True))
    gl=grades(profile);by_grade={g:offers(profile,g) for g in gl}
    missing=sorted({t for t in units for g in gl if not by_grade[g].get(t)},key=float)
    if missing:raise ValueError(f'No offers for {", ".join(missing)} mm; add prices or map the thickness to another one')
    part_area={t:sum(p.area for _,_,p in u) for t,u in units.items()};r=rules(profile['spacing_mm'],profile['margin_mm'])
    # Search sizes: every size some grade does not beat with a larger sheet at the same or a lower price.
    sizes={t:sorted({k for g in gl for k in set(by_grade[g][t])-dominated(by_grade[g][t])},key=area) for t in units}
    dropped={t:sorted({k for g in gl for k in by_grade[g][t]}-set(sizes[t]),key=area) for t in units}
    def holder(t):return lambda keys:all(any(fits(poly,k,r) for k in keys) for _,_,poly in units[t])
    for t in units:
        if not holder(t)(sizes[t]):raise ValueError(f'No {t} mm sheet size holds every part: add a larger size')
    workers=workers or max(1,(os.cpu_count() or 2)-1)
    with ProcessPoolExecutor(workers,initializer=_init,initargs=(units,profile['spacing_mm'],profile['margin_mm'])) as pool:
        jobs=[j for t in units for j in alone(t,sizes[t],holder(t))]
        progress(f'Układanie na pojedynczych rozmiarach: {len(jobs)} wariantów ({", ".join(f"{t} mm" for t in sorted(units,key=float))})...')
        nested=[n for n in pool.map(_nest,jobs) if 'error' not in n]
        # Sheets per size when used alone, so "N sheets of one size first" stops below that count.
        counts={t:{} for t in units}
        for n in nested:counts[n['job'][0]][n['job'][3][0]]=min(len(n['sheets']),counts[n['job'][0]].get(n['job'][3][0],99))
        jobs=[j for t in units for j in candidates(t,sizes[t],counts[t],holder(t))]
        progress(f'Układanie mieszanek rozmiarów: {len(jobs)} wariantów...')
        nested+=[n for n in pool.map(_nest,jobs,chunksize=2) if 'error' not in n]
        result={'supplier':{k:v for k,v in profile.items() if k!='offers'},'left_out':left,'grades':{},'searched':{t:sizes[t] for t in units},'dropped':dropped,'variants':len(nested),
                'parts':{t:{'pieces':len(u),'profiles':len({pid for pid,_,_ in u}),'area_m2':part_area[t]/1e6} for t,u in units.items()}}
        for g in gl:
            progress(f'Ceny i przepakowanie, klasa {g or "-"}...')
            plans={t:[] for t in units};todo=[]
            for t in units:
                opts=by_grade[g][t];unit={k:buy(1,v)[0] for k,v in opts.items()}
                priced=[price_plan(p,opts,part_area[t]) for p in nested if p['job'][0]==t and all(s['size'] in opts for s in p['sheets'])]
                priced.sort(key=lambda p:(p['cost'],-p['used']));plans[t]=priced
                todo+=[(t,p,unit) for p in priced[:TOP]]
            for (t,_,_),p in zip(todo,pool.map(_repack,todo)):plans[t].append(price_plan(p,by_grade[g][t],part_area[t]))
            grade={}
            for t in sorted(units,key=float):
                seen={}
                for p in sorted(plans[t],key=lambda p:(p['cost'],-p['used'],len(p['sheets']))):seen.setdefault(signature(p),p)
                ranked=list(seen.values());best=ranked[0]
                single={k:min((p for p in ranked if set(p['counts'])=={k}),key=lambda p:p['cost'],default=None) for k in sizes[t] if k in by_grade[g][t]}
                simple=min((p for p in ranked if len(p['counts'])<=2),key=lambda p:(p['cost'],-p['used']))
                problems=check(best,units[t])+check(simple,units[t])
                if problems:raise AssertionError(f'{t} mm plan failed its check: {problems[:3]}')
                grade[t]={'best':best,'simple':simple,'densest':max(ranked,key=lambda p:(p['used'],-p['cost'])),'plans':ranked,'single':{k:v for k,v in single.items() if v}}
            total=sum(v['best']['cost'] for v in grade.values());bought=sum(v['best']['bought_m2'] for v in grade.values())
            result['grades'][g]={'thickness':grade,'cost':round(total,2),'bought_m2':bought,'part_m2':sum(part_area.values())/1e6,'used':sum(part_area.values())/1e6/bought}
    result['offers']=[dict(o,name=label(o),zl_m2=o['price']/(o.get('pack',1)*o['size'][0]*o['size'][1]/1e6)) for o in profile['offers']+board_formats(profile)]
    return result
