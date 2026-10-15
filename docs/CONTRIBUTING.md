# Change and review the project

The production geometry starts in `source/model.py` and `source/config.json`.
The documentation tables use `source/specifications.py`.
The PDF book uses the same specification helpers.
The build and packaging modules have separate tests for failure and publication.

## Make a change

1. Keep each change focused on one behavior.
2. Keep calculations in functions with explicit inputs.
3. Put new geometry in the production model before adding downstream output.
4. Run `make specs` after a change to dimensions or material thicknesses.
5. Run `make check`.
6. Run `make lint`.
7. After a change to CAD or production exports, run `make all`.

`make check` includes the generated documentation check.
`make lint` runs Ruff on the modules listed in `pyproject.toml`.
`make format` formats those modules.
Legacy modules enter that list as their responsibilities move into smaller functions.
This scope keeps unrelated formatting changes out of geometry reviews.

## Review a build

1. Read `output/reports/release-validation.json`.
2. Read `output/reports/thickness-tolerance.json` after `make all`.
3. Open the generated PDFs before sending contours to a supplier.
4. Use the [physical joint samples](JOINT-VALIDATION.md) with the real material batch.
5. Save completed physical measurements outside `output/`.

`make build` checks the nominal design and creates its kit.
`make all` also requires the thickness check before it creates the kit.
A release requires both passing reports inside the downloadable ZIP.
`source/release.py` rejects missing, stale or mismatched packaged reports.

## Inspect a failed build

The previous successful output remains in `output/`.
The failed workspace remains under `.build-work/build-*/`.
Its reports are under `output/reports/` inside that workspace.
The terminal output gives the workspace path.

`make clean` explicitly deletes generated output.
It does not delete the retained diagnostic workspaces.
