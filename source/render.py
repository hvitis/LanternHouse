"""CAD-derived illustrations. No generated artwork is used for technical geometry."""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'output/parts.json').read_text())
MESH=json.loads((ROOT/'output/previews/mesh.json').read_text())
def camera(azimuth,elevation=30):
    """Orthographic camera rows: screen x, screen y, depth toward a viewer at this azimuth/elevation (degrees)."""
    f,t=math.radians(azimuth),math.radians(elevation)
    return np.array([[-math.sin(f),math.cos(f),0],[-math.sin(t)*math.cos(f),-math.sin(t)*math.sin(f),math.cos(t)],[math.cos(t)*math.cos(f),math.cos(t)*math.sin(f),math.sin(t)]])
R=camera(-60)
VIEWS=DATA['derived']['views']
def transform(vertices,group,mode):
    # Same hinge rotation and offsets as the open / exploded STEP exports.
    a=np.array(vertices,dtype=float)
    if mode=='open' and group in ('WallLeft','WallRight'):
        sign=1 if group=='WallRight' else -1
        th=math.radians(sign*VIEWS['open_angle']);x=DATA['derived']['hinge_axes'][group][0]
        a[:,0]-=x;rotation=np.array([[math.cos(th),-math.sin(th),0],[math.sin(th),math.cos(th),0],[0,0,1]])
        a=a@rotation.T;a[:,0]+=x
    if mode in ('open','exploded') and group in VIEWS[mode]:a+=np.array(VIEWS[mode][group])
    return a

def render(name,include=None,mode='closed',overlay=False,size=(1800,1800),view=None):
    camera=R if view is None else np.array(view)
    objects=[];points=[]
    for m in MESH:
        if m['group'] in ('Tools','Accessories'):continue
        if include and not include(m):continue
        vv=transform(m['vertices'],m['group'],mode);proj=vv@camera.T;points.append(proj)
        objects.append((m,vv,proj))
    if not objects:return
    pts=np.concatenate(points);lo=pts[:,:2].min(0);hi=pts[:,:2].max(0);pad=110
    scale=min((size[0]-2*pad)/(hi[0]-lo[0]),(size[1]-2*pad)/(hi[1]-lo[1]));center=(lo+hi)/2
    def screen(p):return ((p[0]-center[0])*scale+size[0]/2,size[1]/2-(p[1]-center[1])*scale)
    pixels=np.full((size[1],size[0],3),255,dtype=np.uint8)
    zbuffer=np.full((size[1],size[0]),-np.inf,dtype=np.float32)
    tris=[];light=np.array([-.25,-.55,1]);light/=np.linalg.norm(light)
    for m,vv,proj in objects:
        hexrgb=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],dtype=float)
        rgb=hexrgb(m['color']);palette={h:hexrgb(h) for h in set(m.get('face_colors',[]))}   # clay figures colour each face
        for k,face in enumerate(m['faces']):
            if palette:rgb=palette[m['face_colors'][k]]
            idx=np.array(face);vertices=vv[idx];normal=np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0]);norm=np.linalg.norm(normal)
            shade=.72+.28*abs(float(normal@light/norm)) if norm else .9
            fill=tuple(np.clip(rgb*shade,0,255).astype(int));tris.append(([screen(p) for p in proj[idx]],proj[idx,2],fill))
    # True per-pixel depth prevents rear furniture and gussets showing through walls.
    for polygon,depths,fill in tris:
        a,b,c=np.array(polygon,dtype=np.float32)
        xmin=max(0,int(math.floor(min(a[0],b[0],c[0]))));xmax=min(size[0]-1,int(math.ceil(max(a[0],b[0],c[0]))))
        ymin=max(0,int(math.floor(min(a[1],b[1],c[1]))));ymax=min(size[1]-1,int(math.ceil(max(a[1],b[1],c[1]))))
        if xmax<xmin or ymax<ymin:continue
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<.001:continue
        yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1].astype(np.float32);xx+=.5;yy+=.5
        w1=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        w2=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w3=1-w1-w2
        depth=w1*depths[0]+w2*depths[1]+w3*depths[2]
        target=zbuffer[ymin:ymax+1,xmin:xmax+1];mask=(w1>=-1e-5)&(w2>=-1e-5)&(w3>=-1e-5)&(depth>target)
        target[mask]=depth[mask];pixels[ymin:ymax+1,xmin:xmax+1][mask]=fill
    img=Image.fromarray(pixels).convert('RGBA')
    img.putalpha(Image.fromarray(np.where(np.isfinite(zbuffer),255,0).astype(np.uint8)))
    draw=ImageDraw.Draw(img)
    ids={m['id'] for m,_,_ in objects}
    if overlay:
        for f in DATA['fasteners']:
            if not any(p in ids for p in f['parts']):continue
            origin=np.array(f['origin']);end=origin+np.array(f['axis'])*f['length']
            p,q=origin@camera.T,end@camera.T;a,b=screen(p),screen(q)
            width=max(3,int(f['diameter']*scale));draw.line([a,b],fill='#1B728C',width=width)
            # Two borders mark the screw shank; dashed axis extends through mating wood.
            delta=np.array(b)-np.array(a);length=np.linalg.norm(delta)
            if length:
                normal=np.array([-delta[1],delta[0]])/length*max(2,f['diameter']*scale/2)
                for sign in (-1,1):draw.line([tuple(np.array(a)+sign*normal),tuple(np.array(b)+sign*normal)],fill='#126A84',width=2)
                ext=delta/length*28
                start=np.array(a)-ext;finish=np.array(b)+ext
                for j in range(0,int(np.linalg.norm(finish-start)),12):
                    aa=start+(finish-start)*j/np.linalg.norm(finish-start);bb=start+(finish-start)*min(j+6,np.linalg.norm(finish-start))/np.linalg.norm(finish-start)
                    draw.line([tuple(aa),tuple(bb)],fill='#1286A2',width=2)
                draw.ellipse([a[0]-5,a[1]-5,a[0]+5,a[1]+5],outline='#126A84',width=2)
        for j in DATA['joints']:
            if not any(p in ids for p in j['parts']):continue
            pt=np.array(j['position'])@camera.T;x,y=screen(pt)
            if j.get('outline'):
                outline=[screen(np.array(p)@camera.T) for p in j['outline']];draw.line(outline+[outline[0]],fill='#C37332',width=3)
            else:draw.ellipse([x-7,y-7,x+7,y+7],outline='#C37332',width=3)
            axis=np.array(j['axis']);start=np.array(j['position'])-axis*12;end=np.array(j['position'])+axis*12
            a,b=np.array(screen(start@camera.T)),np.array(screen(end@camera.T));length=np.linalg.norm(b-a)
            if length:
                for off in range(0,int(length),14):draw.line([tuple(a+(b-a)*off/length),tuple(a+(b-a)*min(off+7,length)/length)],fill='#C37332',width=2)
    img.save(ROOT/'output/previews'/f'{name}.png')
    # Projection sidecar so the book can place dimension lines exactly on the image.
    (ROOT/'output/previews'/f'{name}.json').write_text(json.dumps({'camera':camera.tolist(),'center':center.tolist(),'scale':float(scale),'size':list(size),'lo':lo.tolist(),'hi':hi.tolist()}))

