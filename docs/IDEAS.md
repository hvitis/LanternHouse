# Ideas

[`TODO.md`](../TODO.md) is the backlog for the house itself: the rope ladder, window hoods, more figures. This page is about the project around it: how more people could see it, build it and change it. The ideas are grouped by theme, and the most useful ones per unit of effort come first.

## The five most useful next steps

| # | Idea | Effort | Why |
| --- | --- | --- | --- |
| 1 | [US Letter paper option](#us-letter-paper) | medium | Many builders (US, Canada) print on Letter, and a misprinted 1:1 template ruins plywood |
| 2 | [Reproducible build in a container, run in CI](#reproducible-builds-in-a-container) | medium | Linux and Windows users can rebuild, and tagged releases build themselves |
| 3 | [Deterministic outputs](#deterministic-outputs) | small | Two builds of the same source give identical files, so diffs show only real changes |
| 4 | [Generate every number in the docs](#generate-every-number-in-the-docs) | small | The build guide can't drift from the model again |
| 5 | [Download the model for AR](#download-the-model-for-ar) | small | See the house at true scale on the table before buying plywood |

## Done

- **The 3D viewer on GitHub Pages.** `source/export_viewer.py` writes the viewer as a static site, and `.github/workflows/ci.yml` deploys it from `main`. The README links to it.
- **Build kits on GitHub Releases.** `source/release.py` uploads the six PDFs and the build kit to a tagged release. It first checks that the build passed, matches the source on disk, and is committed and pushed.
- **Fast tests and a config schema.** `source/config.schema.json` documents and validates every key, and editors autocomplete it. `source/config_check.py` adds cross-field rules and runs before every build. `tests/` checks the config and the model's geometry in about 10 s without FreeCAD, and CI runs it on every push and pull request.

See [docs/PIPELINE.md](PIPELINE.md#continuous-integration-and-publishing) for how to use them.

## Let people use it without installing anything

### Download the model for AR

Add a "Download GLB" button to the viewer with three.js `GLTFExporter`. On a phone, AR Quick Look (iOS, after conversion to USDZ) or Scene Viewer (Android) can then show the house at true scale on the table where it will stand, before any plywood is bought.

## Make the build reproducible for anyone

### Reproducible builds in a container

The full build has only been run on macOS. A container or devcontainer with FreeCAD 1.1 (the AppImage, or conda-forge `freecad`) plus `requirements.txt` would let Linux and Windows users rebuild everything, and lets CI do the same.

### Full builds in CI

CI already runs the FreeCAD-free checks on every push. With the container, a tag could also run the full rebuild, where `verify.py` fails the build if any release check fails, and then run `source/release.py`. Releases would then no longer depend on one maintainer's Mac.

### Deterministic outputs

ReportLab writes the creation time and a random document ID into every PDF, and the zip stores file times. With `canvas.Canvas(..., invariant=1)`, fixed zip timestamps and sorted JSON keys, two builds of the same source would be byte-identical. Diffs would then show only real changes. That matters once other people send pull requests.

### More cross-field rules

`config_check.py` covers the rules that are certain: doors, roof, hinges, laser stock and sheet margins. Two candidates need a decision on the intended limits first: whether `wall_height` must equal three floor pitches, and how much height the roof needs above the walls. The full build catches both today, just later.

## Reach builders beyond A4, metric and jigsaws

### US Letter paper

`book.py` lays out everything on A4: page size, 190 × 260 tiles with 10 mm overlap, the trim carriers. A `paper` key (`A4` or `letter`) that sets the page size and tile window would make the 1:1 templates printable in North America without scaling.

### A laser-cut edition

The 3 mm sheets already come out as laser files. Possible next steps:

- extend the laser files to every thickness, with a `laser.bed` size such as the common 600 × 400 hobby beds;
- replace the corner gussets with tab-and-slot joints at the facet corners, so the 30° facet angle sets itself;
- add a "laser only" stock preset.

That makes the house a natural makerspace project.

### Presets

Add `source/presets/*.json` and a `--config` option, so a builder can pick a starting point without editing the default: "jigsaw, default stock", "A4 plywood only", "laser 3 mm", "half-scale desk model". The `stock` section already supports alternatives.

### Translations

All book text lives inline in `book.py`, in English. Moving it into per-language string files would allow Polish, Finnish, Swedish and other editions. The Moomins are a Finnish-Swedish story, after all.

## A better build and a better toy

### A cost and time page

`stock.csv` and `hardware.csv` already hold the quantities. Add unit prices to the config (plywood per m² per thickness, hardware, paint, clay), and an estimate of the hours per step. The book could then open with "about € N and N weekends".

### A family track

Mark the steps a child can help with: painting, the printed decor, the shingle strips, the clay figures, furniture glue-ups. Give them picture-only pages. The house is for ages 3–5, but building it can involve them too.

### Generate every number in the docs

The stock tables in `docs/BUILD-GUIDE.md` are regenerated on every build. The dimension list there is still hand-written, and it already drifted once (revision 5 changed the base from 8 to 6 mm and the plinth from 64 to 66 mm). Generating it from `derived.dimensions`, in the same marker-block way, would keep it in step with the model.

### A half-scale variant

An approximately 450 mm desk model, entirely in 3 mm laser plywood, works as a gift or as a cheap test build before the full-size plywood. The furniture would have to scale or be left out. The existing checks would show what still fits.

## Publishing and naming

"Moomin", the Moomin characters and the house's look are protected by Moomin Characters Oy. Non-commercial fan builds are common. Takedown requests usually start with the name in a prominent place, the character likenesses, or anything that is sold. Options, from least to most change:

1. Keep it clearly non-commercial and unofficial (the README says so).
2. Give the repository a descriptive name, such as "round blue tower dollhouse", and describe it as "inspired by".
3. Make the clay figures an optional module, so the house itself contains no character likeness.

Whatever you choose, do not sell kits or printed books under the name without a licence.

## Code health for contributors

- Much of the code is very compact, with several statements per line. A one-time `ruff format` and a `pyproject.toml` would make it easier for newcomers. Do it just after a release, when no other branch is open, because the diff touches every line.
- `book.py` is about 860 lines. Splitting it by section (instructions, parts, templates, decor, appendix) would make the book easier to change.
