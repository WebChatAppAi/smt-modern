"""
Integration tests for the complete SMT pipeline.
"""

import unittest
import os
import tempfile
from pathlib import Path

from smt import SmartMelodyTokenizer
from smt.patterns.detector import PatternDetector
from smt.utils.midi_utils import SMTNote


class TestSMTIntegration(unittest.TestCase):
    """Integration tests for the complete SMT workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.tokenizer = SmartMelodyTokenizer()
        self.pattern_detector = PatternDetector()

    def test_complete_pipeline_with_real_melody(self):
        """Test complete pipeline with a realistic melody."""
        # Create "Twinkle Twinkle Little Star" melody
        twinkle_notes = [
            # Twinkle twinkle
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),  # Twin-
            SMTNote(60, 1.0, 2.0, 80, "C4", "quarter", "mf"),  # kle
            SMTNote(67, 2.0, 3.0, 85, "G4", "quarter", "f"),   # twin-
            SMTNote(67, 3.0, 4.0, 85, "G4", "quarter", "f"),   # kle

            # Little star
            SMTNote(69, 4.0, 5.0, 90, "A4", "quarter", "f"),   # lit-
            SMTNote(69, 5.0, 6.0, 90, "A4", "quarter", "f"),   # tle
            SMTNote(67, 6.0, 8.0, 85, "G4", "half", "mf"),     # star

            # How I wonder
            SMTNote(65, 8.0, 9.0, 80, "F4", "quarter", "mf"),  # How
            SMTNote(65, 9.0, 10.0, 80, "F4", "quarter", "mf"), # I
            SMTNote(64, 10.0, 11.0, 75, "E4", "quarter", "mp"), # won-
            SMTNote(64, 11.0, 12.0, 75, "E4", "quarter", "mp"), # der

            # What you are
            SMTNote(62, 12.0, 13.0, 70, "D4", "quarter", "mp"), # what
            SMTNote(62, 13.0, 14.0, 70, "D4", "quarter", "mp"), # you
            SMTNote(60, 14.0, 16.0, 80, "C4", "half", "mf"),    # are
        ]

        # Step 1: Encode melody to tokens
        encode_result = self.tokenizer.encode_notes(twinkle_notes, "Twinkle Twinkle")

        # Verify encoding
        self.assertEqual(encode_result["metadata"]["num_notes"], len(twinkle_notes))
        self.assertGreater(encode_result["metadata"]["num_tokens"], len(twinkle_notes))
        self.assertIn("[BOS]", encode_result["tokens"])
        self.assertIn("[EOS]", encode_result["tokens"])

        # Step 2: Detect patterns
        patterns = self.pattern_detector.detect_patterns(twinkle_notes)

        # Should detect some patterns (repetitions, scale segments)
        self.assertGreater(len(patterns), 0)

        # Step 3: Decode back to notes
        decoded_notes = self.tokenizer.decode_tokens(encode_result["tokens"])

        # Verify decoding
        self.assertEqual(len(decoded_notes), len(twinkle_notes))

        # Step 4: Verify musical integrity
        for original, decoded in zip(twinkle_notes, decoded_notes):
            self.assertEqual(original.pitch, decoded.pitch)
            self.assertEqual(original.pitch_name, decoded.pitch_name)

    def test_pipeline_with_different_styles(self):
        """Test pipeline with different musical styles."""
        styles = {
            "simple": self.tokenizer.generate_sample_tokens("simple"),
            "scale": self.tokenizer.generate_sample_tokens("scale"),
            "arpeggio": self.tokenizer.generate_sample_tokens("arpeggio")
        }

        for style_name, tokens in styles.items():
            with self.subTest(style=style_name):
                # Decode tokens to notes
                notes = self.tokenizer.decode_tokens(tokens)

                # Re-encode notes
                result = self.tokenizer.encode_notes(notes, f"test_{style_name}")

                # Verify roundtrip
                self.assertGreater(len(notes), 0)
                self.assertEqual(result["metadata"]["num_notes"], len(notes))

                # Detect patterns
                patterns = self.pattern_detector.detect_patterns(notes)

                # Style-specific pattern expectations
                if style_name == "scale":
                    scale_patterns = [p for p in patterns if "scale" in p.pattern_type]
                    self.assertGreater(len(scale_patterns), 0)
                elif style_name == "arpeggio":
                    arpeggio_patterns = [p for p in patterns if "arpeggio" in p.pattern_type]
                    self.assertGreater(len(arpeggio_patterns), 0)

    def test_vocabulary_and_tokenizer_consistency(self):
        """Test consistency between vocabulary and tokenizer."""
        # Generate sample tokens
        sample_tokens = self.tokenizer.generate_sample_tokens("scale")

        # Verify all tokens exist in vocabulary
        for token in sample_tokens:
            self.assertIn(token, self.tokenizer.vocabulary.token_to_id,
                         f"Token '{token}' not found in vocabulary")

        # Test encoding/decoding consistency
        token_ids = self.tokenizer.vocabulary.encode_tokens(sample_tokens)
        decoded_tokens = self.tokenizer.vocabulary.decode_tokens(token_ids)

        self.assertEqual(sample_tokens, decoded_tokens)

    def test_midi_file_io_integration(self):
        """Test MIDI file I/O integration."""
        # Create test melody
        test_melody = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(64, 1.0, 2.0, 85, "E4", "quarter", "f"),
            SMTNote(67, 2.0, 3.0, 80, "G4", "quarter", "mf"),
            SMTNote(72, 3.0, 4.0, 90, "C5", "quarter", "f"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = os.path.join(temp_dir, "test_melody.mid")

            # Save to MIDI
            self.tokenizer.midi_processor.save_midi_file(test_melody, midi_path)
            self.assertTrue(os.path.exists(midi_path))

            # Load from MIDI
            loaded_notes = self.tokenizer.midi_processor.load_midi_file(midi_path)

            # Verify loaded notes
            self.assertEqual(len(loaded_notes), len(test_melody))

            for original, loaded in zip(test_melody, loaded_notes):
                self.assertEqual(original.pitch, loaded.pitch)
                # Allow small timing differences due to MIDI quantization
                self.assertAlmostEqual(original.start_time, loaded.start_time, places=1)

    def test_error_handling_integration(self):
        """Test error handling across the pipeline."""
        # Test with empty notes
        empty_result = self.tokenizer.encode_notes([], "empty")
        self.assertEqual(empty_result["metadata"]["num_notes"], 0)

        empty_decoded = self.tokenizer.decode_tokens(empty_result["tokens"])
        self.assertEqual(len(empty_decoded), 0)

        # Test with invalid tokens
        invalid_tokens = ["[BOS]", "INVALID_TOKEN", "[EOS]"]
        decoded_notes = self.tokenizer.decode_tokens(invalid_tokens)
        self.assertIsInstance(decoded_notes, list)

        # Test pattern detection with minimal notes
        minimal_notes = [SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf")]
        patterns = self.pattern_detector.detect_patterns(minimal_notes)
        self.assertIsInstance(patterns, list)

    def test_performance_with_large_melody(self):
        """Test performance with a larger melody."""
        # Create a long melody (100 notes)
        large_melody = []
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale

        for i in range(100):
            pitch = pitches[i % len(pitches)]
            start_time = i * 0.5
            end_time = start_time + 0.5
            velocity = 70 + (i % 30)  # Varying velocity

            note = SMTNote(
                pitch=pitch,
                start_time=start_time,
                end_time=end_time,
                velocity=velocity,
                pitch_name=self.tokenizer.midi_processor._midi_to_pitch_name(pitch),
                duration_name="eighth",
                dynamic_name=self.tokenizer.midi_processor._velocity_to_dynamic(velocity)
            )
            large_melody.append(note)

        # Test encoding (should complete without timeout)
        result = self.tokenizer.encode_notes(large_melody, "large_melody")

        self.assertEqual(result["metadata"]["num_notes"], 100)
        self.assertGreater(result["metadata"]["compression_ratio"], 0)

        # Test pattern detection (should complete reasonably fast)
        patterns = self.pattern_detector.detect_patterns(large_melody)
        self.assertIsInstance(patterns, list)

        # Should detect scale patterns in this scale-based melody
        scale_patterns = [p for p in patterns if "scale" in p.pattern_type]
        self.assertGreater(len(scale_patterns), 0)

    def test_custom_configuration_integration(self):
        """Test integration with custom configurations."""
        # Custom vocabulary config
        custom_vocab_config = {
            "pitch_range": {"min_octave": 4, "max_octave": 5},
            "durations": ["quarter", "half"],
            "dynamics": ["mf", "f"]
        }

        # Custom pattern detection config
        custom_pattern_config = {
            "min_pattern_length": 2,
            "confidence_threshold": 0.5
        }

        # Create components with custom configs
        custom_tokenizer = SmartMelodyTokenizer(vocab_config=custom_vocab_config)
        custom_detector = PatternDetector(custom_pattern_config)

        # Test with restricted vocabulary
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(64, 1.0, 2.0, 90, "E4", "quarter", "f"),
        ]

        # Should work with custom configuration
        result = custom_tokenizer.encode_notes(test_notes, "custom_test")
        patterns = custom_detector.detect_patterns(test_notes)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(patterns, list)

    def test_token_format_consistency(self):
        """Test that token formats are consistent throughout pipeline."""
        # Generate various token types
        sample_tokens = self.tokenizer.generate_sample_tokens("scale")

        # Check token format consistency
        for token in sample_tokens:
            if token.startswith("NOTE_"):
                # Should have format: NOTE_{pitch}_{duration}_{dynamic}
                parts = token.split("_")
                self.assertEqual(len(parts), 4, f"Invalid note token format: {token}")
                self.assertEqual(parts[0], "NOTE")

            elif token.startswith("REST_"):
                # Should have format: REST_{duration}
                parts = token.split("_")
                self.assertEqual(len(parts), 2, f"Invalid rest token format: {token}")
                self.assertEqual(parts[0], "REST")

            elif token.startswith("PATTERN_"):
                # Should have format: PATTERN_{type}
                parts = token.split("_")
                self.assertGreaterEqual(len(parts), 2, f"Invalid pattern token format: {token}")
                self.assertEqual(parts[0], "PATTERN")

    def test_end_to_end_workflow_with_midi_file(self):
        """Test end-to-end workflow if test MIDI file exists."""
        test_midi_path = Path(__file__).parent / "test_melody.mid"

        # Skip test if no test MIDI file
        if not test_midi_path.exists():
            self.skipTest("No test MIDI file available")
            return

        try:
            # Load MIDI file
            notes = self.tokenizer.midi_processor.load_midi_file(str(test_midi_path))

            if len(notes) == 0:
                self.skipTest("Test MIDI file contains no notes")
                return

            # Encode to tokens
            result = self.tokenizer.encode_midi_file(str(test_midi_path))

            # Verify encoding
            self.assertGreater(result["metadata"]["num_notes"], 0)
            self.assertIn("[BOS]", result["tokens"])
            self.assertIn("[EOS]", result["tokens"])

            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(notes)

            # Decode back
            decoded_notes = self.tokenizer.decode_tokens(result["tokens"])

            # Verify basic properties are preserved
            self.assertEqual(len(decoded_notes), result["metadata"]["num_notes"])

            # Test saving decoded result
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp_file:
                output_path = tmp_file.name

            try:
                self.tokenizer.midi_processor.save_midi_file(decoded_notes, output_path)
                self.assertTrue(os.path.exists(output_path))

                # Load the saved file to verify it's valid
                reloaded_notes = self.tokenizer.midi_processor.load_midi_file(output_path)
                self.assertEqual(len(reloaded_notes), len(decoded_notes))

            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

        except Exception as e:
            self.fail(f"End-to-end workflow failed: {e}")


if __name__ == '__main__':
    unittest.main()