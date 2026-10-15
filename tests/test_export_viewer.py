"""Export failures must preserve source files and the last working site."""
import json

import pytest

import export_viewer


@pytest.fixture
def site(tmp_path, monkeypatch, data):
    dest=tmp_path.resolve()/'site'
    monkeypatch.setattr(export_viewer,'model_data',lambda: data)
    monkeypatch.setattr(export_viewer,'viewer_cut_file',lambda _: {'dxf':'0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n','labels':[]})
    export_viewer.export(dest)
    return dest


def test_export_contains_model_and_only_public_assets(site, data):
    assert json.loads((site/'data/parts.json').read_text(encoding='utf-8'))==json.loads(json.dumps(data))
    published=json.loads((export_viewer.ROOT/'prints/manifest.json').read_text(encoding='utf-8'))['parts']
    prints={f'prints/{f["path"]}' for entry in published.values() for f in entry['files'].values()}
    assert {str(p.relative_to(site)) for p in site.rglob('*') if p.is_file()}=={
        *export_viewer.ASSETS,'data/parts.json','data/house.dxf','data/dxf-labels.json','HOUSE-LICENSE.txt','.nojekyll',export_viewer.MARKER,
        'prints/manifest.json',*prints,
    }


def test_preview_colours_match_exported_dxf_layers(data, tmp_path):
    from dxf_r12 import DXF, thickness_layer
    from model import BOUGHT
    from ezdxf import readfile
    from ezdxf.colors import aci2rgb

    drawing=DXF()
    plywood=[p for p in data['parts'].values() if not p.get('render_only') and p['category'] not in BOUGHT
             and (data['config']['supplier']['include_optional'] or not p.get('optional'))]
    for p in plywood:drawing.polyline(p['outer'],thickness_layer(p['thickness']))
    drawing.save(tmp_path/'preview-colours.dxf')
    exported=readfile(tmp_path/'preview-colours.dxf')
    assert {p['thickness']:p['dxf']['color'] for p in plywood}=={3:'#ff0000',6:'#00ff00'}
    for p in plywood:
        layer=exported.layers.get(p['dxf']['layer'])
        assert layer.color==p['dxf']['aci']
        assert '#'+''.join(f'{c:02x}' for c in aci2rgb(layer.color))==p['dxf']['color']
    assert all('dxf' not in p for p in data['parts'].values() if p not in plywood)


@pytest.mark.parametrize('folder',['.','source','source/viewer','docs','tests','original','output','.github','.venv','..'])
def test_export_refuses_repository_and_parent_folders(folder):
    with pytest.raises(SystemExit,match='Refusing to replace'):
        export_viewer.export(export_viewer.ROOT/folder)


def test_export_refuses_unrelated_existing_directory(tmp_path):
    dest=tmp_path.resolve()/'personal'
    dest.mkdir()
    (dest/'keep.txt').write_text('keep')
    with pytest.raises(SystemExit,match='not a viewer export'):
        export_viewer.export(dest)
    assert (dest/'keep.txt').read_text()=='keep'


def test_export_refuses_symlink(tmp_path, site):
    link=tmp_path.resolve()/'link'
    link.symlink_to(site,target_is_directory=True)
    with pytest.raises(SystemExit,match='Refusing to replace'):
        export_viewer.export(link)
    assert (site/'index.html').exists()


def test_failed_model_build_preserves_previous_site(site, monkeypatch):
    previous=(site/'data/parts.json').read_bytes()
    def fail():
        raise SystemExit('invalid configuration')
    monkeypatch.setattr(export_viewer,'model_data',fail)
    with pytest.raises(SystemExit,match='invalid configuration'):
        export_viewer.export(site)
    assert (site/'data/parts.json').read_bytes()==previous


def test_failed_dxf_build_preserves_previous_site(site, monkeypatch):
    previous=(site/'data/house.dxf').read_bytes()
    def fail(_):raise ValueError('invalid cutting geometry')
    monkeypatch.setattr(export_viewer,'viewer_cut_file',fail)
    with pytest.raises(ValueError,match='invalid cutting geometry'):
        export_viewer.export(site)
    assert (site/'data/house.dxf').read_bytes()==previous


def test_reexport_removes_stale_files(site):
    (site/'stale.txt').touch()
    export_viewer.export(site)
    assert not (site/'stale.txt').exists()
