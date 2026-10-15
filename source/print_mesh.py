"""3D-print meshes: read a binary STL, write the same triangles as 3MF, and check that the part will print.

Pure numpy, so CI can check the published prints again without the CAD kernel. Every check reads the STL that
is offered for download, not the CAD solid it came from. The printer and its limits are in
source/prints/printer.json; the small-parts cylinder is the one the clay figures use (config figures.small_parts).
"""
from __future__ import annotations
import json, math, struct, zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
PRINTER_FILE=ROOT/'source/prints/printer.json'
STL_RECORD=np.dtype([('normal','<f4',3),('corners','<f4',(3,3)),('attribute','<u2')])

def printer():return json.loads(PRINTER_FILE.read_text())
def small_parts():return json.loads((ROOT/'source/config.json').read_text())['figures']['small_parts']

# ---------- mesh files ----------
def read_stl(source):
    """Binary STL (a path or bytes) -> (V (n,3) float, F (m,3) int). Corners at the same point become one vertex."""
    data=source if isinstance(source,(bytes,bytearray)) else Path(source).read_bytes()
    count=struct.unpack_from('<I',data,80)[0] if len(data)>=84 else -1
    if len(data)!=84+50*count:raise ValueError('Not a binary STL file')
    corners=np.frombuffer(data,STL_RECORD,count,84)['corners'].reshape(-1,3)
    V,inverse=np.unique(corners,axis=0,return_inverse=True)
    return V.astype(float),inverse.reshape(-1,3)

def write_3mf(path,V,F,title):
    """The STL's triangles as a 3MF (millimetres). Fixed zip dates keep a rebuilt file byte-identical."""
    vertices=''.join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x,y,z in V)
    triangles=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in F)
    model=('<?xml version="1.0" encoding="UTF-8"?>\n'
      '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
      f'<metadata name="Title">{escape(title)}</metadata><resources><object id="1" type="model" name="{escape(title,{chr(34):"&quot;"})}">'
      f'<mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object></resources>'
      '<build><item objectid="1"/></build></model>')
    parts={'[Content_Types].xml':'<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
           '_rels/.rels':'<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
           '3D/3dmodel.model':model}
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,text in parts.items():
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,text)

# ---------- geometry ----------
def shells(n,F):
    """How many separate pieces (connected sets of triangles) the mesh has."""
    label=np.arange(n)
    while True:
        low=label[F].min(1);new=label.copy();np.minimum.at(new,F.ravel(),np.repeat(low,3));new=new[new]
        if np.array_equal(new,label):return len(np.unique(label[F[:,0]]))
        label=new

