"""
SMT - Smart Melody Tokenizer
============================

A modern, efficient alternative to REMI tokenization for melody generation.

Key Features:
- Compound tokens (note+velocity+duration in one token)
- Musical pattern recognition
- Intuitive control parameters
- 5x faster than REMI due to shorter sequences
- Human-readable token format

Usage:
    from smt import SmartMelodyTokenizer

    tokenizer = SmartMelodyTokenizer()
    tokens = tokenizer.encode_midi_file("melody.mid")
    generated_notes = tokenizer.decode_tokens(tokens)
"""

from .core.tokenizer import SmartMelodyTokenizer
from .core.vocabulary import SMTVocabulary
from .patterns.detector import PatternDetector
from .utils.midi_utils import MIDIProcessor

__version__ = "1.0.0"
__author__ = "SMT Contributors"
__license__ = "MIT"

__all__ = [
    "SmartMelodyTokenizer",
    "SMTVocabulary",
    "PatternDetector",
    "MIDIProcessor"
]