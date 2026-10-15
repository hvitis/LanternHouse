"""Render documentation specifications from the same model used by the book and viewer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- specifications:start -->"
END = "<!-- specifications:end -->"
TARGETS = {"README.md": "en", "README.pl.md": "pl", "docs/BUILD-GUIDE.md": "en"}


def tower_description(config):
    return (
        f"12 flat facets, {config['tower_diameter']:g} across vertices, "
        f"{config['thickness']['wall']:g} mm walls"
    )


def book_rows(data, veranda_apex, right_walls, left_walls):
    """Keep book facts independent of ReportLab rendering and module globals."""
    cfg, der, parts = data["config"], data["derived"], data["parts"]
    plinth, veranda, doors = cfg["plinth"], cfg["veranda"], cfg["doors"]
    drawer, partition = der["drawer"], cfg["partition"]
    floor_tops = " / ".join(f"Z{z:g}" for z in der["floor_tops"])
    deck = next(i for i in data["instances"] if i["design_part"] == "E03")
    deck_z = deck["origin"][2] + deck["w"][2] * parts[deck["part"]]["thickness"]
    windows = der["windows_per_floor"]
    return [
        [
            "Base",
            f"Round D{cfg['base_diameter']:g}, {der['base_thickness']:g} mm plywood, plain green",
        ],
        [
            "Stone plinth",
            f"{plinth['height']:g} high, 12 facets {2 * plinth['apothem']:g} across flats; ground floor top Z{der['floor_tops'][0]:g}",
        ],
        [
            "Hidden drawer",
            f"{drawer['width']:g} wide x {drawer['depth']:.0f} long x {drawer['height']:g} high, in the plinth; pulls out {drawer['travel']:g} mm to the {drawer['side']}",
        ],
        [
            "Rooms",
            f"One divider per storey with a {partition['door_width']:g} x {partition['door_height']:g} doorway: two rooms per floor",
        ],
        [
            "Figures",
            "Thermo-clay " + ", ".join(f"{f['name']} {f['height']:.0f}" for f in der["figures"]),
        ],
        ["Tower", tower_description(cfg)],
        [
            "Floors",
            f"Tops {floor_tops}; clear room height {der['clear_room_height']:g}; attic inside the roof",
        ],
        [
            "Opening walls",
            f"Right {right_walls}. Left {left_walls}. Hinges X+/-{der['hinge_axes']['WallRight'][0]:g}. GP1 stops at {der['views']['open_angle']:g} degrees.",
        ],
        [
            "Roof",
            f"About {cfg['roof_diameter']:g} across; eave Z{der['roof_eave']:g}; lifts off; finial top Z{der['total_height']:g}",
        ],
        [
            "Veranda",
            f"{veranda['width']:g} x {veranda['depth']:g} deck on {veranda['facet']}; deck top Z{deck_z:g}; roof apex about Z{veranda_apex:.0f}",
        ],
        [
            "Doors",
            f"Main {doors['main']}, veranda {doors['veranda']} ({parts['E01']['width']:.1f} x {parts['E01']['height']:.1f}), back {doors['back']} ({parts['E04']['width']:.1f} wide); all open outward",
        ],
        [
            "Windows",
            f"{windows[0]} ground / {windows[1]} middle / {windows[2]} bedroom / {windows[3]} dormers (over {' and '.join(cfg['dormer']['over'])})",
        ],
    ]


def rows(data, language="en"):
    cfg, der, parts = data["config"], data["derived"], data["parts"]
    labels = {
        "en": [
            "Finished height",
            "Base diameter / plywood",
            "Plinth height",
            "Tower diameter / wall plywood",
            "Fixed / opening wall height",
            "Floor plywood / floor tops",
            "Clear room height",
            "Pillars: quantity / section / length",
            "Pillar slot clearance",
            "Roof diameter / eave height",
            "Roof ring: sections / plywood",
            "Base sections",
            "Veranda deck / facet",
            "Drawer travel",
            "Opening wall stop",
            "Floor support strips: ground / upper",
            "Floor joint clearance",
        ],
        "pl": [
            "Wysokość całkowita",
            "Średnica podstawy / sklejka",
            "Wysokość cokołu",
            "Średnica wieży / sklejka ścian",
            "Wysokość ścian stałych / otwieranych",
            "Sklejka podłóg / poziomy podłóg",
            "Wysokość pomieszczeń",
            "Słupki: liczba / przekrój / długość",
            "Luz otworów słupków",
            "Średnica dachu / wysokość okapu",
            "Pierścień dachu: segmenty / sklejka",
            "Segmenty podstawy",
            "Podest werandy / ściana",
            "Wysuw szuflady",
            "Kąt otwarcia ścian",
            "Listwy pod podłogami: parter / piętra",
            "Luz połączeń podłóg",
        ],
    }[language]
    opening = [
        parts[i["part"]]["height"]
        for i in data["instances"]
        if i["group"] in ("WallLeft", "WallRight")
        and i["design_part"].startswith("W")
        and parts[i["part"]]["category"] == "Walls"
    ]
    pillar = parts["P01"]
    ring = der["panels"]["R02"]
    fab = cfg["fabrication"]
    values = [
        f"{der['total_height']:g} mm",
        f"{cfg['base_diameter']:.1f} mm / {cfg['thickness']['base']:g} mm",
        f"{cfg['plinth']['height']:g} mm",
        f"{cfg['tower_diameter']:.1f} mm / {cfg['thickness']['wall']:g} mm",
        f"{cfg['wall_height']:g} mm / {max(opening):g} mm",
        f"{cfg['thickness']['floor']:g} mm / " + ", ".join(f"Z{z:g}" for z in der["floor_tops"]),
        f"{der['clear_room_height']:g} mm",
        f"{der['pillars']['quantity']} / {pillar['thickness']:g} × {pillar['width']:g} mm / {pillar['height']:g} mm",
        f"{fab['pillar_clearance']:g} mm",
        f"{cfg['roof_diameter']:.1f} mm / Z{der['roof_eave']:g}",
        f"{len(ring['sections'])} / {ring['thickness']:g} mm",
        str(len(der["panels"]["B01"]["sections"])),
        f"{cfg['veranda']['width']:.1f} × {cfg['veranda']['depth']:g} mm / {cfg['veranda']['facet']}",
        f"{der['drawer']['travel']:g} mm",
        f"{der['views']['open_angle']:g}°",
        " / ".join(
            f"{t:g} × {w:g} mm" for t, w in (fab["plinth_floor_support"], fab["floor_support"])
        ),
        f"{cfg['cnc']['joint_clearance']:g} mm",
    ]
    return list(zip(labels, values))


def table(data, language="en"):
    title = "| Specification | Value |" if language == "en" else "| Parametr | Wartość |"
    return "\n".join(
        [
            title,
            "| --- | --- |",
            *[f"| {label} | {value} |" for label, value in rows(data, language)],
        ]
    )


def replace_block(text, content):
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
        raise ValueError("Expected exactly one correctly ordered specifications marker pair")
    before, tail = text.split(START)
    _, after = tail.split(END)
    return before + START + "\n" + content + "\n" + END + after


def update(data, root=ROOT, check=False):
    changed = []
    for name, language in TARGETS.items():
        path = root / name
        original = path.read_text()
        generated = replace_block(original, table(data, language))
        if generated != original:
            changed.append(name)
            if not check:
                path.write_text(generated)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if generated specifications differ"
    )
    parser.add_argument(
        "--from-build", action="store_true", help="read this build's output/parts.json"
    )
    args = parser.parse_args()
    if args.from_build:
        data = json.loads((ROOT / "output/parts.json").read_text())
    else:
        import config_check
        import model

        config_check.check()
        data = model.build()
    changed = update(data, check=args.check)
    if args.check and changed:
        raise SystemExit("Stale specifications: " + ", ".join(changed) + ". Run make specs.")
    print("Specifications current." if not changed else "Updated: " + ", ".join(changed))


if __name__ == "__main__":
    main()
