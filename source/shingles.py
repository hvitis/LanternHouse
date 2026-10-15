"""Roof shingle strips that fit the round roof.

The roof is a 12-facet cone. A level course of tiles is straight on each flat facet but turns at every hip, so
a straight paper strip cannot follow it. Each strip here is one course unrolled flat (the development of the
cone): it bends by the facet angle at each hip, where it is creased, and is cut along the hips at its ends.
Low courses are split into pieces of one or two panels; higher, shorter courses wrap more panels in one piece.

Geometry is in mm. Panel coordinates (x along the eave, y up the slope) are those of the R01/R06 profiles;
the development has the cone apex at its origin. Panels are numbered 1-12 from the dormer panel R06, to the
right as seen from outside (anticlockwise from above)."""
import math,random

VIS,GLUE=9.0,5.0          # visible height of a tile course and the glue band hidden under the next course
GAP=2.0                    # cutting gap between strips on the page
TONES=['#C2493F','#B54239','#CF5A4E','#BB4E44','#C9564A']

def hull(points):
    pts=sorted(set((round(x,3),round(y,3)) for x,y in points))
    if len(pts)<3:return pts
    def half(seq):
        out=[]
        for p in seq:
            while len(out)>=2 and (out[-1][0]-out[-2][0])*(p[1]-out[-2][1])-(out[-1][1]-out[-2][1])*(p[0]-out[-2][0])<=0:out.pop()
            out.append(p)
        return out
    return half(pts)[:-1]+half(pts[::-1])[:-1]

def inside(x,y,poly):
    hit=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit

def dot(a,b):return sum(a[k]*b[k] for k in range(3))

class Roof:
    def __init__(self,data):
        P=data['parts'];o=P['R01']['outer'];self.outline=o
        self.rw=o[1][0];self.H=o[2][1];self.tw=abs(o[2][0]-o[3][0]);self.t=P['R01']['thickness']
        self.apex=self.H*self.rw/(self.rw-self.tw);self.alpha=2*math.atan(self.rw/2/self.apex)
        insts=[i for i in data['instances'] if i['part'] in ('R01','R06')]
        angle=lambda i:math.degrees(math.atan2(-i['u'][0],i['u'][1]))
        start=angle(next(i for i in insts if i['part']=='R06'))
        self.panels=sorted(insts,key=lambda i:(angle(i)-start)%360)
        # The R03 top cap covers the cone tip: courses stop where it begins.
        cap=next(i for i in data['instances'] if i['part']=='R03');co=P['R03']['outer']
        cx=sum(x for x,_ in co)/len(co);cy=sum(y for _,y in co)/len(co);capr=max(math.hypot(x-cx,y-cy) for x,y in co)
        v=self.panels[0]['v'];self.cap=capr/math.hypot(v[0],v[1])
        self.rows=[k for k in range(200) if k*VIS<self.H-self.cap]
        self.holes=self.footprints(data)

    def xl(self,y):return (self.rw-self.tw)/2*y/self.H
    def width(self,y):return self.rw-2*self.xl(y)

    def footprints(self,data):
        """Where the dormer and the chimney stand on the roof skin: slice their plates just above each panel's
        outer face and take the convex hull, in that panel's coordinates."""
        P=data['parts'];out={}
        for f,pan in enumerate(self.panels):
            O,u,v,w=pan['origin'],pan['u'],pan['v'],pan['w']
            for name,prefix in (('dormer','DM'),('chimney','CH')):
                pts=[]
                for inst in data['instances']:
                    if not inst['part'].startswith(prefix):continue
                    p=P[inst['part']];corners=[]
                    for c in (0,p['thickness']):
                        corners.append([[inst['origin'][k]+inst['u'][k]*a+inst['v'][k]*b+inst['w'][k]*c for k in range(3)] for a,b in p['outer']])
                    s=lambda X:dot([X[k]-O[k] for k in range(3)],w)-self.t-.25
                    edges=[(q[j],q[(j+1)%len(q)]) for q in corners for j in range(len(q))]+list(zip(corners[0],corners[1]))
                    for a,b in edges:
                        sa,sb=s(a),s(b)
                        if (sa<0)!=(sb<0):
                            t=sa/(sa-sb);X=[a[k]+(b[k]-a[k])*t for k in range(3)]
                            x,y=dot([X[k]-O[k] for k in range(3)],u),dot([X[k]-O[k] for k in range(3)],v)
                            if inside(x,y,self.outline):pts.append((x,y))
                if len(pts)>=3:out.setdefault(f,[]).append((name,hull(pts)))
        return out

    def course(self,k):
        """One facet's share of course k in panel coordinates: tiles, scalloped lower edge and outline."""
        y0=k*VIS;yt=min(y0+VIS+GLUE,self.H);yc=y0+VIS/2
        w=self.width(yc);n=max(1,round(w/VIS));p=w/n;r=p/2;x0=self.xl(yc)
        # Courses alternate: whole tiles meeting at the hips, then tiles centred on the hips (halves either side).
        centres=[x0+(j+.5)*p for j in range(n)] if k%2 else [x0+j*p for j in range(n+1)]
        def bottom(x):
            d=min(min(abs(x-c) for c in centres),r);return y0+r-math.sqrt(r*r-d*d)
        def hip(side):
            x=self.xl(y0) if side<0 else self.rw-self.xl(y0)
            for _ in range(5):x=self.xl(bottom(x)) if side<0 else self.rw-self.xl(bottom(x))
            return x
        xa,xb=hip(-1),hip(1)
        cuts=sorted({xa,xb}|{(a+b)/2 for a,b in zip(centres,centres[1:]) if xa<(a+b)/2<xb})
        lower=[]
        for a,b in zip(cuts,cuts[1:]):
            for i in range(12):x=a+(b-a)*i/12;lower.append((x,bottom(x)))
        lower.append((xb,bottom(xb)))
        top=[(self.xl(yt),yt),(self.rw-self.xl(yt),yt)]
        return {'k':k,'y0':y0,'yt':yt,'r':r,'p':p,'centres':centres,'lower':lower,'top':top,'outline':top+lower[::-1]}

    def to_dev(self,t,m,pt):
        """Panel point of the t-th of m facets in a strip -> development coordinates, strip centred on the y axis."""
        th=(t-(m-1)/2)*self.alpha;x,y=pt[0]-self.rw/2,pt[1]-self.apex
        return (x*math.cos(th)-y*math.sin(th),x*math.sin(th)+y*math.cos(th))

    def strip(self,k,start,m):
        cs=self.course(k);facets=[]
        for t in range(m):
            f=(start+t)%12
            holes=[(name,poly) for name,poly in self.holes.get(f,[]) if min(y for _,y in poly)<cs['yt'] and max(y for _,y in poly)>cs['y0']]
            facets.append({'t':t,'facet':f,'holes':holes})
        top=[self.to_dev(t,m,cs['top'][0]) for t in range(m)]+[self.to_dev(m-1,m,cs['top'][1])]
        lower=[q for t in range(m-1,-1,-1) for q in (self.to_dev(t,m,p) for p in cs['lower'][::-1])]
        poly=top+lower
        xs=[x for x,_ in poly];ys=[y for _,y in poly]
        return {'row':k+1,'start':start,'m':m,'course':cs,'facets':facets,'poly':poly,'bbox':(min(xs),min(ys),max(xs),max(ys))}