def main():
    for pattern in ('*.png','*.json'):
        for old in (ROOT/'output/previews').glob(pattern):
            if old.name!='mesh.json':old.unlink()
    house=lambda m:m['group'] not in ('Furniture','Figures','Garden')
    panel=lambda m:DATA['parts'].get(m['part'],{}).get('assembly_panel') or m.get('design_part',m['part'])
    render('house-closed',house,size=(1800,2400))
    veranda_angle=-75+(int(DATA['config']['veranda']['facet'][1:])-1)*30
    render('house-closed-veranda',house,size=(1800,2400),view=camera(veranda_angle+15))
    render('cover-house',house,size=(2000,2600),view=camera(-25,16))
    render('house-open',house,mode='open',size=(2200,2400))
    render('house-open-furnished',lambda m:m['group']!='Garden',mode='open',size=(2200,2400))
    render('garden',lambda m:m['group'] not in ('Furniture','Figures'),size=(2400,2000))
    render('house-exploded',house,mode='exploded',overlay=True,size=(2200,2800))
    render('frame',lambda m:m['group']=='Fixed' and m['part'] not in [f'W{i:02}' for i in range(1,13)] and not m['part'].startswith('D'),overlay=True)
    render('walls-rear',lambda m:m['group']=='Fixed' and (m['part'].startswith(('W','A02','J0'))),overlay=True)
    render('wall-right',lambda m:m['group']=='WallRight',overlay=True,size=(1800,2300))
    render('wall-left',lambda m:m['group']=='WallLeft',overlay=True,size=(1800,2300))
    render('plinth-drawer',lambda m:m['group']=='Drawer' or panel(m) in ('B01','F00','PL1','DG1','DB1','A04','ES1') or (m['part']=='ET1' and m['group']=='Fixed'),mode='open',overlay=True)
    render('rooms',lambda m:panel(m) in ('F00','F01','F02','PT1','P01','A04'),overlay=True)
    render('roof',lambda m:m['group']=='Roof',overlay=True)
    render('locks',lambda m:m['group']=='RoofLocks' or panel(m)=='F02',overlay=True)
    render('catches',lambda m:m['group'] in ('WallRight','WallLeft') or panel(m) in ('MC1','GP1','F02','F00','B01'),mode='open',overlay=True)
    render('porch',lambda m:m['group']=='Porch',overlay=True)
    render('roof-underside',lambda m:m['group']=='Roof',overlay=True,view=[[.866,.5,0],[.25,-.433,.866],[.433,-.75,-.5]])
    for (name,prefixes),z in zip([('kitchen',('K2','K7','GL','GR')),('living',('V','K4','KS','LG','L1','SS','LC','BK')),('bedroom',('U','L2','ST','BA','BK')),('attic',('N','AC','SB','AB2','AD'))],DATA['derived']['floor_tops']):
        render(name,lambda m,p=prefixes,zz=z: m['group']=='Furniture' and any(m.get('design_part',m['part']).startswith(prefix) for prefix in p) and min(v[2] for v in m['vertices'])>=zz-.1 and max(v[2] for v in m['vertices'])<zz+DATA['config']['floor_pitch'])
    import clay_render
    clay_render.main()
    print('Rendered',len(list((ROOT/'output/previews').glob('*.png'))),'CAD-derived illustrations')
    try:
        import readme_images
        readme_images.update_readme_images(ROOT)
    except Exception as e:
        print(f'Note: readme images update skipped ({e})')

if __name__=='__main__':main()
