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
        assert archive.read("Moomin-House/output/reports/thickness-tolerance.json")
        assert archive.read("Moomin-House/output/reports/release-validation.json")
        assert archive.read("Moomin-House/output/reports/build-manifest.json")


@pytest.mark.parametrize("condition", ["missing", "failed"])
def test_failed_or_missing_tolerance_cannot_replace_previous_kit(project, condition):
    kit = project / "output/Moomin-House-Build-Kit.zip"
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
