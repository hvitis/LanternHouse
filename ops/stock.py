"""Interactive plywood purchase planner: "Optymalne wymiary i cennik".

Pick or create a supplier, type the sheet sizes and prices it offers, and get a PDF with the cheapest sheet sizes
and quantities for the house, the variants they beat, the price list per square metre and the sheet layouts.
Suppliers are saved as ops/suppliers/<name>.json and can be reused, edited or copied for the next supplier.

    make stock                                                    # interactive
    .venv/bin/python ops/stock.py --supplier ops/suppliers/sklejka-krakow.json --yes   # no questions

Offer lines (one per line while editing offers):
    6 420x297 8.71                                  thickness, size, price per sheet
    6 297x210 147.60 x50 kl 1/2 Zestaw 50 A4        a pack of 50, grade 1/2, a name
    6 1525x1525 138.38 cięcie 4=142.80 8=143.98     a board the supplier cuts: up to 4 pieces for 142.80, 8 for 143.98
"""
from __future__ import annotations
import argparse, json, re, sys, time, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'))
import stock

SUPPLIERS=ROOT/'ops/suppliers'
DEFAULTS={'kerf_mm':3,'spacing_mm':3,'margin_mm':10,'max_sheet_mm':None,'thickness_map':{},'include_tools':True,'currency':'zł','grades':['2']}

def slug(name):
    name=unicodedata.normalize('NFKD',name.replace('ł','l').replace('Ł','L')).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-') or 'dostawca'

def number(text):return float(text.replace(',','.'))
def size(text):
    m=re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*[x×*]\s*(\d+(?:[.,]\d+)?)',text.strip())
    if not m:raise ValueError(f'wymiar "{text}" nie ma postaci 420x297')
    return sorted((number(m.group(1)),number(m.group(2))),reverse=True)

def parse_offer(line,grades=()):
    """'6 1525x1525 138.38 x1 kl 1/2 cięcie 4=142.80 8=143.98 Nazwa' -> offer dict."""
    words=line.split()
    if len(words)<3:raise ValueError('potrzebne co najmniej: grubość, wymiar, cena')
    o={'thickness':number(words[0]),'size':size(words[1]),'price':number(words[2]),'pack':1};rest=words[3:];name=[];k=0
    while k<len(rest):
        w=rest[k]
        if re.fullmatch(r'x\d+',w):o['pack']=int(w[1:])
        elif w.lower() in ('kl','kl.','klasa') and k+1<len(rest):o['grade']=rest[k+1].replace('2/2','2');k+=1
        elif w.lower() in ('cięcie','ciecie','cut'):
            tiers=[]
            while k+1<len(rest) and re.fullmatch(r'\d+=\d+(?:[.,]\d+)?',rest[k+1]):
                n,p=rest[k+1].split('=');tiers.append({'pieces':int(n),'price':number(p)});k+=1
            if not tiers:raise ValueError('po "cięcie" podaj progi, np. 4=142.80 8=143.98')
            o['cutting']=tiers
        else:name.append(w)
        k+=1
    o['thickness']=int(o['thickness']) if o['thickness'].is_integer() else o['thickness']
    o['name']=' '.join(name) or f'Sklejka {o["thickness"]:g} mm {o["size"][0]:g}x{o["size"][1]:g}'+(f' ({o["pack"]} szt.)' if o['pack']>1 else '')
    if grades and not o.get('grade'):o['grade']=grades[0]
    return o

def ask(prompt,default=None,cast=str):
    while True:
        hint=f' [{default}]' if default not in (None,'') else ''
        try:text=input(f'{prompt}{hint}: ').strip()
        except EOFError:text=''
        if not text:
            if default is None:print('  (wymagane)');continue
            text=str(default)
        try:return cast(text)
        except ValueError as e:print(f'  {e}')

def yes(prompt,default=True):
    try:text=input(f'{prompt} {"[T/n]" if default else "[t/N]"}: ').strip().lower()
    except EOFError:text=''
    return default if not text else text in ('t','tak','y','yes')

def describe(p):
    return (f'{p["name"]}: {len(p["offers"])} ofert, odstęp {p["spacing_mm"]:g} mm, margines {p["margin_mm"]:g} mm, '
            f'piła {p.get("kerf_mm",0):g} mm'+(f', ceny z {p["checked"]}' if p.get('checked') else ''))

def bed(text):
    return None if text in ('','-','brak','0') else size(text)
