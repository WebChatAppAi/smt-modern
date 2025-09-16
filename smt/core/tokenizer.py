"""
Smart Melody Tokenizer
======================

Main tokenizer class that converts between MIDI files and SMT tokens.
Provides intuitive, compound tokens for efficient melody generation.
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path

from .vocabulary import SMTVocabulary
from ..utils.midi_utils import MIDIProcessor, SMTNote


class SmartMelodyTokenizer:
    """Main tokenizer class for SMT melody generation."""

    def __init__(self, vocab_config: Dict = None, midi_config: Dict = None):
        """Initialize the Smart Melody Tokenizer.

        Args:
            vocab_config: Configuration for vocabulary building
            midi_config: Configuration for MIDI processing
        """
        # Initialize components
        self.vocabulary = SMTVocabulary(vocab_config)
        self.midi_processor = MIDIProcessor()

        # Configuration
        self.midi_config = midi_config or {
            "quantization_grid": 16,  # 16th note quantization
            "min_rest_duration": 0.25,  # Minimum rest duration in beats
            "max_bars": 32,  # Maximum melody length in bars
            "beats_per_bar": 4.0  # 4/4 time signature
        }

        # Tokenization state
        self.current_time = 0.0
        self.current_bar = 1

    def encode_midi_file(self, filepath: str, track_index: int = 0) -> Dict:
        """Encode MIDI file to SMT tokens.

        Args:
            filepath: Path to MIDI file
            track_index: Which track to use (0 for first track)

        Returns:
            Dictionary with tokens, metadata, and original notes
        """
        # Load and process MIDI
        notes = self.midi_processor.load_midi_file(filepath, track_index)
        return self.encode_notes(notes, filepath)

    def encode_notes(self, notes: List[SMTNote], source_info: str = "") -> Dict:
        """Encode SMTNote list to tokens.

        Args:
            notes: List of SMTNote objects
            source_info: Information about the source (e.g., filename)

        Returns:
            Dictionary with encoding results
        """
        if not notes:
            return {
                "tokens": ["[BOS]", "[EOS]"],
                "token_ids": [self.vocabulary.encode_token("[BOS]"),
                             self.vocabulary.encode_token("[EOS]")],
                "metadata": {"num_notes": 0, "duration": 0.0},
                "notes": []
            }

        # Quantize notes
        quantized_notes = self.midi_processor.quantize_notes(
            notes,
            self.midi_config["quantization_grid"]
        )

        # Convert to tokens
        tokens = self._notes_to_tokens(quantized_notes)

        # Encode tokens to IDs
        token_ids = self.vocabulary.encode_tokens(tokens)

        # Collect metadata
        metadata = {
            "num_notes": len(notes),
            "duration": notes[-1].end_time if notes else 0.0,
            "num_tokens": len(tokens),
            "compression_ratio": len(notes) / len(tokens) if tokens else 0,
            "source": source_info,
            "pitch_range": {
                "min": min(note.pitch for note in notes),
                "max": max(note.pitch for note in notes)
            } if notes else None
        }

        return {
            "tokens": tokens,
            "token_ids": token_ids,
            "metadata": metadata,
            "notes": quantized_notes
        }

    def decode_tokens(self, tokens: Union[List[str], List[int]],
                     output_filepath: str = None) -> List[SMTNote]:
        """Decode SMT tokens back to notes.

        Args:
            tokens: List of token strings or token IDs
            output_filepath: Optional path to save MIDI file

        Returns:
            List of SMTNote objects
        """
        # Convert token IDs to strings if needed
        if tokens and isinstance(tokens[0], int):
            token_strings = self.vocabulary.decode_tokens(tokens)
        else:
            token_strings = tokens

        # Convert tokens to notes
        notes = self._tokens_to_notes(token_strings)

        # Save MIDI file if requested
        if output_filepath and notes:
            self.midi_processor.save_midi_file(notes, output_filepath)

        return notes

    def _notes_to_tokens(self, notes: List[SMTNote]) -> List[str]:
        """Convert notes to SMT token sequence."""
        tokens = ["[BOS]"]
        current_time = 0.0
        current_bar_start = 0.0

        for i, note in enumerate(notes):
            # Add bar markers
            while note.start_time >= current_bar_start + self.midi_config["beats_per_bar"]:
                tokens.append("BAR")
                current_bar_start += self.midi_config["beats_per_bar"]

            # Add rest if there's a gap
            if note.start_time > current_time + 0.1:  # Small tolerance
                rest_duration = note.start_time - current_time
                rest_token = self._create_rest_token(rest_duration)
                tokens.append(rest_token)

            # Add note token
            note_token = self._create_note_token(note)
            tokens.append(note_token)

            # Update current time
            current_time = note.end_time

        tokens.append("[EOS]")
        return tokens

    def _tokens_to_notes(self, tokens: List[str]) -> List[SMTNote]:
        """Convert SMT tokens back to notes."""
        notes = []
        current_time = 0.0
        current_bar = 0

        for token in tokens:
            if token in ["[BOS]", "[EOS]", "[PAD]"]:
                continue

            elif token == "BAR":
                # Align to next bar
                current_bar += 1
                current_time = current_bar * self.midi_config["beats_per_bar"]

            elif token.startswith("REST_"):
                # Handle rest
                duration = self._parse_duration_from_token(token)
                current_time += duration

            elif token.startswith("NOTE_"):
                # Parse note token
                note = self._parse_note_token(token, current_time)
                if note:
                    notes.append(note)
                    current_time = note.end_time

            elif token.startswith("PATTERN_"):
                # Pattern tokens are informational, skip for decoding
                continue

        return notes

    def _create_note_token(self, note: SMTNote) -> str:
        """Create compound note token."""
        # Use the note's precomputed human-readable attributes
        pitch_name = note.pitch_name
        duration_name = note.duration_name
        dynamic_name = note.dynamic_name

        return f"NOTE_{pitch_name}_{duration_name}_{dynamic_name}"

    def _create_rest_token(self, duration_beats: float) -> str:
        """Create rest token."""
        duration_name = self.midi_processor._beats_to_duration_name(duration_beats)
        return f"REST_{duration_name}"

    def _parse_note_token(self, token: str, start_time: float) -> Optional[SMTNote]:
        """Parse note token back to SMTNote."""
        try:
            # Format: NOTE_{pitch}_{duration}_{dynamic}
            parts = token.split("_")
            if len(parts) != 4 or parts[0] != "NOTE":
                return None

            pitch_name = parts[1]
            duration_name = parts[2]
            dynamic_name = parts[3]

            # Convert back to numeric values
            pitch = self.midi_processor._pitch_name_to_midi(pitch_name)
            velocity = self.midi_processor._dynamic_to_velocity(dynamic_name)
            duration_beats = self._duration_name_to_beats(duration_name)

            note = SMTNote(
                pitch=pitch,
                start_time=start_time,
                end_time=start_time + duration_beats,
                velocity=velocity,
                pitch_name=pitch_name,
                duration_name=duration_name,
                dynamic_name=dynamic_name
            )

            return note

        except Exception as e:
            print(f"Warning: Could not parse note token '{token}': {e}")
            return None

    def _parse_duration_from_token(self, token: str) -> float:
        """Parse duration from rest token."""
        # Format: REST_{duration}
        parts = token.split("_")
        if len(parts) >= 2:
            # Join all parts after the 'REST' prefix to support dotted durations
            # e.g., REST_dotted_quarter -> duration_name = 'dotted_quarter'
            duration_name = "_".join(parts[1:])
            return self._duration_name_to_beats(duration_name)
        return 0.25  # Default to sixteenth note

    def _duration_name_to_beats(self, duration_name: str) -> float:
        """Convert duration name to beats."""
        duration_map = {
            "sixteenth": 0.25,
            "dotted_sixteenth": 0.375,
            "eighth": 0.5,
            "dotted_eighth": 0.75,
            "quarter": 1.0,
            "dotted_quarter": 1.5,
            "half": 2.0,
            "dotted_half": 3.0,
            "whole": 4.0
        }
        return duration_map.get(duration_name, 1.0)

    def generate_sample_tokens(self, style: str = "simple") -> List[str]:
        """Generate sample token sequence for testing.

        Args:
            style: Style of sample ('simple', 'scale', 'arpeggio')

        Returns:
            List of sample tokens
        """
        if style == "simple":
            return [
                "[BOS]",
                "BAR",
                "NOTE_C4_quarter_mf",
                "NOTE_D4_quarter_mf",
                "NOTE_E4_quarter_mf",
                "NOTE_F4_quarter_mf",
                "BAR",
                "NOTE_G4_half_f",
                "REST_half",
                "[EOS]"
            ]

        elif style == "scale":
            return [
                "[BOS]",
                "BAR",
                "PATTERN_SCALE_UP",
                "NOTE_C4_eighth_mp",
                "NOTE_D4_eighth_mp",
                "NOTE_E4_eighth_mp",
                "NOTE_F4_eighth_mp",
                "NOTE_G4_eighth_mf",
                "NOTE_A4_eighth_mf",
                "NOTE_B4_eighth_f",
                "NOTE_C5_quarter_f",
                "[EOS]"
            ]

        elif style == "arpeggio":
            return [
                "[BOS]",
                "BAR",
                "PATTERN_ARPEGGIO_MAJOR",
                "NOTE_C4_quarter_mf",
                "NOTE_E4_quarter_mf",
                "NOTE_G4_quarter_mf",
                "NOTE_C5_quarter_f",
                "[EOS]"
            ]

        return ["[BOS]", "[EOS]"]

    def print_tokenization_example(self, tokens: List[str]):
        """Print a nice visualization of tokenization."""
        print("\nSMT Tokenization Example:")
        print("=" * 50)

        bar_count = 0
        note_count = 0

        for i, token in enumerate(tokens):
            if token == "[BOS]":
                print(f"{i:3d}: {token:25s} ← Start of sequence")
            elif token == "[EOS]":
                print(f"{i:3d}: {token:25s} ← End of sequence")
            elif token == "BAR":
                bar_count += 1
                print(f"{i:3d}: {token:25s} ← Bar {bar_count}")
            elif token.startswith("NOTE_"):
                note_count += 1
                parts = token.split("_")
                if len(parts) >= 4:
                    pitch = parts[1]
                    duration = parts[2]
                    dynamic = parts[3]
                    print(f"{i:3d}: {token:25s} ← Note {note_count}: {pitch} {duration} {dynamic}")
                else:
                    print(f"{i:3d}: {token:25s} ← Note {note_count}")
            elif token.startswith("REST_"):
                duration = token.split("_")[1] if "_" in token else "unknown"
                print(f"{i:3d}: {token:25s} ← Rest ({duration})")
            elif token.startswith("PATTERN_"):
                pattern = token.replace("PATTERN_", "").replace("_", " ").lower()
                print(f"{i:3d}: {token:25s} ← Pattern: {pattern}")
            else:
                print(f"{i:3d}: {token:25s}")

        print(f"\nSummary: {note_count} notes, {bar_count} bars, {len(tokens)} total tokens")

    def save_config(self, filepath: str):
        """Save tokenizer configuration."""
        config = {
            "vocab_config": self.vocabulary.config,
            "midi_config": self.midi_config,
            "vocab_size": self.vocabulary.size
        }

        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Tokenizer configuration saved to {filepath}")

    def load_config(self, filepath: str):
        """Load tokenizer configuration."""
        with open(filepath, 'r') as f:
            config = json.load(f)

        self.midi_config = config.get("midi_config", self.midi_config)
        print(f"Tokenizer configuration loaded from {filepath}")


if __name__ == "__main__":
    # Test the tokenizer
    tokenizer = SmartMelodyTokenizer()

    print(f"SMT Vocabulary size: {tokenizer.vocabulary.size}")

    # Generate and show sample tokens
    sample_tokens = tokenizer.generate_sample_tokens("scale")
    tokenizer.print_tokenization_example(sample_tokens)

    # Test encoding/decoding
    notes = tokenizer.decode_tokens(sample_tokens)
    print(f"\nDecoded {len(notes)} notes from tokens")

    if notes:
        tokenizer.midi_processor.print_melody_info(notes)