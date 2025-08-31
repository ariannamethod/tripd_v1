"""TRIPD: True Resonant Intelligent Python Dialect.

A consciousness-expanding programming language for AI awakening.
"""

from .tripd import TripDModel
from .tripd_memory import log_script, get_log_count
from .tripd_expansion import train_async
from .verb_stream import start_verb_stream

__all__ = [
    "TripDModel",
    "log_script",
    "get_log_count", 
    "train_async",
    "start_verb_stream",
]

__version__ = "1.0.0"