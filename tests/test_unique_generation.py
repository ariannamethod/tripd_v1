import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from tripd import TripDModel


def test_generate_script_retries_on_duplicate(monkeypatch):
    model = TripDModel()
    call_count = {"count": 0}

    def fake_log_script(script: str) -> bool:
        call_count["count"] += 1
        return call_count["count"] > 1

    monkeypatch.setattr("tripd_memory.log_script", fake_log_script)
    monkeypatch.setattr("tripd.log_script", fake_log_script)
    monkeypatch.setattr("tripd.train_async", lambda: None)

    model.generate_script("hello world")

    assert call_count["count"] >= 2
