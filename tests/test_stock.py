"""Plywood purchase optimizer: part selection, pricing, board formats, nesting checks, the supplier script and PDF."""
import importlib.util, json
from pathlib import Path
import pytest
from pypdf import PdfReader
import stock
from model import BOUGHT

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ops_stock',ROOT/'ops/stock.py');ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

def test_only_wooden_house_parts_are_counted(data):
    units,left=stock.house_parts(data)
    counted={pid for u in units.values() for pid,_,_ in u}
    for pid in counted:
        p=data['parts'][pid]
        assert not p.get('render_only') and p['category'] not in stock.DISPLAY+BOUGHT,pid
    expected=sum(p['quantity'] for p in data['parts'].values() if not p.get('render_only') and p['category'] not in stock.DISPLAY+BOUGHT)
    assert sum(len(u) for u in units.values())==expected
    # The garden scene and the woodpile stand around the house: display only, never on a sheet.
    assert not counted & {'GT1','GB1','GG2','GW1','GH1','GX1','GL01','WP1','WP2','WP3'}
    assert {'W01','F00','R01','P01','J01'}<=counted
    assert left['display']>0 and left['bought']>0 and left['hardware']>0 and left['fasteners']>0

def test_woodpile_is_display_only(data):
    for pid in ('WP1','WP2','WP3'):
        assert data['parts'][pid]['category']=='Furniture' and data['parts'][pid]['render_only']
    assert {i['group'] for i in data['instances'] if i['part'] in ('WP1','WP2','WP3')}=={'Furniture'}

def test_thickness_map_moves_parts(data):
    units,_=stock.house_parts(data,{'4':3,'8':6})
    assert set(units)=={'3','6'}
    plain,_=stock.house_parts(data)
    assert len(units['3'])==len(plain['3'])+len(plain.get('4',[])) and len(units['6'])==len(plain['6'])+len(plain.get('8',[]))

def test_tools_can_be_left_out(data):
    units,left=stock.house_parts(data,tools=False)
    assert not {pid for u in units.values() for pid,_,_ in u}&{'R05','T01','T02'} and left['tools']>0

def test_buy_mixes_singles_and_whole_packs():
    single,pack=(1,4.0,'single'),(10,30.0,'pack')
    assert stock.buy(3,[single,pack])==(12.0,[('single',3)])
    assert stock.buy(8,[single,pack])==(30.0,[('pack',1)])
    assert stock.buy(11,[single,pack])==(34.0,[('single',1),('pack',1)])

def test_board_formats_subtract_the_kerf():
    p={'name':'T','spacing_mm':12,'margin_mm':10,'kerf_mm':3,'offers':[{'thickness':6,'size':[1525,1525],'price':100,'cutting':[{'pieces':4,'price':104},{'pieces':8,'price':105}]}]}
    f={(tuple(o['size']),o['pack']):o['price'] for o in stock.board_formats(p)}
    assert f[((761,761),4)]==104 and f[((1525,761),2)]==104 and f[((1525,506),3)]==104
    assert f[((761,506),6)]==105 and f[((761,379),8)]==105
    assert all(o['pack']<=8 and min(o['size'])>=stock.MIN_FORMAT for o in stock.board_formats(p))

def test_dominated_sizes_are_dropped():
    opts={'420x297':[(1,8.0,None)],'500x300':[(1,7.5,None)],'297x210':[(1,3.0,None)]}
    assert stock.dominated(opts)=={'420x297'}

def test_pack_keeps_spacing_and_places_every_piece():
    from shapely.geometry import box
    units=[(f'X{k}',1,box(0,0,40,30)) for k in range(9)]+[('L',1,box(0,0,180,20))]
    r=stock.rules(5,10);units.sort(key=stock.ORDERS['box'])
    sheets=stock.pack('6',units,['200x100','120x100'],r)
    plan={'sheets':[stock.strip(s) for s in sheets]}
    assert stock.check(plan,units)==[]
    with pytest.raises(ValueError):stock.pack('6',[('L',1,box(0,0,300,20))],['200x100'],r)

def test_offer_lines_from_the_script():
    o=ops.parse_offer('6 1525x1525 138,38 cięcie 4=142.80 8=143,98 Arkusz do cięcia',['1/2'])
    assert o['size']==[1525,1525] and o['price']==138.38 and o['grade']=='1/2' and o['name']=='Arkusz do cięcia'
    assert o['cutting']==[{'pieces':4,'price':142.8},{'pieces':8,'price':143.98}]
    o=ops.parse_offer('3 297x210 147.60 x50 kl 2/2')
    assert (o['thickness'],o['size'],o['pack'],o['grade'])==(3,[297,210],50,'2')
    with pytest.raises(ValueError):ops.parse_offer('6 420-297 8.71')
    assert ops.slug('Sklejka Kraków')=='sklejka-krakow' and ops.tmap('4=3,8=6')=={'4':3.0,'8':6.0}

def test_example_supplier_profile():
    p=stock.load_profile(ROOT/'ops/suppliers/sklejka-krakow.json')
    assert p['kerf_mm']==3 and any(o['size']==[420,297] for o in p['offers'])
    for t in (3,6):
        for g in p['grades']:assert '420x297' in stock.offers(p,g)[f'{t}']

def test_profile_round_trip(tmp_path):
    p=stock.load_profile(ROOT/'ops/suppliers/sklejka-krakow.json');stock.save_profile(p,tmp_path/'p.json')
    assert json.loads((tmp_path/'p.json').read_text())==p

def test_optimize_and_report(tmp_path):
    """A small house on two sizes: the cheapest plan is found, checked, and printed."""
    def part(w,h,q,t=6,cat='Structure'):return {'outer':[[0,0],[w,0],[w,h],[0,h]],'quantity':q,'thickness':t,'category':cat}
    data={'parts':{'A':part(150,80,4),'B':part(60,40,6),'C':part(20,20,3,3),'F':part(50,50,2,6,'Furniture'),'S':part(10,10,4,6,'Purchased wood')},'hardware':[],'fasteners':[]}
    data['parts']['F']['render_only']=True
    profile={'name':'Test','spacing_mm':5,'margin_mm':5,'kerf_mm':3,'currency':'zł','offers':[
        {'thickness':6,'size':[200,100],'price':10},{'thickness':6,'size':[100,60],'price':2},
        {'thickness':3,'size':[100,60],'price':1},{'thickness':6,'size':[420,297],'price':40}]}
    res=stock.optimize(data,profile,workers=2,progress=lambda m:None)
    G=res['grades']['']
    assert res['parts']['6']['pieces']==10 and res['parts']['3']['pieces']==3
    best=G['thickness']['6']['best'];assert best['cost']<=40 and stock.check(best,stock.house_parts(data)[0]['6'])==[]
    assert G['thickness']['3']['best']['counts']=={'100x60':1}
    path=__import__('stock_report').build(res,tmp_path/'r.pdf')
    text=''.join(page.extract_text() for page in PdfReader(path).pages)
    assert 'Optymalne wymiary i cennik' in text and 'Rekomendacja' in text and 'Porównanie wariantów' in text and 'Cennik' in text
    json.dumps(stock.summary(res))
