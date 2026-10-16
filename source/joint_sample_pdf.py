"""Print the workshop procedures and full-size sample templates."""

from __future__ import annotations

import cnc
import naming
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from shapely import affinity
from shapely.geometry import Polygon, box


def lines(c, text, y, size=10, leading=14):
    c.setFont("Helvetica", size)
    for line in simpleSplit(text, "Helvetica", size, A4[0] - 40 * mm):
        c.drawString(20 * mm, y, line)
        y -= leading
    return y - 5


def heading(c, title, subtitle):
    c.setFont("Helvetica-Bold", 15)
    c.drawString(15 * mm, A4[1] - 18 * mm, title)
    return lines(c, subtitle, A4[1] - 28 * mm, 9, 12)


def scale_bar(c):
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.line(20 * mm, 10 * mm, 120 * mm, 10 * mm)
    for x in (20, 120):
        c.line(x * mm, 8 * mm, x * mm, 12 * mm)
    c.setFont("Helvetica", 8)
    c.drawString(125 * mm, 9 * mm, "100 mm / print 100%")


def manual_features(c, p, x, y, min_drill=2):
    """Blue circles show hand drilling only, never an instruction to cut through."""
    c.setStrokeColorRGB(0, 0.3, 0.8)
    c.setLineWidth(0.4)
    c.setDash(2, 2)
    for h in p["holes"]:
        if (
            p["material"] == "plywood"
            and (h.get("depth") or p["thickness"]) >= p["thickness"]
            and h["diameter"] >= min_drill
        ):
            continue
        c.circle(x + h["x"] * mm, y + h["y"] * mm, h["diameter"] / 2 * mm)
    c.setDash()


def assembly_map(c, pack, test):
    """A true-size plan restores the relationship lost when coupons are packed for cutting."""
    panels = [
        pack["parts"][sid]
        for sid in test["samples"]
        if pack["parts"][sid]["source"]["frame"] == "world"
    ]
    positioned = [
        affinity.translate(Polygon(p["outer"], p["cuts"]), *p["source"]["origin_mm"])
        for p in panels
    ]
    x0 = min(p.bounds[0] for p in positioned)
    y0 = min(p.bounds[1] for p in positioned)
    y1 = max(p.bounds[3] for p in positioned)
    y = heading(
        c,
        test["id"] + " - assembly map",
        "Top view / scale 1:1 / blue dashed shapes: supports beneath the floor",
    )
    y = lines(
        c,
        "Place the cut pieces in these positions. This page is an assembly reference, not a laser input.",
        y,
    )
    ox, oy = 35 * mm - x0 * mm, y - 20 * mm - y1 * mm
    for p, poly in zip(panels, positioned):
        cnc.draw(c, [("polygon", list(poly.exterior.coords)[:-1])], mm, ox, oy, line_width=0.15)
        q = poly.representative_point()
        c.setFont("Helvetica", 8)
        c.drawString(ox + q.x * mm, oy + q.y * mm, p["id"])
    c.setStrokeColorRGB(0, 0.3, 0.8)
    c.setDash(3, 2)
    if test["id"] == "J01":
        seam = pack["config"]["fabrication"]["seam_y"]
        width = pack["config"]["fabrication"]["floor_support"][1]
        supports = [box(x - width / 2, seam - 60, x + width / 2, seam + 60) for x in (40, 70)]
    elif test["id"] == "J02":
        width = pack["config"]["fabrication"]["plinth_floor_support"][1]
        supports = [box(-width / 2, y0, width / 2, y1)]
    else:
        width = pack["config"]["fabrication"]["plinth_floor_support"][1]
        seam = pack["config"]["fabrication"]["seam_y"]
        supports = [box(30, seam - width / 2, 90, seam + width / 2)]
    for poly in supports:
        cnc.draw(
            c,
            [("polygon", list(poly.exterior.coords)[:-1])],
            mm,
            ox,
            oy,
            line_width=0.15,
            color=(0, 0.3, 0.8),
        )
    c.setDash()
    scale_bar(c)
    c.showPage()


