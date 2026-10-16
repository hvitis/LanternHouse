"""The "Optymalne wymiary i cennik" PDF: what to buy from one supplier, the variants it beat, the price list and the
sheet layouts. Input is the result of stock.optimize; the text is Polish, like the supplier documents."""
from __future__ import annotations
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from shapely.geometry import Polygon
from supplier import fonts, REGULAR, BOLD
from stock import area, ssize
import naming

TITLE='Optymalne wymiary i cennik'
W,H=A4;M=16*mm;INK=colors.HexColor('#284849');TEAL=colors.HexColor('#197F98');RUST=colors.HexColor('#B56535')
PALE=colors.HexColor('#EEF4F4');GRID=colors.HexColor('#B8C9CA');BEST=colors.HexColor('#DCEFE3')
PART={'3':colors.HexColor('#F3D9B1'),'4':colors.HexColor('#E7C9A0'),'6':colors.HexColor('#CFE1E6'),'8':colors.HexColor('#C9D3EA')}

def zl(v,cur='zł'):return f'{v:,.2f}'.replace(',',' ').replace('.',',')+f' {cur}'
def pct(v):return f'{100*v:.1f}'.replace('.',',')+' %'
def m2(v):return f'{v:.3f}'.replace('.',',')+' m²'
def fmt(key):a,b=ssize(key);return f'{a:g} × {b:g}'
def grade_name(g):return f'klasa {g}' if g else 'bez podziału na klasy'
def counts_text(plan):return ', '.join(f'{n}× {fmt(k)}' for k,n in sorted(plan['counts'].items(),key=lambda kv:-area(kv[0])))
def thick(t):return f'{t} mm'

class Doc:
    """A4 pages with a running header, a y cursor that breaks pages, and wrapped tables."""
    def __init__(self,path,supplier):
        fonts();self.c=canvas.Canvas(str(path),pagesize=A4);self.c.setTitle(TITLE);self.c.setAuthor(supplier['name']);self.c.setSubject(f'{naming.NAME}: zakup sklejki')
        self.supplier=supplier;self.page=0;self.y=0;self.section=''
    def new(self,section=None):
        if self.page:self.footer();self.c.showPage()
        self.page+=1;self.section=section or self.section;c=self.c
        c.setFillColor(INK);c.setFont(BOLD,9);c.drawString(M,H-10*mm,TITLE);c.setFont(REGULAR,9)
        c.drawRightString(W-M,H-10*mm,f'{self.supplier["name"]} · {self.section}');c.setStrokeColor(GRID);c.line(M,H-12*mm,W-M,H-12*mm)
        self.y=H-20*mm
    def footer(self):
        c=self.c;c.setFont(REGULAR,8);c.setFillColor(colors.grey)
        c.drawString(M,9*mm,f'{naming.NAME} · {datetime.date.today().isoformat()}');c.drawRightString(W-M,9*mm,f'strona {self.page}')
    def need(self,h):
        if self.y-h<16*mm:self.new()
    def heading(self,text,size=13):
        self.need(16*mm);self.y-=size*.4*mm;self.c.setFillColor(TEAL);self.c.setFont(BOLD,size);self.c.drawString(M,self.y,text);self.y-=4*mm
    def text(self,text,size=9,font=None,color=INK,indent=0):
        lines=simpleSplit(text,font or REGULAR,size,W-2*M-indent);self.y-=size*.2*mm
        for line in lines:
            self.need(size*.42*mm+1.5*mm);self.c.setFillColor(color);self.c.setFont(font or REGULAR,size);self.c.drawString(M+indent,self.y,line);self.y-=size*.42*mm+1.5*mm
        self.y-=1*mm
    def table(self,widths,header,rows,size=8,shade=()):
        """Columns in mm (the last one takes the rest); rows wrap; a row index in `shade` is highlighted."""
        widths=list(widths)+[W/mm-2*M/mm-sum(widths)];lead=size*.42*mm+1.2*mm
        def cells(row,font):return [simpleSplit(str(v),font,size,w*mm-2*mm) or [''] for v,w in zip(row,widths)]
        def draw(row,font,fill=None):
            parts=cells(row,font);h=max(map(len,parts))*lead+1.6*mm
            if self.y-h<16*mm:self.new();draw(header,BOLD,PALE)
            c=self.c;x=M
            if fill:c.setFillColor(fill);c.rect(M,self.y-h,W-2*M,h,stroke=0,fill=1)
            c.setFillColor(INK);c.setFont(font,size)
            for lines,w in zip(parts,widths):
                for k,line in enumerate(lines):c.drawString(x+1*mm,self.y-(k+1)*lead+.4*mm,line)
                x+=w*mm
            self.y-=h;c.setStrokeColor(GRID);c.setLineWidth(.4);c.line(M,self.y,W-M,self.y)
        draw(header,BOLD,PALE)
        for k,row in enumerate(rows):draw(row,REGULAR,BEST if k in shade else None)
        self.y-=3*mm
    def save(self):self.footer();self.c.save()

