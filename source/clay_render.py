"""Soft clay-look renders of the thermo-clay Rowan family figures (orthographic, true scale, transparent).

A small numpy rasteriser fills a G-buffer (depth, normal, colour, occlusion) from the clay meshes and
shades it like matte polymer clay: wrapped key light, cool fill, rim light, a gentle satin highlight
and occlusion taken from the signed distance field. A JSON sidecar records pixels per millimetre.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import clay

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/previews'
PX=16          # render pixels per mm; images are saved at half that after anti-aliasing
VIEWS={'front':(0,0),'side':(-90,0),'back':(180,0),'three-quarter':(-38,14)}

def camera(az,el):
    f,t=math.radians(az),math.radians(el)
    return np.array([[-math.sin(f),math.cos(f),0],[-math.sin(t)*math.cos(f),-math.sin(t)*math.sin(f),math.cos(t)],[math.cos(t)*math.cos(f),math.cos(t)*math.sin(f),math.sin(t)]])

def srgb_to_linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def linear_to_srgb(c):c=np.clip(c,0,1);return np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)

def occlusion(name,V,N,step=.7,count=5):
    """Ambient occlusion from the distance field: how much the surface is closed in along its normal."""
    ao=np.zeros(len(V))
    for i in range(1,count+1):
        h=step*i;d,_=clay.field(name,V+N*h);ao+=(h-np.minimum(d,h))/h*.5**i
    return np.clip(1-1.6*ao,0,1)

def rasterise(xy,depth,F,attrs,size,chunk=20000):
    """Nearest-surface G-buffer: per pixel the interpolated attributes of the front-most triangle."""
    Wd,Ht=size;zbuf=np.full(Wd*Ht,-np.inf);out=np.zeros((Wd*Ht,attrs.shape[1]));hit=np.zeros(Wd*Ht,bool)
    for s in range(0,len(F),chunk):
        f=F[s:s+chunk];A,B,C=xy[f[:,0]],xy[f[:,1]],xy[f[:,2]]
        x0=np.floor(np.minimum.reduce([A[:,0],B[:,0],C[:,0]])).astype(int);y0=np.floor(np.minimum.reduce([A[:,1],B[:,1],C[:,1]])).astype(int)
        x1=np.ceil(np.maximum.reduce([A[:,0],B[:,0],C[:,0]])).astype(int);y1=np.ceil(np.maximum.reduce([A[:,1],B[:,1],C[:,1]])).astype(int)
        S=int(max((x1-x0).max(),(y1-y0).max()))+1
        ox,oy=np.meshgrid(np.arange(S),np.arange(S));ox=ox.ravel();oy=oy.ravel()
        px=x0[:,None]+ox[None,:]+.5;py=y0[:,None]+oy[None,:]+.5
        den=(B[:,1]-C[:,1])*(A[:,0]-C[:,0])+(C[:,0]-B[:,0])*(A[:,1]-C[:,1]);ok=np.abs(den)>1e-9;den=np.where(ok,den,1)
        w0=((B[:,1]-C[:,1])[:,None]*(px-C[:,0][:,None])+(C[:,0]-B[:,0])[:,None]*(py-C[:,1][:,None]))/den[:,None]
        w1=((C[:,1]-A[:,1])[:,None]*(px-C[:,0][:,None])+(A[:,0]-C[:,0])[:,None]*(py-C[:,1][:,None]))/den[:,None];w2=1-w0-w1
        m=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)&ok[:,None]&(px<Wd)&(py<Ht)&(px>=0)&(py>=0)
        t,k=np.nonzero(m);w=np.stack([w0[t,k],w1[t,k],w2[t,k]],1)
        pix=(py[t,k].astype(int))*Wd+px[t,k].astype(int);z=(w*depth[f[t]]).sum(1)
        order=np.lexsort((-z,pix));pix,z,t,w=pix[order],z[order],t[order],w[order]
        first=np.r_[True,pix[1:]!=pix[:-1]];pix,z,t,w=pix[first],z[first],t[first],w[first]
        near=z>zbuf[pix];pix,z,t,w=pix[near],z[near],t[near],w[near]
        zbuf[pix]=z;hit[pix]=True;out[pix]=np.einsum('ij,ijk->ik',w,attrs[f[t]])
    return zbuf.reshape(Ht,Wd),hit.reshape(Ht,Wd),out.reshape(Ht,Wd,-1)

def shade(N,albedo,ao,black):
    """Matte clay: wrapped key light, cool fill, soft rim, sky ambient with occlusion, low satin highlight."""
    unit=lambda v:np.array(v)/np.linalg.norm(v)
    key,fill,rim=unit([-.5,.62,.6]),unit([.75,.05,.66]),unit([.35,.45,-.82])
    wrap=lambda l,w:np.clip((N@l+w)/(1+w),0,1)[...,None]
    a=ao[...,None]
    diffuse=1.05*wrap(key,.35)*np.array([1,.97,.92])*(.55+.45*a)+.3*wrap(fill,.2)*np.array([.86,.92,1])*a
    sky=(.34+.16*N[...,1:2])*a;rimlight=.28*np.clip(N@rim+.15,0,1)[...,None]**2
    half=unit(key+np.array([0,0,1]));spec=np.clip(N@half,0,1)[...,None]**22*np.where(black[...,None],.22,.09)
    return albedo*(diffuse+sky+rimlight)+spec*(.4+.6*a)

def render_view(name,view,step=.45,px=PX):
    OUT.mkdir(parents=True,exist_ok=True)
    V,F,Nrm,C,mat=clay.mesh(name,step)
    R=camera(*VIEWS[view]);P=V@R.T
    lo,hi=P[:,:2].min(0),P[:,:2].max(0);pad=4
    Wd,Ht=int((hi[0]-lo[0]+2*pad)*px),int((hi[1]-lo[1]+2*pad)*px)
    xy=np.stack([(P[:,0]-lo[0]+pad)*px,(hi[1]+pad-P[:,1])*px],1)
    ao=occlusion(name,V,Nrm)
    pal=srgb_to_linear(np.array([[int(h[i:i+2],16)/255 for i in (1,3,5)] for h in clay.COLOURS.values()]))
    attrs=np.concatenate([Nrm@R.T,pal[C],ao[:,None],(C==clay.BLACK)[:,None]],1).astype(float)
    z,hit,g=rasterise(xy,P[:,2],F,attrs,(Wd,Ht))
    N=g[...,:3];N/=np.maximum(np.linalg.norm(N,axis=-1,keepdims=True),1e-9)
    albedo=g[...,3:6]
    col=linear_to_srgb(shade(N,albedo,g[...,6],g[...,7]>.5))
    rgba=np.zeros((Ht,Wd,4),np.uint8);rgba[...,:3]=(col*255).astype(np.uint8);rgba[...,3]=hit*255
    img=Image.fromarray(rgba,'RGBA')
    # Soft contact shadow under the flat base.
    base=V[:,2]<.6;ground=np.zeros((Ht,Wd),np.uint8);sh=Image.fromarray(ground);d=ImageDraw.Draw(sh)
    bx=xy[base];gy=float(xy[base][:,1].max())
    d.ellipse([bx[:,0].min()-2*px,gy-1.8*px,bx[:,0].max()+2*px,gy+1.2*px],fill=110)
    sh=sh.filter(ImageFilter.GaussianBlur(1.6*px));shadow=Image.new('RGBA',img.size,(60,62,58,0));shadow.putalpha(sh)
    shadow.alpha_composite(img);img=shadow.resize((Wd//2,Ht//2),Image.LANCZOS)
    path=OUT/f'clay-{name}-{view}.png';img.save(path)
    # Ground line and true scale for the book: millimetres per saved pixel and the base line position.
    meta={'view':view,'px_per_mm':px/2,'width_mm':Wd/px,'height_mm':Ht/px,'ground_from_top_mm':float(hi[1]+pad),'left_mm':float(pad-lo[0])}
    (OUT/f'clay-{name}-{view}.json').write_text(json.dumps(meta))
    return path

def family(names=('elias','mira','ada','theo'),view='three-quarter',gap=6):
    """The figures side by side at one scale, standing on one ground line."""
    OUT.mkdir(parents=True,exist_ok=True)
    ims=[Image.open(OUT/f'clay-{n}-{view}.png') for n in names];metas=[json.loads((OUT/f'clay-{n}-{view}.json').read_text()) for n in names]
    k=metas[0]['px_per_mm'];ground=max(m['ground_from_top_mm'] for m in metas)*k;below=max(im.height-m['ground_from_top_mm']*k for im,m in zip(ims,metas))
    sheet=Image.new('RGBA',(int(sum(im.width for im in ims)+gap*k*(len(ims)-1)),int(ground+below)),(0,0,0,0));x=0
    for im,m in zip(ims,metas):sheet.alpha_composite(im,(int(x),int(ground-m['ground_from_top_mm']*k)));x+=im.width+gap*k
    sheet.save(OUT/'clay-family.png')

def main():
    for name in clay.DESIGNS:
        for view in VIEWS:render_view(name,view)
    family()
    print('Rendered',len(clay.DESIGNS)*len(VIEWS),'clay figure views and the family picture')

if __name__=='__main__':main()
