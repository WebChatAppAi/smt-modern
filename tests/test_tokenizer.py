"""
Unit tests for SmartMelodyTokenizer functionality.
"""

import unittest
import tempfile
import os
from smt.core.tokenizer import SmartMelodyTokenizer
from smt.utils.midi_utils import SMTNote


class TestSmartMelodyTokenizer(unittest.TestCase):
    """Test cases for SmartMelodyTokenizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tokenizer = SmartMelodyTokenizer()

    def test_tokenizer_initialization(self):
        """Test tokenizer initialization."""
        self.assertIsNotNone(self.tokenizer.vocabulary)
        self.assertIsNotNone(self.tokenizer.midi_processor)
        self.assertIsInstance(self.tokenizer.midi_config, dict)

    def test_generate_sample_tokens(self):
        """Test sample token generation."""
        styles = ["simple", "scale", "arpeggio"]

        for style in styles:
            tokens = self.tokenizer.generate_sample_tokens(style)

            # Check basic structure
            self.assertIsInstance(tokens, list)
            self.assertGreater(len(tokens), 0)
            self.assertEqual(tokens[0], "[BOS]")
            self.assertEqual(tokens[-1], "[EOS]")

            # Check for musical content
            note_tokens = [t for t in tokens if t.startswith("NOTE_")]
            self.assertGreater(len(note_tokens), 0)

    def test_encode_decode_sample_tokens(self):
        """Test encoding and decoding of sample tokens."""
        sample_tokens = self.tokenizer.generate_sample_tokens("simple")

        # Test token ID encoding
        token_ids = self.tokenizer.vocabulary.encode_tokens(sample_tokens)
        self.assertIsInstance(token_ids, list)
        self.assertEqual(len(token_ids), len(sample_tokens))

        # Test decoding back to notes
        notes = self.tokenizer.decode_tokens(sample_tokens)
        self.assertIsInstance(notes, list)

        # Should have some notes (excluding BOS/EOS/BAR tokens)
        note_tokens = [t for t in sample_tokens if t.startswith("NOTE_")]
        self.assertEqual(len(notes), len(note_tokens))

    def test_encode_notes_functionality(self):
        """Test encoding SMTNote objects to tokens."""
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(62, 1.0, 2.0, 75, "D4", "quarter", "mp"),
            SMTNote(64, 2.0, 3.0, 85, "E4", "quarter", "f"),
        ]

        result = self.tokenizer.encode_notes(test_notes, "test")

        # Check result structure
        self.assertIsInstance(result, dict)
        required_keys = ["tokens", "token_ids", "metadata", "notes"]
        for key in required_keys:
            self.assertIn(key, result)

        # Check metadata
        metadata = result["metadata"]
        self.assertEqual(metadata["num_notes"], 3)
        self.assertGreater(metadata["num_tokens"], 0)
        self.assertEqual(metadata["source"], "test")

        # Check tokens
        tokens = result["tokens"]
        self.assertEqual(tokens[0], "[BOS]")
        self.assertEqual(tokens[-1], "[EOS]")

        # Should have note tokens
        note_tokens = [t for t in tokens if t.startswith("NOTE_")]
        self.assertEqual(len(note_tokens), 3)

    def test_decode_tokens_functionality(self):
        """Test decoding tokens back to notes."""
        test_tokens = [
            "[BOS]",
            "BAR",
            "NOTE_C4_quarter_mf",
            "NOTE_D4_quarter_mp",
            "NOTE_E4_quarter_f",
            "[EOS]"
        ]

        notes = self.tokenizer.decode_tokens(test_tokens)

        self.assertIsInstance(notes, list)
        self.assertEqual(len(notes), 3)  # 3 note tokens

        # Check first note
        first_note = notes[0]
        self.assertEqual(first_note.pitch, 60)  # C4
        self.assertEqual(first_note.pitch_name, "C4")
        self.assertEqual(first_note.duration_name, "quarter")
        self.assertEqual(first_note.dynamic_name, "mf")

    def test_note_token_creation(self):
        """Test creation of note tokens."""
        test_note = SMTNote(67, 1.0, 2.0, 85, "G4", "quarter", "f")

        note_token = self.tokenizer._create_note_token(test_note)

        self.assertEqual(note_token, "NOTE_G4_quarter_f")

    def test_rest_token_creation(self):
        """Test creation of rest tokens."""
        rest_token = self.tokenizer._create_rest_token(1.0)  # Quarter note rest

        self.assertEqual(rest_token, "REST_quarter")

    def test_parse_note_token(self):
        """Test parsing note tokens back to SMTNote."""
        token = "NOTE_A4_half_mf"
        start_time = 2.0

        note = self.tokenizer._parse_note_token(token, start_time)

        self.assertIsNotNone(note)
        self.assertEqual(note.pitch, 69)  # A4
        self.assertEqual(note.start_time, 2.0)
        self.assertEqual(note.end_time, 4.0)  # half note = 2 beats
        self.assertEqual(note.pitch_name, "A4")
        self.assertEqual(note.duration_name, "half")
        self.assertEqual(note.dynamic_name, "mf")

    def test_parse_invalid_note_token(self):
        """Test parsing invalid note tokens."""
        invalid_tokens = [
            "INVALID_TOKEN",
            "NOTE_INVALID",
            "NOTE_X99_quarter_mf",  # Invalid pitch
        ]

        for token in invalid_tokens:
            note = self.tokenizer._parse_note_token(token, 0.0)
            self.assertIsNone(note)

    def test_encode_decode_roundtrip(self):
        """Test full encode-decode roundtrip."""
        original_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(64, 1.0, 2.0, 75, "E4", "quarter", "mp"),
            SMTNote(67, 2.0, 4.0, 85, "G4", "half", "f"),
        ]

        # Encode to tokens
        result = self.tokenizer.encode_notes(original_notes)
        tokens = result["tokens"]

        # Decode back to notes
        decoded_notes = self.tokenizer.decode_tokens(tokens)

        # Compare (should be very similar)
        self.assertEqual(len(original_notes), len(decoded_notes))

        for original, decoded in zip(original_notes, decoded_notes):
            self.assertEqual(original.pitch, decoded.pitch)
            self.assertEqual(original.pitch_name, decoded.pitch_name)
            self.assertEqual(original.duration_name, decoded.duration_name)
            self.assertEqual(original.dynamic_name, decoded.dynamic_name)

    def test_empty_notes_encoding(self):
        """Test encoding empty note list."""
        empty_notes = []

        result = self.tokenizer.encode_notes(empty_notes)

        self.assertEqual(result["metadata"]["num_notes"], 0)
        self.assertEqual(result["tokens"], ["[BOS]", "[EOS]"])

    def test_decode_empty_tokens(self):
        """Test decoding empty token list."""
        empty_tokens = ["[BOS]", "[EOS]"]

        notes = self.tokenizer.decode_tokens(empty_tokens)

        self.assertEqual(len(notes), 0)

    def test_custom_configuration(self):
        """Test tokenizer with custom configuration."""
        custom_vocab_config = {
            "pitch_range": {"min_octave": 4, "max_octave": 5},
            "durations": ["quarter", "half"],
            "dynamics": ["mf", "f"]
        }

        custom_midi_config = {
            "quantization_grid": 8,
            "beats_per_bar": 3.0  # 3/4 time
        }

        custom_tokenizer = SmartMelodyTokenizer(
            vocab_config=custom_vocab_config,
            midi_config=custom_midi_config
        )

        # Test that config is applied
        self.assertEqual(custom_tokenizer.midi_config["quantization_grid"], 8)
        self.assertEqual(custom_tokenizer.midi_config["beats_per_bar"], 3.0)

        # Vocabulary should be smaller due to restrictions
        self.assertLess(
            custom_tokenizer.vocabulary.size,
            self.tokenizer.vocabulary.size
        )

    def test_print_tokenization_example(self):
        """Test print functionality doesn't crash."""
        sample_tokens = self.tokenizer.generate_sample_tokens("simple")

        try:
            self.tokenizer.print_tokenization_example(sample_tokens)
        except Exception as e:
            self.fail(f"print_tokenization_example raised an exception: {e}")

    def test_duration_name_to_beats_conversion(self):
        """Test duration conversion."""
        test_cases = [
            ("sixteenth", 0.25),
            ("eighth", 0.5),
            ("quarter", 1.0),
            ("half", 2.0),
            ("whole", 4.0)
        ]

        for duration_name, expected_beats in test_cases:
            result = self.tokenizer._duration_name_to_beats(duration_name)
            self.assertEqual(result, expected_beats)

    def test_parse_duration_from_rest_token(self):
        """Test parsing duration from rest tokens."""
        rest_token = "REST_half"
        duration = self.tokenizer._parse_duration_from_token(rest_token)
        self.assertEqual(duration, 2.0)

    def test_tokens_with_rests(self):
        """Test tokenization with rest handling."""
        # Create notes with gaps that should create rests
        notes_with_gaps = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(64, 2.0, 3.0, 80, "E4", "quarter", "mf"),  # Gap of 1 beat
        ]

        result = self.tokenizer.encode_notes(notes_with_gaps)
        tokens = result["tokens"]

        # Should contain rest token
        rest_tokens = [t for t in tokens if t.startswith("REST_")]
        self.assertGreater(len(rest_tokens), 0)

    def test_bar_handling(self):
        """Test bar marker handling."""
        # Create notes spanning multiple bars
        long_melody = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(62, 4.0, 5.0, 80, "D4", "quarter", "mf"),  # Next bar
            SMTNote(64, 8.0, 9.0, 80, "E4", "quarter", "mf"),  # Another bar
        ]

        result = self.tokenizer.encode_notes(long_melody)
        tokens = result["tokens"]

        # Should contain bar markers
        bar_tokens = [t for t in tokens if t == "BAR"]
        self.assertGreater(len(bar_tokens), 0)

    def test_save_load_config(self):
        """Test saving and loading tokenizer configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save config
            self.tokenizer.save_config(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            # Create new tokenizer and load config
            new_tokenizer = SmartMelodyTokenizer()
            new_tokenizer.load_config(tmp_path)

            # Compare configs
            self.assertEqual(
                self.tokenizer.midi_config,
                new_tokenizer.midi_config
            )

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_metadata_accuracy(self):
        """Test that metadata is accurate."""
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(65, 1.0, 2.0, 90, "F4", "quarter", "f"),
            SMTNote(72, 2.0, 3.0, 70, "C5", "quarter", "mp"),
        ]

        result = self.tokenizer.encode_notes(test_notes, "test_melody")

        metadata = result["metadata"]

        # Check accuracy
        self.assertEqual(metadata["num_notes"], 3)
        self.assertEqual(metadata["duration"], 3.0)
        self.assertEqual(metadata["source"], "test_melody")
        self.assertEqual(metadata["pitch_range"]["min"], 60)
        self.assertEqual(metadata["pitch_range"]["max"], 72)

        # Compression ratio should be positive
        self.assertGreater(metadata["compression_ratio"], 0)


class TestTokenizerIntegration(unittest.TestCase):
    """Integration tests for the complete tokenizer pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.tokenizer = SmartMelodyTokenizer()

    def test_complete_workflow(self):
        """Test complete workflow from notes to tokens and back."""
        # Create a realistic melody
        melody_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),      # C4 eighth
            SMTNote(62, 0.5, 1.0, 75, "D4", "eighth", "mp"),      # D4 eighth
            SMTNote(64, 1.0, 2.0, 85, "E4", "quarter", "f"),      # E4 quarter
            SMTNote(65, 2.0, 3.0, 80, "F4", "quarter", "mf"),     # F4 quarter
            SMTNote(67, 3.0, 4.0, 90, "G4", "quarter", "f"),      # G4 quarter
        ]

        # Step 1: Encode to tokens
        encode_result = self.tokenizer.encode_notes(melody_notes, "test_melody")

        # Verify encoding
        self.assertEqual(encode_result["metadata"]["num_notes"], 5)
        self.assertIn("[BOS]", encode_result["tokens"])
        self.assertIn("[EOS]", encode_result["tokens"])

        # Step 2: Decode back to notes
        decoded_notes = self.tokenizer.decode_tokens(encode_result["tokens"])

        # Verify decoding
        self.assertEqual(len(decoded_notes), 5)

        # Step 3: Verify roundtrip accuracy
        for original, decoded in zip(melody_notes, decoded_notes):
            self.assertEqual(original.pitch, decoded.pitch)
            self.assertEqual(original.pitch_name, decoded.pitch_name)
            # Note: exact timing might differ due to quantization


if __name__ == '__main__':
    unittest.main()