def purchase_rows(plan,cur):
    rows=[]
    for line in plan['lines']:
        what='; '.join(f'{b["units"]}× {b["offer"]["name"]} ({zl(b["offer"]["price"],cur)}'+(f', {b["offer"]["pack"]} szt.' if b['offer'].get('pack',1)>1 else '')+')' for b in line['buy'])
        rows.append([fmt(line['size']),line['sheets'],what,zl(line['cost'],cur)])
    return rows

def cutting_notes(plan):
    """Text for the order's UWAGI field when formats are cut from a board."""
    notes=[]
    for line in plan['lines']:
        for b in line['buy']:
            cut=b['offer'].get('cut')
            if cut:
                a,c=cut['grid'];L,S=ssize(line['size'])
                notes.append(f'{b["units"]}× arkusz {cut["board"][0]:g}x{cut["board"][1]:g} mm: proszę pociąć na {a*c} formatek {L:g} x {S:g} mm (piła {cut["kerf"]:g} mm).')
    return notes

def a3_plan(T):return T['single'].get('420x297')

def overview(d,res):
    s=res['supplier'];cur=s.get('currency','zł');d.new('podsumowanie');c=d.c
    c.setFillColor(INK);c.setFont(BOLD,22);c.drawString(M,d.y-4*mm,TITLE);d.y-=12*mm
    d.text(f'{naming.NAME}: sklejka na elementy konstrukcji domu. Ile arkuszy, jakich wymiarów i za ile, żeby kupić jak najmniej i jak najlepiej wykorzystać arkusze.',10)
    d.heading('Dostawca i ustawienia',11)
    tmap=', '.join(f'{k} → {v:g} mm' for k,v in (s.get('thickness_map') or {}).items()) or 'brak (grubości jak w projekcie)'
    bed=s.get('max_sheet_mm');bed=f'{max(bed):g} × {min(bed):g} mm' if bed else 'bez limitu'
    d.table([52],['Pozycja','Wartość'],[
        ['Dostawca',f'{s["name"]} {s.get("url","")}'],['Ceny z dnia',s.get('checked','')],
        ['Minimalny odstęp między elementami',f'{s["spacing_mm"]:g} mm'+(f' ({s["spacing_note"]})' if s.get('spacing_note') else '')],
        ['Margines od krawędzi arkusza',f'{s["margin_mm"]:g} mm (elementy tak długie jak arkusz zachowują krawędzie fabryczne na końcach)'],
        ['Szerokość cięcia piły dostawcy',f'{s.get("kerf_mm",0):g} mm (formatki cięte z dużego arkusza)'],
        ['Maksymalny arkusz na maszynie',bed],['Zamiana grubości',tmap],
        ['Narzędzia montażowe i próbki',('wliczone' if s.get('include_tools',True) else 'pominięte')+' (próbki T01/T02; szablon kąta dachu R05 jest z tektury)']]+
        ([['Uwagi dostawcy',s['note']]] if s.get('note') else []))
    d.heading('Zakres: tylko drewniane elementy konstrukcji domu',11)
    rows=[[thick(t),p['pieces'],p['profiles'],m2(p['area_m2'])] for t,p in sorted(res['parts'].items(),key=lambda kv:float(kv[0]))]
    d.table([30,30,30],['Grubość','Elementy','Profile','Powierzchnia elementów'],rows)
    left=res['left_out']
    d.text(f'Pominięte: {left.get("display",0)} elementów tylko do wizualizacji (meble, figurki rodziny Rowan, ogród z namiotem, drewutnia), '
           f'{left.get("bought",0)} kupowanych elementów z litego drewna i opakowań, {left.get("hardware",0)} pozycji okuć (zawiasy, magnesy, baterie) '
           f'i {left.get("fasteners",0)} wkrętów.',8,color=colors.grey)
    for g,G in res['grades'].items():
        d.heading(f'Rekomendacja: {grade_name(g)}',11)
        rows=[];notes=[]
        for t,T in G['thickness'].items():
            for r in purchase_rows(T['best'],cur):rows.append([thick(t)]+r)
            notes+=cutting_notes(T['best'])
        d.table([18,24,15,95],['Grubość','Format mm','Arkuszy','Co kupić (sztuk × produkt)','Koszt'],rows)
        a3=[a3_plan(T) for T in G['thickness'].values()]
        line=f'Razem {zl(G["cost"],cur)} · kupiona powierzchnia {m2(G["bought_m2"])} · pokrycie elementami {pct(G["used"])}'
        d.text(line,10,BOLD)
        if all(a3):
            cost=sum(p['cost'] for p in a3);bought=sum(p['bought_m2'] for p in a3)
            d.text(f'Dla porównania same arkusze A3 (420 × 297): {zl(cost,cur)}, {sum(len(p["sheets"]) for p in a3)} arkuszy, pokrycie {pct(G["part_m2"]/bought)}; '
                   f'rekomendacja jest tańsza o {zl(cost-G["cost"],cur)} ({pct((cost-G["cost"])/cost)}).',9)
        if notes:d.text('Do pola UWAGI w zamówieniu: '+' '.join(notes),9,color=RUST)
        simpler=[(t,T) for t,T in G['thickness'].items() if T['simple'] is not T['best']]
        if simpler:
            d.text('Prostsze zamówienie (najwyżej dwa formaty na grubość), gdy wiele formatów to kłopot:',9,BOLD)
            rows=[];notes=[]
            for t,T in simpler:
                for r in purchase_rows(T['simple'],cur):rows.append([thick(t)]+r)
                notes+=cutting_notes(T['simple'])
            d.table([18,24,15,95],['Grubość','Format mm','Arkuszy','Co kupić (sztuk × produkt)','Koszt'],rows)
            extra=sum(T['simple']['cost']-T['best']['cost'] for _,T in simpler)
            d.text(f'Razem z tym wariantem {zl(G["cost"]+extra,cur)} (drożej o {zl(extra,cur)}).'+(' Do pola UWAGI: '+' '.join(notes) if notes else ''),9)

