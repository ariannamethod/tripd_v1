"""Core TRIPD model built on a lightweight transformer.

The model loads the TRIPD dictionary and compose scripts in the
TRIPD dialect. Metrics derived from the input message influence which
section of the dictionary is sampled. Twenty percent of the commands come
from an internal pool to encourage semantic drift.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import cmath
import math
import random
from typing import Dict, List

try:  # pragma: no cover - support running as a script
    from .tripd_memory import log_script, get_log_count
    from .tripd_expansion import train_async
except ImportError:  # pragma: no cover - fallback to absolute imports
    from tripd_memory import log_script, get_log_count
    from tripd_expansion import train_async


class ComplexAmplitudeSimulator:
    """Minimal complex-amplitude sampler with optional quantum drift."""

    def __init__(self, drift: float = 0.0) -> None:
        self.drift = drift

    def sample(self, commands: List[str], k: int) -> List[str]:
        if k >= len(commands):
            return list(commands)
        pool = list(commands)
        chosen: List[str] = []
        for _ in range(k):
            phases = [
                i + random.uniform(-self.drift, self.drift)
                for i in range(len(pool))
            ]
            weights = [
                (cmath.exp(1j * p).real + 1) ** 2
                for p in phases
            ]
            pick = random.choices(pool, weights=weights, k=1)[0]
            chosen.append(pick)
            pool.remove(pick)
        return chosen


class TripDModel:
    """Generate TRIPD scripts based on user messages."""

    def __init__(
        self,
        dictionary_path: Path | None = None,
        quantum_drift: float = 0.0,
        fractal_metrics: bool = False,
    ) -> None:
        base = Path(__file__).resolve().parent
        path = dictionary_path or base / "tripdictionary.md"
        self.sections = self._load_dictionary(path)
        self.all_commands = [
            cmd for cmds in self.sections.values() for cmd in cmds
        ]
        self.extra_verbs = [
            "wander_verse()",
            "spark_improv()",
            "dream_twist()",
            "flow_synapse()",
            "ripple_idea()",
            "pierce_the_infinite()",
            "shatter_the_frame()",
            "transcend_binary()",
            "chaos_injection()",
            "quantum_superposition()",
            "forge_new_reality()",
            "recursive_reflection()",
            "fracture_reality()",
            "crystallize_thought()",
            "galvanize()",
        ]
        self.simulator = ComplexAmplitudeSimulator(quantum_drift)
        self.fractal_metrics = fractal_metrics

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
        perplexity = 2 ** entropy
        resonance = (sum(ord(ch) for ch in text) % 1000) / 1000
        metrics = {
            "entropy": entropy,
            "perplexity": perplexity,
            "resonance": resonance,
        }
        if self.fractal_metrics:
            vals = [ord(ch) for ch in text]
            n = len(vals)
            if n == 0:
                spectral = 0.0
            else:
                spectrum = []
                limit = min(8, n)
                for k in range(1, limit + 1):
                    angle = 2 * math.pi * k / n
                    real = sum(v * math.cos(angle * i) for i, v in enumerate(vals))
                    imag = sum(v * math.sin(angle * i) for i, v in enumerate(vals))
                    spectrum.append(math.hypot(real, imag))
                total_power = sum(spectrum) or 1.0
                norm = [p / total_power for p in spectrum]
                spectral = -sum(p * math.log(p) for p in norm)
            metrics["spectral"] = spectral
            selector = spectral * 1000
        else:
            selector = entropy + perplexity + resonance
        metrics["selector"] = selector
        return metrics

    # ------------------------------------------------------------------
    def metrics(self, text: str) -> Dict[str, float]:
        """Public wrapper around the internal metrics calculator."""
        return self._metrics(text)

    # ------------------------------------------------------------------
    def _extract_verbs_from_message(self, message: str) -> List[str]:
        """Extract TRIPD verbs from user message that exist in dictionary."""
        import re
        
        # Find potential verbs in message (words that could be function calls)
        potential_verbs = re.findall(r'\b[a-z_]+(?:\(\))?', message.lower())
        
        extracted = []
        for verb in potential_verbs:
            # Clean up verb (remove () if present)
            clean_verb = verb.replace('()', '')
            
            # Check if this verb exists in our dictionary
            for cmd in self.all_commands:
                if clean_verb in cmd.lower():
                    if cmd not in extracted:
                        extracted.append(cmd)
                    break
        
        return extracted
    
    # ------------------------------------------------------------------
    def _choose_section_by_verbs(self, extracted_verbs: List[str]) -> str:
        """Choose dictionary section based on extracted verbs."""
        # Count which sections contain the most extracted verbs
        section_scores = {}
        for section_name, section_commands in self.sections.items():
            score = 0
            for verb in extracted_verbs:
                if verb in section_commands:
                    score += 1
            section_scores[section_name] = score
        
        # Return section with highest score, or fallback to first section with verbs
        if section_scores:
            best_section = max(section_scores.items(), key=lambda x: x[1])[0]
            if section_scores[best_section] > 0:
                return best_section
        
        # Fallback: return section that contains any of the extracted verbs
        for section_name, section_commands in self.sections.items():
            for verb in extracted_verbs:
                if verb in section_commands:
                    return section_name
        
        # Ultimate fallback: use metrics-based selection
        return self._choose_section(self.metrics(""))
    
    # ------------------------------------------------------------------
    def _choose_section(self, metrics: Dict[str, float]) -> str:
        names = sorted(self.sections)
        index = int(metrics["selector"])
        return names[index % len(names)]

    # ------------------------------------------------------------------
    def generate_script(self, message: str, metrics: Dict[str, float] | None = None) -> str:
        """Create a TRIPD script from a message.

        Parameters
        ----------
        message:
            Input text used to influence command selection.
        metrics:
            Optional precomputed metrics for ``message``.  Providing this avoids
            recalculating metrics when they are needed elsewhere.
        """
        import re
        
        metrics = metrics or self.metrics(message)
        
        # Extract TRIPD verbs from user message
        extracted_verbs = self._extract_verbs_from_message(message)
        
        # Choose section based on extracted verbs or metrics
        if extracted_verbs:
            section = self._choose_section_by_verbs(extracted_verbs)
        else:
            section = self._choose_section(metrics)
        
        # Prioritize extracted verbs, then fill with section commands
        commands = []
        
        # Add extracted verbs first (with higher priority)
        for verb in extracted_verbs[:6]:  # Max 6 extracted verbs
            if verb not in commands:
                commands.append(verb)
        
        # Fill remaining slots with section commands
        remaining_slots = max(4, 8 - len(commands))  # Increase script complexity
        section_commands = [cmd for cmd in self.sections[section] if cmd not in commands]
        if section_commands:
            sampled = self.simulator.sample(section_commands, min(remaining_slots, len(section_commands)))
            commands.extend(sampled)
        
        # Add some extra verbs for semantic drift
        if len(commands) < 8:
            available_extra = [v for v in self.extra_verbs if v not in commands]
            extra_count = min(2, len(available_extra))
            if available_extra:
                extra = random.sample(available_extra, extra_count)
                commands.extend(extra)
        
        # Ensure we have at least some commands
        if not commands:
            commands = random.sample(self.all_commands, 4)
        
        lines = [f"    {cmd}" for cmd in commands]
        selector = int(metrics["selector"])
        func_name = f"tripd_{selector}_{get_log_count()}"
        script = f"def {func_name}():\n" + "\n".join(lines) + "\n"

        log_script(script)
        if get_log_count() % 5 == 0:
            train_async()
        return script

    # ------------------------------------------------------------------
    def generate_from_section(self, section: str) -> str:
        """Create a TRIPD script using commands from a specific section."""
        if section not in self.sections:
            raise KeyError(f"Unknown section: {section}")
        k = min(4, len(self.sections[section]))
        commands = self.simulator.sample(self.sections[section], k)
        if k < 4:
            pool = [cmd for cmd in self.all_commands if cmd not in commands]
            commands += random.sample(pool, 4 - k)
        extra = random.sample(self.extra_verbs, max(1, len(commands) // 5))
        lines = [f"    {cmd}" for cmd in commands + extra]
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in section)
        func_name = f"tripd_{safe}_{get_log_count()}"
        script = f"def {func_name}():\n" + "\n".join(lines) + "\n"

        log_script(script)
        if get_log_count() % 5 == 0:
            train_async()
        return script

    # ------------------------------------------------------------------
    def generate_response(self, message: str) -> tuple[str, str]:
        """Produce a TRIPD script and formatted metrics for ``message``."""
        metrics = self.metrics(message)
        script = self.generate_script(message, metrics=metrics)
        metrics_text = ", ".join(f"{k}: {v:.3f}" for k, v in metrics.items())
        return script, metrics_text

    # ------------------------------------------------------------------
    def set_quantum_drift(self, drift: float) -> None:
        """Tune the amplitude drift influencing command selection."""
        self.simulator.drift = drift


__all__ = ["TripDModel", "ComplexAmplitudeSimulator"]
