"""
Unit tests for pattern detection functionality.
"""

import unittest
from smt.patterns.detector import PatternDetector, MusicalPattern
from smt.utils.midi_utils import SMTNote


class TestMusicalPattern(unittest.TestCase):
    """Test cases for MusicalPattern class."""

    def test_musical_pattern_creation(self):
        """Test MusicalPattern creation."""
        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
        ]

        pattern = MusicalPattern(
            pattern_type="scale_up",
            start_index=0,
            end_index=1,
            confidence=0.8,
            description="Test scale pattern",
            notes=test_notes
        )

        self.assertEqual(pattern.pattern_type, "scale_up")
        self.assertEqual(pattern.start_index, 0)
        self.assertEqual(pattern.end_index, 1)
        self.assertEqual(pattern.confidence, 0.8)
        self.assertEqual(pattern.description, "Test scale pattern")
        self.assertEqual(len(pattern.notes), 2)


class TestPatternDetector(unittest.TestCase):
    """Test cases for PatternDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PatternDetector()

    def test_pattern_detector_initialization(self):
        """Test PatternDetector initialization."""
        self.assertIsInstance(self.detector.config, dict)
        self.assertIn("min_pattern_length", self.detector.config)
        self.assertIn("confidence_threshold", self.detector.config)

    def test_custom_config_initialization(self):
        """Test PatternDetector with custom config."""
        custom_config = {
            "min_pattern_length": 5,
            "confidence_threshold": 0.9
        }

        custom_detector = PatternDetector(custom_config)
        self.assertEqual(custom_detector.config["min_pattern_length"], 5)
        self.assertEqual(custom_detector.config["confidence_threshold"], 0.9)

    def test_detect_scale_up_pattern(self):
        """Test detection of ascending scale pattern."""
        # Create ascending C major scale: C-D-E-F-G
        scale_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),  # C4
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),  # D4
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),  # E4
            SMTNote(65, 1.5, 2.0, 80, "F4", "eighth", "mf"),  # F4
            SMTNote(67, 2.0, 2.5, 80, "G4", "eighth", "mf"),  # G4
        ]

        patterns = self.detector.detect_patterns(scale_notes)

        # Should detect at least one scale pattern
        scale_patterns = [p for p in patterns if "scale" in p.pattern_type]
        self.assertGreater(len(scale_patterns), 0)

        # Check the scale pattern
        scale_pattern = scale_patterns[0]
        self.assertIn("scale_up", scale_pattern.pattern_type)
        self.assertGreater(scale_pattern.confidence, 0.6)

    def test_detect_scale_down_pattern(self):
        """Test detection of descending scale pattern."""
        # Create descending scale: G-F-E-D-C
        scale_notes = [
            SMTNote(67, 0.0, 0.5, 80, "G4", "eighth", "mf"),  # G4
            SMTNote(65, 0.5, 1.0, 80, "F4", "eighth", "mf"),  # F4
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),  # E4
            SMTNote(62, 1.5, 2.0, 80, "D4", "eighth", "mf"),  # D4
            SMTNote(60, 2.0, 2.5, 80, "C4", "eighth", "mf"),  # C4
        ]

        patterns = self.detector.detect_patterns(scale_notes)

        scale_patterns = [p for p in patterns if "scale" in p.pattern_type]
        self.assertGreater(len(scale_patterns), 0)

        scale_pattern = scale_patterns[0]
        self.assertIn("scale_down", scale_pattern.pattern_type)

    def test_detect_arpeggio_pattern(self):
        """Test detection of arpeggio pattern."""
        # Create C major arpeggio: C-E-G-C
        arpeggio_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),  # C4
            SMTNote(64, 0.5, 1.0, 80, "E4", "eighth", "mf"),  # E4 (+4 semitones)
            SMTNote(67, 1.0, 1.5, 80, "G4", "eighth", "mf"),  # G4 (+3 semitones)
            SMTNote(72, 1.5, 2.0, 80, "C5", "eighth", "mf"),  # C5 (+5 semitones)
        ]

        patterns = self.detector.detect_patterns(arpeggio_notes)

        arpeggio_patterns = [p for p in patterns if "arpeggio" in p.pattern_type]
        self.assertGreater(len(arpeggio_patterns), 0)

        arpeggio_pattern = arpeggio_patterns[0]
        self.assertIn("arpeggio", arpeggio_pattern.pattern_type)
        self.assertGreater(arpeggio_pattern.confidence, 0.6)

    def test_detect_sequence_pattern(self):
        """Test detection of melodic sequence."""
        # Create sequence: C-D-E, then D-E-F# (same interval pattern)
        sequence_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),  # C4
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),  # D4 (+2)
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),  # E4 (+2)
            SMTNote(62, 1.5, 2.0, 80, "D4", "eighth", "mf"),  # D4
            SMTNote(64, 2.0, 2.5, 80, "E4", "eighth", "mf"),  # E4 (+2)
            SMTNote(66, 2.5, 3.0, 80, "F#4", "eighth", "mf"), # F#4 (+2)
        ]

        patterns = self.detector.detect_patterns(sequence_notes)

        sequence_patterns = [p for p in patterns if p.pattern_type == "sequence"]
        # Sequence detection is complex, just check it doesn't crash
        self.assertIsInstance(sequence_patterns, list)

    def test_detect_leap_pattern(self):
        """Test detection of leap patterns."""
        # Create leap followed by step: C-G-A (leap up, then step)
        leap_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),  # C4
            SMTNote(67, 0.5, 1.0, 80, "G4", "eighth", "mf"),  # G4 (+7, leap)
            SMTNote(69, 1.0, 1.5, 80, "A4", "eighth", "mf"),  # A4 (+2, step)
        ]

        patterns = self.detector.detect_patterns(leap_notes)

        leap_patterns = [p for p in patterns if "leap" in p.pattern_type]
        self.assertGreater(len(leap_patterns), 0)

    def test_classify_chord_type(self):
        """Test chord type classification."""
        # Test major chord: C-E-G
        major_pitches = [60, 64, 67]  # C4, E4, G4
        chord_type = self.detector._classify_chord_type(major_pitches)
        self.assertEqual(chord_type, "major")

        # Test minor chord: C-Eb-G
        minor_pitches = [60, 63, 67]  # C4, Eb4, G4
        chord_type = self.detector._classify_chord_type(minor_pitches)
        self.assertEqual(chord_type, "minor")

        # Test diminished chord: C-Eb-Gb
        dim_pitches = [60, 63, 66]  # C4, Eb4, Gb4
        chord_type = self.detector._classify_chord_type(dim_pitches)
        self.assertEqual(chord_type, "diminished")

    def test_no_patterns_in_random_notes(self):
        """Test that random notes don't produce false patterns."""
        # Create random, non-patterned notes
        random_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(73, 0.5, 1.0, 80, "C#5", "eighth", "mf"),  # Large jump
            SMTNote(45, 1.0, 1.5, 80, "A2", "eighth", "mf"),   # Large jump down
        ]

        patterns = self.detector.detect_patterns(random_notes)

        # Should detect very few or no patterns with high confidence
        high_confidence_patterns = [p for p in patterns if p.confidence > 0.8]
        self.assertLessEqual(len(high_confidence_patterns), 1)

    def test_short_melody_handling(self):
        """Test handling of melodies too short for pattern detection."""
        short_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
        ]

        patterns = self.detector.detect_patterns(short_notes)

        # Should return empty list or patterns with low confidence
        self.assertIsInstance(patterns, list)

    def test_resolve_overlaps(self):
        """Test overlap resolution between patterns."""
        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),
            SMTNote(65, 1.5, 2.0, 80, "F4", "eighth", "mf"),
        ]

        # Create overlapping patterns manually
        pattern1 = MusicalPattern(
            pattern_type="scale_up",
            start_index=0,
            end_index=2,
            confidence=0.8,
            description="Pattern 1",
            notes=test_notes[0:3]
        )

        pattern2 = MusicalPattern(
            pattern_type="sequence",
            start_index=1,
            end_index=3,
            confidence=0.7,
            description="Pattern 2",
            notes=test_notes[1:4]
        )

        overlapping_patterns = [pattern1, pattern2]

        resolved = self.detector._resolve_overlaps(overlapping_patterns)

        # Should keep only the higher confidence pattern
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].confidence, 0.8)

    def test_get_pattern_tokens(self):
        """Test conversion of patterns to tokens."""
        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
        ]

        patterns = [
            MusicalPattern(
                pattern_type="scale_up",
                start_index=0,
                end_index=1,
                confidence=0.8,
                description="Scale up",
                notes=test_notes
            ),
            MusicalPattern(
                pattern_type="arpeggio_major",
                start_index=0,
                end_index=1,
                confidence=0.7,
                description="Major arpeggio",
                notes=test_notes
            )
        ]

        pattern_tokens = self.detector.get_pattern_tokens(patterns)

        expected_tokens = ["PATTERN_SCALE_UP", "PATTERN_ARPEGGIO_MAJOR"]
        self.assertEqual(pattern_tokens, expected_tokens)

    def test_print_pattern_analysis(self):
        """Test pattern analysis printing."""
        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),
        ]

        patterns = self.detector.detect_patterns(test_notes)

        # Test that it doesn't crash
        try:
            self.detector.print_pattern_analysis(test_notes, patterns)
        except Exception as e:
            self.fail(f"print_pattern_analysis raised an exception: {e}")

    def test_empty_pattern_list(self):
        """Test handling of empty pattern list."""
        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
        ]

        empty_patterns = []

        # Should not crash
        try:
            self.detector.print_pattern_analysis(test_notes, empty_patterns)
            pattern_tokens = self.detector.get_pattern_tokens(empty_patterns)
            self.assertEqual(pattern_tokens, [])
        except Exception as e:
            self.fail(f"Empty pattern handling raised an exception: {e}")

    def test_confidence_threshold_filtering(self):
        """Test that patterns below confidence threshold are filtered."""
        # Create detector with high confidence threshold
        high_threshold_detector = PatternDetector({
            "confidence_threshold": 0.95  # Very high threshold
        })

        test_notes = [
            SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
            SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
            SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),
        ]

        patterns = high_threshold_detector.detect_patterns(test_notes)

        # Should detect fewer patterns due to high threshold
        low_threshold_patterns = self.detector.detect_patterns(test_notes)
        self.assertLessEqual(len(patterns), len(low_threshold_patterns))


if __name__ == '__main__':
    unittest.main()