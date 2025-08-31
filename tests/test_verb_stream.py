import importlib.util
import socket
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

memory = _load("tripd_pkg.tripd_memory", "tripd/tripd_memory.py")
expansion = _load("tripd_pkg.tripd_expansion", "tripd/tripd_expansion.py")
tripd = _load("tripd_pkg.tripd", "tripd/__init__.py")
verb_stream = _load("tripd_pkg.verb_stream", "tripd/verb_stream.py")
TripDModel = tripd.TripDModel
start_verb_stream = verb_stream.start_verb_stream


def test_unix_socket_stream(tmp_path):
    model = TripDModel()
    sock = tmp_path / "verbs.sock"
    start_verb_stream(model, unix_socket=str(sock))
    time.sleep(0.1)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(sock))
        client.sendall(b"test_verb()\n")
    time.sleep(0.1)
    assert "test_verb()" in model.extra_verbs