def write_pdf(pack, layouts, path, fingerprint, process):
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    c.setTitle(f"{naming.NAME} - critical joint workshop samples")
    y = heading(
        c,
        "Critical joint workshop samples",
        f"Model {fingerprint[:12]} / process: {process} / all physical results pending",
    )
    for text in (
        "Use the same plywood batch, grain direction, hardware, finish and adhesives as the house.",
        "Measure each nominal plywood thickness at five positions before cutting.",
        "Record the machine, cutter or laser settings, compensation, glue and cure time in the CSV log.",
        "Use the machine supplier's compensation for nominal contours. These files contain no compensated toolpaths.",
        "Measure each CAL square and hole before sanding. Record both sizes in the log.",
        "Black lines are through cuts. Blue circles mark hand drilling, with the face and depth in the drilling CSV.",
        "Print the templates at 100% actual size. Measure the 100 mm bar before using a template.",
        "Write the sample IDs on the scrap pieces with a pencil before assembly.",
        "The roof turn-button catch test is unavailable. The current production model contains no catch.",
        "These samples check local fit and bond workmanship. Full assembly loads and physical safety remain untested.",
        "Keep magnets and workshop samples away from children. Enclose each magnet before trying the catch.",
        "Copy the completed results outside output/ before a full rebuild deletes that folder.",
    ):
        y = lines(c, text, y)
    c.showPage()
    cfg = pack["config"]
    y = heading(
        c,
        "Materials and hardware",
        "Make one of each labeled sample. Use the same materials as the house.",
    )
    items = [
        "Plywood: one 190 x 230 mm cutting area in 3 mm, and one in 6 mm for the default laser pack.",
        f"Hinge: one {cfg['wall_hinge']['height']:g} x {cfg['wall_hinge']['open_width']:g} mm butt hinge.",
        f"Screws: four D{pack['hinge_screw']['diameter']:g} x {pack['hinge_screw']['length']:g} mm countersunk wood screws.",
        f"Magnet: one D{cfg['magnets']['magnet'][0]:g} x {cfg['magnets']['magnet'][1]:g} mm magnet.",
        f"Steel disc: one D{cfg['magnets']['disc'][0]:g} x {cfg['magnets']['disc'][1]:g} mm disc.",
        f"Plug: D{cfg['magnets']['plug']:g} hardwood dowel, cut to close the bore behind the magnet.",
        "Adhesives: the planned wood glue and slow two-part epoxy. Record the specified cure times.",
        "Tools: calipers, a depth stop, drills, clamps, a flat surface and a ruler.",
    ]
    for text in items:
        y = lines(c, text, y)
    for p in pack["parts"].values():
        if p["material"] != "plywood":
            y = lines(
                c,
                f"{p['id']}: {p['material']}, {p['width']:.2f} x {p['height']:.2f} x {p['thickness']:g} mm.",
                y,
                9,
                12,
            )
    c.showPage()
    for test in pack["tests"]:
        y = heading(c, f"{test['id']} - {test['name']}", "Samples: " + ", ".join(test["samples"]))
        for n, step in enumerate(test["procedure"], 1):
            y = lines(c, f"{n}. {step}", y)
        y = lines(c, "Acceptance: " + test["acceptance"], y - 8)
        y = lines(c, "Scope: " + test["limitation"], y - 8)
        for measurement in test["measurements"]:
            y = lines(c, measurement + ": _____________________________________", y, 9, 12)
        lines(
            c,
            "Result: PENDING / PASS / FAIL     Operator: __________     Date: __________",
            y - 12,
            9,
        )
        c.showPage()
        if test["id"] in ("J01", "J02", "J03"):
            assembly_map(c, pack, test)
    for sheet in layouts:
        heading(
            c,
            sheet["id"] + " - cutting template",
            f"{sheet['width']} x {sheet['height']} mm cutting window / {sheet['thickness']:g} mm plywood / scale 1:1",
        )
        curves = cnc.through_cuts(pack, sheet)
        cnc.draw(c, curves, mm, 10 * mm, 20 * mm, line_width=0.15)
        for item in sheet["items"]:
            p = pack["parts"][item["part"]]
            x, y = (10 + item["x"]) * mm, (20 + item["y"]) * mm
            manual_features(c, p, x, y, pack["config"]["cnc"]["min_drill"])
            c.setFillColorRGB(0, 0.3, 0.8)
            c.setFont("Helvetica", 5)
            if p["width"] < 20 and p["height"] > 40:
                c.saveState()
                c.translate(x + 3 * mm, y + 3 * mm)
                c.rotate(90)
                c.drawString(0, 0, p["id"])
                c.restoreState()
            else:
                c.drawString(x + mm, y + mm, p["id"])
        c.setFillColorRGB(0, 0, 0)
        scale_bar(c)
        c.showPage()
    # Bought hardwood and packing have their own templates, never plywood cut-sheet entries.
    for p in pack["parts"].values():
        if p["material"] == "plywood":
            continue
        y = heading(
            c,
            p["id"] + " - prepare separately",
            f"{p['material']} / {p['width']:g} x {p['height']:g} x {p['thickness']:g} mm / make one",
        )
        y = lines(c, p["note"], y, 9, 12)
        for h in p["holes"]:
            y = lines(
                c,
                f"{h['id']}: D{h['diameter']:g}, depth {h.get('depth') or p['thickness']:g} mm, "
                f"entry {h.get('entry', 'top')}, X{h['x']:g} Y{h['y']:g} from the lower-left datum.",
                y,
                9,
                12,
            )
        ox, oy = 30 * mm, y - p["height"] * mm - 10 * mm
        c.setStrokeColorRGB(0, 0, 0)
        cnc.draw(c, [("polygon", p["outer"])], mm, ox, oy, line_width=0.15)
        manual_features(c, p, ox, oy)
        lines(
            c,
            "Blue circles locate drilling. Read the drilling CSV for entry face and depth.",
            oy - 15,
            9,
            12,
        )
        scale_bar(c)
        c.showPage()
    c.save()
