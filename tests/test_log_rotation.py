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


def test_log_rotation(monkeypatch, tmp_path):
    memory = _load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
    log_path = tmp_path / "scripts.log"
    monkeypatch.setattr(memory, "_LOG_PATH", log_path)
    monkeypatch.setattr(memory, "_LOG_MAX_BYTES", 100)
    memory._SCRIPTS_INDEX.clear()
    memory._SCRIPT_LIST.clear()
    memory._CACHE_LOADED = False
    memory._load_cache()

    for i in range(20):
        memory.log_script(f"script_{i}")

    rotated = log_path.with_suffix(log_path.suffix + ".1")
    assert rotated.exists()
    assert log_path.exists()
    assert any("script_19" in line for line in log_path.read_text().splitlines())