def tmap(text):
    if text in ('','-','brak'):return {}
    out={}
    for pair in re.split(r'[,; ]+',text):
        a,b=pair.split('=');out[f'{number(a):g}']=number(b)
    return out

def settings(p):
    p['name']=ask('Nazwa dostawcy',p.get('name'))
    p['url']=ask('Strona www (- = brak)',p.get('url') or '-');p['url']='' if p['url']=='-' else p['url']
    p['kerf_mm']=ask('Szerokość cięcia piły dostawcy przy cięciu formatek [mm]',f'{p.get("kerf_mm",3):g}',number)
    print('  Odstęp między elementami zależy od tego, kto wycina kształty: frezarka CNC około 12 mm, laser około 3 mm.')
    p['spacing_mm']=ask('Minimalny odstęp między elementami [mm]',f'{p.get("spacing_mm",3):g}',number)
    p['margin_mm']=ask('Margines od krawędzi arkusza [mm]',f'{p.get("margin_mm",10):g}',number)
    old=p.get('max_sheet_mm');p['max_sheet_mm']=ask('Największy arkusz, jaki przyjmie maszyna, np. 1300x2500 (- = bez limitu)',f'{old[0]:g}x{old[1]:g}' if old else '-',bed)
    old=','.join(f'{k}={v:g}' for k,v in (p.get('thickness_map') or {}).items())
    p['thickness_map']=ask('Zamiana grubości, której dostawca nie ma, np. 4=3,8=6 (- = brak)',old or '-',tmap)
    old=','.join(p.get('grades') or [])
    g=ask('Klasy sklejki do porównania, np. 1/2,2 (- = bez klas)',old or '-',str)
    p['grades']=[] if g in ('-','') else [x.strip().replace('2/2','2') for x in g.split(',') if x.strip()]
    p['include_tools']=yes('Wliczyć próbki pasowania (T01, T02)?',p.get('include_tools',True))
    p['checked']=ask('Data cen',p.get('checked') or time.strftime('%Y-%m-%d'))
    return p

def show(p,t=None):
    for k,o in enumerate(p['offers'],1):
        if t is not None and float(o['thickness'])!=t:continue
        tiers=' cięcie '+' '.join(f'{c["pieces"]}={c["price"]:g}' for c in o['cutting']) if o.get('cutting') else ''
        print(f'  {k:3}) {o["thickness"]:g} mm  {o["size"][0]:g}x{o["size"][1]:g}  {o["price"]:.2f} {p.get("currency","zł")}'
              +(f'  x{o["pack"]}' if o.get('pack',1)>1 else '')+(f'  kl {o["grade"]}' if o.get('grade') else '')+tiers+f'  {o["name"]}')

def edit_offers(p):
    print('\nOferty: wpisz po jednej w wierszu. Pusty wiersz lub "gotowe" kończy.')
    print('  GRUBOŚĆ WYMIAR CENA [xSZTUK] [kl KLASA] [cięcie N=CENA ...] [nazwa]')
    print('  np. 6 420x297 8.71   |   6 297x210 147.60 x50 kl 1/2   |   6 1525x1525 138.38 cięcie 4=142.80 8=143.98')
    print('  Polecenia: lista [GRUBOŚĆ], usuń NR, wyczyść GRUBOŚĆ')
    while True:
        try:line=input('> ').strip()
        except EOFError:line=''
        if line.lower() in ('','gotowe','koniec'):return p
        cmd,_,arg=line.partition(' ')
        try:
            if cmd.lower()=='lista':show(p,number(arg) if arg else None)
            elif cmd.lower() in ('usuń','usun'):o=p['offers'].pop(int(arg)-1);print(f'  usunięto: {o["name"]}')
            elif cmd.lower() in ('wyczyść','wyczysc'):
                t=number(arg);n=len(p['offers']);p['offers']=[o for o in p['offers'] if float(o['thickness'])!=t];print(f'  usunięto {n-len(p["offers"])} ofert {t:g} mm')
            else:
                o=parse_offer(line,p.get('grades') or ());p['offers'].append(o);print(f'  dodano: {o["thickness"]:g} mm {o["size"][0]:g}x{o["size"][1]:g} {o["price"]:.2f} x{o["pack"]}'+(f' kl {o["grade"]}' if o.get('grade') else ''))
        except (ValueError,IndexError) as e:print(f'  nie rozumiem: {e}')

def needed(p,data):
    units,_=stock.house_parts(data,p.get('thickness_map'),p.get('include_tools',True))
    have={f'{float(o["thickness"]):g}' for o in p['offers']}
    return sorted(units,key=float),[t for t in sorted(units,key=float) if t not in have]

