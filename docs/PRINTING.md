# 3D-printable furniture

The house's furniture and accessories can also be 3D printed. Each design is a short Python file. Its STL, 3MF and STEP files are generated on the Mac, and the [prints page](https://hvitis.github.io/moominshouse/prints.html) shows every published design in 3D with its print checks and downloads.

| Where | What runs | Needs |
| --- | --- | --- |
| **Mac** | `make studio`: a live preview in the browser while you (or Claude) change a design. `make prints`: generate and publish the files. | `.venv` with `requirements-print.txt` (build123d, a CAD library on the OpenCASCADE kernel) |
| **Web** | `prints.html` in the GitHub Pages site: view, check and download each published design | Nothing: it reads the committed files in `prints/` |
| **CI** | Re-reads every published STL, reruns the print checks, and fails if `prints/` is older than its sources | numpy only |

## Quick start

```sh
.venv/bin/python -m pip install -r requirements-print.txt   # once
make studio                                                  # opens http://127.0.0.1:8766/ (or the next free port)
```

Edit `source/prints/chair.py` and save. The page rebuilds the chair and shows it about half a second later, without losing the camera. Each design's measurements are sliders in the studio. A slider rebuilds the part on the Mac. Its value is kept until you press **Back to the design's values**, and nothing is written to the design file. When you like a value, change its default in `PARAMS`.

When the design is ready:

```sh
make prints          # build the changed designs into prints/ (a design that fails a check is not published)
git add source/prints prints && git commit && git push      # CI deploys the prints page from main
```

## Working with Claude

Ask Claude in the terminal for a change, for example "make the chair back 5 mm taller and add a heart cut-out". With `make studio` running, Claude changes `source/prints/chair.py` and you see the result in the browser as soon as it saves. Claude reads the build lines the studio prints in the terminal. It also takes screenshots with

```sh
node source/print_shot.mjs chair                 # output/prints/shots/chair-{iso,front,side,under}.png
```

so it can look at the part, and at the red overhangs, before saying it is done. The script finds the running studio through `output/prints/studio-url.txt`.

## Writing a design

A design is `source/prints/<name>.py`. Files starting with `_` are ignored.

```python
"""One-line summary, shown under the title.

Longer notes on how it is designed, shown below the print checks.
"""
from build123d import Box, Pos

TITLE='Stool'
NOTES='Print upright, no supports.'          # printing advice, shown under the downloads
COLOR='wood'                                 # a key of "colors" in source/config.json, or #rrggbb
PARAMS={'size':(36,32,60,.5)}                # name: (default, min, max, step[, unit]); unit defaults to mm
# TOY=False                                  # only for parts that are not toys: skips the small-parts check

def build(size):
    return Pos(0,0,size/2)*Box(size,size,size)
```

`build()` returns a build123d solid. The generator moves it so it stands centred on the bed at z=0, so the design does not need to place it. An exception in `build()` shows in the studio as an error over the last good build, with the line of the design file it came from. Raise a `ValueError` with a helpful message for measurements that cannot work together. `chair.py` does this when the seat is too low for its 45° arches.

## The print checks

Every check reads the STL that is offered for download, not the CAD solid it came from (`source/print_mesh.py`). The limits are in `source/prints/printer.json`. Set them to match your printer: changing the file rebuilds every design in the studio, and `make prints` republishes them.

| Check | Fails or warns when |
| --- | --- |
| Closed solid | An edge is not shared by exactly two faces: holes or doubled edges. **Fail** |
| One piece | The mesh has more than one shell: a floating piece or a sealed hollow. **Fail** |
| Fits the printer | It does not fit the bed (either way round) less `bed_margin`, or it is taller than the build volume. **Fail** |
| Stands flat on the bed | Less than `min_base_area` mm² touches the bed: **warn**, add a brim. Under 1 mm²: **fail** |
| No supports needed | A surface leans out more than `max_overhang` degrees from vertical (1° of grace for faceted cones). **Warn**. The page paints these faces red |
| Walls thick enough | The thinnest wall at `wall_samples` sampled places, measured straight into the part, is under `min_wall`. **Fail**. A red dot marks the place |
| Too big to swallow | The part fits the EN 71-1 small-parts cylinder (config `figures.small_parts`, the same rule as the clay figures). **Fail**, unless the design sets `TOY=False` |

The page also gives the size, the solid weight and a rough weight at the profile's `shell` and `infill`. Your slicer gives the real weight and time.

## Files

| Path | Role |
| --- | --- |
| `source/prints/*.py` | The designs |
| `source/prints/printer.json` | Printer, material and check limits |
| `source/print_build.py` | Builds a design to STL, 3MF and STEP and checks it. `make prints` publishes the changed designs into `prints/` |
| `source/print_mesh.py` | Reads STL files, writes 3MF files and runs the print checks (numpy only) |
| `source/print_studio.py` | The live studio: watches `source/prints/`, rebuilds into `output/prints/live/`, pushes each build to the page |
| `source/viewer/prints.html`, `prints.js` | The page, used by both the studio and the published site |
| `source/print_shot.mjs` | Screenshots of the running studio |
| `prints/` | The published files and `manifest.json` (committed; generated, never edited by hand) |
| `tests/test_prints.py`, `tests/prints-smoke.mjs` | The checks on hand-made meshes, the published prints re-checked from their STL files, and the page in a browser |

A design whose source, `printer.json`, small-parts rule or mesh tolerance changed is out of date until `make prints` runs again. Its hash in `prints/manifest.json` no longer matches, and `pytest` (and so CI) fails with a message that says so. `make prints` only rebuilds designs whose hash changed, so files for unchanged designs stay byte-identical. Pass `--force` to `source/print_build.py` to rebuild every design anyway.
