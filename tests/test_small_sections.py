import importlib.util
import sys
import random
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

memory = _load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
expansion = _load("tripd_pkg.tripd_expansion", "tripd/tripd_expansion.py")
tripd = _load("tripd_pkg.tripd", "tripd/__init__.py")
TripDModel = tripd.TripDModel


@pytest.mark.parametrize("num_cmds", [1, 2, 3])
def test_generate_from_small_section(tmp_path, num_cmds):
    memory._LOG_PATH = tmp_path / "scripts.log"
    expansion._TRAIN_LOG = tmp_path / "train.log"
    dictionary = "## small\n" + "\n".join(f"cmd{i}()" for i in range(num_cmds))
    dictionary += "\n\n## pool\n" + "\n".join(f"pool{i}()" for i in range(4)) + "\n"
    path = tmp_path / "dict.md"
    path.write_text(dictionary)

    model = TripDModel(path)
    random.seed(0)
    script = model.generate_from_section("small")
    lines = [line.strip() for line in script.splitlines()[1:] if line.strip()]
    extra_set = set(model.extra_verbs)
    commands = [line for line in lines if line not in extra_set]

    assert len(commands) == 4
    for i in range(num_cmds):
        assert f"cmd{i}()" in commands
    if num_cmds < 4:
        assert any(f"pool{i}()" in commands for i in range(4))


@pytest.mark.parametrize("num_cmds", [1, 2, 3])
def test_generate_script_with_small_section(tmp_path, num_cmds):
    memory._LOG_PATH = tmp_path / "scripts.log"
    expansion._TRAIN_LOG = tmp_path / "train.log"

    dictionary = "## small\n" + "\n".join(f"cmd{i}()" for i in range(num_cmds))
    dictionary += "\n\n## pool\n" + "\n".join(f"pool{i}()" for i in range(4)) + "\n"
    path = tmp_path / "dict.md"
    path.write_text(dictionary)

    model = TripDModel(path)
    random.seed(0)
    model._choose_section = lambda metrics: "small"
    script = model.generate_script("msg")
    lines = [line.strip() for line in script.splitlines()[1:] if line.strip()]
    extra_set = set(model.extra_verbs)
    commands = [line for line in lines if line not in extra_set]

    assert len(commands) == 4
    for i in range(num_cmds):
        assert f"cmd{i}()" in commands
    if num_cmds < 4:
        assert any(f"pool{i}()" in commands for i in range(4))
