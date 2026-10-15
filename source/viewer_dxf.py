"""Build the preview's supplier DXF without FreeCAD, reusing matching production nesting."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import cut_file
import nest
from model import BOUGHT

ROOT=Path(__file__).resolve().parents[1]

def geometry_key(data):
    """Only inputs used by nesting and cutting; CAD-only joints and rendered scenery do not affect the drawing."""
    fields=('thickness','outer','outercircle','cuts','holes','retained_edges','quantity','optional')
    parts={pid:{k:p[k] for k in fields if k in p} for pid,p in data['parts'].items()
           if not p.get('render_only') and p['category'] not in BOUGHT}
    cfg=data['config']
    return json.dumps([parts,{k:cfg[k] for k in ('stock','nest_spacing','stock_margin','cnc','supplier')}],sort_keys=True)

def preview(data):
    """Return the cutting file and label positions. Labels never enter the manufacturing DXF."""
    cached=None
    try:
        previous=json.loads((ROOT/'output/parts.json').read_text())
        candidate=json.loads((ROOT/'output/nesting.json').read_text())
        if geometry_key(previous)==geometry_key(data):
            cut_file.supplier.sheets_for(data,candidate,cut_file.supplier.settings(data['config']))
            nest.validate(candidate['sheets'])
            if all(s['spacing']==data['config']['nest_spacing'] for s in candidate['sheets']):cached=candidate
    except (OSError,ValueError,KeyError,AssertionError):
        pass
    if cached is None:
        cfg=data['config']
        sheets=nest.nest_set(data,lambda p:not p.get('render_only') and not p.get('optional'),'PLY',cfg['stock']['main'])
        nest.validate(sheets)
        cached={'sheets':sheets,'optional_sheets':[]}
    labels=[]
    sheets=cut_file.supplier.sheets_for(data,cached,cut_file.supplier.settings(data['config']))
    slots=cut_file.layout(sheets)
    for sheet in sheets:
        ox,oy=slots[sheet['id']]
        for item in sheet['items']:
            p=data['parts'][item['part']]
            x,y=cut_file.cnc.transform(p,item,p['width']/2,p['height']/2)
            labels.append({'id':item['part'],'copy':item['copy'],'layer':cut_file.layer(sheet['thickness']),'x':x+ox,'y':y+oy})
    with TemporaryDirectory(prefix='moomin-viewer-dxf-') as temporary:
        path=Path(temporary)/'house.dxf'
        cut_file.build(data,cached,path)
        return {'dxf':path.read_text(),'labels':labels}

def drawing(data):
    return preview(data)['dxf']
