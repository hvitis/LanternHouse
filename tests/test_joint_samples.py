"""Fabrication samples must preserve production geometry and keep physical results pending."""

import csv
import json

import cnc
import joint_samples as js
import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from shapely import affinity
from shapely.geometry import box


@pytest.fixture(scope="module")
def pack(data):
    return js.make_pack(data)


def test_samples_are_exact_crops_of_production_profiles(data, pack):
    for p in pack["parts"].values():
        source = p["source"]
        if source is None:
            continue
        original = data["parts"][source["part"]]
        assert p["thickness"] == original["thickness"]
        if source["frame"] == "world":
            instance = next(i for i in data["instances"] if i["id"] == source["instance"])
            expected = js.world_shape(data, instance)
        else:
            expected = js.shape(original)
        if source["crop_mm"]:
            expected = expected.intersection(box(*source["crop_mm"]))
        restored = affinity.translate(js.shape(p), *source["origin_mm"])
        assert restored.symmetric_difference(expected).area < 1e-7, p["id"]


@pytest.mark.parametrize("process", ["laser", "router", "hand"])
def test_every_plywood_sample_occurs_once_with_clear_lanes(pack, process):
    seen = []
    gap = max(3, pack["config"]["cnc"]["tool_diameter"] + 2) if process == "router" else 3
    for sheet in js.sheets(pack, process):
        placed = []
        for item in sheet["items"]:
            p = pack["parts"][item["part"]]
            assert p["material"] == "plywood"
            assert p["thickness"] == sheet["thickness"]
            poly = affinity.translate(js.shape(p), item["x"], item["y"])
            assert box(5, 5, sheet["width"] - 5, sheet["height"] - 5).buffer(1e-7).covers(poly)
            assert all(poly.distance(other) >= gap - 1e-7 for other in placed)
            placed.append(poly)
            seen.append(p["id"])
    assert sorted(seen) == sorted(
        p["id"] for p in pack["parts"].values() if p["material"] == "plywood"
    )
    if process == "laser":
        assert len(js.sheets(pack, process)) == 2


def test_slot_and_magnet_features_retain_the_production_dimensions(data, pack):
    slot = pack["parts"]["SLOT"]
    assert len(slot["cuts"]) == 1
    original = data["parts"][slot["source"]["part"]]
    assert js.Polygon(slot["cuts"][0]).area == pytest.approx(js.Polygon(original["cuts"][0]).area)
    block = pack["parts"]["CATCH-BLOCK"]
    h = block["holes"][0]
    assert h["entry"] == "bottom"
    assert block["thickness"] - h["depth"] == data["config"]["magnets"]["skin"]
    disc = pack["parts"]["CATCH-DISC"]
    sheet = {
        "id": "TEST",
        "items": [{"part": disc["id"], "copy": 1, "x": 0, "y": 0, "angle": 0}],
        "thickness": disc["thickness"],
    }
    assert not any(kind == "circle" for kind, _ in cnc.through_cuts(pack, sheet))


def test_written_pack_is_scaled_and_never_overwrites_measurements(data, tmp_path):
    dest = js.write_pack(data, tmp_path)
    result = dest / "physical-results.csv"
    rows = list(csv.DictReader(result.open()))
    assert all(r["result"] == "pending" and not r["value"] for r in rows)
    saved = result.read_text().replace("pending", "measured by builder", 1)
    result.write_text(saved)
    js.write_pack(data, tmp_path)
    assert result.read_text() == saved
    manifest = json.loads((dest / "samples.json").read_text())
    assert manifest["physical_status"] == "not_tested"
    assert manifest["unavailable"][0]["status"] == "unavailable"
    doc = PdfReader(dest / "Workshop-Joint-Samples.pdf")
    templates = [p for p in doc.pages if "cutting template" in p.extract_text()]
    assert len(templates) == 2
    assert all(float(p.mediabox.width) == pytest.approx(A4[0], abs=0.001) for p in doc.pages)
    assert all("100 mm / print 100%" in p.extract_text() for p in templates)
    for sheet in manifest["sheets"]:
        import ezdxf

        drawing = ezdxf.readfile(dest / f"{sheet['id']}-through.dxf")
        assert not drawing.audit().has_errors
        assert drawing.header["$INSUNITS"] == 4
        assert not drawing.modelspace().query("TEXT")
