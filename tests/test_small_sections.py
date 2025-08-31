import importlib.util
import sys
import random
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent

def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, BASE / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

memory = _load("tripd_pkg.tripd_memory", "tripd_memory.py")
expansion = _load("tripd_pkg.tripd_expansion", "tripd_expansion.py")
tripd = _load("tripd_pkg.tripd", "tripd.py")
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
