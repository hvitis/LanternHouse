"""Export failures must preserve source files and the last working site."""
import json

import pytest

import export_viewer


@pytest.fixture
def site(tmp_path, monkeypatch, data):
    dest=tmp_path.resolve()/'site'
    monkeypatch.setattr(export_viewer,'model_data',lambda: data)
    export_viewer.export(dest)
    return dest


def test_export_contains_model_and_only_public_assets(site, data):
    assert json.loads((site/'data/parts.json').read_text(encoding='utf-8'))==json.loads(json.dumps(data))
    assert {str(p.relative_to(site)) for p in site.rglob('*') if p.is_file()}=={
        *export_viewer.ASSETS,'data/parts.json','HOUSE-LICENSE.txt','.nojekyll',export_viewer.MARKER,
    }


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


def test_reexport_removes_stale_files(site):
    (site/'stale.txt').touch()
    export_viewer.export(site)
    assert not (site/'stale.txt').exists()
