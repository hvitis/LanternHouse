# Moomin House

**English** · [Polski](README.pl.md)

**A plywood dollhouse that is entirely generated from code.** One Python model and one config file produce the FreeCAD CAD, the nested cut sheets, a printable A4 building book with 1:1 templates, the renders and an interactive 3D viewer. Automated checks prove that the walls, doors, drawer and roof all move clear of each other.

<p align="center">
  <img src="docs/images/cover.jpg" width="380" alt="Book cover: the round blue tower with a red cone roof and a small veranda, standing in a summer meadow">
</p>

The house is a round blue tower with a red spire roof, three floors and an attic. All plywood parts fit A3 stock (297 × 420 mm). CNC machining and calibrated A4 templates support company cutting and DIY work. The front walls swing open on real hinges, the roof with its two dormers lifts off, a permanent veranda with a rope ladder stands on the side, a back door leads to the woodpile, and a drawer is hidden in the stone plinth. Six thermo-clay figures live in the house: the Moomin family, Snufkin, the Snork Maiden and Little My.

<p align="center">
  <b><a href="https://hvitis.github.io/MoominsHouse/">Open the 3D model in your browser</a></b> &nbsp;·&nbsp;
  <b><a href="https://github.com/hvitis/moominshouse/releases/latest">Download the building book (PDF)</a></b>
</p>

