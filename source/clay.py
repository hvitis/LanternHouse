"""Moomin family as thermo-clay (oven-hardening polymer clay) figures.

Each figure is a smooth union of rounded lumps (signed distance functions), the way clay pieces are
pressed together. A surface-nets mesh of the zero level gives the 3D shape for the viewer, the CAD
solid and the book renders; counting grid points inside gives the clay volume per colour.
Local frame: feet flat on z=0, snout toward +x, y to the figure's left. Pure numpy, millimetres.
"""
from __future__ import annotations
import base64, json, math
from functools import lru_cache
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'source/config.json').read_text())
NAMES={'pappa':'Moominpappa','mamma':'Moominmamma','troll':'Moomintroll'}
WHITE,BLACK,APRON=0,1,2
COLOURS={'white':'#F1EDE4','black':'#2B2B2E','red':'#C8443B'}
STRIPE=2.2   # apron stripe width, design units

def _rot(rx=0,ry=0,rz=0):
    a,b,c=(math.radians(v) for v in (rx,ry,rz))
    X=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Y=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Z=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    return Z@Y@X

# ---------- primitives: each returns a function P(...,3) -> signed distance (design units) ----------
# Each also records its lump size (f.dims) for the modelling list and its parameters (f.spec) for the CAD solid.
def _sized(f,*dims,spec=None):f.dims=dims;f.spec=spec;return f
def ellipsoid(c,r,rot=(0,0,0)):
    c=np.array(c,float);r=np.array(r,float);R=_rot(*rot)
    def f(P):
        q=(P-c)@R;k0=np.linalg.norm(q/r,axis=-1);k1=np.linalg.norm(q/(r*r),axis=-1)
        return k0*(k0-1)/np.maximum(k1,1e-9)
    return _sized(f,*sorted(2*r,reverse=True),spec=('ellipsoid',c.tolist(),r.tolist(),R.tolist()))
def sphere(c,r):
    c=np.array(c,float);return _sized(lambda P:np.linalg.norm(P-c,axis=-1)-r,2*r,spec=('ellipsoid',c.tolist(),[r]*3,np.eye(3).tolist()))
def capsule(a,b,ra,rb=None):
    a=np.array(a,float);b=np.array(b,float);ab=b-a;rb=ra if rb is None else rb
    def f(P):
        t=np.clip(((P-a)@ab)/(ab@ab),0,1)
        return np.linalg.norm(P-a-t[...,None]*ab,axis=-1)-(ra+(rb-ra)*t)
    return _sized(f,2*max(ra,rb),float(np.linalg.norm(ab))+ra+rb,spec=('capsule',a.tolist(),b.tolist(),ra,rb))
def cylinder(c,r,h,round_=.5):
    """Upright cylinder, centre c, radius r, half-height h, edges rounded."""
    c=np.array(c,float)
    def f(P):
        q=P-c;dx=np.hypot(q[...,0],q[...,1])-r+round_;dz=np.abs(q[...,2])-h+round_
        return np.minimum(np.maximum(dx,dz),0)+np.hypot(np.maximum(dx,0),np.maximum(dz,0))-round_
    return _sized(f,2*r,2*h,spec=('cylinder',c.tolist(),r,h,round_))
def box(c,half,round_=1.0):
    c=np.array(c,float);half=np.array(half,float)
    def f(P):
        q=np.abs(P-c)-half+round_
        return np.linalg.norm(np.maximum(q,0),axis=-1)+np.minimum(q.max(-1),0)-round_
    return _sized(f,*(2*half),spec=('box',c.tolist(),half.tolist(),round_))
def handle(c,R,r):
    """Upper half of a ring in the xz plane: a bag handle."""
    c=np.array(c,float)
    def f(P):
        q=P-c;return np.maximum(np.hypot(np.hypot(q[...,0],q[...,2])-R,q[...,1])-r,-q[...,2])
    return _sized(f,2*r,2*R,spec=('handle',c.tolist(),R,r))

