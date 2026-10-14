"""Book cover: a painted summer scene around the CAD render of the house, with a hand-lettered title.

Everything is drawn here (no generated artwork): sky, sun, clouds, hills, meadow, path, trees and
flowers, then the current house render from render.py, then the title blended into the sky.
"""
from __future__ import annotations
import json, math, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT=Path(__file__).resolve().parents[1]
W,H=1754,2480   # A4 portrait at about 212 dpi
FONT='/System/Library/Fonts/Supplemental/ChalkboardSE.ttc'   # rounded, hand-lettered children's font

def font(size,bold=True):
    try:return ImageFont.truetype(FONT,size,index=2 if bold else 1)
    except OSError:pass
    try:return ImageFont.truetype('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',size)
    except OSError:return ImageFont.load_default(size)   # Windows and minimal Linux: Pillow's bundled font

def gradient(top,bottom,h0,h1):
    t=np.clip((np.arange(H)[:,None]-h0)/max(h1-h0,1),0,1)
    return (np.array(top)[None,None,:]*(1-t[...,None])+np.array(bottom)[None,None,:]*t[...,None]).repeat(W,1)

def ridge(rnd,y0,amp,waves):
    xs=np.arange(W);y=np.full(W,float(y0))
    for k in range(waves):y+=amp/(k+1)*np.sin(xs/W*math.pi*(k+1.3)+rnd.uniform(0,6))
    return y

def blob(draw,cx,cy,r,fill,rnd,n=7,spread=.6):
    for _ in range(n):
        a=rnd.uniform(0,2*math.pi);d=rnd.uniform(0,r*spread);rr=r*rnd.uniform(.55,.9)
        x,y=cx+d*math.cos(a),cy+d*math.sin(a)*.8;draw.ellipse([x-rr,y-rr,x+rr,y+rr],fill=fill)

