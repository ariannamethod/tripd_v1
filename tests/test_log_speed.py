import importlib.util
import sys
import time
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


def test_log_script_speed(monkeypatch, tmp_path):
    memory = _load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
    log_path = tmp_path / "scripts.log"
    monkeypatch.setattr(memory, "_LOG_PATH", log_path)
    memory._SCRIPTS_INDEX.clear()
    memory._CACHE_LOADED = False
    memory._load_cache()

    for i in range(5000):
        memory.log_script(f"script_{i}")

    start = time.perf_counter()
    memory.log_script("final_script")
    duration = time.perf_counter() - start

    assert duration < 0.05
