# Build the Moomin House on this machine. FreeCAD 1.1+ supplies the CAD kernel; everything else runs in .venv.
# Every target stops at the first failed check.
FREECAD_PYTHON ?= /Applications/FreeCAD.app/Contents/Resources/bin/python
PYTHON ?= .venv/bin/python
FREECAD_ENV = MOOMIN_HEADLESS=1 QT_QPA_PLATFORM=offscreen
# The venv also sees other projects' site-packages; their pytest plugins must not load here.
TEST_ENV = PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

.PHONY: all check build tolerance clean viewer site help

all: check build tolerance  ## Config check and tests, full rebuild, then the plywood thickness check

check:  ## Config schema and rules, then the model tests (seconds, no FreeCAD)
	$(PYTHON) source/config_check.py
	$(TEST_ENV) $(PYTHON) -m pytest -q

build:  ## Empty output/, then CAD, sheets, renders, book, release checks and the build kit
	$(PYTHON) source/rebuild.py --freecad-python "$(FREECAD_PYTHON)"

tolerance:  ## The house from the nominal templates with the thinnest and thickest measured plywood
	$(FREECAD_ENV) "$(FREECAD_PYTHON)" source/thickness_check.py

clean:  ## Remove every generated file in output/
	$(PYTHON) source/rebuild.py --clean-only

viewer:  ## Open the 3D viewer in the browser
	$(PYTHON) source/serve.py --open

site:  ## Export the static 3D viewer to _site/ (no FreeCAD)
	$(PYTHON) source/export_viewer.py _site

help:  ## List the targets
	@grep -E '^[a-z]+:.*## ' Makefile | sed 's/:.*## /\t/'