def smin(a,b,k):
    if k<=0:return np.minimum(a,b)
    h=np.clip(.5+.5*(b-a)/k,0,1);return b*(1-h)+a*h-k*h*(1-h)

# ---------- the family ----------
def _troll(ears=True):
    """Ops: (sdf, material, blend, lump name). Moomintroll's body; the parents reuse it at a larger scale."""
    ops=[(ellipsoid((0,0,15.5),(13.5,13,13)),WHITE,0,'body egg'),
         (ellipsoid((.5,0,25.5),(11.5,11,10.5)),WHITE,4,'chest'),
         (ellipsoid((.5,0,36.5),(10.8,10.4,10.6)),WHITE,4,'head ball'),
         (ellipsoid((11.5,0,35),(10.5,8.4,7.4),(0,6,0)),WHITE,3,'snout')]
    for s in (1,-1):
        ops+=[(capsule((0,6*s,10.5),(1,6.3*s,3.4),4.4),WHITE,2,'legs'),
              (ellipsoid((3,6.3*s,2.4),(6.2,4,2.6)),WHITE,1.5,'feet'),
              (capsule((2.5,10.6*s,27),(7,13.4*s,18.6),2.5),WHITE,1.6,'arms'),
              (sphere((7.4,13.7*s,17.6),3.0),WHITE,1,'hands')]
    ops+=[(capsule((-12,0,10),(-23.5,0,2.6),2.0,1.6),WHITE,1.4,'tail'),       # resting on the floor
          (ellipsoid((-25.5,0,3.2),(3.4,2.7,3.0)),WHITE,.8,'tuft')]
    if ears:
        for s in (1,-1):ops.append((ellipsoid((-2.5,4.3*s,47.4),(2.4,1.9,4.6),(12*s,-10,0)),WHITE,1.2,'ears'))
    for s in (1,-1):ops.append((ellipsoid((12.6,3.7*s,40.6),(1.3,1.45,2.5),(0,-28,0)),BLACK,0,'eyes'))
    return ops

def _apron(P,body):
    """1 mm thick striped apron pressed onto Mamma's front, from hip to chest."""
    region=np.maximum.reduce([3-P[...,0],6.5-P[...,2],P[...,2]-26.5])
    return np.maximum(body-1.0,region)

DESIGNS={
  # name: (target height mm from config figures.heights, extra ops, torso apron?)
  'troll':(CFG['figures']['heights']['troll'],lambda:_troll(),False),
  'mamma':(CFG['figures']['heights']['mamma'],lambda:_troll()+[(box((9.4,-15.4,10.2),(5.4,2.1,3.6),1.2),BLACK,.4,'handbag'),(handle((9.4,-15.4,13.4),2.6,.6),BLACK,.3,'handle')],True),
  'pappa':(CFG['figures']['heights']['pappa'],lambda:_troll(ears=False)+[(cylinder((.5,0,45.8),11.6,.8,.5),BLACK,.6,'hat brim'),(cylinder((.5,0,53.6),7.6,7.8,.9),BLACK,.3,'hat crown')],False),
}

def _design_field(name,P):
    _,make,apron=DESIGNS[name];ops=make()
    d=ops[0][0](P);mat=np.full(P.shape[:-1],ops[0][1],np.int8);torso=None
    for k,(f,m,blend,_) in enumerate(ops[1:],1):
        di=f(P);mat[di<d]=m;d=smin(d,di,blend)
        if k==1:torso=d.copy()
    if apron:
        da=_apron(P,torso);mat[da<d]=APRON;d=np.minimum(d,da)
    return np.maximum(d,-P[...,2]),mat   # flat underside so it stands

@lru_cache(None)
def scale(name):
    """Design-to-mm factor so the figure's top lands at its target height."""
    g=np.mgrid[-30:30:.4,-20:20:.4,0:70:.4].transpose(1,2,3,0)
    d,_=_design_field(name,g);top=g[d<0][:,2].max()
    i=np.argwhere(d<0);j=i[np.argmax(g[d<0][:,2])];x,y=g[tuple(j)][:2];lo,hi=top,top+.5
    for _ in range(40):
        mid=(lo+hi)/2;inside=_design_field(name,np.array([[x,y,mid]]))[0][0]<0;lo,hi=(mid,hi) if inside else (lo,mid)
    return DESIGNS[name][0]/lo

