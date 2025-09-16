"""
MIDI Processing Utilities
========================

Handles MIDI file I/O, note extraction, quantization, and conversion
between MIDI format and SMT internal representation.
"""

import numpy as np
import miditoolkit
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class SMTNote:
    """Internal representation of a musical note."""
    pitch: int              # MIDI pitch (0-127)
    start_time: float      # Start time in beats
    end_time: float        # End time in beats
    velocity: int          # MIDI velocity (0-127)
    pitch_name: str = ""   # Human-readable pitch name (e.g., "C4")
    duration_name: str = ""  # Human-readable duration (e.g., "quarter")
    dynamic_name: str = ""   # Human-readable dynamic (e.g., "mf")


class MIDIProcessor:
    """Processes MIDI files for SMT tokenization."""

    def __init__(self, ticks_per_beat: int = 480):
        """Initialize MIDI processor.

        Args:
            ticks_per_beat: MIDI resolution (ticks per quarter note)
        """
        self.ticks_per_beat = ticks_per_beat
        self.quantization_grid = 16  # 16th note quantization by default

    def load_midi_file(self, filepath: str, track_index: int = 0) -> List[SMTNote]:
        """Load MIDI file and extract notes from specified track.

        Args:
            filepath: Path to MIDI file
            track_index: Which track to extract (0 for first/main track)

        Returns:
            List of SMTNote objects
        """
        try:
            midi_obj = miditoolkit.midi.parser.MidiFile(filepath)

            # Get the specified track
            if track_index >= len(midi_obj.instruments):
                print(f"Warning: Track {track_index} not found, using track 0")
                track_index = 0

            if not midi_obj.instruments:
                raise ValueError("No instruments found in MIDI file")

            instrument = midi_obj.instruments[track_index]
            notes = instrument.notes

            # Convert to SMTNote format
            smt_notes = []
            for note in notes:
                start_beats = note.start / self.ticks_per_beat
                end_beats = note.end / self.ticks_per_beat

                smt_note = SMTNote(
                    pitch=note.pitch,
                    start_time=start_beats,
                    end_time=end_beats,
                    velocity=note.velocity,
                    pitch_name=self._midi_to_pitch_name(note.pitch),
                    duration_name=self._beats_to_duration_name(end_beats - start_beats),
                    dynamic_name=self._velocity_to_dynamic(note.velocity)
                )
                smt_notes.append(smt_note)

            # Sort by start time
            smt_notes.sort(key=lambda x: x.start_time)

            print(f"Loaded {len(smt_notes)} notes from {filepath}")
            return smt_notes

        except Exception as e:
            raise Exception(f"Error loading MIDI file {filepath}: {str(e)}")

    def save_midi_file(self, notes: List[SMTNote], filepath: str, tempo: int = 120):
        """Save SMTNote list to MIDI file.

        Args:
            notes: List of SMTNote objects
            filepath: Output file path
            tempo: Tempo in BPM
        """
        # Create new MIDI object
        midi_obj = miditoolkit.midi.parser.MidiFile()
        midi_obj.ticks_per_beat = self.ticks_per_beat

        # Create instrument
        instrument = miditoolkit.midi.containers.Instrument(
            program=0,  # Piano
            is_drum=False,
            name="Generated Melody"
        )

        # Convert SMTNotes to MIDI notes
        for smt_note in notes:
            midi_note = miditoolkit.midi.containers.Note(
                velocity=smt_note.velocity,
                pitch=smt_note.pitch,
                start=int(smt_note.start_time * self.ticks_per_beat),
                end=int(smt_note.end_time * self.ticks_per_beat)
            )
            instrument.notes.append(midi_note)

        midi_obj.instruments.append(instrument)

        # Add tempo
        tempo_change = miditoolkit.midi.containers.TempoChange(tempo=tempo, time=0)
        midi_obj.tempo_changes.append(tempo_change)

        # Save file
        midi_obj.dump(filepath)
        print(f"Saved {len(notes)} notes to {filepath}")

    def quantize_notes(self, notes: List[SMTNote], grid: int = None) -> List[SMTNote]:
        """Quantize note timings to grid.

        Args:
            notes: List of SMTNote objects
            grid: Quantization grid (16 = 16th notes, 8 = 8th notes, etc.)

        Returns:
            List of quantized SMTNote objects
        """
        if grid is None:
            grid = self.quantization_grid

        quantized_notes = []
        beat_subdivision = 1.0 / (grid / 4)  # Size of one grid unit in beats

        for note in notes:
            # Quantize start time
            quantized_start = round(note.start_time / beat_subdivision) * beat_subdivision

            # Quantize duration, ensure minimum duration
            original_duration = note.end_time - note.start_time
            quantized_duration = max(
                round(original_duration / beat_subdivision) * beat_subdivision,
                beat_subdivision  # Minimum one grid unit
            )

            quantized_note = SMTNote(
                pitch=note.pitch,
                start_time=quantized_start,
                end_time=quantized_start + quantized_duration,
                velocity=note.velocity,
                pitch_name=note.pitch_name,
                duration_name=self._beats_to_duration_name(quantized_duration),
                dynamic_name=note.dynamic_name
            )
            quantized_notes.append(quantized_note)

        return quantized_notes

    def _midi_to_pitch_name(self, midi_pitch: int) -> str:
        """Convert MIDI pitch number to note name."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (midi_pitch // 12) - 1
        note = note_names[midi_pitch % 12]
        return f"{note}{octave}"

    def _pitch_name_to_midi(self, pitch_name: str) -> int:
        """Convert note name to MIDI pitch number."""
        note_map = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
                   "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

        # Handle both C#4 and Cs4 formats
        if "#" in pitch_name:
            note = pitch_name[:-1]
            octave = int(pitch_name[-1])
        elif "s" in pitch_name:  # Sharp notation like Cs4
            note = pitch_name[:-2] + "#"
            octave = int(pitch_name[-1])
        else:
            note = pitch_name[:-1]
            octave = int(pitch_name[-1])

        return (octave + 1) * 12 + note_map[note]

    def _beats_to_duration_name(self, duration_beats: float) -> str:
        """Convert duration in beats to duration name."""
        # Common durations in beats (4/4 time)
        duration_map = {
            0.25: "sixteenth",
            0.375: "dotted_sixteenth",
            0.5: "eighth",
            0.75: "dotted_eighth",
            1.0: "quarter",
            1.5: "dotted_quarter",
            2.0: "half",
            3.0: "dotted_half",
            4.0: "whole"
        }

        # Find closest duration
        closest_duration = min(duration_map.keys(),
                             key=lambda x: abs(x - duration_beats))

        # If very close to a standard duration, use it
        if abs(duration_beats - closest_duration) < 0.1:
            return duration_map[closest_duration]
        else:
            # Default to quarter note for unusual durations
            return "quarter"

    def _velocity_to_dynamic(self, velocity: int) -> str:
        """Convert MIDI velocity to musical dynamic marking."""
        if velocity < 20:
            return "pp"    # pianissimo
        elif velocity < 40:
            return "p"     # piano
        elif velocity < 60:
            return "mp"    # mezzo-piano
        elif velocity < 80:
            return "mf"    # mezzo-forte
        elif velocity < 100:
            return "f"     # forte
        else:
            return "ff"    # fortissimo

    def _dynamic_to_velocity(self, dynamic: str) -> int:
        """Convert musical dynamic to MIDI velocity."""
        dynamic_map = {
            "pp": 25,
            "p": 35,
            "mp": 50,
            "mf": 65,
            "f": 85,
            "ff": 100
        }
        return dynamic_map.get(dynamic, 65)  # Default to mf

    def get_melody_statistics(self, notes: List[SMTNote]) -> Dict:
        """Get statistics about the melody."""
        if not notes:
            return {}

        pitches = [note.pitch for note in notes]
        durations = [note.end_time - note.start_time for note in notes]
        velocities = [note.velocity for note in notes]

        stats = {
            "num_notes": len(notes),
            "pitch_range": {
                "min": min(pitches),
                "max": max(pitches),
                "span": max(pitches) - min(pitches)
            },
            "duration_info": {
                "total_beats": notes[-1].end_time if notes else 0,
                "avg_note_duration": np.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations)
            },
            "velocity_info": {
                "avg_velocity": np.mean(velocities),
                "min_velocity": min(velocities),
                "max_velocity": max(velocities)
            },
            "note_density": len(notes) / (notes[-1].end_time if notes else 1)
        }

        return stats

    def print_melody_info(self, notes: List[SMTNote], max_notes: int = 10):
        """Print human-readable melody information."""
        if not notes:
            print("No notes found")
            return

        stats = self.get_melody_statistics(notes)

        print(f"\nMelody Information:")
        print(f"  Total notes: {stats['num_notes']}")
        print(f"  Duration: {stats['duration_info']['total_beats']:.1f} beats")
        print(f"  Pitch range: {self._midi_to_pitch_name(stats['pitch_range']['min'])} - "
              f"{self._midi_to_pitch_name(stats['pitch_range']['max'])}")
        print(f"  Note density: {stats['note_density']:.1f} notes/beat")

        print(f"\nFirst {min(max_notes, len(notes))} notes:")
        for i, note in enumerate(notes[:max_notes]):
            print(f"  {i+1:2d}: {note.pitch_name:4s} {note.duration_name:12s} "
                  f"{note.dynamic_name:2s} (t={note.start_time:.2f}-{note.end_time:.2f})")

        if len(notes) > max_notes:
            print(f"  ... and {len(notes) - max_notes} more notes")


if __name__ == "__main__":
    # Test MIDI processing
    processor = MIDIProcessor()

    # Test with a simple melody
    test_notes = [
        SMTNote(60, 0.0, 1.0, 80),  # C4 quarter note
        SMTNote(62, 1.0, 2.0, 75),  # D4 quarter note
        SMTNote(64, 2.0, 3.0, 85),  # E4 quarter note
        SMTNote(65, 3.0, 4.0, 80),  # F4 quarter note
    ]

    # Add pitch names and other info
    for note in test_notes:
        note.pitch_name = processor._midi_to_pitch_name(note.pitch)
        note.duration_name = processor._beats_to_duration_name(note.end_time - note.start_time)
        note.dynamic_name = processor._velocity_to_dynamic(note.velocity)

    processor.print_melody_info(test_notes)
    processor.save_midi_file(test_notes, "test_melody.mid")