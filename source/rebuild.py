"""Build in an isolated workspace and publish only a complete, checked result."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "source",
    "docs",
    "tests",
    "prints",
    ".github",
    "ops",
    "requirements",
    "README.md",
    "README.pl.md",
    "LICENSE",
    "Makefile",
    "package.json",
    "package-lock.json",
    "pytest.ini",
    "pyproject.toml",
    ".gitignore",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(root=ROOT):
    """Explicitly discard generated output, including local sample logs."""
    out = root / "output"
    if out.is_symlink():
        raise RuntimeError("Refusing to clean a symlinked output directory")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()


def snapshot(root, workspace):
    baseline = {}
    for name in INPUTS:
        source, dest = root / name, workspace / name
        if not source.exists():
            continue
        if source.is_dir():
            shutil.copytree(
                source, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
            )
            for path in dest.rglob("*"):
                if path.is_file():
                    baseline[str(path.relative_to(workspace))] = digest(path)
        else:
            shutil.copy2(source, dest)
            baseline[name] = digest(dest)
    return baseline


def run_pipeline(workspace, freecad_python, lang="pl", tolerance=False, runner=subprocess.run):
    print("Checking source syntax before CAD build", flush=True)
    for path in sorted((workspace / "source").rglob("*.py")):
        compile(path.read_bytes(), str(path), "exec")
    env = dict(os.environ, LANTERNWOOD_HEADLESS="1", QT_QPA_PLATFORM="offscreen")

    def run(script, cad=False, args=()):
        print(f"Building: {script}", flush=True)
        runner(
            [freecad_python if cad else sys.executable, str(workspace / "source" / script), *args],
            cwd=workspace,
            env=env,
            check=True,
        )

    for script in ("build_cad.py", "audit_connections.py"):
        run(script, cad=True)
    for script in (
        "nest.py",
        "stackup.py",
        "risk_audit.py",
        "render.py",
        "cover.py",
        "readme_images.py",
        "decorate_cad.py",
    ):
        run(script)
    run("specifications.py", args=("--from-build",))
    run("book.py", args=("--lang", lang))
    run("cut_file.py")
    run("verify.py")
    if tolerance:
        run("thickness_check.py", cad=True)
    run("package.py", args=("--require-tolerance",) if tolerance else ())


def publish(root, workspace, baseline):
    """Rollback output and generated documentation if publication fails."""
    for name, expected in baseline.items():
        if not (root / name).is_file() or digest(root / name) != expected:
            raise RuntimeError(
                f"Inputs changed during the build: {name}. The previous output is preserved."
            )
    output, built, previous = root / "output", workspace / "output", workspace / "previous-output"
    if output.is_symlink():
        raise RuntimeError("Refusing to replace a symlinked output directory")
    if not (built / "Lanternwood-House-Build-Kit.zip").is_file():
        raise RuntimeError("Build has no packaged kit; the previous output is preserved")
    generated = [
        name
        for name, old in baseline.items()
        if (
            name.startswith("docs/")
            or name in ("README.md", "README.pl.md", ".github/social-preview.png")
        )
        and digest(workspace / name) != old
    ]
    originals = {name: (root / name).read_bytes() for name in generated}
    moved = False
    try:
        if output.exists():
            output.rename(previous)
        built.rename(output)
        moved = True
        for name in generated:
            shutil.copy2(workspace / name, root / name)
    except BaseException:
        for name, content in originals.items():
            (root / name).write_bytes(content)
        if moved:
            output.rename(built)
        if previous.exists():
            previous.rename(output)
        raise


def rebuild(root, freecad_python, lang="pl", tolerance=False, pipeline=run_pipeline):
    work = root / ".build-work"
    work.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="build-", dir=work))
    print(f"Build workspace: {workspace}", flush=True)
    try:
        baseline = snapshot(root, workspace)
        pipeline(workspace, freecad_python, lang, tolerance)
        publish(root, workspace, baseline)
    except BaseException:
        print(f"Build failed. Previous output preserved. Diagnostics: {workspace}", file=sys.stderr)
        raise
    else:
        shutil.rmtree(workspace)
        print(f"Published successful build: {root / 'output'}", flush=True)


def main():
    import config_check
    from supplier import languages

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freecad-python", help="FreeCAD bundled Python executable")
    parser.add_argument("--lang", choices=languages(), default="pl")
    parser.add_argument(
        "--tolerance",
        action="store_true",
        help="require thickness checks before packaging and publishing",
    )
    parser.add_argument("--clean-only", action="store_true", help="explicitly discard output/")
    args = parser.parse_args()
    if args.clean_only:
        clean()
        print("output/ emptied")
        return
    if not args.freecad_python:
        parser.error("--freecad-python is required")
    config_check.check()
    executable = str(Path(args.freecad_python).resolve())
    if not Path(executable).is_file():
        parser.error(f"FreeCAD Python does not exist: {executable}")
    rebuild(ROOT, executable, args.lang, args.tolerance)


if __name__ == "__main__":
    main()