def main():
    rnd=random.Random(7);horizon=int(H*.56)
    img=Image.fromarray(gradient((150,205,236),(253,243,216),0,horizon).astype(np.uint8)).convert('RGBA')
    # Sun with a soft halo.
    glow=Image.new('RGBA',(W,H));g=ImageDraw.Draw(glow);sx,sy=int(W*.83),int(H*.17)
    for r,a in ((260,40),(190,70),(130,120)):g.ellipse([sx-r,sy-r,sx+r,sy+r],fill=(255,240,180,a))
    g.ellipse([sx-95,sy-95,sx+95,sy+95],fill=(255,228,140,255));img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    # Clouds.
    clouds=Image.new('RGBA',(W,H));c=ImageDraw.Draw(clouds)
    for cx,cy,s in ((300,560,1.0),(1250,470,.8),(820,690,.6),(1500,760,.55),(160,860,.5)):
        for _ in range(9):
            r=rnd.uniform(55,95)*s;x=cx+rnd.uniform(-150,150)*s;y=cy+rnd.uniform(-35,25)*s;c.ellipse([x-r,y-r*.8,x+r,y+r*.8],fill=(255,255,255,215))
    img.alpha_composite(clouds.filter(ImageFilter.GaussianBlur(6)))
    # Hills, far to near.
    land=Image.new('RGBA',(W,H));l=ImageDraw.Draw(land)
    for y0,amp,col in ((horizon-60,55,(151,190,160)),(horizon,45,(124,176,108)),(horizon+90,35,(110,168,86))):
        ys=ridge(rnd,y0,amp,3);l.polygon([(0,H)]+[(x,ys[x]) for x in range(0,W,6)]+[(W,H)],fill=col+(255,))
    img.alpha_composite(land.filter(ImageFilter.GaussianBlur(3)))
    meadow_top=horizon+150
    meadow=Image.fromarray(gradient((128,184,92),(86,146,62),meadow_top,H).astype(np.uint8)).convert('RGBA')
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon([(0,H)]+[(x,meadow_top+25*math.sin(x/W*5)) for x in range(0,W,6)]+[(W,H)],fill=255)
    img.paste(meadow,(0,0),mask.filter(ImageFilter.GaussianBlur(4)))
    # Winding path from the bottom edge to the house.
    path=Image.new('RGBA',(W,H));p=ImageDraw.Draw(path);pts=[]
    for k in range(40):
        t=k/39;y=H*.99-t*(H*.99-H*.84);x=W*.47+math.sin(t*3.2)*W*.12*(1-t)+W*.04*t;w=W*.16*(1-t)+W*.05
        pts.append((x,y,w))
    p.polygon([(x-w/2,y) for x,y,w in pts]+[(x+w/2,y) for x,y,w in reversed(pts)],fill=(233,212,160,255))
    img.alpha_composite(path.filter(ImageFilter.GaussianBlur(5)))
    # Trees.
    trees=Image.new('RGBA',(W,H));t=ImageDraw.Draw(trees)
    for tx,ty,s in ((180,1420,1.15),(1590,1470,1.0),(1420,1330,.7),(420,1300,.6)):
        t.rectangle([tx-14*s,ty,tx+14*s,ty+190*s],fill=(120,88,60,255))
        for col,dy in (((70,128,66),0),((92,152,78),-40),((122,178,96),-80)):blob(t,tx,ty-90*s+dy*s,110*s,col+(255,),rnd)
    img.alpha_composite(trees.filter(ImageFilter.GaussianBlur(2)))
    # Grass strokes and wildflowers on the meadow.
    grass=ImageDraw.Draw(img)
    for _ in range(5200):
        x=rnd.uniform(0,W);y=rnd.uniform(meadow_top+30,H);h=rnd.uniform(8,22)*(.5+(y-meadow_top)/(H-meadow_top))
        grass.line([(x,y),(x+rnd.uniform(-4,4),y-h)],fill=rnd.choice([(84,140,58),(104,162,70),(140,190,96)]),width=2)
    for _ in range(420):
        x=rnd.uniform(0,W);y=rnd.uniform(meadow_top+60,H);r=rnd.uniform(4,9)*(.5+(y-meadow_top)/(H-meadow_top))
        if abs(x-W*.5)<W*.12 and y>H*.8:continue
        col=rnd.choice([(255,255,255),(255,222,90),(240,150,170),(196,150,220),(255,190,110)])
        for a in range(5):grass.ellipse([x+r*math.cos(a*1.257)-r*.6,y+r*math.sin(a*1.257)-r*.6,x+r*math.cos(a*1.257)+r*.6,y+r*math.sin(a*1.257)+r*.6],fill=col)
        grass.ellipse([x-r*.45,y-r*.45,x+r*.45,y+r*.45],fill=(250,200,60))
    # The house itself, from the CAD render, on a soft shadow.
    house=Image.open(ROOT/'output/previews/cover-house.png').convert('RGBA');bbox=house.getbbox();house=house.crop(bbox)
    # Sized so the finial stays below the subtitle and the base clears the book's bottom band.
    scale=W*.54/house.width;house=house.resize((int(house.width*scale),int(house.height*scale)),Image.LANCZOS)
    hx=int(W*.5-house.width*.5);hy=int(H*.885-house.height)
    shadow=Image.new('RGBA',(W,H));ImageDraw.Draw(shadow).ellipse([hx+house.width*.08,hy+house.height*.9,hx+house.width*.95,hy+house.height*1.02],fill=(40,70,40,110))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)));img.alpha_composite(house,(hx,hy))
    # Paper grain for a painted feel.
    grain=(np.random.default_rng(3).normal(0,7,(H,W,1))).repeat(3,2);arr=np.array(img).astype(float);arr[...,:3]=np.clip(arr[...,:3]+grain,0,255)
    img=Image.fromarray(arr.astype(np.uint8),'RGBA')
    # Hand-lettered title, letter by letter with a little bounce, blended with a soft shadow and glow.
    title='Moomin House';f=font(232);sub=font(78,False)
    layer=Image.new('RGBA',(W,H));shade=Image.new('RGBA',(W,H))
    widths=[f.getlength(ch) for ch in title];x=(W-sum(widths)-8*len(title))/2;y0=165
    palette=[(47,127,191),(210,70,60)]
    for k,ch in enumerate(title):
        if ch==' ':x+=widths[k]+8;continue
        tile=Image.new('RGBA',(int(widths[k])+80,330));td=ImageDraw.Draw(tile)
        td.text((40,20),ch,font=f,fill=palette[k%2 if k<6 else (k+1)%2]+(255,),stroke_width=12,stroke_fill=(255,255,255,255))
        tile=tile.rotate(rnd.uniform(-6,6),resample=Image.BICUBIC,expand=False);dy=int(14*math.sin(k*1.3))
        layer.alpha_composite(tile,(int(x-40),y0+dy));sh=Image.new('RGBA',tile.size,(30,60,70,0));sh.putalpha(tile.getchannel('A').point(lambda v:int(v*.45)))
        shade.alpha_composite(sh,(int(x-40)+10,y0+dy+14));x+=widths[k]+8
    img.alpha_composite(shade.filter(ImageFilter.GaussianBlur(10)));img.alpha_composite(layer)
    text='A plywood house, made by hand';tw=sub.getlength(text)
    glow=Image.new('RGBA',(W,H));ImageDraw.Draw(glow).text(((W-tw)/2,y0+300),text,font=sub,fill=(255,255,255,255),stroke_width=10,stroke_fill=(255,255,255,255))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(img).text(((W-tw)/2,y0+300),text,font=sub,fill=(40,72,73,255))
    img.convert('RGB').save(ROOT/'output/previews/cover.png',optimize=True)
    print('Cover saved: output/previews/cover.png')

if __name__=='__main__':main()
