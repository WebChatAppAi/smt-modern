"""
Musical Pattern Detector
=======================

Detects common musical patterns in melodies for enhanced tokenization.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from ..utils.midi_utils import SMTNote


@dataclass
class MusicalPattern:
    """Represents a detected musical pattern."""
    pattern_type: str       # Type of pattern (scale, arpeggio, sequence, etc.)
    start_index: int        # Starting note index
    end_index: int          # Ending note index
    confidence: float       # Detection confidence (0-1)
    description: str        # Human-readable description
    notes: List[SMTNote]    # Notes involved in the pattern


class PatternDetector:
    """Detects musical patterns in melody sequences."""

    def __init__(self, config: Dict = None):
        """Initialize pattern detector.

        Args:
            config: Configuration for pattern detection
        """
        self.config = config or self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration for pattern detection."""
        return {
            "min_pattern_length": 3,
            "max_pattern_length": 8,
            "scale_tolerance": 1,      # Semitones tolerance for scale detection
            "arpeggio_tolerance": 2,   # Semitones tolerance for arpeggio detection
            "sequence_min_repetitions": 2,
            "confidence_threshold": 0.7
        }

    def detect_patterns(self, notes: List[SMTNote]) -> List[MusicalPattern]:
        """Detect all patterns in a melody.

        Args:
            notes: List of SMTNote objects

        Returns:
            List of detected patterns
        """
        if len(notes) < self.config.get("min_pattern_length", 3):
            return []

        patterns = []

        # Detect different types of patterns
        patterns.extend(self._detect_scales(notes))
        patterns.extend(self._detect_arpeggios(notes))
        patterns.extend(self._detect_sequences(notes))
        patterns.extend(self._detect_intervals(notes))

        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= self.config.get("confidence_threshold", 0.7)]

        # Remove overlapping patterns (keep highest confidence)
        patterns = self._resolve_overlaps(patterns)

        return patterns

    def _detect_scales(self, notes: List[SMTNote]) -> List[MusicalPattern]:
        """Detect scale passages."""
        patterns = []
        min_length = self.config.get("min_pattern_length", 3)
        max_length = min(self.config.get("max_pattern_length", 8), len(notes))

        for start in range(len(notes) - min_length + 1):
            for length in range(min_length, max_length + 1):
                if start + length > len(notes):
                    break

                segment = notes[start:start + length]
                pattern = self._analyze_scale_pattern(segment, start)

                if pattern and pattern.confidence >= 0.6:
                    patterns.append(pattern)

        return patterns

    def _analyze_scale_pattern(self, segment: List[SMTNote], start_idx: int) -> Optional[MusicalPattern]:
        """Analyze if a segment is a scale pattern."""
        if len(segment) < 3:
            return None

        pitches = [note.pitch for note in segment]
        intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]

        # Check for stepwise motion (1-2 semitones)
        stepwise_count = sum(1 for interval in intervals if abs(interval) <= 2)
        stepwise_ratio = stepwise_count / len(intervals)

        if stepwise_ratio >= 0.8:  # 80% stepwise motion
            # Determine direction
            direction = "up" if np.mean(intervals) > 0 else "down"
            pattern_type = f"scale_{direction}"

            confidence = stepwise_ratio * 0.8 + (0.2 if len(segment) >= 5 else 0)

            return MusicalPattern(
                pattern_type=pattern_type,
                start_index=start_idx,
                end_index=start_idx + len(segment) - 1,
                confidence=confidence,
                description=f"Scale passage ({direction}) with {len(segment)} notes",
                notes=segment
            )

        return None

    def _detect_arpeggios(self, notes: List[SMTNote]) -> List[MusicalPattern]:
        """Detect arpeggio patterns."""
        patterns = []
        min_length = max(3, self.config.get("min_pattern_length", 3))
        max_length = min(self.config.get("max_pattern_length", 8), len(notes))

        for start in range(len(notes) - min_length + 1):
            for length in range(min_length, max_length + 1):
                if start + length > len(notes):
                    break

                segment = notes[start:start + length]
                pattern = self._analyze_arpeggio_pattern(segment, start)

                if pattern and pattern.confidence >= 0.6:
                    patterns.append(pattern)

        return patterns

    def _analyze_arpeggio_pattern(self, segment: List[SMTNote], start_idx: int) -> Optional[MusicalPattern]:
        """Analyze if a segment is an arpeggio pattern."""
        if len(segment) < 3:
            return None

        pitches = [note.pitch for note in segment]
        intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]

        # Check for third and fourth intervals (3-5 semitones)
        chord_intervals = sum(1 for interval in intervals if 3 <= abs(interval) <= 5)
        chord_ratio = chord_intervals / len(intervals)

        if chord_ratio >= 0.6:  # 60% chord intervals
            # Determine chord quality based on intervals
            chord_type = self._classify_chord_type(pitches)
            direction = "up" if np.mean(intervals) > 0 else "down"

            confidence = chord_ratio * 0.7 + (0.3 if len(segment) >= 4 else 0)

            return MusicalPattern(
                pattern_type=f"arpeggio_{chord_type}",
                start_index=start_idx,
                end_index=start_idx + len(segment) - 1,
                confidence=confidence,
                description=f"Arpeggio ({chord_type}, {direction}) with {len(segment)} notes",
                notes=segment
            )

        return None

    def _classify_chord_type(self, pitches: List[int]) -> str:
        """Classify chord type based on pitch intervals."""
        if len(pitches) < 3:
            return "unknown"

        # Normalize to root position
        normalized = [(p - pitches[0]) % 12 for p in pitches]
        normalized.sort()

        # Common chord patterns
        if {0, 4, 7}.issubset(set(normalized)):
            return "major"
        elif {0, 3, 7}.issubset(set(normalized)):
            return "minor"
        elif {0, 3, 6}.issubset(set(normalized)):
            return "diminished"
        elif {0, 4, 8}.issubset(set(normalized)):
            return "augmented"
        else:
            return "unknown"

    def _detect_sequences(self, notes: List[SMTNote]) -> List[MusicalPattern]:
        """Detect melodic sequences (repeated patterns at different pitch levels)."""
        patterns = []
        min_pattern_size = 2
        max_pattern_size = 4

        for pattern_size in range(min_pattern_size, max_pattern_size + 1):
            for start in range(len(notes) - pattern_size * 2):
                # Check if pattern repeats
                pattern = self._find_sequence_pattern(notes, start, pattern_size)
                if pattern:
                    patterns.append(pattern)

        return patterns

    def _find_sequence_pattern(self, notes: List[SMTNote], start: int, pattern_size: int) -> Optional[MusicalPattern]:
        """Find sequence pattern starting at given position."""
        if start + pattern_size * 2 > len(notes):
            return None

        # Extract first pattern
        pattern1 = notes[start:start + pattern_size]
        intervals1 = [pattern1[i+1].pitch - pattern1[i].pitch for i in range(len(pattern1)-1)]

        repetitions = 1
        current_pos = start + pattern_size

        # Look for repetitions
        while current_pos + pattern_size <= len(notes):
            pattern_candidate = notes[current_pos:current_pos + pattern_size]
            intervals_candidate = [pattern_candidate[i+1].pitch - pattern_candidate[i].pitch
                                 for i in range(len(pattern_candidate)-1)]

            # Check if intervals match (allowing for transposition)
            if intervals1 == intervals_candidate:
                repetitions += 1
                current_pos += pattern_size
            else:
                break

        if repetitions >= self.config.get("sequence_min_repetitions", 2):
            end_idx = start + (repetitions * pattern_size) - 1
            confidence = min(0.9, 0.5 + (repetitions - 2) * 0.15)

            return MusicalPattern(
                pattern_type="sequence",
                start_index=start,
                end_index=end_idx,
                confidence=confidence,
                description=f"Melodic sequence repeated {repetitions} times",
                notes=notes[start:end_idx + 1]
            )

        return None

    def _detect_intervals(self, notes: List[SMTNote]) -> List[MusicalPattern]:
        """Detect characteristic interval patterns."""
        patterns = []

        if len(notes) < 3:
            return patterns

        # Look for leap patterns (intervals > 4 semitones)
        for i in range(len(notes) - 2):
            interval1 = abs(notes[i+1].pitch - notes[i].pitch)
            interval2 = abs(notes[i+2].pitch - notes[i+1].pitch)

            if interval1 > 4 and interval2 <= 2:  # Leap followed by step
                direction = "up" if notes[i+1].pitch > notes[i].pitch else "down"
                pattern = MusicalPattern(
                    pattern_type=f"leap_{direction}",
                    start_index=i,
                    end_index=i + 2,
                    confidence=0.7,
                    description=f"Leap {direction} followed by step",
                    notes=notes[i:i+3]
                )
                patterns.append(pattern)

        return patterns

    def _resolve_overlaps(self, patterns: List[MusicalPattern]) -> List[MusicalPattern]:
        """Resolve overlapping patterns by keeping highest confidence."""
        if not patterns:
            return patterns

        # Sort by confidence (highest first)
        patterns.sort(key=lambda x: x.confidence, reverse=True)

        resolved = []
        used_indices = set()

        for pattern in patterns:
            # Check if this pattern overlaps with already selected patterns
            pattern_indices = set(range(pattern.start_index, pattern.end_index + 1))

            if not pattern_indices.intersection(used_indices):
                resolved.append(pattern)
                used_indices.update(pattern_indices)

        return resolved

    def get_pattern_tokens(self, patterns: List[MusicalPattern]) -> List[str]:
        """Convert detected patterns to SMT pattern tokens.

        Args:
            patterns: List of detected patterns

        Returns:
            List of pattern token strings
        """
        tokens = []

        for pattern in patterns:
            token = f"PATTERN_{pattern.pattern_type.upper()}"
            tokens.append(token)

        return tokens

    def print_pattern_analysis(self, notes: List[SMTNote], patterns: List[MusicalPattern]):
        """Print human-readable pattern analysis."""
        print(f"\\nPattern Analysis for melody with {len(notes)} notes:")
        print(f"Detected {len(patterns)} patterns:")

        if not patterns:
            print("  No significant patterns detected.")
            return

        for i, pattern in enumerate(patterns, 1):
            print(f"\\n  Pattern {i}: {pattern.description}")
            print(f"    Type: {pattern.pattern_type}")
            print(f"    Position: notes {pattern.start_index + 1}-{pattern.end_index + 1}")
            print(f"    Confidence: {pattern.confidence:.2f}")
            print(f"    Notes: {' -> '.join([note.pitch_name for note in pattern.notes])}")