def comparison(d,res):
    cur=res['supplier'].get('currency','zł')
    for g,G in res['grades'].items():
        d.new(f'porównanie, {grade_name(g)}');d.heading(f'Porównanie wariantów: {grade_name(g)}')
        d.text('Każdy wariant to pełne ułożenie wszystkich elementów danej grubości na arkuszach. Pokrycie to powierzchnia elementów podzielona przez kupioną powierzchnię arkuszy. Wyróżnione wiersze: rekomendacja (najtańsza), najprostsza (najwyżej dwa formaty) i najgęstsza (największe pokrycie). Formatki cięte z dużego arkusza kupuje się całym arkuszem; niewykorzystane formatki zostają jako zapas.',8,color=colors.grey)
        for t,T in G['thickness'].items():
            d.heading(f'{thick(t)}: najtańsze mieszanki formatów',10)
            top=T['plans'][:10]
            for extra in (T['simple'],T['densest']):
                if extra not in top:top.append(extra)
            def tag(p):return ' (rekomendacja)' if p is T['best'] else ' (najprostsza)' if p is T['simple'] else ' (najgęstsza)' if p is T['densest'] else ''
            rows=[[k+1,counts_text(p)+tag(p),len(p['sheets']),m2(p['bought_m2']),pct(p['used']),zl(p['cost'],cur)] for k,p in enumerate(top)]
            d.table([8,82,14,24,18],['#','Formaty i liczba arkuszy','Arkuszy','Kupiono','Pokrycie','Koszt'],rows,shade={k for k,p in enumerate(top) if tag(p)})
            d.heading(f'{thick(t)}: jeden format na wszystko',10)
            single=sorted(T['single'].values(),key=lambda p:p['cost'])
            rows=[[fmt(next(iter(p['counts']))),len(p['sheets']),m2(p['bought_m2']),pct(p['used']),zl(p['cost'],cur),zl(p['cost']-T['best']['cost'],cur)] for p in single]
            d.table([30,16,26,20,28],['Format mm','Arkuszy','Kupiono','Pokrycie','Koszt','Drożej o'],rows)
        if res.get('dropped') and any(res['dropped'].values()):
            d.text('Pominięte w wyszukiwaniu (większy format kosztuje tyle samo lub mniej przy każdej liczbie arkuszy): '+
                   '; '.join(f'{thick(t)}: '+', '.join(fmt(k) for k in v) for t,v in sorted(res['dropped'].items(),key=lambda kv:float(kv[0])) if v)+'.',8,color=colors.grey)

