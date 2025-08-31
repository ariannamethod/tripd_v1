import importlib.util
import math
import sys
import types
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent


def _load(name: str, file: str):
    pkg = name.split(".")[0]
    if pkg not in sys.modules:
        package = types.ModuleType(pkg)
        package.__path__ = [str(BASE / "tripd")]
        sys.modules[pkg] = package
    spec = importlib.util.spec_from_file_location(name, BASE / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    parent = sys.modules[pkg]
    parts = name.split(".")
    if len(parts) > 1:
        setattr(parent, parts[1], module)
        if file.endswith("__init__.py"):
            for sym in getattr(module, "__all__", []):
                setattr(parent, sym, getattr(module, sym))
    return module

# Load modules under a package name to satisfy relative imports
_load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
_load("tripd_pkg.tripd_expansion", "tripd/tripd_expansion.py")
tripd = _load("tripd_pkg.tripd", "tripd/__init__.py")
TripDModel = tripd.TripDModel


def test_public_metrics():
    model = TripDModel()
    metrics = model.metrics("abc")
    assert metrics["entropy"] == pytest.approx(math.log2(3), abs=1e-12)
    assert metrics["perplexity"] == pytest.approx(3.0, abs=1e-12)
    assert metrics["resonance"] == pytest.approx(0.294, abs=1e-12)


def test_resonance_differs_for_texts():
    model = TripDModel()
    r1 = model.metrics("abc")["resonance"]
    r2 = model.metrics("abd")["resonance"]
    assert r1 != r2
