"""The web drawing must use current cutting geometry, even when output/ contains an older build."""
import copy
import json

import viewer_dxf


def job(tmp_path,monkeypatch):
    part={'id':'TEST','name':'Test part','category':'Walls','thickness':3,'width':50,'height':20,
          'quantity':1,'outer':[[0,0],[50,0],[50,20],[0,20]],'cuts':[],'holes':[]}
    cfg={'stock':{'main':{}},'nest_spacing':3,'stock_margin':10,'cnc':{},'supplier':{}}
    data={'parts':{'TEST':part},'config':cfg}
    sheet={'id':'PLY3-01','thickness':3,'width':297,'height':420,'spacing':3,'laser':False,'window':[10,0,287,420],
           'items':[{'part':'TEST','copy':1,'angle':0,'x':10,'y':10,'outer':[[10,10],[60,10],[60,30],[10,30]]}]}
    out=tmp_path/'output';out.mkdir()
    (out/'parts.json').write_text(json.dumps(data));(out/'nesting.json').write_text(json.dumps({'sheets':[sheet]}))
    monkeypatch.setattr(viewer_dxf,'ROOT',tmp_path)
    return data,sheet


def test_matching_production_layout_is_reused(tmp_path,monkeypatch):
    data,_=job(tmp_path,monkeypatch)
    def fail(*args):raise AssertionError('A matching production layout must not be re-nested')
    monkeypatch.setattr(viewer_dxf.nest,'nest_set',fail)
    text=viewer_dxf.drawing(data)
    assert 'CUT_3MM' in text and 'POLYLINE' in text and '60.000000' in text


def test_piece_ids_are_separate_from_cutting_paths(tmp_path,monkeypatch):
    data,_=job(tmp_path,monkeypatch)
    preview=viewer_dxf.preview(data)
    assert preview['labels']==[{'id':'TEST','copy':1,'layer':'CUT_3MM','x':35,'y':20}]
    assert 'TEXT' not in preview['dxf'] and 'TEST' not in preview['dxf']


def test_changed_part_cannot_reuse_stale_nesting(tmp_path,monkeypatch):
    data,sheet=job(tmp_path,monkeypatch)
    changed=copy.deepcopy(data);changed['parts']['TEST']['outer'][1][0]=55
    calls=[]
    def repack(current,*args):
        calls.append(current['parts']['TEST']['outer'][1][0]);return [sheet]
    monkeypatch.setattr(viewer_dxf.nest,'nest_set',repack)
    text=viewer_dxf.drawing(changed)
    assert calls==[55] and '65.000000' in text


def test_fresh_checkout_builds_dxf_without_generated_files(tmp_path,monkeypatch):
    data,sheet=job(tmp_path,monkeypatch)
    (tmp_path/'output/nesting.json').unlink()
    monkeypatch.setattr(viewer_dxf.nest,'nest_set',lambda *args:[sheet])
    assert 'POLYLINE' in viewer_dxf.drawing(data)
