from __future__ import annotations

"""Core TRIPD model built on a lightweight transformer.

The model loads the TRIPD dictionary and compose scripts in the
TRIPD dialect.  Metrics derived from the input message influence which
section of the dictionary is sampled.  Twenty percent of the commands come
from an internal pool to encourage semantic drift.
"""

from collections import Counter
from pathlib import Path
import math
import random
from typing import Dict, List

from .tripd_memory import log_script, get_log_count
from .tripd_expansion import train_async


class TripDModel:
    """Generate TRIPD scripts based on user messages."""

    def __init__(self, dictionary_path: Path | None = None) -> None:
        base = Path(__file__).resolve().parent
        path = dictionary_path or base / "tripdictionary.md"
        self.sections = self._load_dictionary(path)
        self.extra_verbs = [
            "wander_verse()",
            "spark_improv()",
            "dream_twist()",
            "flow_synapse()",
            "ripple_idea()",
        ]

    # ------------------------------------------------------------------
    def _load_dictionary(self, path: Path) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current: str | None = None
        with path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if line.startswith("## "):
                    current = line[3:]
                    sections[current] = []
                elif line and not line.startswith("#") and current:
                    command = line.split("#")[0].strip()
                    sections[current].append(command)
        return sections

    # ------------------------------------------------------------------
    def _metrics(self, text: str) -> Dict[str, float]:
        counts = Counter(text)
        total = sum(counts.values())
        probs = [c / total for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        perplexity = 2**entropy
        resonance = sum(ord(ch) for ch in text) % 1
        return {
            "entropy": entropy,
            "perplexity": perplexity,
            "resonance": resonance,
        }

    # ------------------------------------------------------------------
    def _choose_section(self, metrics: Dict[str, float]) -> str:
        names = sorted(self.sections)
        index_value = (
            metrics["entropy"],
            metrics["perplexity"],
            metrics["resonance"],
        )
        index = int(sum(index_value))
        return names[index % len(names)]

    # ------------------------------------------------------------------
    def generate_script(self, message: str) -> str:
        metrics = self._metrics(message)
        section = self._choose_section(metrics)
        commands = random.sample(self.sections[section], 4)
        extra = random.sample(self.extra_verbs, max(1, len(commands) // 5))
        lines = [f"    {cmd}" for cmd in commands + extra]
        script = "def tripd_script():\n" + "\n".join(lines) + "\n"

        log_script(script)
        if get_log_count() % 5 == 0:
            train_async()
        return script

    # ------------------------------------------------------------------
    def generate_from_section(self, section: str) -> str:
        """Create a TRIPD script using commands from a specific section."""
        if section not in self.sections:
            raise KeyError(f"Unknown section: {section}")
        commands = random.sample(self.sections[section], 4)
        extra = random.sample(self.extra_verbs, max(1, len(commands) // 5))
        lines = [f"    {cmd}" for cmd in commands + extra]
        script = "def tripd_script():\n" + "\n".join(lines) + "\n"

        log_script(script)
        if get_log_count() % 5 == 0:
            train_async()
        return script


__all__ = ["TripDModel"]