def field(name,P):
    """Signed distance (mm, negative inside) and material id at points P (..., 3) in the figure frame."""
    s=scale(name);d,mat=_design_field(name,np.asarray(P,float)/s);return d*s,mat

def gradient(name,P,eps=.02):
    g=np.zeros_like(P)
    for k in range(3):
        e=np.zeros(3);e[k]=eps;g[:,k]=(field(name,P+e)[0]-field(name,P-e)[0])/(2*eps)
    return g

@lru_cache(None)
def _grid(name,step):
    """Signed distances on a grid that covers the figure with one empty cell all round."""
    s=scale(name);lo=np.array([-30,-20,-.5])*s;hi=np.array([30,20,70])*s
    coarse=np.mgrid[lo[0]:hi[0]:1.5,lo[1]:hi[1]:1.5,lo[2]:hi[2]:1.5].transpose(1,2,3,0)
    pts=coarse[field(name,coarse)[0]<1.5]
    lo=np.floor((pts.min(0)-3)/step)*step;lo[2]=-2*step;hi=pts.max(0)+3
    axes=[np.arange(lo[k],hi[k]+step,step) for k in range(3)]
    G=np.stack(np.meshgrid(*axes,indexing='ij'),-1);d,mat=field(name,G)
    return G,d,mat

CORNERS=np.array([(i,j,k) for k in (0,1) for j in (0,1) for i in (0,1)])
EDGES=[(a,b) for a in range(8) for b in range(8) if a<b and np.abs(CORNERS[a]-CORNERS[b]).sum()==1]

TETS=[(0,1,3,7),(0,3,2,7),(0,2,6,7),(0,6,4,7),(0,4,5,7),(0,5,1,7)]   # Kuhn split: neighbours share diagonals
def _tet_table():
    table={}
    for code in range(1,15):
        S=[c for c in range(4) if code>>c&1];O=[c for c in range(4) if c not in S]
        if len(S) in (1,3):
            a=S[0] if len(S)==1 else O[0];r=[c for c in range(4) if c!=a];table[code]=[[(a,r[0]),(a,r[1]),(a,r[2])]]
        else:
            (a,b),(c,d)=S,O;table[code]=[[(a,c),(a,d),(b,d)],[(a,c),(b,d),(b,c)]]
    return table

def _active(inside):
    n=np.array(inside.shape);code=np.zeros(n-1,np.int16)
    for bit,(i,j,k) in enumerate(CORNERS):code|=inside[i:n[0]-1+i,j:n[1]-1+j,k:n[2]-1+k].astype(np.int16)<<bit
    return code,(code>0)&(code<255)

def _nets(G,d,step):
    """Surface nets: one vertex per crossed cell, one quad per crossed grid edge. Regular, light meshes
    for display; an ambiguous saddle face can pinch an edge, so volumes and CAD use _tetra."""
    inside=d<0;n=np.array(d.shape);code,active=_active(inside)
    cells=np.argwhere(active);vid=np.full(n-1,-1,np.int64);vid[active]=np.arange(len(cells))
    acc=np.zeros((len(cells),3));cnt=np.zeros(len(cells))
    for a,b in EDGES:
        fa=d[tuple((cells+CORNERS[a]).T)];fb=d[tuple((cells+CORNERS[b]).T)];x=(fa<0)!=(fb<0)
        t=fa[x]/(fa[x]-fb[x]);acc[x]+=CORNERS[a]+t[:,None]*(CORNERS[b]-CORNERS[a]);cnt[x]+=1
    V=G[0,0,0]+(cells+acc/cnt[:,None])*step
    faces=[]
    for ax in range(3):
        o=[(ax+1)%3,(ax+2)%3]
        sl=[slice(None)]*3;sl[ax]=slice(0,n[ax]-1);s0=inside[tuple(sl)];sl[ax]=slice(1,n[ax]);s1=inside[tuple(sl)]
        e=np.argwhere(s0!=s1)
        e=e[(e[:,o[0]]>0)&(e[:,o[1]]>0)&(e[:,o[0]]<n[o[0]]-1)&(e[:,o[1]]<n[o[1]]-1)]
        quads=[]
        for du,dv in ((0,0),(1,0),(1,1),(0,1)):
            c=e.copy();c[:,o[0]]-=1-du;c[:,o[1]]-=1-dv;quads.append(vid[tuple(c.T)])
        q=np.stack(quads,1);faces+=[q[:,[0,1,2]],q[:,[0,2,3]]]
    return V,np.concatenate(faces)

