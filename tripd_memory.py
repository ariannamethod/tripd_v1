from __future__ import annotations

"""Utility functions for tracking generated TRIPD scripts.

This module stores each produced script in a JSON lines log file so that
scripts are never repeated.  The log also provides a simple count used by
training routines to trigger periodic fine‑tuning once enough examples have
been collected.
"""

from pathlib import Path
import json
from typing import List

_LOG_PATH = Path(__file__).resolve().parent / "scripts.log"


def _ensure_log() -> None:
    """Create the log file if it does not yet exist."""
    if not _LOG_PATH.exists():
        _LOG_PATH.touch()


def load_scripts() -> List[str]:
    """Return a list of all previously generated scripts."""
    _ensure_log()
    scripts: List[str] = []
    with _LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                scripts.append(json.loads(line)["script"])
            except Exception:
                # Ignore malformed lines while keeping the log readable.
                continue
    return scripts


def log_script(script: str) -> None:
    """Persist a script if it has not been seen before."""
    scripts = set(load_scripts())
    if script in scripts:
        return
    _ensure_log()
    with _LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"script": script}) + "\n")


def get_log_count() -> int:
    """Return how many unique scripts have been recorded."""
    return len(load_scripts())
