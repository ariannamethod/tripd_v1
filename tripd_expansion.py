"""Asynchronous model expansion utilities for TRIPD.

The real project would fine‑tune a transformer on collected scripts.
For demonstration purposes we simply record when a training event would
occur and run the task in a background thread.
"""

from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Iterable
import time

from .tripd_memory import load_scripts

_TRAIN_LOG = Path(__file__).resolve().parent / "training.log"


def _train_on_scripts(scripts: Iterable[str]) -> None:
    """Pretend to fine‑tune a model on the provided scripts."""
    # A realistic implementation would invoke torch/transformers here.
    scripts = list(scripts)
    time.sleep(0.1)  # Simulate a bit of work.
    timestamp = int(time.time())
    with open(_TRAIN_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"{timestamp}\t{len(scripts)}\n")


def train_async() -> None:
    """Launch an asynchronous training job using the latest scripts."""
    scripts = load_scripts()[-5:]
    thread = Thread(target=_train_on_scripts, args=(scripts,), daemon=True)
    thread.start()