def _tetra(G,d,step):
    """Marching tetrahedra on the Kuhn split of every cube: always a closed 2-manifold."""
    inside=(d<0).ravel();f=d.ravel();P=G.reshape(-1,3);n=d.shape;_,active=_active(d<0)
    base=np.ravel_multi_index(np.argwhere(active).T,n);off=np.array([np.ravel_multi_index(tuple(c),n) for c in CORNERS])
    table=_tet_table();edges=[]
    for tet in TETS:
        g=base[:,None]+off[list(tet)][None,:];code=inside[g]@np.array([1,2,4,8])
        for c,tris in table.items():
            sel=g[code==c]
            for tri in tris:edges.append(np.stack([np.stack([sel[:,a],sel[:,b]],-1) for a,b in tri],1))
    E=np.concatenate(edges);lo,hi=E.min(-1),E.max(-1);keys=lo*P.shape[0]+hi
    uniq,inv=np.unique(keys.ravel(),return_inverse=True);a,b=uniq//P.shape[0],uniq%P.shape[0]
    t=f[a]/(f[a]-f[b]);V=P[a]+t[:,None]*(P[b]-P[a])
    return V,inv.reshape(-1,3)

@lru_cache(None)
def mesh(name,step=1.0,watertight=False):
    """Triangle mesh of the clay surface with vertices projected onto it and smooth normals."""
    G,d,_=_grid(name,step);V,F=(_tetra if watertight else _nets)(G,d,step)
    for _ in range(4):
        f,_=field(name,V);g=gradient(name,V);V=V-np.clip(f/np.maximum((g*g).sum(1),1e-9),-step,step)[:,None]*g
    V[:,2]=np.maximum(V[:,2],0)
    Nrm=gradient(name,V);Nrm/=np.linalg.norm(Nrm,axis=1,keepdims=True)
    # Orient every triangle along the outward gradient.
    a,b,c=V[F[:,0]],V[F[:,1]],V[F[:,2]];flip=(np.cross(b-a,c-a)*(Nrm[F[:,0]]+Nrm[F[:,1]]+Nrm[F[:,2]])).sum(1)<0
    F[flip]=F[flip][:,[0,2,1]]
    _,mat=field(name,V);return V,F,Nrm,colour_index(V,mat,name),mat

def colour_index(V,mat,name):
    """Palette index per point: white, black, or red / white apron stripes."""
    out=np.where(mat==BLACK,1,0)
    stripe=(np.floor(V[:,1]/(STRIPE*scale(name)))%2==0)
    return np.where((mat==APRON)&stripe,2,out).astype(np.uint8)

def mesh_volume(V,F):
    a,b,c=V[F[:,0]],V[F[:,1]],V[F[:,2]];return float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6)

def closed(F):
    e=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),1);_,count=np.unique(e,axis=0,return_counts=True)
    return bool((count==2).all())