if __name__ == "__main__":
    # Test pattern detection
    from ..utils.midi_utils import SMTNote, MIDIProcessor

    # Create test melody with patterns
    processor = MIDIProcessor()

    # Scale pattern: C-D-E-F-G
    scale_notes = [
        SMTNote(60, 0.0, 0.5, 80, "C4", "eighth", "mf"),
        SMTNote(62, 0.5, 1.0, 80, "D4", "eighth", "mf"),
        SMTNote(64, 1.0, 1.5, 80, "E4", "eighth", "mf"),
        SMTNote(65, 1.5, 2.0, 80, "F4", "eighth", "mf"),
        SMTNote(67, 2.0, 2.5, 80, "G4", "eighth", "mf"),
    ]

    # Arpeggio pattern: C-E-G-C
    arpeggio_notes = [
        SMTNote(60, 3.0, 3.5, 80, "C4", "eighth", "mf"),
        SMTNote(64, 3.5, 4.0, 80, "E4", "eighth", "mf"),
        SMTNote(67, 4.0, 4.5, 80, "G4", "eighth", "mf"),
        SMTNote(72, 4.5, 5.0, 80, "C5", "eighth", "mf"),
    ]

    test_melody = scale_notes + arpeggio_notes

    # Detect patterns
    detector = PatternDetector()
    patterns = detector.detect_patterns(test_melody)

    detector.print_pattern_analysis(test_melody, patterns)

    # Show pattern tokens
    pattern_tokens = detector.get_pattern_tokens(patterns)
    print(f"\\nPattern tokens: {pattern_tokens}")