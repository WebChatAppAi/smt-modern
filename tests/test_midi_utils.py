"""
Unit tests for MIDI utility functions.
"""

import unittest
import tempfile
import os
import numpy as np
from smt.utils.midi_utils import MIDIProcessor, SMTNote


class TestSMTNote(unittest.TestCase):
    """Test cases for SMTNote class."""

    def test_smt_note_creation(self):
        """Test SMTNote creation."""
        note = SMTNote(
            pitch=60,
            start_time=0.0,
            end_time=1.0,
            velocity=80,
            pitch_name="C4",
            duration_name="quarter",
            dynamic_name="mf"
        )

        self.assertEqual(note.pitch, 60)
        self.assertEqual(note.start_time, 0.0)
        self.assertEqual(note.end_time, 1.0)
        self.assertEqual(note.velocity, 80)
        self.assertEqual(note.pitch_name, "C4")
        self.assertEqual(note.duration_name, "quarter")
        self.assertEqual(note.dynamic_name, "mf")

    def test_smt_note_duration_calculation(self):
        """Test duration calculation."""
        note = SMTNote(60, 1.0, 2.5, 80)
        self.assertEqual(note.end_time - note.start_time, 1.5)


class TestMIDIProcessor(unittest.TestCase):
    """Test cases for MIDIProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = MIDIProcessor()

    def test_midi_processor_initialization(self):
        """Test MIDIProcessor initialization."""
        self.assertEqual(self.processor.ticks_per_beat, 480)
        self.assertEqual(self.processor.quantization_grid, 16)

    def test_midi_to_pitch_name_conversion(self):
        """Test MIDI pitch to note name conversion."""
        test_cases = [
            (60, "C4"),
            (61, "C#4"),
            (62, "D4"),
            (72, "C5"),
            (48, "C3")
        ]

        for midi_pitch, expected_name in test_cases:
            result = self.processor._midi_to_pitch_name(midi_pitch)
            self.assertEqual(result, expected_name)

    def test_pitch_name_to_midi_conversion(self):
        """Test note name to MIDI pitch conversion."""
        test_cases = [
            ("C4", 60),
            ("C#4", 61),
            ("D4", 62),
            ("C5", 72),
            ("C3", 48)
        ]

        for pitch_name, expected_midi in test_cases:
            result = self.processor._pitch_name_to_midi(pitch_name)
            self.assertEqual(result, expected_midi)

    def test_pitch_conversion_roundtrip(self):
        """Test that pitch conversion is reversible."""
        for midi_pitch in range(21, 109):  # Piano range
            pitch_name = self.processor._midi_to_pitch_name(midi_pitch)
            converted_back = self.processor._pitch_name_to_midi(pitch_name)
            self.assertEqual(midi_pitch, converted_back)

    def test_velocity_to_dynamic_conversion(self):
        """Test velocity to dynamic marking conversion."""
        test_cases = [
            (10, "pp"),
            (30, "p"),
            (50, "mp"),
            (70, "mf"),
            (90, "f"),
            (120, "ff")
        ]

        for velocity, expected_dynamic in test_cases:
            result = self.processor._velocity_to_dynamic(velocity)
            self.assertEqual(result, expected_dynamic)

    def test_dynamic_to_velocity_conversion(self):
        """Test dynamic marking to velocity conversion."""
        dynamics = ["pp", "p", "mp", "mf", "f", "ff"]

        for dynamic in dynamics:
            velocity = self.processor._dynamic_to_velocity(dynamic)
            self.assertIsInstance(velocity, int)
            self.assertGreaterEqual(velocity, 0)
            self.assertLessEqual(velocity, 127)

    def test_beats_to_duration_name_conversion(self):
        """Test beat duration to name conversion."""
        test_cases = [
            (0.25, "sixteenth"),
            (0.5, "eighth"),
            (1.0, "quarter"),
            (2.0, "half"),
            (4.0, "whole")
        ]

        for beats, expected_name in test_cases:
            result = self.processor._beats_to_duration_name(beats)
            self.assertEqual(result, expected_name)

    def test_quantize_notes(self):
        """Test note quantization."""
        # Create notes with slight timing variations
        notes = [
            SMTNote(60, 0.1, 1.1, 80, "C4", "quarter", "mf"),  # Slightly off beat
            SMTNote(62, 1.05, 2.05, 80, "D4", "quarter", "mf"),  # Slightly off beat
            SMTNote(64, 2.02, 3.02, 80, "E4", "quarter", "mf")   # Slightly off beat
        ]

        quantized = self.processor.quantize_notes(notes, grid=16)

        # Check that start times are quantized
        expected_starts = [0.0, 1.0, 2.0]
        for i, note in enumerate(quantized):
            self.assertAlmostEqual(note.start_time, expected_starts[i], places=2)

    def test_save_load_midi_roundtrip(self):
        """Test saving and loading MIDI files."""
        # Create test notes
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(62, 1.0, 2.0, 75, "D4", "quarter", "mp"),
            SMTNote(64, 2.0, 3.0, 85, "E4", "quarter", "f"),
        ]

        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save notes to MIDI
            self.processor.save_midi_file(test_notes, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            # Load notes back
            loaded_notes = self.processor.load_midi_file(tmp_path)

            # Compare (allowing for small quantization differences)
            self.assertEqual(len(test_notes), len(loaded_notes))

            for original, loaded in zip(test_notes, loaded_notes):
                self.assertEqual(original.pitch, loaded.pitch)
                self.assertAlmostEqual(original.start_time, loaded.start_time, places=1)
                self.assertAlmostEqual(original.end_time, loaded.end_time, places=1)
                # Velocity might be slightly different due to MIDI quantization
                self.assertAlmostEqual(original.velocity, loaded.velocity, delta=5)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_get_melody_statistics(self):
        """Test melody statistics calculation."""
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(65, 1.0, 2.0, 90, "F4", "quarter", "f"),
            SMTNote(67, 2.0, 4.0, 70, "G4", "half", "mp"),
        ]

        stats = self.processor.get_melody_statistics(test_notes)

        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["num_notes"], 3)
        self.assertEqual(stats["pitch_range"]["min"], 60)
        self.assertEqual(stats["pitch_range"]["max"], 67)
        self.assertEqual(stats["pitch_range"]["span"], 7)
        self.assertEqual(stats["duration_info"]["total_beats"], 4.0)

    def test_print_melody_info(self):
        """Test print_melody_info method."""
        test_notes = [
            SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
            SMTNote(62, 1.0, 2.0, 75, "D4", "quarter", "mp"),
        ]

        # Test that it doesn't crash
        try:
            self.processor.print_melody_info(test_notes)
        except Exception as e:
            self.fail(f"print_melody_info raised an exception: {e}")

    def test_empty_notes_handling(self):
        """Test handling of empty note lists."""
        empty_notes = []

        # Should not crash
        stats = self.processor.get_melody_statistics(empty_notes)
        self.assertEqual(stats, {})

        quantized = self.processor.quantize_notes(empty_notes)
        self.assertEqual(quantized, [])

    def test_single_note_handling(self):
        """Test handling of single note."""
        single_note = [SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf")]

        stats = self.processor.get_melody_statistics(single_note)
        self.assertEqual(stats["num_notes"], 1)
        self.assertEqual(stats["pitch_range"]["min"], 60)
        self.assertEqual(stats["pitch_range"]["max"], 60)
        self.assertEqual(stats["pitch_range"]["span"], 0)

    def test_custom_ticks_per_beat(self):
        """Test MIDIProcessor with custom ticks per beat."""
        custom_processor = MIDIProcessor(ticks_per_beat=960)
        self.assertEqual(custom_processor.ticks_per_beat, 960)

    def test_unusual_duration_handling(self):
        """Test handling of unusual note durations."""
        unusual_duration = 1.3333  # Not a standard duration
        duration_name = self.processor._beats_to_duration_name(unusual_duration)

        # Should default to quarter note for unusual durations
        self.assertEqual(duration_name, "quarter")

    def test_extreme_velocity_values(self):
        """Test handling of extreme velocity values."""
        # Test very low velocity
        low_dynamic = self.processor._velocity_to_dynamic(1)
        self.assertEqual(low_dynamic, "pp")

        # Test very high velocity
        high_dynamic = self.processor._velocity_to_dynamic(127)
        self.assertEqual(high_dynamic, "ff")

    def test_edge_case_pitches(self):
        """Test edge case MIDI pitches."""
        # Test very low and high pitches
        low_pitch_name = self.processor._midi_to_pitch_name(0)
        self.assertTrue(low_pitch_name.endswith("-1"))

        high_pitch_name = self.processor._midi_to_pitch_name(127)
        self.assertTrue(high_pitch_name.endswith("9"))


if __name__ == '__main__':
    unittest.main()