@lru_cache(None)
def stats(name):
    """Size, clay volume per colour, clay to buy (g) and the clay an optional foil core saves.
    Volume from the closed 1 mm mesh; colour shares and the core from a 0.5 mm grid."""
    V,F=mesh(name,1.0,True)[:2];G,d,mat=_grid(name,.5);inside=d<0
    cfg=CFG['figures']['clay'];total=mesh_volume(V,F)
    counts=np.bincount(colour_index(G[inside],mat[inside],name),minlength=3).astype(float)
    by={k:total*counts[j]/counts.sum() for j,k in enumerate(COLOURS)}
    # Foil core: white body deeper than the clay wall; a ball of the same volume is easy to scrunch.
    core=float(((d<-cfg['foil_wall'])&(mat==WHITE)).sum()*.5**3)
    lo,hi=V.min(0),V.max(0)
    return {'key':name,'name':NAMES[name],'scale':float(scale(name)),'height':float(hi[2]),'length':float(hi[0]-lo[0]),'width':float(hi[1]-lo[1]),
            'volume_mm3':total,'by_colour_mm3':by,'grams':grams(total),'grams_by_colour':{k:grams(v) for k,v in by.items()},
            'core_mm3':core,'core_ball_mm':2*(3*core/(4*math.pi))**(1/3),'grams_with_core':grams(total-core),
            'closed':closed(F),'triangles':len(F)}

def lumps(name):
    """Modelling list: each named lump with its size in mm (pairs counted once, 'x2')."""
    s=scale(name);out={}
    for f,m,_,label in DESIGNS[name][1]():
        if label:out.setdefault(label,[f.dims,m,0])[2]+=1
    return [(label,[d*s for d in dims],'black' if m==BLACK else 'white',n) for label,(dims,m,n) in out.items()]

def lumps_spec(name):
    """Every lump as (kind, parameters in mm, colour id) for building an exact CAD solid."""
    s=scale(name);out=[]
    for f,m,_,_ in DESIGNS[name][1]():
        kind,*args=f.spec
        mm=[(np.array(v)*s).tolist() for v in args]
        if kind=='ellipsoid':mm[2]=args[2]   # rotation is not scaled
        out.append(((kind,*mm),m))
    return out

@lru_cache(None)
def hard_volume(name,step=.5):
    """Volume (mm3) of the plain union of the lumps, without the smoothed joins or the apron:
    the shape of the exact CAD solid, so the two can be compared."""
    s=scale(name);G=_grid(name,step)[0]/s;d=np.full(G.shape[:-1],np.inf)
    for f,_,_,_ in DESIGNS[name][1]():d=np.minimum(d,f(G))
    return float(((d<0)&(G[...,2]>=0)).sum()*step**3)

def grams(volume_mm3):
    """Clay to buy: volume x density plus the handling allowance."""
    cfg=CFG['figures']['clay'];return volume_mm3/1000*cfg['density']*(1+cfg['allowance'])

def footprint(name):
    """Plan outline (convex hull, mm) of the whole figure, for placing it in a room."""
    P=mesh(name,1.0)[0][:,:2]
    pts=sorted(set(map(tuple,np.round(P,2))))
    def half(points):
        h=[]
        for p in points:
            while len(h)>=2 and (h[-1][0]-h[-2][0])*(p[1]-h[-2][1])-(h[-1][1]-h[-2][1])*(p[0]-h[-2][0])<=0:h.pop()
            h.append(p)
        return h[:-1]
    return [list(map(float,p)) for p in half(pts)+half(pts[::-1])]

def packed(name,step=1.0):
    """Viewer mesh as base64 little-endian arrays: float32 positions, uint16 index, uint8 palette index."""
    V,F,_,C,_=mesh(name,step)
    assert len(V)<65536
    b64=lambda a:base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()
    return {'positions':b64(V.astype('<f4')),'index':b64(F.astype('<u2')),'colour':b64(C.astype('u1')),'palette':list(COLOURS.values()),'vertices':len(V),'triangles':len(F)}

if __name__=='__main__':
    import time
    for name in DESIGNS:
        t=time.time();s=stats(name);print(f'{s["name"]}: {s["height"]:.1f} tall, {s["volume_mm3"]/1000:.1f} cm3, {s["grams"]:.0f} g',{k:round(v) for k,v in s['grams_by_colour'].items()},f'core saves {s["grams"]-s["grams_with_core"]:.0f} g ({time.time()-t:.1f} s)')
