"""
SMT Vocabulary Builder
=====================

Creates a comprehensive vocabulary for melody tokenization with:
- Special tokens for structure
- Compound note tokens
- Musical pattern tokens
- Rest tokens
- Control tokens
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path


class SMTVocabulary:
    """Smart Melody Tokenizer Vocabulary Builder."""

    def __init__(self, config: Dict = None):
        """Initialize vocabulary with configuration.

        Args:
            config: Dictionary with vocabulary configuration options
        """
        self.config = config or self._default_config()
        self.vocab = []
        self.token_to_id = {}
        self.id_to_token = {}
        self._build_vocabulary()

    def _default_config(self) -> Dict:
        """Default vocabulary configuration."""
        return {
            "pitch_range": {
                "min_octave": 3,
                "max_octave": 6,
                "include_accidentals": True
            },
            "durations": ["sixteenth", "eighth", "quarter", "half", "whole", "dotted_quarter", "dotted_half"],
            "dynamics": ["pp", "p", "mp", "mf", "f", "ff"],
            "patterns": {
                "scales": ["scale_up", "scale_down", "chromatic_up", "chromatic_down"],
                "intervals": ["step", "skip", "leap", "octave"],
                "arpeggios": ["arpeggio_major", "arpeggio_minor", "arpeggio_dim", "arpeggio_aug"],
                "rhythmic": ["syncopated", "steady", "accelerando", "ritardando"]
            },
            "structural": ["phrase_start", "phrase_end", "motif_repeat", "sequence"],
            "max_vocab_size": 2000
        }

    def _build_vocabulary(self):
        """Build complete vocabulary."""
        self.vocab = []

        # 1. Special tokens
        self._add_special_tokens()

        # 2. Structural tokens
        self._add_structural_tokens()

        # 3. Compound note tokens
        self._add_note_tokens()

        # 4. Rest tokens
        self._add_rest_tokens()

        # 5. Pattern tokens
        self._add_pattern_tokens()

        # 6. Control tokens
        self._add_control_tokens()

        # Build mappings
        self._build_mappings()

        print(f"Built SMT vocabulary with {len(self.vocab)} tokens")

    def _add_special_tokens(self):
        """Add special tokens for model control."""
        special_tokens = [
            "[PAD]",     # Padding token
            "[BOS]",     # Beginning of sequence
            "[EOS]",     # End of sequence
            "[MASK]",    # Masked token for training
            "[UNK]",     # Unknown token
            "[SEP]"      # Separator token
        ]
        self.vocab.extend(special_tokens)

    def _add_structural_tokens(self):
        """Add structural music tokens."""
        structural_tokens = [
            "BAR",           # Bar boundary
            "PHRASE_START",  # Start of musical phrase
            "PHRASE_END",    # End of musical phrase
            "SECTION_A",     # Song section markers
            "SECTION_B",
            "VERSE",
            "CHORUS",
            "BRIDGE"
        ]
        self.vocab.extend(structural_tokens)

    def _add_note_tokens(self):
        """Add compound note tokens: NOTE_{pitch}_{duration}_{dynamic}."""
        pitches = self._get_pitch_names()
        durations = self.config["durations"]
        dynamics = self.config["dynamics"]

        note_count = 0
        for pitch in pitches:
            for duration in durations:
                for dynamic in dynamics:
                    if note_count < self.config.get("max_vocab_size", 2000) - 200:  # Reserve space for other tokens
                        token = f"NOTE_{pitch}_{duration}_{dynamic}"
                        self.vocab.append(token)
                        note_count += 1

    def _add_rest_tokens(self):
        """Add rest tokens with durations."""
        durations = self.config["durations"]

        for duration in durations:
            # Handle dotted durations by replacing dots with underscores
            safe_duration = duration.replace(".", "_")
            token = f"REST_{safe_duration}"
            self.vocab.append(token)

    def _add_pattern_tokens(self):
        """Add musical pattern tokens."""
        patterns = self.config.get("patterns", {})

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                token = f"PATTERN_{pattern.upper()}"
                self.vocab.append(token)

    def _add_control_tokens(self):
        """Add control and meta tokens."""
        control_tokens = [
            # Tempo markings
            "TEMPO_SLOW", "TEMPO_MEDIUM", "TEMPO_FAST", "TEMPO_VERY_FAST",

            # Key signatures (common keys)
            "KEY_C_MAJOR", "KEY_G_MAJOR", "KEY_D_MAJOR", "KEY_A_MAJOR",
            "KEY_F_MAJOR", "KEY_BB_MAJOR", "KEY_A_MINOR", "KEY_E_MINOR",

            # Time signatures
            "TIME_4_4", "TIME_3_4", "TIME_2_4", "TIME_6_8",

            # Style hints
            "STYLE_LEGATO", "STYLE_STACCATO", "STYLE_MARCATO",

            # Articulation
            "ACCENT", "TENUTO", "SLUR_START", "SLUR_END"
        ]
        self.vocab.extend(control_tokens)

    def _get_pitch_names(self) -> List[str]:
        """Generate pitch names based on configuration."""
        pitches = []
        note_names = ["C", "D", "E", "F", "G", "A", "B"]

        if self.config["pitch_range"].get("include_accidentals", True):
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

        for octave in range(
            self.config["pitch_range"]["min_octave"],
            self.config["pitch_range"]["max_octave"] + 1
        ):
            for note in note_names:
                pitches.append(f"{note}{octave}")

        return pitches

    def _build_mappings(self):
        """Build token-to-ID and ID-to-token mappings."""
        self.token_to_id = {token: idx for idx, token in enumerate(self.vocab)}
        self.id_to_token = {idx: token for token, idx in self.token_to_id.items()}

    def encode_token(self, token: str) -> int:
        """Convert token to ID."""
        return self.token_to_id.get(token, self.token_to_id["[UNK]"])

    def decode_token(self, token_id: int) -> str:
        """Convert ID to token."""
        return self.id_to_token.get(token_id, "[UNK]")

    def encode_tokens(self, tokens: List[str]) -> List[int]:
        """Convert list of tokens to IDs."""
        return [self.encode_token(token) for token in tokens]

    def decode_tokens(self, token_ids: List[int]) -> List[str]:
        """Convert list of IDs to tokens."""
        return [self.decode_token(token_id) for token_id in token_ids]

    def save(self, filepath: str):
        """Save vocabulary to file."""
        vocab_data = {
            "vocab": self.vocab,
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "config": self.config,
            "size": len(self.vocab)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, indent=2, ensure_ascii=False)

        print(f"Vocabulary saved to {filepath}")

    def load(self, filepath: str):
        """Load vocabulary from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)

        self.vocab = vocab_data["vocab"]
        self.token_to_id = vocab_data["token_to_id"]
        self.id_to_token = {int(k): v for k, v in vocab_data["id_to_token"].items()}
        self.config = vocab_data["config"]

        print(f"Vocabulary loaded from {filepath} ({len(self.vocab)} tokens)")

    @property
    def size(self) -> int:
        """Get vocabulary size."""
        return len(self.vocab)

    def get_special_tokens(self) -> Dict[str, int]:
        """Get special token mappings."""
        special_tokens = {}
        for token in ["[PAD]", "[BOS]", "[EOS]", "[MASK]", "[UNK]", "[SEP]"]:
            if token in self.token_to_id:
                special_tokens[token] = self.token_to_id[token]
        return special_tokens

    def print_sample_tokens(self, n: int = 20):
        """Print sample tokens for inspection."""
        print(f"\nSample tokens from SMT vocabulary ({self.size} total):")
        print("-" * 50)

        # Show special tokens
        print("Special tokens:")
        for i, token in enumerate(self.vocab[:6]):
            print(f"  {i:3d}: {token}")

        print("\nStructural tokens:")
        structural_start = 6
        for i in range(structural_start, min(structural_start + 8, len(self.vocab))):
            print(f"  {i:3d}: {self.vocab[i]}")

        print("\nNote tokens (sample):")
        note_tokens = [t for t in self.vocab if t.startswith("NOTE_")]
        for i, token in enumerate(note_tokens[:5]):
            idx = self.token_to_id[token]
            print(f"  {idx:3d}: {token}")

        print("\nPattern tokens:")
        pattern_tokens = [t for t in self.vocab if t.startswith("PATTERN_")]
        for i, token in enumerate(pattern_tokens[:5]):
            idx = self.token_to_id[token]
            print(f"  {idx:3d}: {token}")


if __name__ == "__main__":
    # Test vocabulary creation
    vocab = SMTVocabulary()
    vocab.print_sample_tokens()
    vocab.save("smt_vocabulary.json")