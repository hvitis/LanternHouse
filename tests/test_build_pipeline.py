"""A failed build or publication must leave the previous deliverables usable."""

import subprocess
from pathlib import Path

import pytest
import rebuild


@pytest.fixture
def project(tmp_path):
    (tmp_path / "source").mkdir()
    (tmp_path / "source/config.json").write_text("original source")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/BUILD-GUIDE.md").write_text("original guide")
    (tmp_path / "output").mkdir()
    (tmp_path / "output/old.pdf").write_bytes(b"previous successful build")
    return tmp_path


def test_failed_pipeline_preserves_previous_output_and_docs(project):
    def fail(workspace, *_):
        (workspace / "output/reports").mkdir(parents=True)
        (workspace / "output/reports/failure.json").write_text("diagnostic")
        (workspace / "docs/BUILD-GUIDE.md").write_text("unpublished")
        raise subprocess.CalledProcessError(1, "CAD")

    with pytest.raises(subprocess.CalledProcessError):
        rebuild.rebuild(project, "freecad-python", pipeline=fail)
    assert (project / "output/old.pdf").read_bytes() == b"previous successful build"
    assert (project / "docs/BUILD-GUIDE.md").read_text() == "original guide"
    assert list((project / ".build-work").glob("*/output/reports/failure.json"))


def finish(workspace, *_):
    (workspace / "output").mkdir()
    (workspace / "output/Moomin-House-Build-Kit.zip").write_bytes(b"new kit")
    (workspace / "docs/BUILD-GUIDE.md").write_text("new guide")


def test_success_publishes_complete_output_without_stale_files(project):
    rebuild.rebuild(project, "freecad-python", pipeline=finish)
    assert not (project / "output/old.pdf").exists()
    assert (project / "output/Moomin-House-Build-Kit.zip").read_bytes() == b"new kit"
    assert (project / "docs/BUILD-GUIDE.md").read_text() == "new guide"
    assert not list((project / ".build-work").iterdir())


def test_input_change_during_build_preserves_output(project):
    def changed(workspace, *_):
        finish(workspace)
        (project / "source/config.json").write_text("concurrent edit")

    with pytest.raises(RuntimeError, match="Inputs changed"):
        rebuild.rebuild(project, "freecad-python", pipeline=changed)
    assert (project / "output/old.pdf").exists()
    assert (project / "source/config.json").read_text() == "concurrent edit"


def test_document_publication_failure_rolls_back_output(project, monkeypatch):
    original = rebuild.shutil.copy2

    def fail_document(source, dest, **kwargs):
        if Path(dest) == project / "docs/BUILD-GUIDE.md":
            raise OSError("simulated full disk")
        return original(source, dest, **kwargs)

    monkeypatch.setattr(rebuild.shutil, "copy2", fail_document)
    with pytest.raises(OSError, match="full disk"):
        rebuild.rebuild(project, "freecad-python", pipeline=finish)
    assert (project / "output/old.pdf").read_bytes() == b"previous successful build"
    assert (project / "docs/BUILD-GUIDE.md").read_text() == "original guide"


def test_thickness_check_precedes_packaging_and_failure_stops_package(tmp_path):
    calls = []

    def runner(command, **_):
        calls.append(command)

    rebuild.run_pipeline(tmp_path, "cad-python", tolerance=True, runner=runner)
    names = [Path(command[1]).name for command in calls]
    assert names.index("verify.py") < names.index("thickness_check.py") < names.index("package.py")
    assert "--require-tolerance" in calls[-1]
    calls.clear()

    def failed(command, **_):
        calls.append(command)
        if Path(command[1]).name == "thickness_check.py":
            raise subprocess.CalledProcessError(1, command)

    with pytest.raises(subprocess.CalledProcessError):
        rebuild.run_pipeline(tmp_path, "cad-python", tolerance=True, runner=failed)
    assert all(Path(command[1]).name != "package.py" for command in calls)


def test_source_syntax_error_stops_before_starting_cad(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "book.py").write_text('text = f"{broken\\expression}"\n')
    calls = []

    with pytest.raises(SyntaxError):
        rebuild.run_pipeline(tmp_path, "cad-python", runner=lambda *args, **_: calls.append(args))

    assert calls == []
