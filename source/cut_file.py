"""One DXF holding everything the supplier cuts, for shops that want the whole job in a single vector file.

    .venv/bin/python source/cut_file.py      # needs output/parts.json and output/nesting.json (make build)

Cutting paths only: no sheet frames, labels or engraving. Every A3 sheet keeps its validated nesting and sits in its
own 297 x 420 mm slot. The slots run in rows by thickness (3 mm, then 6 mm), left to right in sheet order, the order of
the reference maps in Lanternwood-House-Supplier.pdf. Each thickness has its own layer and colour (CUT_3MM ...), so laser
software can give each its own power. Outlines are closed, the fixed walls' factory blank ends included, so the file
still works when the shop re-nests onto larger boards; on a 420 mm A3 blank those two lines lie on the factory edge.
Blind pockets and holes, underside features and holes below the minimum drill are not in the file; the report in
output/reports/supplier-cut-file.json lists them.
"""
import json
from collections import Counter
from pathlib import Path
import cnc, naming, supplier
from dxf_r12 import DXF, COLOURS, thickness_layer as layer

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'output'/naming.SUPPLIER_CUT_DXF
REPORT=ROOT/'output/reports/supplier-cut-file.json'
COLUMNS=6;GAP=20;THICKNESS_GAP=60   # sheets per row; mm between sheets, and between thickness blocks

def layout(sheets):
    """Lower-left corner of each sheet's slot: one block of rows per thickness, first thickness at the top, so every
    coordinate is positive."""
    rows=[]
    for s in sheets:
        if not rows or rows[-1][0]['thickness']!=s['thickness'] or len(rows[-1])==COLUMNS:rows.append([])
        rows[-1].append(s)
    slots={};y=0
    for i in range(len(rows)-1,-1,-1):
        x=0
        for s in rows[i]:slots[s['id']]=(x,y);x+=s['width']+GAP
        if i:y+=max(s['height'] for s in rows[i])+(GAP if rows[i-1][0]['thickness']==rows[i][0]['thickness'] else THICKNESS_GAP)
    return slots

def build(data,nest,path=OUTPUT):
    """Write the cut file; return its report (layers, sheet slots and the features left out)."""
    sheets=supplier.sheets_for(data,nest,supplier.settings(data.get('config',{})))   # the supplier PDF's sheets and checks
    slots=layout(sheets);d=DXF();records=[];left_out=[];hand=[]
    for s in sheets:
        (ox,oy),name=slots[s['id']],layer(s['thickness']);curves=cnc.through_cuts(data,s)
        for kind,curve in curves:
            if kind=='circle':x,y,r=curve;d.circle(x+ox,y+oy,r,name)
            else:d.polyline([(x+ox,y+oy) for x,y in curve],name,closed=kind=='polygon')
        ops,by_hand=cnc.features(data,s);hand+=by_hand
        left_out+=[{'sheet':s['id'],'operation':op,'count':len(c)} for op,c in ops.items() if not cnc.is_through(op,s['thickness'])]
        records.append({'id':s['id'],'thickness_mm':s['thickness'],'layer':name,'origin_mm':[ox,oy],'size_mm':[s['width'],s['height']],'parts':len(s['items']),'paths':len(curves)})
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);d.save(path)
    layers={}
    for r in records:
        entry=layers.setdefault(r['layer'],{'thickness_mm':r['thickness_mm'],'colour':COLOURS.get(r['layer']),'sheets':0,'parts':0,'paths':0})
        entry['sheets']+=1;entry['parts']+=r['parts'];entry['paths']+=r['paths']
    width=max(r['origin_mm'][0]+r['size_mm'][0] for r in records);height=max(r['origin_mm'][1]+r['size_mm'][1] for r in records)
    return {'file':path.name,'format':'DXF R12 (AC1009), millimetres, 1:1','content':'cutting paths only: closed outlines, openings and through holes; no frames, text or engraving',
            'extent_mm':[width,height],'layers':layers,'sheets':records,'blind_operations_not_in_file':left_out,
            'hand_features_not_in_file':dict(Counter(f'{h["feature"]} D{h["diameter"]:g} ({h["reason_code"]})' for h in hand))}

def main():
    data=json.loads((ROOT/'output/parts.json').read_text());nest=json.loads((ROOT/'output/nesting.json').read_text())
    report=build(data,nest);REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2))
    print(f'{OUTPUT.relative_to(ROOT)}: {len(report["sheets"])} sheets, '+', '.join(f'{k} {v["paths"]} paths' for k,v in report['layers'].items())+
          f'; {report["extent_mm"][0]:g} x {report["extent_mm"][1]:g} mm')

if __name__=='__main__':main()
