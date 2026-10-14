"""Printer-margin-aware individual part templates: at most two A4 pages."""
import math
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm


def layout(width,height):
    """Choose page orientation and tile axis with 10 mm overlap; never rescale."""
    candidates=[]
    for paper,tw,th,bottom in ((A4,190,250,15),(landscape(A4),277,165,13)):
        for nx,ny in ((1,1),(1,2),(2,1)):
            if width<=nx*tw-(nx-1)*10+1e-6 and height<=ny*th-(ny-1)*10+1e-6:
                candidates.append((nx*ny,0 if paper==A4 else 1,paper,tw,th,bottom,nx,ny))
    if not candidates:raise ValueError(f'{width:g} × {height:g} mm cannot fit two printable A4 pages')
    _,_,paper,tw,th,bottom,nx,ny=min(candidates)
    return {'paper':paper,'tile_width':tw,'tile_height':th,'bottom':bottom,'columns':nx,'rows':ny,'overlap':10}


def pages(book,parts,draw_sheet,scale_bar,calibration):
    calibration(book);index=[];c=book.c
    for pid,p in sorted(parts.items(),key=lambda item:(item[1]['thickness'],item[0])):
        spec=layout(p['width'],p['height']);tw,th=spec['tile_width'],spec['tile_height'];nx,ny=spec['columns'],spec['rows'];paper=spec['paper'];first=book.n+1
        sheet={'id':pid,'laser':False,'items':[{'part':pid,'copy':1,'angle':0,'x':0,'y':0}]}
        for row in range(ny):
            for col in range(nx):
                c.setPageSize(paper);pw,ph=paper
                c.setFillColorRGB(1,1,1);c.rect(0,0,pw,ph,fill=1,stroke=0)
                c.setFillColorRGB(0,0,0);c.setFont('Helvetica-Bold',10)
                c.drawString(10*mm,ph-13*mm,f'{pid} / {p["thickness"]:g} mm / make {p["quantity"]} / column {col+1}/{nx}, row {row+1}/{ny}')
                c.setFont('Helvetica',7);c.drawString(10*mm,ph-18*mm,'ACTUAL SIZE 100% / 10 mm overlap / align shared crosshairs / no Fit or Shrink')
                x0,y0=col*(tw-10),row*(th-10);ox,oy=10*mm,spec['bottom']*mm
                c.saveState();clip=c.beginPath();clip.rect(ox,oy,tw*mm,th*mm);c.clipPath(clip,stroke=0,fill=0)
                draw_sheet(c,sheet,mm,ox-x0*mm,oy-y0*mm)
                c.setStrokeColorRGB(.55,.55,.55);c.setLineWidth(.35)
                # Crosshairs lie in the shared overlap, expressed in part coordinates.
                marks=[]
                if nx==2:marks=[(tw-5,y) for y in (10,min(p['height']-5,th-10))]
                if ny==2:marks=[(x,th-5) for x in (5,min(p['width']-5,tw-10))]
                for x,y in marks:
                    xx,yy=ox+(x-x0)*mm,oy+(y-y0)*mm;c.line(xx-3,yy,xx+3,yy);c.line(xx,yy-3,xx,yy+3)
                c.restoreState()
                c.setFont('Helvetica',6);c.drawString(10*mm,10*mm,'Black: finished profile. Hole IDs and depths: dimensioned parts. Grey crosses: paper alignment only.')
                scale_bar(c,pw-110*mm,ph-27*mm)
                book.n+=1;c.showPage()
        index.append({'part':pid,'sheet':pid,'quantity':p['quantity'],'thickness':p['thickness'],'first_tile_page':first,'last_tile_page':book.n,'overview_page':None,'columns':nx,'rows':ny,'skipped_tiles':[],'paper_mm':[round(v/mm) for v in paper],'overlap_mm':10})
    c.setPageSize(A4)
    return index
