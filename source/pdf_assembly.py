"""Merge the book with printed contents, clickable links and absolute-page bookmarks."""
import io,math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader,PdfWriter
from pypdf.annotations import Link
import naming
from supplier import fonts,REGULAR,BOLD

def combine(sections,destination):
    """Sections contain path/title/entries; entry page numbers are local and one-based."""
    fonts();readers=[PdfReader(s['path']) for s in sections];entries=[]
    for n,section in enumerate(sections):
        entries.append({'title':section['title'],'section':n,'local_page':1,'level':0})
        entries.extend(dict(e,section=n,local_page=e['page'],level=1) for e in section.get('entries',[]))
    per_page=32;toc_pages=math.ceil(len(entries)/per_page)
    starts=[];offset=0
    for n,reader in enumerate(readers):
        starts.append(offset);offset+=len(reader.pages)+(toc_pages if n==0 else 0)
    for e in entries:
        local=e['local_page']-1
        e['complete_page']=starts[e['section']]+local+1+(toc_pages if e['section']==0 and local>0 else 0)
    buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=A4);width,height=A4;links=[]
    for page in range(toc_pages):
        c.setFillColorRGB(0,0,0);c.setFont(BOLD,23);c.drawString(40,height-60,'Contents' if page==0 else 'Contents / continued')
        c.setFont(REGULAR,9);c.drawString(40,height-82,'Page numbers match the complete PDF in your viewer.')
        for row,e in enumerate(entries[page*per_page:(page+1)*per_page]):
            y=height-117-row*20;x=40+e['level']*13;font=BOLD if e['level']==0 else REGULAR
            size=9;title=e['title']
            while c.stringWidth(title,font,size)>width-x-90 and size>7:size-=.25
            c.setFont(font,size);c.drawString(x,y,title);c.drawRightString(width-40,y,str(e['complete_page']))
            links.append({'toc_page':page+2,'rect':(x,y-4,width-40,y+11),'target':e['complete_page']})
        c.setFont(REGULAR,8);c.drawString(40,24,f'{naming.NAME.upper()} / CONTENTS');c.drawRightString(width-40,24,str(page+2));c.showPage()
    c.save();buf.seek(0);writer=PdfWriter()
    writer.append(readers[0],pages=(0,1),import_outline=False)
    writer.append(PdfReader(buf),import_outline=False)
    writer.append(readers[0],pages=(1,len(readers[0].pages)),import_outline=False)
    for reader in readers[1:]:writer.append(reader,import_outline=False)
    writer.add_outline_item('Contents',1);parent=None
    for e in entries:
        obj=writer.add_outline_item(e['title'],e['complete_page']-1,parent=parent if e['level'] else None)
        if not e['level']:parent=obj
    for link in links:writer.add_annotation(link['toc_page']-1,Link(rect=link['rect'],target_page_index=link['target']-1))
    writer.add_metadata({'/Title':f'{naming.NAME} | Complete plywood CAD building book','/Author':f'{naming.NAME} CAD workshop'})
    with open(destination,'wb') as f:writer.write(f)
    return {'complete_pages':len(writer.pages),'contents_pages':toc_pages,'entries':entries,'sections':[{'title':s['title'],'pdf':str(s['path'].name),'first_page':starts[n]+1,'last_page':starts[n]+len(readers[n].pages)+(toc_pages if n==0 else 0)} for n,s in enumerate(sections)]}