def choose(args):
    if args.supplier:return stock.load_profile(args.supplier),Path(args.supplier)
    files=sorted(SUPPLIERS.glob('*.json'));profiles=[stock.load_profile(f) for f in files]
    print('\nDostawcy (ops/suppliers):')
    for k,p in enumerate(profiles,1):print(f'  {k}) {describe(p)}')
    print('  n) nowy dostawca')
    while True:
        pick=ask('Wybierz',1 if profiles else 'n').lower()
        if pick=='n':
            p=settings(dict(DEFAULTS,name='',offers=[]));return p,SUPPLIERS/f'{slug(p["name"])}.json'
        if pick.isdigit() and 1<=int(pick)<=len(profiles):return profiles[int(pick)-1],files[int(pick)-1]
        print('  podaj numer z listy albo n')

def run(p,data,out,workers):
    t0=time.time();res=stock.optimize(data,p,workers=workers,progress=lambda m:print('  '+m,flush=True))
    import stock_report
    out.parent.mkdir(parents=True,exist_ok=True);stock_report.build(res,out)
    summary=ROOT/'output/reports'/f'{out.stem}.json';summary.parent.mkdir(parents=True,exist_ok=True);summary.write_text(json.dumps(stock.summary(res),ensure_ascii=False,indent=1))
    cur=p.get('currency','zł');print(f'\nGotowe w {time.time()-t0:.0f} s. Wariantów ułożenia: {res["variants"]}.')
    for g,G in res['grades'].items():
        print(f'\n{("Klasa "+g) if g else "Rekomendacja"}: {G["cost"]:.2f} {cur}, pokrycie {100*G["used"]:.1f} %')
        for t,T in G['thickness'].items():
            b=T['best'];print(f'  {t} mm: '+', '.join(f'{n}× {k}' for k,n in sorted(b['counts'].items(),key=lambda kv:-stock.area(kv[0])))+f'  = {b["cost"]:.2f} {cur} (pokrycie {100*b["used"]:.1f} %)')
    print(f'\nPDF:  {out}\nJSON: {summary}')
    return res

def main():
    ap=argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--supplier',help='profil dostawcy (JSON); bez tego: wybór z listy')
    ap.add_argument('--yes',action='store_true',help='bez pytań: profil jak jest, od razu obliczenia')
    ap.add_argument('--parts',help='output/parts.json zamiast budowania modelu (szybciej, ale może być nieaktualny)')
    ap.add_argument('--out',help='ścieżka PDF (domyślnie output/pdf/Optymalne-wymiary-i-cennik-<dostawca>.pdf)')
    ap.add_argument('--workers',type=int,help='liczba procesów (domyślnie do 8)')
    args=ap.parse_args()
    print('Optymalne wymiary i cennik: zakup sklejki na Domek Muminków')
    p,path=choose(args)
    if not args.yes:
        print('\n'+describe(p))
        if p.get('offers') and yes('Zmienić ustawienia dostawcy?',False):settings(p)
        if not p.get('offers') or yes('Dodać, zmienić lub usunąć oferty?',False):edit_offers(p)
    print('\nWczytywanie modelu domu...',flush=True)
    data=json.loads(Path(args.parts).read_text()) if args.parts else __import__('model').build()
    while True:
        need,missing=needed(p,data)
        if not missing:break
        print(f'\nDom potrzebuje grubości {", ".join(need)} mm; brak ofert dla: {", ".join(missing)} mm.')
        if args.yes:sys.exit('Dodaj oferty albo zamianę grubości w profilu dostawcy.')
        if yes('Zamienić brakujące grubości na inne (np. 4=3)?',True):p['thickness_map'].update(ask('Zamiana, np. 4=3,8=6','-',tmap))
        else:edit_offers(p)
    stock.check_profile(p)
    if not args.yes and yes(f'Zapisać dostawcę do {path.relative_to(ROOT)}?',True):SUPPLIERS.mkdir(parents=True,exist_ok=True);stock.save_profile(p,path);print(f'  zapisano {path.relative_to(ROOT)}')
    out=Path(args.out) if args.out else ROOT/'output/pdf'/f'Optymalne-wymiary-i-cennik-{slug(p["name"])}.pdf'
    print('\nObliczenia (zwykle 1 do 3 minut)...',flush=True);run(p,data,out,args.workers)

if __name__=='__main__':main()
