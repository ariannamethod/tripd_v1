import importlib.util
import sys
import types
from pathlib import Path

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

_load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
_load("tripd_pkg.tripd_expansion", "tripd/tripd_expansion.py")
tripd = _load("tripd_pkg.tripd", "tripd/__init__.py")
TripDModel = tripd.TripDModel


def test_selector_differs_between_modes():
    text = "fractal energy"
    deterministic = TripDModel()
    fractal = TripDModel(fractal_metrics=True)
    sel_det = deterministic.metrics(text)["selector"]
    sel_frac = fractal.metrics(text)["selector"]
    assert sel_det != sel_frac


def test_section_differs_between_modes():
    text = "fractal energy"
    deterministic = TripDModel()
    fractal = TripDModel(fractal_metrics=True)
    sec_det = deterministic._choose_section(deterministic.metrics(text))
    sec_frac = fractal._choose_section(fractal.metrics(text))
    assert sec_det != sec_frac
