"""Generate production-derived joint samples and a blank workshop measurement log.

    make joints
    .venv/bin/python source/joint_samples.py --process router

This prepares a physical experiment. It never reports a physical test as passed.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

import cnc
from dxf_r12 import DXF
from joint_sample_pdf import write_pdf
from shapely import affinity
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[1]
SHEET = (190, 230)


def shape(part):
    return Polygon(part["outer"], part["cuts"])


def world_shape(data, instance):
    """A horizontal production profile in the house XY frame."""
    u, v, o = instance["u"], instance["v"], instance["origin"]
    return affinity.affine_transform(
        shape(data["parts"][instance["part"]]), [u[0], v[0], u[1], v[1], o[0], o[1]]
    )


def local_point(instance, point):
    delta = [point[k] - instance["origin"][k] for k in range(3)]
    return [sum(delta[k] * instance[axis][k] for k in range(3)) for axis in ("u", "v")]


def make_pack(data):
    """Crop existing profiles without changing their joint edges, holes or thicknesses."""
    parts, tests = {}, []

    def sample(sid, source, window=None, frame="local", instance=None, material="plywood"):
        original = data["parts"][source]
        production = world_shape(data, instance) if frame == "world" else shape(original)
        cropped = production.intersection(window) if window is not None else production
        if cropped.geom_type != "Polygon" or cropped.is_empty or not cropped.is_valid:
            raise ValueError(f"{sid}: the sample must be one valid connected polygon")
        x0, y0, x1, y1 = cropped.bounds
        p = {
            "id": sid,
            "name": original["name"],
            "thickness": original["thickness"],
            "outer": [[x - x0, y - y0] for x, y in list(cropped.exterior.coords)[:-1]],
            "cuts": [[[x - x0, y - y0] for x, y in list(r.coords)[:-1]] for r in cropped.interiors],
            "holes": [],
            "width": x1 - x0,
            "height": y1 - y0,
            "quantity": 1,
            "material": material,
            "note": original.get("note", ""),
            "source": {
                "part": source,
                "instance": instance["id"] if instance else None,
                "frame": frame,
                "crop_mm": list(window.bounds) if window is not None else None,
                "origin_mm": [x0, y0],
            },
        }
        for h in original["holes"]:
            if frame == "world":
                u, v, o = instance["u"], instance["v"], instance["origin"]
                x, y = [o[k] + u[k] * h["x"] + v[k] * h["y"] for k in (0, 1)]
            else:
                x, y = h["x"], h["y"]
            radius = max(h["diameter"], h.get("countersink", 0)) / 2
            if not cropped.buffer(1e-7).covers(Point(x, y).buffer(radius)):
                if cropped.intersects(Point(x, y).buffer(radius)):
                    raise ValueError(f"{sid}: a crop clips drilling feature {h['id']}")
                continue
            p["holes"].append(dict(h, x=x - x0, y=y - y0))
        parts[sid] = p
        return sid

    def test(tid, name, ids, steps, acceptance, measurements, limitation):
        tests.append(
            {
                "id": tid,
                "name": name,
                "samples": ids,
                "status": "pending",
                "procedure": steps,
                "acceptance": acceptance,
                "measurements": measurements,
                "limitation": limitation,
            }
        )

    # Floor samples retain their production assembly coordinates in source metadata.
    seam = data["config"]["fabrication"]["seam_y"]
    floor = [i for i in data["instances"] if i["design_part"] == "F01"]
    z = min(i["origin"][2] for i in floor)
    floor = [i for i in floor if abs(i["origin"][2] - z) < 1e-6]
    window = box(20, seam - 60, 90, seam + 60)
    finger = []
    for i in floor:
        if world_shape(data, i).intersection(window).area > 1:
            finger.append(sample(f"FINGER-{len(finger) + 1}", i["part"], window, "world", i))
    supports = [
        p
        for p in data["parts"].values()
        if p["name"].startswith("Floor seam support") and p.get("assembly_panel") == "F01"
    ]
    support = max(supports, key=lambda p: max(p["width"], p["height"]))
    for n in (1, 2):
        finger.append(sample(f"FINGER-SUPPORT-{n}", support["id"]))
    test(
        "J01",
        "Upper-floor finger seam",
        finger,
        [
            "Place FINGER-1 and FINGER-2 in their original positions on a flat surface.",
            "Press the teeth together by hand.",
            "Center both support strips under the seam, at house X40 and X70.",
            "Glue the joint with the production adhesive.",
            "After the stated cure time, inspect the seam and support bonds.",
        ],
        "The teeth seat by hand. Both faces lie flat. No veneer splits or visible bond separation occur.",
        ["dry seam gap mm", "surface step mm", "cured seam observations"],
        "This small sample checks fit and bond workmanship. It does not reproduce a full floor load.",
    )

    # The center puzzle joint and the ground-floor straight seam use different support widths.
    ground = [
        i
        for i in data["instances"]
        if i["design_part"] == "F00" and data["parts"][i["part"]].get("assembly_panel") == "F00"
    ]
    panel = data["derived"]["panels"]["F00"]
    knobs = panel["front_split"]["knobs"]
    knob_y = panel["origin"][1] + knobs[len(knobs) // 2][0]
    for tid, prefix, name, window in (
        ("J02", "PUZZLE", "Ground-floor puzzle seam", box(-30, knob_y - 20, 30, knob_y + 20)),
        ("J03", "STRAIGHT", "Ground-floor straight seam", box(30, seam - 25, 90, seam + 25)),
    ):
        ids = []
        for i in ground:
            if world_shape(data, i).intersection(window).area > 1:
                ids.append(sample(f"{prefix}-{len(ids) + 1}", i["part"], window, "world", i))
        strip = next(
            p
            for p in data["parts"].values()
            if p["name"].startswith("Floor seam support")
            and p.get("assembly_panel") == "F00"
            and max(p["width"], p["height"]) >= 60
        )
        # A shorter production strip preserves the same thickness and cross section.
        length = 40 if prefix == "PUZZLE" else 60
        sw = box(0, 0, min(strip["width"], length), min(strip["height"], length))
        ids.append(sample(f"{prefix}-SUPPORT", strip["id"], sw))
        test(
            tid,
            name,
            ids,
            [
                f"Place {prefix}-1 and {prefix}-2 on a flat surface in their original positions.",
                "Seat the pieces from above by hand.",
                "Center the support strip beneath the seam.",
                "Glue the pieces with the production adhesive.",
                "After the stated cure time, inspect both faces and the support bond.",
            ],
            "The pieces seat without a hammer. No veneer splits or visible bond separation occur.",
            ["dry seam gap mm", "surface step mm", "cured seam observations"],
            "This sample does not reproduce the full drawer bay or its bending loads.",
        )

    # One unchanged dogbone opening, surrounded by 8 mm of the original floor.
    slot_part = next(
        p for p in data["parts"].values() if p.get("assembly_panel") == "F01" and p["cuts"]
    )
    slot = Polygon(slot_part["cuts"][0])
    ids = [
        sample("SLOT", slot_part["id"], box(*slot.buffer(8).bounds)),
        sample("PILLAR", "P01", box(0, 0, data["parts"]["P01"]["width"], 60)),
    ]
    test(
        "J04",
        "Pillar through floor slot",
        ids,
        [
            "Measure the plywood thickness at five positions.",
            "Measure the slot across its straight walls, away from the corner reliefs.",
            "Slide PILLAR through SLOT before paint.",
            "Apply the planned finish to a second trial area.",
            "After the finish cures, repeat the fit.",
        ],
        "The pillar slides through by hand without splitting the slot or stripping the finish.",
        [
            "plywood thickness min mm",
            "plywood thickness max mm",
            "straight slot width mm",
            "pillar width mm",
            "fit before finish",
            "fit after finish",
        ],
        "A short pillar does not check alignment across two complete floor levels.",
    )

    joint = next(j for j in data["joints"] if j["id"].startswith("J-Hinge-"))
    wall = next(i for i in data["instances"] if i["id"] == joint["parts"][0])
    cx, cy = local_point(wall, joint["position"])
    window = box(cx - 16, cy - 16, cx + 16, cy + 16)
    ids = []
    for n in (1, 2):
        ids.extend(
            [
                sample(f"HINGE-WALL-{n}", wall["part"], window),
                sample(f"HINGE-BLOCK-{n}", "A02", material="hardwood"),
                sample(f"HINGE-SHIM-{n}", "A06", material="packing"),
            ]
        )
    screw = next(f for f in data["fasteners"] if f["type"] == "SC1")
    test(
        "J05",
        "Wall hinge backing and screw fit",
        ids,
        [
            "Compare the real hinge with both hole patterns before drilling.",
            "Glue each backing block behind its matching wall holes.",
            "After the stated cure time, drill the hardwood pilots through the real hinge.",
            f"Fit one real hinge with four D{screw['diameter']:g} x {screw['length']:g} mm screws and both shims.",
            "Open and close the hinge 20 times.",
            "Inspect the screw tips, backing blocks, shims and plywood.",
        ],
        "The hinge fits without forcing holes. Screw tips stay enclosed. No splitting, loose screws or bond separation occur.",
        [
            "actual hinge height mm",
            "actual hole pitch mm",
            "actual shim thickness mm",
            "screw length mm",
            "cycle count",
            "observations after cycling",
        ],
        "The small wall pieces do not reproduce the full wall angle, shell weight or hinge pull-out load.",
    )

    disc_part = next(
        p
        for p in data["parts"].values()
        if p.get("assembly_panel") == "F02"
        and any("Wall-catch steel disc" in h["purpose"] for h in p["holes"])
    )
    h = next(h for h in disc_part["holes"] if "Wall-catch steel disc" in h["purpose"])
    ids = [
        sample("CATCH-BLOCK", "MC1", material="hardwood"),
        sample("CATCH-SKIN", "MC1", material="hardwood"),
        sample(
            "CATCH-DISC", disc_part["id"], box(h["x"] - 12, h["y"] - 12, h["x"] + 12, h["y"] + 12)
        ),
    ]
    test(
        "J06",
        "Enclosed magnetic catch",
        ids,
        [
            "Measure the actual hardwood thickness before setting the depth stop.",
            "Drill CATCH-SKIN without a magnet, with the production depth stop.",
            "Cut that spare block through its bore center.",
            "Measure the remaining wood at the working face.",
            "Drill CATCH-BLOCK from the hidden face with the same depth stop.",
            "Install the magnet and hardwood plug with the specified epoxy.",
            "Prepare the blind steel-disc recess in CATCH-DISC by hand.",
            "After the stated cure time, inspect the enclosure and the disc bond.",
            f"Try the catch at the production {data['config']['wall_catch']['gap']:g} mm air gap.",
            "Open the catch 20 times.",
        ],
        f"The spare block retains at least {data['config']['magnets']['skin']:g} mm of wood. "
        "No magnet is exposed. The plug and disc remain fixed during repeated opening.",
        [
            "bore depth mm",
            "sectioned spare skin mm",
            "air gap mm",
            "opening cycle count",
            "measured opening force N",
            "enclosure and bond observations",
        ],
        "This sample does not prove resistance to destructive abuse or certify toy safety.",
    )

    cleat = next(i for i in data["instances"] if i["design_part"] == "R04")
    cp = data["parts"][cleat["part"]]
    contact = Polygon(
        [(cleat["origin"][k] + cleat["u"][k] * x + cleat["w"][k] * t) for k in (0, 1)]
        for x, t in ((0, 0), (cp["width"], 0), (cp["width"], cp["thickness"]), (0, cp["thickness"]))
    )
    window = box(*contact.buffer(8).bounds)
    ids = [sample("ROOF-CLEAT", cleat["part"], material="hardwood")]
    for i in data["instances"]:
        if i["design_part"] == "R02" and world_shape(data, i).intersection(window).area > 1:
            ids.append(sample(f"ROOF-RING-{len(ids)}", i["part"], window, "world", i))
    test(
        "J07",
        "Roof ring to cleat bond",
        ids,
        [
            "Place the ring sample flat in its original position under the cleat.",
            "Keep the wood grain along the sloping edge of the cleat.",
            "Glue the level cleat bottom to the ring with the production adhesive.",
            "After the stated cure time, inspect the contact and the bond.",
        ],
        "The cleat sits flat on the ring. No rocking, veneer splitting or visible bond separation occur.",
        ["contact length mm", "cured bond observations"],
        "This sample does not check the complete cone, roof lifting or retention.",
    )

    for t in (3, 6):
        sid = f"CAL-{t}"
        parts[sid] = {
            "id": sid,
            "name": "30 mm calibration square with D10 hole",
            "thickness": t,
            "outer": [[0, 0], [30, 0], [30, 30], [0, 30]],
            "cuts": [],
            "holes": [
                {
                    "id": "H01",
                    "x": 15,
                    "y": 15,
                    "diameter": 10,
                    "depth": None,
                    "purpose": "Calibration through hole",
                }
            ],
            "width": 30,
            "height": 30,
            "quantity": 1,
            "material": "plywood",
            "note": "Record the finished size before sanding. Nominal geometry has no kerf compensation.",
            "source": None,
        }
    return {
        "config": copy.deepcopy(data["config"]),
        "parts": parts,
        "tests": tests,
        "physical_status": "not_tested",
        "unavailable": [
            {
                "test": "Roof turn-button catch",
                "status": "unavailable",
                "reason": "The current production model contains no roof catch or turn-button parts.",
            }
        ],
        "hinge_screw": screw,
        "roof_contact_xy_mm": list(contact.exterior.coords)[:-1],
    }


def sheets(pack, process):
    """Small deterministic shelves, with manufacturing lanes and no printed labels in cut files."""
    gap = max(
        pack["config"]["nest_spacing"],
        pack["config"]["cnc"]["tool_diameter"] + 2 if process == "router" else 3,
    )
    output = []
    for thickness in sorted(
        {p["thickness"] for p in pack["parts"].values() if p["material"] == "plywood"}
    ):
        sheet = None
        x = y = row = 0
        parts = sorted(
            (
                p
                for p in pack["parts"].values()
                if p["material"] == "plywood" and p["thickness"] == thickness
            ),
            key=lambda p: (-p["height"], p["id"]),
        )
        for p in parts:
            if p["width"] > SHEET[0] - 10 or p["height"] > SHEET[1] - 10:
                raise ValueError(f"{p['id']}: sample exceeds the A4 cutting window")
            if sheet is None or y + p["height"] > SHEET[1] - 5:
                sheet = {
                    "id": f"JOINT-{thickness:g}MM-{len(output) + 1}",
                    "thickness": thickness,
                    "width": SHEET[0],
                    "height": SHEET[1],
                    "items": [],
                }
                output.append(sheet)
                x = y = 5
                row = 0
            if x + p["width"] > SHEET[0] - 5:
                x = 5
                y += row + gap
                row = 0
                if y + p["height"] > SHEET[1] - 5:
                    sheet = {
                        "id": f"JOINT-{thickness:g}MM-{len(output) + 1}",
                        "thickness": thickness,
                        "width": SHEET[0],
                        "height": SHEET[1],
                        "items": [],
                    }
                    output.append(sheet)
                    y = 5
            sheet["items"].append({"part": p["id"], "copy": 1, "angle": 0, "x": x, "y": y})
            x += p["width"] + gap
            row = max(row, p["height"])
    return output


def write_pack(data, dest, process="laser"):
    pack = make_pack(data)
    fingerprint = hashlib.sha256(
        json.dumps(data, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    pack.update(model_sha256=fingerprint, process=process, sheets=sheets(pack, process))
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    # Use a model-specific directory, so old contours cannot be mistaken for the new pack.
    dest = dest / fingerprint[:12] / process
    dest.mkdir(parents=True, exist_ok=True)
    drill = []
    for p in pack["parts"].values():
        for h in p["holes"]:
            drill.append(
                {
                    "sample": p["id"],
                    "material": p["material"],
                    "hole": h["id"],
                    "x_mm": h["x"],
                    "y_mm": h["y"],
                    "diameter_mm": h["diameter"],
                    "depth_mm": h.get("depth") or p["thickness"],
                    "entry_face": h.get("entry", "top"),
                    "mode": "through"
                    if (h.get("depth") or p["thickness"]) >= p["thickness"]
                    else "blind",
                    "purpose": h["purpose"],
                }
            )
    with (dest / "drilling.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(drill[0]))
        writer.writeheader()
        writer.writerows(drill)
    for sheet in pack["sheets"]:
        curves = cnc.through_cuts(pack, sheet)
        dxf = DXF()
        cnc._add(dxf, curves, f"CUT_{sheet['thickness']:g}MM")
        dxf.save(dest / f"{sheet['id']}-through.dxf")
        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet["width"]}mm" height="{sheet["height"]}mm" viewBox="0 0 {sheet["width"]} {sheet["height"]}">',
            f'<g transform="translate(0 {sheet["height"]}) scale(1 -1)" fill="none" stroke="black" stroke-width="0.01">',
        ]
        for kind, curve in curves:
            if kind == "circle":
                x, y, r = curve
                svg.append(f'<circle cx="{x}" cy="{y}" r="{r}"/>')
            else:
                svg.append('<polygon points="' + " ".join(f"{x},{y}" for x, y in curve) + '"/>')
        (dest / f"{sheet['id']}-through.svg").write_text("\n".join(svg + ["</g>", "</svg>"]) + "\n")
    results = dest / "physical-results.csv"
    if not results.exists():
        with results.open("w", newline="") as f:
            fields = [
                "model_sha256",
                "test",
                "measurement",
                "value",
                "result",
                "operator",
                "date",
                "plywood_batch",
                "process_settings",
                "compensation_mm",
                "adhesive",
                "cure_time",
                "notes",
            ]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for test in pack["tests"]:
                for measurement in test["measurements"]:
                    writer.writerow(
                        {
                            "model_sha256": fingerprint,
                            "test": test["id"],
                            "measurement": measurement,
                            "result": "pending",
                        }
                    )
            for t in (3, 6):
                for measurement in (
                    "stock thickness min mm",
                    "stock thickness max mm",
                    "square X mm",
                    "square Y mm",
                    "hole diameter mm",
                ):
                    writer.writerow(
                        {
                            "model_sha256": fingerprint,
                            "test": f"CAL-{t}",
                            "measurement": measurement,
                            "result": "pending",
                        }
                    )
    write_pdf(pack, pack["sheets"], dest / "Workshop-Joint-Samples.pdf", fingerprint, process)
    (dest / "samples.json").write_text(json.dumps(pack, indent=2, allow_nan=False) + "\n")
    files = sorted(
        p
        for p in dest.iterdir()
        if p.is_file() and p.name not in ("checksums.json", "physical-results.csv")
    )
    (dest / "checksums.json").write_text(
        json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, indent=2)
        + "\n"
    )
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, default=ROOT / "output/joint-samples")
    parser.add_argument("--process", choices=("laser", "router", "hand"), default="laser")
    args = parser.parse_args()
    import config_check
    import model

    config_check.check()
    dest = write_pack(model.build(), args.dest, args.process)
    print(f"Prepared joint samples: {dest}")
    print(
        "Physical status: NOT TESTED. Cut, assemble and record workshop measurements in physical-results.csv."
    )


if __name__ == "__main__":
    main()
