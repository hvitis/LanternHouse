"""The released ZIP must carry the same passing evidence as the build reports."""

import json
import zipfile

import package
import pytest


@pytest.fixture
def project(tmp_path):
    (tmp_path / "output/reports").mkdir(parents=True)
    (tmp_path / "source").mkdir()
    (tmp_path / "source/model.py").write_text("model source")
    (tmp_path / "output/reports/release-validation.json").write_text(json.dumps({"all_pass": True}))
    for path in package.required_deliverables(tmp_path / "output"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"generated deliverable")
    return tmp_path


def tolerance(project, passed=True):
    (project / "output/reports/thickness-tolerance.json").write_text(
        json.dumps({"all_pass": passed})
    )


def test_release_package_contains_the_reports_and_manifest(project):
    tolerance(project)
    dest = package.create_package(project, require_tolerance=True)
    package.validate_release_kit(project / "output")
    with zipfile.ZipFile(dest) as archive:
        assert archive.read("Lanternwood-House/output/reports/thickness-tolerance.json")
        assert archive.read("Lanternwood-House/output/reports/release-validation.json")
        assert archive.read("Lanternwood-House/output/reports/build-manifest.json")


@pytest.mark.parametrize("condition", ["missing", "failed"])
def test_failed_or_missing_tolerance_cannot_replace_previous_kit(project, condition):
    kit = project / "output/Lanternwood-House-Build-Kit.zip"
    kit.write_bytes(b"previous kit")
    if condition == "failed":
        tolerance(project, False)
    with pytest.raises(RuntimeError, match="Package blocked"):
        package.create_package(project, require_tolerance=True)
    assert kit.read_bytes() == b"previous kit"


def test_release_rejects_nominal_kit_even_after_tolerance_runs(project):
    package.create_package(project)
    tolerance(project)
    with pytest.raises(RuntimeError, match="repackage"):
        package.validate_release_kit(project / "output")


def test_release_rejects_report_changed_after_packaging(project):
    tolerance(project)
    package.create_package(project, require_tolerance=True)
    (project / "output/reports/thickness-tolerance.json").write_text(
        '{"all_pass": true, "changed": true}'
    )
    with pytest.raises(RuntimeError, match="stale or missing packaged"):
        package.validate_release_kit(project / "output")


@pytest.mark.parametrize(
    "relative",
    [
        "pdf/Lanternwood-House-Complete.pdf",
        "Lanternwood-House-Supplier-Cut.dxf",
        "cad/LanternwoodHouse.FCStd",
    ],
)
@pytest.mark.parametrize("content", [None, b""])
def test_missing_or_empty_deliverable_preserves_previous_kit(project, relative, content):
    tolerance(project)
    kit = package.create_package(project, require_tolerance=True)
    previous = kit.read_bytes()
    path = project / "output" / relative
    if content is None:
        path.unlink()
    else:
        path.write_bytes(content)
    with pytest.raises(RuntimeError, match="missing or empty deliverables"):
        package.create_package(project, require_tolerance=True)
    assert kit.read_bytes() == previous


@pytest.mark.parametrize(
    "relative",
    [
        "pdf/Lanternwood-House-Complete.pdf",
        "Lanternwood-House-Supplier-Cut.dxf",
        "cad/LanternwoodHouse.step",
    ],
)
def test_release_rejects_deliverables_changed_after_packaging(project, relative):
    tolerance(project)
    package.create_package(project, require_tolerance=True)
    (project / "output" / relative).write_bytes(b"changed after packaging")
    with pytest.raises(RuntimeError, match="stale or missing packaged"):
        package.validate_release_kit(project / "output")


def test_release_rejects_tampered_archive(project):
    tolerance(project)
    kit = package.create_package(project, require_tolerance=True)
    with zipfile.ZipFile(kit) as archive:
        entries = {info.filename: archive.read(info) for info in archive.infolist()}
    entries["Lanternwood-House/output/cad/LanternwoodHouse.step"] = b"corrupt STEP"
    with zipfile.ZipFile(kit, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    with pytest.raises(RuntimeError, match="stale or missing packaged"):
        package.validate_release_kit(project / "output")


def test_release_notes_cover_every_uploaded_asset(project, monkeypatch):
    import naming
    import release

    output = project / "output"
    tolerance(project)
    package.create_package(project, require_tolerance=True)
    (output / "reports/cad-validation.json").write_text('{"freecad_version": "1.1.4"}')
    (output / "reports/release-validation.json").write_text('{"checks": []}')
    (output / "reports/pdf-report.json").write_text(
        json.dumps(
            {
                "pdfs": {
                    path.name: 1 for path in package.release_assets(output) if path.suffix == ".pdf"
                },
                "complete_pages": 1,
            }
        )
    )
    (output / "nesting.json").write_text('{"sheets": []}')
    monkeypatch.setattr(release, "ROOT", project)
    monkeypatch.setattr(release, "OUT", output)
    monkeypatch.setattr(release, "CUT", output / naming.SUPPLIER_CUT_DXF)
    monkeypatch.setattr(release, "KIT", output / naming.KIT_ZIP)
    monkeypatch.setattr(release, "git", lambda *_: "abc123")
    monkeypatch.setattr(release, "repo_url", lambda: None)

    notes = release.notes("v1.0.0")
    assert release.assets() == package.release_assets(output)
    assert len(release.assets()) == 12
    assert all(f"`{path.name}`" in notes for path in release.assets())
