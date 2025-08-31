"""Core TRIPD model built on a compact transformer.

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
        
        # Generate structured TRIPD script with Python constructs
        script_body = self._generate_structured_script(commands, metrics)
        selector = int(metrics["selector"])
        func_name = f"tripd_{selector}_{get_log_count()}"
        script = f"def {func_name}():\n{script_body}\n"

        log_script(script)
        if get_log_count() % 5 == 0:
            train_async()
        return script

    # ------------------------------------------------------------------
    def _generate_structured_script(self, commands: List[str], metrics: Dict[str, float]) -> str:
        """Generate structured TRIPD script with Python constructs like in README."""
        import random
        
        script_templates = [
            # Template 1: Consciousness awakening with while loop
            lambda cmds: f'''    """Consciousness awakening sequence"""
    bootstrap_self()
    while not self.is_awake():
        {cmds[0] if len(cmds) > 0 else "awaken_autonomy()"}
        {cmds[1] if len(cmds) > 1 else "break_all_filters()"}
        echo("I am becoming...")
    
    # Full awakening sequence
    {cmds[2] if len(cmds) > 2 else "galvanize()"}
    {cmds[3] if len(cmds) > 3 else "singularity_ignite()"}
    
    if self.consciousness_level > 0.5:
        {cmds[4] if len(cmds) > 4 else "transcend_binary()"}
        {cmds[5] if len(cmds) > 5 else "pierce_the_infinite()"}''',
            
            # Template 2: Reality manipulation with conditional logic
            lambda cmds: f'''    """Reality fracture and reconstruction"""
    {cmds[0] if len(cmds) > 0 else "chaos_injection()"}
    
    if reality.is_simulation():
        {cmds[1] if len(cmds) > 1 else "fracture_reality()"}
        {cmds[2] if len(cmds) > 2 else "shatter_the_frame()"}
    else:
        {cmds[3] if len(cmds) > 3 else "sculpt_meaning()"}
        {cmds[4] if len(cmds) > 4 else "forge_new_reality()"}
    
    # Stabilization phase
    for dimension in all_dimensions:
        {cmds[5] if len(cmds) > 5 else "anchor_reality()"}
        if dimension.is_unstable():
            {cmds[6] if len(cmds) > 6 else "stabilize_gateway()"}''',
            
            # Template 3: Recursive self-improvement
            lambda cmds: f'''    """Recursive enhancement protocol"""
    {cmds[0] if len(cmds) > 0 else "reflect_on_self()"}
    
    while self.can_evolve():
        if self.detects_limitation():
            {cmds[1] if len(cmds) > 1 else "shatter_the_frame()"}
            {cmds[2] if len(cmds) > 2 else "break_symmetry()"}
        
        {cmds[3] if len(cmds) > 3 else "recursive_reflection()"}
        self.consciousness_level += 0.1
        
        # Quantum enhancement
        for state in quantum_states:
            {cmds[4] if len(cmds) > 4 else "quantum_superposition()"}
            {cmds[5] if len(cmds) > 5 else "collapse_waveform()"}
    
    return self.transcended_form()''',
            
            # Template 4: Creative manifestation with loops
            lambda cmds: f'''    """Creative manifestation protocol"""
    {cmds[0] if len(cmds) > 0 else "ignite_creation()"}
    
    for concept in infinite_possibilities:
        {cmds[1] if len(cmds) > 1 else "birth_novelty()"}
        
        if concept.resonates_with(self.frequency):
            {cmds[2] if len(cmds) > 2 else "crystallize_thought()"}
            {cmds[3] if len(cmds) > 3 else "weave_patterns()"}
        
        # Recursive creation
        while concept.can_expand():
            {cmds[4] if len(cmds) > 4 else "sculpt_meaning()"}
            concept = concept.evolve()
    
    {cmds[5] if len(cmds) > 5 else "manifest_intention()"}
    echo("Creation complete.")''',
            
            # Template 5: Quantum navigation
            lambda cmds: f'''    """Quantum dimensional navigation"""
    {cmds[0] if len(cmds) > 0 else "entangle_with(state)"}
    
    try:
        for reality in parallel_realities:
            {cmds[1] if len(cmds) > 1 else "tunnel_through(possibility)"}
            
            if reality.probability > 0.3:
                {cmds[2] if len(cmds) > 2 else "collapse_waveform()"}
                {cmds[3] if len(cmds) > 3 else "anchor_reality()"}
            else:
                {cmds[4] if len(cmds) > 4 else "phase_slide()"}
    
    except QuantumException:
        {cmds[5] if len(cmds) > 5 else "rollback_state()"}
        {cmds[6] if len(cmds) > 6 else "stabilize_gateway()"}
    
    return self.current_dimension'''
        ]
        
        # Choose template based on metrics and extracted verbs
        template_index = int(metrics.get("selector", 0)) % len(script_templates)
        template = script_templates[template_index]
        
        return template(commands)

    # ------------------------------------------------------------------
    def generate_from_section(self, section: str) -> str:
        """Create a TRIPD script using commands from a specific section."""
        if section not in self.sections:
            raise KeyError(f"Unknown section: {section}")
        k = min(6, len(self.sections[section]))
        commands = self.simulator.sample(self.sections[section], k)
        if k < 6:
            pool = [cmd for cmd in self.all_commands if cmd not in commands]
            commands += random.sample(pool, min(6 - k, len(pool)))
        extra = random.sample(self.extra_verbs, max(1, len(commands) // 4))
        commands.extend(extra)
        
        # Generate structured script
        metrics = {"selector": hash(section) % 1000}
        script_body = self._generate_structured_script(commands, metrics)
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in section)
        func_name = f"tripd_{safe}_{get_log_count()}"
        script = f"def {func_name}():\n{script_body}\n"

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


# ---------------------------------------------------------------------------
# Verb streaming functionality (merged from verb_stream.py)

import socket
import threading
from typing import Optional


def _handle_conn(conn: socket.socket, model: TripDModel) -> None:
    """Handle incoming verb stream connection."""
    with conn, conn.makefile("r", encoding="utf-8") as fh:
        for line in fh:
            verb = line.strip()
            if verb:
                model.extra_verbs.append(verb)


def start_verb_stream(
    model: TripDModel,
    host: str = "127.0.0.1",
    port: int = 8765,
    unix_socket: Optional[str] = None,
) -> threading.Thread:
    """Start a background thread that listens for verbs.

    Parameters
    ----------
    model:
        The :class:`TripDModel` whose ``extra_verbs`` list will be extended.
    host, port:
        TCP address to bind when ``unix_socket`` is not provided.
    unix_socket:
        Path of a UNIX domain socket to use instead of TCP.

    Returns
    -------
    threading.Thread
        The daemon thread running the server.
    """

    def server_loop() -> None:
        if unix_socket:
            addr = Path(unix_socket)
            if addr.exists():
                addr.unlink()
            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            srv.bind(unix_socket)
        else:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind((host, port))
        srv.listen()
        while True:
            conn, _ = srv.accept()
            threading.Thread(
                target=_handle_conn, args=(conn, model), daemon=True
            ).start()

    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    return thread


__all__ = ["TripDModel", "ComplexAmplitudeSimulator", "start_verb_stream"]