def price_list(d,res):
    cur=res['supplier'].get('currency','zł');d.new('cennik');d.heading('Cennik: cena za metr kwadratowy')
    d.text('Wszystkie oferty dostawcy dla potrzebnych grubości, od najtańszej za m². "Z arkusza" to formatki cięte przez dostawcę z dużego arkusza (cena za cały arkusz z cięciem, wymiar po odjęciu cięć piły).',8,color=colors.grey)
    by={}
    for o in res['offers']:
        if f'{float(o["thickness"]):g}' in res['parts']:by.setdefault((f'{float(o["thickness"]):g}',o.get('grade') or ''),[]).append(o)
    for (t,g),offers in sorted(by.items(),key=lambda kv:(float(kv[0][0]),kv[0][1])):
        d.heading(f'{thick(t)}, {grade_name(g)}',10)
        rows=[[f'{o["size"][0]:g} × {o["size"][1]:g}',o.get('pack',1),zl(o['price'],cur),zl(o['price']/o.get('pack',1),cur),zl(o['zl_m2'],cur),f'z arkusza {o["cut"]["board"][0]:g}×{o["cut"]["board"][1]:g}, cięcie na {o["pack"]} (piła {o["cut"]["kerf"]:g} mm)' if o.get('cut') else o['name']]
              for o in sorted(offers,key=lambda o:o['zl_m2'])]
        d.table([24,12,22,22,22],['Format mm','Szt.','Cena','Za arkusz','Za m²','Produkt'],rows,7)

def layouts(d,res):
    """The recommended sheets of the first grade, largest first, all of one thickness at one scale."""
    g,G=next(iter(res['grades'].items()))
    for t,T in G['thickness'].items():
        plan=T['best'];sheets=sorted(plan['sheets'],key=lambda s:-area(s['size']));d.new(f'rozkład {thick(t)}')
        d.heading(f'Rozkład elementów {thick(t)}: rekomendacja, {grade_name(g)}')
        d.text(f'{counts_text(plan)}. Wszystkie arkusze w jednej skali. Linia przerywana: margines {res["supplier"]["margin_mm"]:g} mm; odstęp między elementami co najmniej {res["supplier"]["spacing_mm"]:g} mm. Numery to identyfikatory części z instrukcji.',8,color=colors.grey)
        # Narrow strips sit four to a row, near-square sheets two; two rows fit a page.
        tall=max(s['height']/s['width'] for s in sheets);cols=1 if len(sheets)==1 else 4 if tall>=3 else 3 if tall>=1.8 else 2
        gap=6*mm;cw=(W-2*M-(cols-1)*gap)/cols;k=min(min(cw/s['width'],(112*mm if cols>1 else 200*mm)/s['height']) for s in sheets)
        for r in range(0,len(sheets),cols):
            row=sheets[r:r+cols];rh=max(s['height'] for s in row)*k;d.need(rh+12*mm);top=d.y-6*mm
            for j,s in enumerate(row):
                sheet(d.c,s,M+j*(cw+gap),top,k,f'Arkusz {r+j+1}: {fmt(s["size"])} mm · {len(s["items"])} el. · pokrycie {pct(sum(Polygon(i["outer"]).area for i in s["items"])/area(s["size"]))}',t)
            d.y=top-rh-5*mm