def strips(data,max_w=186.0,max_h=110.0):
    """All strips, eave course first. Each course uses the largest whole number of panels per strip (a divisor
    of 12) that still fits the page; seams move half a strip along from one course to the next."""
    roof=Roof(data);out=[]
    for k in roof.rows:
        for m in (12,6,4,3,2,1):
            s=roof.strip(k,0,m);x0,y0,x1,y1=s['bbox']
            if x1-x0<=max_w and y1-y0<=max_h:break
        shift=(k%2)*(m//2 if m>1 else 0)
        out+=[roof.strip(k,(shift+q*m)%12,m) for q in range(12//m)]
    return roof,out

def profiles(poly,step=.5):
    """Lowest and highest y of a polygon in each 0.5 mm column, from its left edge."""
    x0=min(x for x,_ in poly);x1=max(x for x,_ in poly);n=int(math.ceil((x1-x0)/step))+1;lo=[math.inf]*n;hi=[-math.inf]*n
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia,ib=sorted(((a[0]-x0)/step,(b[0]-x0)/step))
        for i in range(max(0,int(math.floor(ia))),min(n-1,int(math.ceil(ib)))+1):
            if b[0]==a[0]:y=(a[1],b[1])
            else:
                t=min(1,max(0,(x0+i*step-a[0])/(b[0]-a[0])));y=(a[1]+(b[1]-a[1])*t,)
            lo[i]=min(lo[i],*y);hi[i]=max(hi[i],*y)
    return lo,hi

def turn(poly,angle):
    c,s=round(math.cos(math.radians(angle))),round(math.sin(math.radians(angle)))
    return [(x*c-y*s,x*s+y*c) for x,y in poly]

def pack(items,width,height,gap=GAP,step=.5,key=lambda s:(-s['m'],s['row']%2,s['row'],s['start'])):
    """Skyline packing of the curved strips on pages width x height (mm). The largest strips go first; strips of
    one size come in alternate courses, so each can nest inside the one two courses below (18 mm smaller radius).
    Single-panel strips stand on end; every strip takes the first page with room. Returns pages of
    (strip, x, y, angle): the strip turned by angle about its development origin, which lands at (x, y)."""
    cols=int(width/step);reach=int(math.ceil(gap/step));pages=[];skies=[]
    order=sorted(items,key=key)
    for s in order:
        shapes=[]
        # Single-panel strips are wider than half the page: stood on end they pack side by side.
        for angle in ((90,270) if s['m']==1 else (0,180)):
            poly=turn(s['poly'],angle);lo,hi=profiles(poly,step)
            if len(lo)<=cols:shapes.append((angle,min(x for x,_ in poly),min(y for _,y in poly),max(y for _,y in poly),lo,hi))
        if not shapes:raise ValueError(f'Shingle strip of course {s["row"]} does not fit the page')
        best=None
        for p,sky in enumerate(skies+[[0.0]*cols]):
            for angle,x0,y0,y1,lo,hi in shapes:
                n=len(lo)
                for off in range(0,cols-n+1,2):
                    base=max(sky[off+i]-(lo[i]-y0) for i in range(n))
                    if base+(y1-y0)<=height and (best is None or (p,base+(y1-y0))<best[0]):best=((p,base+(y1-y0)),p,angle,off,base,x0,y0,lo,hi)
            if best:break
        _,p,angle,off,base,x0,y0,lo,hi=best
        if p==len(skies):skies.append([0.0]*cols);pages.append([])
        sky=skies[p]
        for i in range(len(lo)):
            top=base+(hi[i]-y0)+gap
            for j in range(max(0,off+i-reach),min(cols,off+i+reach+1)):sky[j]=max(sky[j],top)
        pages[p].append((s,off*step-x0,base-y0,angle))
    return pages

def _mask(poly,step):
    """Filled raster of a polygon (shifted to its own corner) at `step` mm per cell, rows = y."""
    from PIL import Image, ImageDraw
    import numpy as np
    x0=min(x for x,_ in poly);y0=min(y for _,y in poly)
    w=int(math.ceil((max(x for x,_ in poly)-x0)/step))+2;h=int(math.ceil((max(y for _,y in poly)-y0)/step))+2
    im=Image.new('1',(w,h),0);ImageDraw.Draw(im).polygon([((x-x0)/step+.5,(y-y0)/step+.5) for x,y in poly],fill=1,outline=1)
    return np.array(im,dtype=bool),x0,y0

def pack_raster(items,width,height,gap=GAP,step=.5):
    """First-fit raster packing: the curved strips drop into the hollows under their neighbours' arcs, which a
    column skyline cannot reach. Every orientation is tried on every open page; a strip goes to the lowest,
    then leftmost, free spot of the first page it fits. Same result format as pack()."""
    import numpy as np
    W,H=int(width/step),int(height/step);grow=int(math.ceil(gap/step))
    def dilate(m):
        out=m.copy()
        for _ in range(grow):
            g=out.copy();g[1:]|=out[:-1];g[:-1]|=out[1:];g[:,1:]|=out[:,:-1];g[:,:-1]|=out[:,1:];out=g
        return out
    pages=[];occ=[];order=sorted(items,key=lambda s:-(s['bbox'][2]-s['bbox'][0])*(s['bbox'][3]-s['bbox'][1]))
    for s in order:
        shapes=[]
        for angle in (0,90,180,270):
            poly=turn(s['poly'],angle);m,x0,y0=_mask(poly,step)
            if m.shape[0]<=H and m.shape[1]<=W:shapes.append((angle,m,x0,y0))
        if not shapes:raise ValueError(f'Shingle strip of course {s["row"]} does not fit the page')
        placed=None
        for p in range(len(occ)+1):
            grid=occ[p] if p<len(occ) else np.zeros((H,W),bool);F=np.fft.rfft2(grid.astype(float))
            best=None
            for angle,m,x0,y0 in shapes:
                k=np.zeros((H,W));k[:m.shape[0],:m.shape[1]]=m
                hits=np.fft.irfft2(F*np.conj(np.fft.rfft2(k)),s=(H,W))[:H-m.shape[0]+1,:W-m.shape[1]+1]
                free=np.argwhere(hits<.5)
                if len(free):
                    oy,ox=free[np.lexsort((free[:,1],free[:,0]))[0]]
                    if best is None or (oy+m.shape[0],ox)<(best[0][0],best[0][1]):best=((oy+m.shape[0],ox),angle,m,x0,y0,oy,ox)
            if best:placed=(p,best);break
        p,(_,angle,m,x0,y0,oy,ox)=placed
        if p==len(occ):occ.append(np.zeros((H,W),bool));pages.append([])
        block=np.zeros((H,W),bool);block[oy:oy+m.shape[0],ox:ox+m.shape[1]]=m;occ[p]|=dilate(block)
        pages[p].append((s,ox*step-x0,oy*step-y0,angle))
    return pages

def best_pack(items,width,height,gap=GAP):
    """The packing with fewer pages, after an exact check that no two strips on a page come closer than the gap."""
    from shapely.geometry import Polygon
    from shapely import affinity
    options=[pack(items,width,height,gap)]
    try:options.append(pack_raster(items,width,height,gap))
    except ValueError:pass
    for pages in sorted(options,key=len):
        ok=True
        for page in pages:
            polys=[affinity.translate(Polygon(turn(s['poly'],a)),x,y) for s,x,y,a in page]
            if any(p.bounds[0]<-.01 or p.bounds[1]<-.01 or p.bounds[2]>width+.01 or p.bounds[3]>height+.01 for p in polys):ok=False;break
            if any(polys[i].distance(polys[j])<gap-.3 for i in range(len(polys)) for j in range(i+1,len(polys))):ok=False;break
        if ok:return pages
    return options[0]
