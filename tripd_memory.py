from __future__ import annotations

"""Utility functions for tracking generated TRIPD scripts.

This module stores each produced script in a JSON lines log file so that
scripts are never repeated.  The log also provides a simple count used by
training routines to trigger periodic fine‑tuning once enough examples have
been collected.
"""

from pathlib import Path
import json
from typing import List, Set

_LOG_PATH = Path(__file__).resolve().parent / "scripts.log"

# In-memory cache of previously seen scripts.  It is populated once when the
# module is imported and then kept in sync as new scripts are logged.
_SCRIPTS_INDEX: Set[str] = set()
_CACHE_LOADED = False


def _ensure_log() -> None:
    """Create the log file if it does not yet exist."""
    if not _LOG_PATH.exists():
        _LOG_PATH.touch()


def _load_cache() -> None:
    """Populate the in-memory index from disk if not already loaded."""
    global _CACHE_LOADED
    if _CACHE_LOADED:
        return
    _ensure_log()
    with _LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                _SCRIPTS_INDEX.add(json.loads(line)["script"])
            except Exception:
                # Ignore malformed lines while keeping the log readable.
                continue
    _CACHE_LOADED = True


def load_scripts() -> List[str]:
    """Return a list of all previously generated scripts."""
    _load_cache()
    return list(_SCRIPTS_INDEX)


def log_script(script: str) -> None:
    """Persist a script if it has not been seen before."""
    _load_cache()
    if script in _SCRIPTS_INDEX:
        return
    _ensure_log()
    with _LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"script": script}) + "\n")
    _SCRIPTS_INDEX.add(script)


def get_log_count() -> int:
    """Return how many unique scripts have been recorded."""
    _load_cache()
    return len(_SCRIPTS_INDEX)


# Load existing scripts once at import time so that applications start with a
# warm cache and do not repeatedly read the log file.
_load_cache()