def sheet(c,s,x,top,k,caption,t):
    """One sheet at scale k hanging from `top` at x, its caption above."""
    sw,sh=s['width'],s['height'];ox=x;oy=top-sh*k
    c.setFillColor(INK);c.setFont(BOLD,7.5);c.drawString(x,top+2*mm,caption)
    c.setStrokeColor(INK);c.setLineWidth(.6);c.setFillColor(colors.white);c.rect(ox,oy,sw*k,sh*k,stroke=1,fill=1)
    x0,_,x1,_=s['window'];c.setDash(2,2);c.setStrokeColor(GRID);c.line(ox+x0*k,oy,ox+x0*k,oy+sh*k);c.line(ox+x1*k,oy,ox+x1*k,oy+sh*k)
    if s.get('edge'):c.line(ox,oy+s['edge']*k,ox+sw*k,oy+s['edge']*k);c.line(ox,oy+(sh-s['edge'])*k,ox+sw*k,oy+(sh-s['edge'])*k)
    c.setDash();fill=PART.get(t,PALE)
    for item in s['items']:
        pts=item['outer'];p=c.beginPath();p.moveTo(ox+pts[0][0]*k,oy+pts[0][1]*k)
        for px,py in pts[1:]:p.lineTo(ox+px*k,oy+py*k)
        p.close();c.setFillColor(fill);c.setStrokeColor(RUST);c.setLineWidth(.35);c.drawPath(p,stroke=1,fill=1)
        poly=Polygon(pts);a,b,cc,dd=poly.bounds;size=min(6.5,max(3.2,min(cc-a,dd-b)*k*.45))
        if max(cc-a,dd-b)*k>4*mm:
            pt=poly.representative_point();c.setFillColor(INK);c.setFont(REGULAR,size);c.drawCentredString(ox+pt.x*k,oy+pt.y*k-size*.35,item['part'])

def method(d,res):
    s=res['supplier'];d.new('metoda');d.heading('Metoda i założenia')
    for text in [
        f'Elementy: wszystkie płaskie części domu ze sklejki z aktualnego modelu (source/model.py), w liczbie sztuk z instrukcji. Bez mebli, figurek, ogrodu i drewutni (tylko wizualizacja), bez kupowanych listew z litego drewna, okuć i wkrętów.',
        f'Układanie: algorytm z projektu (nest.py) na siatce 1 mm, obrót o 90°, odstęp co najmniej {s["spacing_mm"]:g} mm między elementami i {s["margin_mm"]:g} mm od krawędzi. Każdy element trafia na pierwszy arkusz z miejscem; nowy arkusz to najmniejszy format, który go pomieści.',
        f'Wyszukiwanie: sprawdzono łącznie {res.get("variants","wiele")} pełnych ułożeń: dla każdej grubości każdy format osobno (dwie kolejności elementów), pary: format mieszczący wszystkie elementy z mniejszym, wszystkie formaty naraz oraz 1 do 4 dużych arkuszy na początek. Po ułożeniu najmniej zapełnione arkusze są opróżniane do wolnych miejsc na pozostałych, a w najtańszych wariantach każdy arkusz zastępowany jest tańszymi mniejszymi, jeśli mieszczą wszystkie jego elementy.',
        'Cena: najtańszy sposób kupienia potrzebnej liczby arkuszy z ofert dostawcy (pojedyncze arkusze i paczki, paczek nie dzieli się). Formatki z dużego arkusza liczone są jako cały arkusz z cięciem; wymiar formatki to arkusz pomniejszony o cięcia piły, podzielony równo.',
        'Pokrycie: powierzchnia obrysów elementów (bez wycięć okien i otworów) podzielona przez kupioną powierzchnię arkuszy.',
        'Nie uwzględniono: kierunku słojów (elementy mogą być obrócone o 90°), kosztu dostawy i cięcia kształtów. Przy zamianie grubości (np. 4 → 3 mm) obrysy pozostają jak w projekcie; przed zamówieniem trzeba przebudować projekt z nowymi grubościami.',
        'Kontrola rekomendacji i prostszego wariantu: każdy element ułożony dokładnie raz, w obrębie arkusza, z zachowanym odstępem. Wynik: OK (inaczej PDF nie powstaje).']:
        d.text(text,9)

def build(res,path):
    d=Doc(path,res['supplier']);overview(d,res);comparison(d,res);layouts(d,res);price_list(d,res);method(d,res);d.save();return path
