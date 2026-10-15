# Build the Moomin House on this machine. FreeCAD 1.1+ supplies the CAD kernel; everything else runs in .venv.
# Every target stops at the first failed check.
FREECAD_PYTHON ?= /Applications/FreeCAD.app/Contents/Resources/bin/python
PYTHON ?= .venv/bin/python
FREECAD_ENV = MOOMIN_HEADLESS=1 QT_QPA_PLATFORM=offscreen

.PHONY: all check build tolerance stackup cutfile clean viewer site stress images prints studio help

all: check build tolerance  ## Config check and tests, full rebuild, then the plywood thickness check
	$(PYTHON) source/package.py

stress:  ## Physical real stress tests with FreeCAD FEM, CalculiX, and Eurocode 5 analytics
	$(FREECAD_ENV) "$(FREECAD_PYTHON)" source/run_stress_tests.py

check:  ## Config schema and rules, then the model tests (seconds, no FreeCAD)
	$(PYTHON) source/config_check.py
	$(PYTHON) -m pytest -q

build:  ## Empty output/, then CAD, sheets, renders, book, release checks and the build kit
	$(PYTHON) source/rebuild.py --freecad-python "$(FREECAD_PYTHON)"

tolerance:  ## The house from the nominal templates with the thinnest and thickest measured plywood
	$(FREECAD_ENV) "$(FREECAD_PYTHON)" source/thickness_check.py

stackup:  ## Joint-by-joint plywood tolerance chains and the toy-safety audit (needs output/parts.json)
	$(PYTHON) source/stackup.py
	$(PYTHON) source/risk_audit.py

cutfile:  ## Rewrite the single supplier cut DXF from the current nesting (needs a build)
	$(PYTHON) source/cut_file.py

clean:  ## Remove every generated file in output/
	$(PYTHON) source/rebuild.py --clean-only

viewer:  ## Open the 3D viewer in the browser
	$(PYTHON) source/serve.py --open

site:  ## Export the static 3D viewer to _site/ (no FreeCAD)
	$(PYTHON) source/export_viewer.py _site

stock:  ## Interactive plywood purchase planner: supplier sizes and prices to the "Optymalne wymiary i cennik" PDF
	$(PYTHON) ops/stock.py

prints:  ## Generate the changed 3D-print designs (source/prints/) into prints/ for the site (Mac; requirements-print.txt)
	$(PYTHON) source/print_build.py

studio:  ## Live 3D-print studio in the browser: edit source/prints/*.py or move the sliders and the part follows
	$(PYTHON) source/print_studio.py --open

images:  ## Rerender and update README images in docs/images/
	$(PYTHON) source/readme_images.py --rerender

help:  ## List the targets
	@grep -E '^[a-z]+:.*## ' Makefile | sed 's/:.*## /\t/'
