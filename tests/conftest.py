"""Fast checks that need no FreeCAD: the config schema and the pure-Python model.

    .venv/bin/python -m pip install -r requirements-dev.txt
    .venv/bin/python -m pytest

The full solid-kernel checks (overlaps, wall swing, door sweep, PDFs) run in source/rebuild.py.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))

@pytest.fixture(scope='session')
def cfg():
    import config_check
    return config_check.check()

@pytest.fixture(scope='session')
def data():
    """One model build (about 10 s) shared by every test."""
    import model
    return model.build()
