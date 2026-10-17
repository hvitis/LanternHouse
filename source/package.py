"""Create the reviewable build kit, excluding local runtimes, CAD backups and the third-party reference photos."""

import hashlib
import json
import zipfile
from pathlib import Path

import naming

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/BUILD-GUIDE.md"  # holds the generated stock tables


def release_assets(output):
    """The standalone downloads attached to every tagged release."""
    return [
        output / "pdf" / name
        for name in (
            naming.PDF_COMPLETE,
            naming.PDF_INSTRUCTIONS,
            naming.PDF_CUTTING_TEMPLATES,
            naming.PDF_DIMENSIONED_PARTS,
            naming.PDF_DECOR,
            naming.PDF_CLAY_FAMILY,
            naming.PDF_3MM_HAND_TEMPLATES,
            naming.PDF_SUPPLIER,
            naming.PDF_SUPPLIER_SUMMARY,
            f"{naming.PREFIX}-Supplier.csv",
        )
    ] + [output / naming.SUPPLIER_CUT_DXF, output / naming.KIT_ZIP]


def required_deliverables(output):
    """Downloads and assembly files that must be present before packaging."""
    return release_assets(output)[:-1] + [
        output / "cad" / name
        for name in (
            naming.CAD_DOCUMENT,
            f"{naming.CAD_STEM}.step",
            f"{naming.CAD_STEM}-open.step",
            f"{naming.CAD_STEM}-exploded.step",
        )
    ]


def validate_deliverables(output):
    missing = [
        str(path.relative_to(output))
        for path in required_deliverables(output)
        if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise RuntimeError("Package blocked: missing or empty deliverables: " + ", ".join(missing))


def stock_table(sheets):
    groups = {}
    for s in sheets:
        key = (s["thickness"], s["width"], s["height"], bool(s.get("existing_stock")))
        groups[key] = groups.get(key, 0) + 1
    rows = ["| Thickness | Sheet size | Quantity |", "| --- | --- | --- |"]
    for (t, w, h, existing), q in sorted(
        groups.items(), key=lambda kv: (-kv[0][0], -kv[0][1] * kv[0][2])
    ):
        rows.append(f"| {t:g} mm | {w:g} × {h:g} | {q}{' existing' if existing else ''} |")
    return "\n".join(rows)


def update_stock_tables(path=GUIDE, nesting_path=None):
    """Refresh the generated stock tables in the build guide from the current nesting."""
    if not path.exists():
        return
    nest = json.loads((nesting_path or ROOT / "output/nesting.json").read_text())
    text = path.read_text()
    for key, sheets in (("main", nest["sheets"]), ("optional", nest.get("optional_sheets", []))):
        start, end = f"<!-- stock:{key}:start -->", f"<!-- stock:{key}:end -->"
        if start in text and end in text:
            text = (
                text[: text.index(start) + len(start)]
                + "\n"
                + stock_table(sheets)
                + "\n"
                + text[text.index(end) :]
            )
    path.write_text(text)


def validate_reports(output, require_tolerance=False):
    reports = output / "reports"
    report = json.loads((reports / "release-validation.json").read_text())
    if report.get("all_pass") is not True:
        raise RuntimeError("Package blocked: resolve failed release checks")
    tolerance = reports / "thickness-tolerance.json"
    if require_tolerance and not tolerance.exists():
        raise RuntimeError("Package blocked: thickness-tolerance.json is required")
    if tolerance.exists() and json.loads(tolerance.read_text()).get("all_pass") is not True:
        raise RuntimeError("Package blocked: resolve failed thickness checks")
    return tolerance.exists()


def create_package(root=None, require_tolerance=False):
    root = ROOT if root is None else root
    output = root / "output"
    checked = validate_reports(output, require_tolerance)
    validate_deliverables(output)
    update_stock_tables(root / "docs/BUILD-GUIDE.md", output / "nesting.json")
    dest = output / "Lanternwood-House-Build-Kit.zip"
    manifest_path = output / "reports/build-manifest.json"
    files = []
    for folder in ("source", "docs", "tests", "prints", ".github", "output", "requirements"):
        if not (root / folder).is_dir():
            continue
        for path in (root / folder).rglob("*"):
            if not path.is_file() or path in (dest, manifest_path):
                continue
            if "__pycache__" in path.parts or path.name == ".DS_Store":
                continue
            if path.suffix in (".FCBak", ".FCStd1", ".zip"):
                continue
            # Physical measurements belong to the builder, not a public build kit.
            if "joint-samples" in path.relative_to(root).parts:
                continue
            files.append(path)
    files.extend(
        root / name
        for name in (
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
        if (root / name).exists()
    )
    files.sort()
    manifest = {
        "validation": "output/reports/release-validation.json",
        "tolerance_checked": checked,
        "files": [
            {
                "path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in files
        ],
    }
    payload = json.dumps(manifest, indent=2) + "\n"
    # A failed ZIP write leaves the previous kit and its manifest in place.
    temporary = output / ".build-kit-pending.zip"
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
            for path in files:
                info = zipfile.ZipInfo(
                    "Lanternwood-House/" + str(path.relative_to(root)), (2000, 1, 1, 0, 0, 0)
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())
            archive.writestr("Lanternwood-House/output/reports/build-manifest.json", payload)
        temporary.replace(dest)
        manifest_path.write_text(payload)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Packaged {len(files)} files / {dest.stat().st_size / 1024 / 1024:.1f} MB / {dest}")
    return dest


def validate_release_kit(output):
    """Verify deliverables and passing evidence inside the exact downloadable archive."""
    validate_reports(output, require_tolerance=True)
    validate_deliverables(output)
    manifest_path = output / "reports/build-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("tolerance_checked") is not True:
        raise RuntimeError("Release blocked: repackage after the thickness check")
    recorded = {item["path"]: item["sha256"] for item in manifest["files"]}
    required = {
        "output/" + str(path.relative_to(output)) for path in required_deliverables(output)
    } | {"output/reports/release-validation.json", "output/reports/thickness-tolerance.json"}
    if required - recorded.keys():
        raise RuntimeError("Release blocked: missing packaged deliverables or reports")
    with zipfile.ZipFile(output / "Lanternwood-House-Build-Kit.zip") as archive:
        embedded = archive.read("Lanternwood-House/output/reports/build-manifest.json")
        if embedded != manifest_path.read_bytes():
            raise RuntimeError(
                "Release blocked: the kit manifest differs from the current manifest"
            )
        if archive.testzip() is not None:
            raise RuntimeError("Release blocked: corrupt build kit")
        for relative, expected in recorded.items():
            packaged = hashlib.sha256(archive.read("Lanternwood-House/" + relative)).hexdigest()
            if expected != packaged:
                raise RuntimeError(f"Release blocked: stale or missing packaged {relative}")
            if relative.startswith("output/"):
                current = hashlib.sha256((output.parent / relative).read_bytes()).hexdigest()
                if expected != current:
                    raise RuntimeError(f"Release blocked: stale or missing packaged {relative}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-tolerance", action="store_true")
    args = parser.parse_args()
    create_package(require_tolerance=args.require_tolerance)


if __name__ == "__main__":
    main()