def wall_samples(T,normal,area,count,seed=1):
    """Wall thickness at up to `count` faces: the distance from the face centre straight into the part to the
    far surface. Half the samples are picked by area and half by number, so small thin details are found too.
    Returns (thicknesses, sample points)."""
    m=len(T);rng=np.random.default_rng(seed)
    if m<=count:pick=np.arange(m)
    else:pick=np.unique(np.concatenate([rng.choice(m,count//2,p=area/area.sum()),rng.choice(m,count-count//2)]))
    origin=T[pick].mean(1)-normal[pick]*1e-4;direction=-normal[pick]
    e1,e2=T[:,1]-T[:,0],T[:,2]-T[:,0];best=np.full(len(pick),np.inf)
    for s in range(0,len(pick),64):   # Moller-Trumbore, 64 rays against every triangle at once
        o,d=origin[s:s+64,None],direction[s:s+64,None]
        p=np.cross(d,e2);det=(e1*p).sum(-1);ok=np.abs(det)>1e-12;inv=np.where(ok,1/np.where(ok,det,1),0)
        tv=o-T[:,0];u=(tv*p).sum(-1)*inv;q=np.cross(tv,e1);v=(d*q).sum(-1)*inv;t=(e2*q).sum(-1)*inv
        hit=ok&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>1e-6)
        best[s:s+64]=np.where(hit,t,np.inf).min(1)
    found=np.isfinite(best);return best[found],origin[found]

def overhanging(normal,T,limit):
    """Faces leaning out further than `limit` degrees from vertical, not counting faces on the bed."""
    steep=-normal[:,2]>math.sin(math.radians(limit+1))   # 1 degree of grace for faceted cones and 45 degree roofs
    return steep&(T[:,:,2].max(1)>T[:,:,2].min()+1e-3)

# ---------- the report ----------
def check(id,label,status,detail,**extra):return {'id':id,'label':label,'status':status,'detail':detail,**extra}

def analyse(V,F,printer,toy=True,small=None):
    """Size, volume, weight and the printability checks for one mesh standing on z=0.
    Each check is pass, warn (it prints, with care) or fail (it will not print, or breaks a safety rule)."""
    T=V[F];cross=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);twice=np.linalg.norm(cross,axis=1)
    keep=twice>1e-12;T,F,cross,twice=T[keep],F[keep],cross[keep],twice[keep]   # drop zero-area slivers
    normal=cross/twice[:,None];area=twice/2
    volume=float(np.einsum('ij,ij->i',T[:,0],np.cross(T[:,1],T[:,2])).sum()/6)
    lo,hi=V.min(0),V.max(0);size=hi-lo;checks=[]

    # Closed: every edge is shared by exactly two triangles that wind opposite ways round it.
    n=len(V);edges=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]).astype(np.int64)
    forward=np.sort(edges[:,0]*n+edges[:,1]);backward=np.sort(edges[:,1]*n+edges[:,0])
    closed=bool(len(np.unique(forward))==len(forward) and np.array_equal(forward,backward) and volume>0)
    checks.append(check('closed','Closed solid','pass' if closed else 'fail',
        'Watertight, every edge shared by two faces.' if closed else 'The mesh has holes or doubled edges, so slicers may fill or drop parts of it.'))
    pieces=shells(n,F)
    checks.append(check('pieces','One piece','pass' if pieces==1 else 'fail',
        'One connected solid.' if pieces==1 else f'{pieces} separate shells: a floating piece, or a sealed hollow inside.'))

    bx,by,bz=printer['bed'];margin=printer['bed_margin'];x,y=size[0]+2*margin,size[1]+2*margin
    fits=size[2]<=bz and ((x<=bx and y<=by) or (x<=by and y<=bx))
    checks.append(check('bed','Fits the printer','pass' if fits else 'fail',
        f'{size[0]:.1f} × {size[1]:.1f} × {size[2]:.1f} mm on a {bx:g} × {by:g} × {bz:g} mm build volume.'))

    flat=(normal[:,2]<-.9999)&(T[:,:,2].max(1)<lo[2]+1e-3);contact=float(area[flat].sum())
    need=printer['min_base_area']
    checks.append(check('base','Stands flat on the bed','pass' if contact>=need else 'warn' if contact>=1 else 'fail',
        f'{contact:.0f} mm² touches the bed.'+('' if contact>=need else f' Under {need:g} mm²: add a brim so it does not come loose.' if contact>=1 else ' It rests on a point or an edge: give it a flat bottom.')))

    limit=printer['max_overhang'];steep=overhanging(normal,T,limit);hang=float(area[steep].sum())
    checks.append(check('overhang','No supports needed','pass' if hang<1 else 'warn',
        f'Nothing leans out more than {limit:g}° from vertical.' if hang<1 else
        f'{hang:.0f} mm² leans out more than {limit:g}° from vertical (red in the view): it needs supports, or a bridge.'))

    thick,points=wall_samples(T,normal,area,printer['wall_samples'])
    least=float(thick.min()) if len(thick) else 0.0;where=points[thick.argmin()].round(2).tolist() if len(thick) else None
    need=printer['min_wall']
    checks.append(check('wall','Walls thick enough','pass' if least>=need else 'fail',
        f'Thinnest wall {least:.2f} mm (at least {need:g} mm; {len(thick)} places measured).',at=where))

    if toy:
        d,l=small or small_parts();a,b,c=sorted(size)
        swallow=b<=d and c<=l
        checks.append(check('small_parts','Too big to swallow','fail' if swallow else 'pass',
            f'Fits the Ø{d:g} × {l:g} mm small-parts cylinder (EN 71-1): a choking hazard for under-3s. Make it wider than {d:g} mm or longer than {l:g} mm.' if swallow else
            f'Does not fit the Ø{d:g} × {l:g} mm small-parts cylinder (EN 71-1).'))

    material=printer['material'];density=material['density']/1000   # g/mm3
    shell=min(volume,float(area.sum())*printer['shell'])
    status='fail' if any(c['status']=='fail' for c in checks) else 'warn' if any(c['status']=='warn' for c in checks) else 'pass'
    return {'size':[round(float(s),2) for s in size],'volume':round(volume,1),'area':round(float(area.sum()),1),'triangles':int(len(F)),
            'grams':{'solid':round(volume*density,1),'estimate':round((shell+(volume-shell)*printer['infill'])*density,1)},
            'checks':checks,'status':status}