> This is an unofficial, non-commercial fan project. It is not affiliated with or endorsed by Moomin Characters Oy or by the makers of any commercial Moomin house kit. See [Trademarks](#trademarks-and-licence).

<table>
  <tr>
    <td align="center"><img src="docs/images/house-closed.webp" width="250" alt="Closed house, seen from the veranda side"><br><sub>Closed, veranda side</sub></td>
    <td align="center"><img src="docs/images/house-open.webp" width="290" alt="Walls swung open and the roof lifted, showing the furnished floors"><br><sub>Walls open, roof lifted</sub></td>
    <td align="center"><img src="docs/images/house-exploded.webp" width="250" alt="Exploded view of the structural assemblies"><br><sub>Exploded assemblies</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/images/clay-family.webp" width="520" alt="Clay figures of Moominpappa with a top hat, Moominmamma with a striped apron and handbag, Moomintroll, the Snork Maiden, Snufkin and Little My"><br>
  <sub>The thermo-clay family and friends, modelled as lumps of clay with volumes and grams per colour</sub>
</p>

<!-- specifications:start -->
| Specification | Value |
| --- | --- |
| Finished height | 778.4 mm |
| Base diameter / plywood | 522.7 mm / 6 mm |
| Plinth height | 61.6 mm |
| Tower diameter / wall plywood | 326.7 mm / 3 mm |
| Fixed / opening wall height | 420 mm / 418 mm |
| Floor plywood / floor tops | 6 mm / Z73.6, Z213.6, Z353.6, Z493.6 |
| Clear room height | 134 mm |
| Pillars: quantity / section / length | 4 / 6 × 16.8 mm / 402 mm |
| Pillar slot clearance | 0.6 mm |
| Roof diameter / eave height | 373.3 mm / Z493.6 |
| Roof ring: sections / plywood | 3 / 3 mm |
| Base sections | 8 |
| Veranda deck / facet | 149.3 × 84 mm / W07 |
| Drawer travel | 200 mm |
| Opening wall stop | 100° |
| Floor support strips: ground / upper | 3 × 4 mm / 3 × 12 mm |
| Floor joint clearance | 0.1 mm |
<!-- specifications:end -->

## Features

- **A real build, not just a model.** Every part has a plywood thickness, an outline, its holes and its jigsaw starter holes, packed onto real sheet sizes. The book contains tiled 1:1 templates with a calibration square, hinge checking templates, a hardware shopping list and step-by-step assembly.
- **Play features.** Two front wall shells open to 100°, where a magnet sealed inside a small garden post holds each one open; catches under the attic floor hold them shut. Three entrance doors open outward and each floor has two rooms joined by a door on cotton-tape hinges. The roof lifts off the tower. A captive drawer slides 200 mm out of the plinth. Optional LED lighting has its wire holes and a screw-closed battery hatch.
- **One config drives everything.** Height, base, plinth, drawer, doors, veranda position and size, hinge hole patterns, plywood stock and colours all live in `source/config.json`.
- **Checked automatically.** Every build checks for solid overlaps, samples the wall swing every 5° up to the 100° stop and sweeps all six doors. It also checks drawer travel to its stop, roof lift, window clearance, that every clay figure passes upright through every doorway and is too big to swallow, that every magnet is sealed in wood, that every piece belongs to one assembly step, cut-sheet spacing, part and hardware counts, and the PDF print scale. Separate checks rebuild the house with the thinnest and thickest measured plywood, follow the tolerance chain of each joint, and compute the tip-over force with the walls open. Any failed check stops the build.
- **Clay figures.** Moominpappa, Moominmamma, Moomintroll, Snufkin, the Snork Maiden and Little My are signed-distance "lumps" pressed together like real clay. The build computes each figure's volume, the grams of clay per colour, and the saving from a foil core.
- **Many output formats.** A native FreeCAD document, STEP solids (closed, open, exploded, one per build part), DXF profiles, sheet layouts as SVG, CNC operation files as SVG and DXF, PDFs and CSV shopping lists.

## Try it: the 3D viewer (no FreeCAD needed)

The quickest way is the [online viewer](https://hvitis.github.io/MoominsHouse/). It is rebuilt from `main` on every push. To run it locally, or to see your own config changes, you need Python 3.12+ and git.

```sh
git clone https://github.com/hvitis/moominshouse.git
cd moominshouse
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python source/serve.py --open
```

On Windows, use `py -3.12 -m venv .venv`, and run `.venv\Scripts\python` in place of `.venv/bin/python`.

On the first start, `serve.py` builds `output/parts.json` from the model, which takes about 10 seconds. It also prepares the supplier DXF. A matching production build supplies the layout immediately; a fresh checkout computes the layout, which can take several minutes. It then opens http://127.0.0.1:8765/, or the next free port. The viewer works offline, because three.js is vendored, and the server only listens on your own machine.

Furniture and the garden scene appear only in the 3D viewer and renders. The build kit contains no furniture CAD plans, cutting sheets or printouts.

In the viewer you can:

- open the walls about their real hinge axes, swing the doors, lift or remove the roof, and slide the drawer out;
- show or hide the veranda, the furniture, the clay figures, the screws and hinge axes, and the dimensions;
- X-ray the walls, explode the assemblies, or cut the model above any height;
- click any part to see its ID, size, quantity and assembly note, or a figure to see how much clay it needs;
- enable **Piece IDs** to show the build codes on the model;
- search an exact part or instance ID to enable X-ray, highlight matching pieces in yellow and center the camera;
- open **Settings → DXF** for the supplier drawing, with pan, zoom, thickness layers and a separate **Piece IDs** toggle. Open another DXF or download the displayed file.

After you edit `source/config.json`, run `serve.py --rebuild` to see the change.

## 3D-printable furniture

The [prints page](https://hvitis.github.io/MoominsHouse/#printables) shows furniture you can 3D print for the house. You can turn each piece in 3D, see its print checks (it fits the printer, needs no supports, has thick enough walls and is too big to swallow) and download STL, 3MF or STEP files. Each piece is a short Python file in `source/prints/`. On the Mac, `make studio` opens a live preview that rebuilds the part each time its file is saved or a measurement slider moves. `make prints` publishes the files for the site. It is the **3D printables** tab of the online viewer, and CI publishes it with the viewer on every push to `main`. See [3D-printable furniture](docs/PRINTING.md).

## Generate the build files

Run `make joints` to prepare the [physical joint samples](docs/JOINT-VALIDATION.md) before cutting the complete house.

The PDFs, CAD files and cut sheets are **not in this repository**. Together they are about 100 MB, and they are rebuilt from source.

**If you only want to build the house,** download the PDFs and the build kit from the [latest release](https://github.com/hvitis/moominshouse/releases/latest). Generate the files yourself only if you change the design.

**1. Install FreeCAD 1.1 or later.** The CAD stages run in FreeCAD's bundled Python, which supplies the OpenCASCADE kernel, numpy and shapely.

| OS | Install | `--freecad-python` |
| --- | --- | --- |
| macOS (tested) | `brew install --cask freecad` | `/Applications/FreeCAD.app/Contents/Resources/bin/python` |
| Linux (untested) | Download the AppImage from [freecad.org](https://www.freecad.org/downloads.php), then run `./FreeCAD_*.AppImage --appimage-extract` | `squashfs-root/usr/bin/python` |
| Windows (untested) | Use the installer from [freecad.org](https://www.freecad.org/downloads.php) | for example `"C:\Program Files\FreeCAD 1.1\bin\python.exe"` |

Before a full build, check that this interpreter can load everything the build needs:

```sh
FREECAD_PYTHON=/Applications/FreeCAD.app/Contents/Resources/bin/python
"$FREECAD_PYTHON" -c "import sys,pathlib; sys.path.insert(0,str(pathlib.Path(sys.executable).resolve().parent.parent/'lib')); import FreeCAD, Part, Sketcher, numpy, shapely; print('FreeCAD', '.'.join(FreeCAD.Version()[:3]), 'OK')"
```

**2. Set up the normal Python environment** (the same as for the viewer above).

**3. Rebuild everything:**

```sh
make all        # config check and tests, full rebuild, plywood thickness check
```

`make` uses the macOS FreeCAD path; elsewhere pass yours, for example `make all FREECAD_PYTHON=squashfs-root/usr/bin/python`. `make help` lists the single steps (`check`, `build`, `tolerance`, `clean`, `viewer`, `site`, `stock`, `cutfile`). Without `make`, run `.venv/bin/python source/rebuild.py --freecad-python "$FREECAD_PYTHON"` with `--tolerance` to include the thickness check before packaging.

The rebuild takes about two minutes and the thickness check about one. The rebuild uses an isolated workspace. `make all` runs the thickness check before packaging. It replaces `output/` only after every required stage succeeds. A failed build preserves the previous output and keeps diagnostics in `.build-work/`. You get:

| Path | Contents |
| --- | --- |
| `output/pdf/` | Nine PDFs with A4 workshop pages and native A3 supplier sheets: the complete book, instructions, cutting templates, dimensioned parts, decor (palette, stone panels, roof shingle strips) and the clay family, 3 mm hand templates and a supplier appendix |
| `output/cad/` | `MoominHouse.FCStd` (native, editable), STEP assemblies (closed, open, exploded) and `parts/*.step` |
| `output/dxf/` | One DXF per profile, full-size sheet layouts (`*-layout.svg`), and CNC operation files for every thickness (`*-cnc-*.svg`, `*-cnc-*.dxf`) |
| `output/previews/` | CAD-derived renders and clay renders |
| `output/reports/` | `release-validation.json` (every check), `cad-validation.json`, `thickness-tolerance.json`, `parts.csv`, `hardware.csv`, `stock.csv` |
| `output/Moomin-House-Supplier-Cut.dxf` | Everything the supplier cuts in one DXF R12 file: cutting lines only, one layer per thickness |
| `output/Moomin-House-Build-Kit.zip` | All of the above plus the source, in one package |

Then read the [build guide](docs/BUILD-GUIDE.md) before you print anything. The 1:1 templates must be printed at 100 % and measured.

For CNC machining, read [docs/SUPPLIER-READINESS.md](docs/SUPPLIER-READINESS.md) first, then send `Moomin-House-Supplier.pdf` (it now opens with the specification and a checklist to confirm) and either `Moomin-House-Supplier-Cut.dxf` (every cutting line in one file, as most shops ask) or the matching operation CSV, DXF R12 and SVG files. Native A3 production pages cover the only two plywood thicknesses, 3 and 6 mm. Each page contains one operation without labels or a background. Separate reference pages identify the parts, machining faces, and depths. The complete book remains entirely A4 and includes an A4 supplier summary. Large individual parts use two A4 template pages with overlap. `Moomin-House-3mm-Hand-Templates.pdf` remains available for thin parts only. Add `--lang en` to `source/rebuild.py` for English supplier text.

`make build` writes the supplier cut file, `output/Moomin-House-Supplier-Cut.dxf`, and every `v*` release attaches it. `make cutfile` rewrites it in about a second from the last build's nesting. After a design or config change, run `make build` instead, so the DXF and the supplier PDF's sheet maps come from the same nesting.

To choose which plywood to buy, run `make stock`. It asks for a supplier (or reuses one saved in `ops/suppliers/`), the sheet sizes, prices and packs it sells, the minimum distance between parts, the edge margin and the supplier's saw kerf. It then nests every plywood part of the house (no furniture, figures, garden, woodpile, hardware or screws) on many mixes of those sizes, including formats the supplier saws from a large board, and writes `output/pdf/Optymalne-wymiary-i-cennik-<supplier>.pdf`: the cheapest sizes and quantities per grade, the variants they beat, the price per m² and the sheet layouts. `ops/suppliers/sklejka-krakow.json` is a worked example.

The default cutting layout uses **3 mm laser spacing** and **grade 2/2 birch plywood for every sheet**, in both 3 and 6 mm. The saved supplier profile prices grade 2 only. Router cutting requires wider lanes and a new nesting.

Fixed walls are 420 mm tall and retain the blank end edges. Opening walls are 418 mm tall. Four continuous 402 mm pillars pass through both intermediate floors. All floor plates use 6 mm plywood. Each floor is a rear piece and two front pieces locked together on the house axis by a CNC puzzle joint. The ground floor joins over 3 mm thick, 4 mm wide strips, the upper floors' finger joints over 3 × 12 mm strips. The base and roof ring use the sections listed in the generated specifications. Positioning maps show the seams and supports. Check a physical floor-joint sample before assembly. The company must confirm cutters, hold-down, boundary cutting, and tolerances.

## Change the design

1. Edit `source/config.json`. For example, change `height`, `veranda.facet`, `doors`, `plinth.drawer.travel`, `figures.levels`, or `stock` to match the plywood you have. Editors that understand JSON Schema autocomplete and explain every key from `source/config.schema.json`.
2. Check the config in about a second: `.venv/bin/python source/config_check.py`. It catches typos, wrong types and contradictions, such as two doors on one facet or a hinge that doesn't fit on the wall.
3. Preview the change: `.venv/bin/python source/serve.py --rebuild --open`.
4. Run the fast tests (about 10 s, no FreeCAD):
   ```sh
   .venv/bin/python -m pip install -r requirements-dev.txt
   make check
   ```
5. Run `make all`, and read `output/reports/release-validation.json` (and `make stackup` for the joint tolerance chains and the safety audit). The checks tell you whether the walls still swing clear, the drawer still slides, the figures still fit the doors, and everything still fits the sheets. `thickness-tolerance.json` tells you whether real plywood within the measured band in `thickness_tolerance` would close any clearance.

`make specs` updates the generated specification tables in both READMEs and the build guide. The tests reject stale tables. [CONTRIBUTING.md](docs/CONTRIBUTING.md) describes the formatting checks.

[docs/PIPELINE.md](docs/PIPELINE.md) explains every stage, the data model, every config key, and how releases and the online viewer are published.

## Repository layout

```
source/                  everything that generates the house
  config.json            design parameters
  config.schema.json     what every parameter means, its units and limits
  config_check.py        validates a config before building
  model.py               parts and placements (single source of truth)
  architecture.py        veranda, entrances, dormers, battens, ladder, plinth details
  clay.py                thermo-clay figures
  build_cad.py           FreeCAD CAD + checks                     (FreeCAD Python)
  nest.py, stock.py      A3 sheet nesting; plywood purchase planner (make stock)
  render.py, cover.py, book.py, verify.py, package.py             (normal Python)
  rebuild.py             builds in isolation and publishes checked output
  thickness_check.py     the house rebuilt with real, measured plywood  (FreeCAD Python)
  serve.py, viewer/      interactive 3D viewer (three.js r160 vendored)
  export_viewer.py       the viewer as a static site (GitHub Pages)
  release.py             uploads the PDFs and build kit to a GitHub release
tests/                   model and export tests, static viewer browser checks
.github/workflows/       cached viewer export and Pages on main; full builds on release
docs/                    build guide, pipeline, publishing, ideas, README images
original/                your own reference photos (git-ignored)
output/                  generated, git-ignored
_site/                   exported static viewer, git-ignored
Makefile                 make all / check / build / tolerance / clean / viewer / site
package.json             optional local browser checks (Node.js + Playwright)
README.md                English documentation
README.pl.md             Polish documentation
TODO.md                  backlog for the house itself, in priority order
PLAN.md                  design log of revisions 2–6
LICENSE                  CC BY-NC-SA 4.0
```

## Documentation

- [Build guide](docs/BUILD-GUIDE.md): what you are building, printing and cutting, stock and hardware, assembly, the clay figures and the checks.
- [How the build works](docs/PIPELINE.md): runtimes, stages, data model, config reference and workflows.
- [3D-printable furniture](docs/PRINTING.md): the designs, the live studio, the print checks and publishing.
- [Ideas](docs/IDEAS.md): where the project could go next (Letter paper, a container build, a laser edition, presets).
- [Publish on GitHub](docs/PUBLISHING.md): repository setup, GitHub Pages and browser checks.
- [TODO](TODO.md): open improvements to the house itself.

## Safety

This is a design for a hand-built wooden toy, not a certified toy. The CAD checks prove clearances, but not glue strength, stability or toy safety; [RISKS.md](RISKS.md) records every hazard found and what the design does about it. Dry-fit it with your real plywood and hinges first and work through the "Dry-fit and safety checks" page of the book. Round every exposed edge. Strap the house to the room wall with the anti-tip kit: the generated risk audit records the estimated tipping force for the current design. The four magnets are sealed inside hardwood blocks; check that none ever shows. Use only primer, paint and varnish declared to EN 71-3; the book names example products.

## Status

- Tested on macOS (Apple silicon) with Python 3.12 and FreeCAD 1.1.4. Linux and Windows should work with FreeCAD's bundled Python, but have not been tried yet.
- The design is checked in CAD but has not yet been built in plywood. Expect to adjust tolerances after a first dry fit.

## Trademarks and licence

Copyright © 2026 hvitis. The code, the design and everything the build generates from them are licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) ([`LICENSE`](LICENSE)). You may share and adapt the house for non-commercial purposes, if you give credit and share your changes under the same licence.

The vendored three.js files in `source/viewer/vendor/` keep their own MIT licence (`THREE-LICENSE.txt`).
The DejaVu fonts keep their own licence in `source/fonts/LICENSE_DEJAVU`.

Moomin, the Moomin characters and the Moomin house are trademarks and copyrighted works of Moomin Characters Oy. This licence does not and cannot grant any rights in them. This repository is a personal, non-commercial fan project. It does not include, and must not be used to distribute, official artwork or product photos. Do not sell kits, books or figures made from it.

<p align="center">
  <img src="docs/images/social-preview.png" width="800" alt="Moomin House: a plywood dollhouse generated entirely from code">
</p>

