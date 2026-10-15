"""A3 nesting: true-shape placement keeps the lane spacing, uses a part's hollows, and the squeeze pass joins sheets."""
from shapely.geometry import Polygon, box
import nest, stock

RULES=nest.cnc_rules(12,10)

def place_all(sheet,parts):
    for pid,poly in parts:
        found=nest.try_place(pid,poly,sheet);assert found,pid
        angle,x,y,pp,bp=found;sheet['placed'].append(pp);sheet['items'].append({'part':pid,'outer':list(pp.exterior.coords)[:-1]});nest.update_grid(sheet,pp)
    return sheet['placed']

def test_a_small_part_goes_into_the_hollow_of_a_ring():
    # A C-shaped ring half fills the sheet's width; its 200 x 150 hollow is the only room left beside it.
    ring=Polygon([(0,0),(277,0),(277,380),(0,380),(0,330),(237,330),(237,50),(0,50)])
    sheet=nest.new_sheet(6,297,420,RULES)
    c,small=place_all(sheet,[('R',ring),('S',box(0,0,60,60))])
    assert small.within(Polygon([(10,50),(247,50),(247,340),(10,340)])),small.bounds   # inside the hollow
    assert c.distance(small)>=12-.02

def test_spacing_holds_for_every_placed_pair():
    parts=[(f'P{k}',Polygon([(0,0),(40+k*7,0),(0,30+k*5)])) for k in range(12)]+[(f'Q{k}',box(0,0,25,90)) for k in range(6)]
    placed=place_all(nest.new_sheet(3,297,420,RULES),parts)
    assert all(a.distance(b)>=12-.05 for i,a in enumerate(placed) for b in placed[i+1:])

def test_squeeze_joins_two_half_empty_sheets():
    units=[('A',1,box(0,0,120,120)),('B',1,box(0,0,120,120))]
    def repack(us):return stock.pack(6.0,us,[],RULES,'420x297',999)
    sheets=repack(units[:1])+repack(units[1:])
    joined=stock.squeeze(6.0,sheets,{u[:2]:u for u in units},repack)
    assert len(sheets)==2 and len(joined)==1 and len(joined[0]['items'])==2
