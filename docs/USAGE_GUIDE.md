# SMT Usage Guide

Complete guide for using the Smart Melody Tokenizer in various scenarios.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Configuration](#advanced-configuration)
4. [Pattern Detection](#pattern-detection)
5. [Training Data Preparation](#training-data-preparation)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

```bash
# Clone and install
git clone https://github.com/your-org/smt-modern
cd smt-modern
pip install -e .

# Or install from PyPI (when published)
pip install smt-modern
```

### Quick Test

```python
from smt import SmartMelodyTokenizer

# Initialize tokenizer
tokenizer = SmartMelodyTokenizer()

# Generate and examine sample tokens
tokens = tokenizer.generate_sample_tokens("scale")
tokenizer.print_tokenization_example(tokens)

# Check vocabulary size
print(f"Vocabulary size: {tokenizer.vocabulary.size}")
```

---

## Basic Usage

### 1. Encoding MIDI Files

```python
from smt import SmartMelodyTokenizer

tokenizer = SmartMelodyTokenizer()

# Encode a MIDI file
result = tokenizer.encode_midi_file("path/to/melody.mid")

print(f"Original notes: {result['metadata']['num_notes']}")
print(f"Generated tokens: {result['metadata']['num_tokens']}")
print(f"Compression ratio: {result['metadata']['compression_ratio']:.2f}")

# Access the tokens
tokens = result['tokens']
token_ids = result['token_ids']
```

### 2. Decoding Tokens to MIDI

```python
# Decode tokens back to notes
notes = tokenizer.decode_tokens(tokens)

# Save as MIDI file
tokenizer.midi_processor.save_midi_file(notes, "output.mid")

# Print melody information
tokenizer.midi_processor.print_melody_info(notes)
```

### 3. Working with Notes Directly

```python
from smt.utils.midi_utils import SMTNote

# Create notes programmatically
melody = [
    SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
    SMTNote(62, 1.0, 2.0, 75, "D4", "quarter", "mp"),
    SMTNote(64, 2.0, 3.0, 85, "E4", "quarter", "f"),
]

# Encode notes
result = tokenizer.encode_notes(melody, "my_melody")
```

---

## Advanced Configuration

### Custom Vocabulary

```python
from smt import SmartMelodyTokenizer

# Jazz-specific vocabulary
jazz_config = {
    "pitch_range": {
        "min_octave": 3,
        "max_octave": 7,
        "include_accidentals": True
    },
    "durations": [
        "eighth", "quarter", "half",
        "dotted_eighth", "dotted_quarter",  # Swing rhythms
        "triplet_eighth"
    ],
    "dynamics": ["pp", "p", "mp", "mf", "f", "ff"],
    "patterns": {
        "scales": ["scale_up", "scale_down", "chromatic", "bebop"],
        "intervals": ["step", "skip", "leap", "octave", "tritone"],
        "jazz_specific": ["blue_note", "altered_chord", "walking_bass"]
    },
    "max_vocab_size": 3000
}

jazz_tokenizer = SmartMelodyTokenizer(vocab_config=jazz_config)
```

### Custom MIDI Processing

```python
# Classical music configuration
classical_config = {
    "quantization_grid": 32,  # Finer quantization for classical precision
    "min_rest_duration": 0.125,  # Thirty-second note rests
    "max_bars": 64,  # Longer pieces
    "beats_per_bar": 4.0
}

classical_tokenizer = SmartMelodyTokenizer(
    midi_config=classical_config
)
```

### Genre-Specific Configurations

```python
# Pop music
pop_config = {
    "vocab_config": {
        "pitch_range": {"min_octave": 3, "max_octave": 6},
        "durations": ["eighth", "quarter", "half"],
        "dynamics": ["mp", "mf", "f"],
        "patterns": {
            "scales": ["scale_up", "scale_down"],
            "rhythmic": ["syncopated", "steady"]
        }
    },
    "midi_config": {
        "quantization_grid": 16,
        "beats_per_bar": 4.0
    }
}

# Electronic music
electronic_config = {
    "vocab_config": {
        "durations": ["sixteenth", "eighth", "quarter"],  # Precise rhythms
        "dynamics": ["mf", "f", "ff"],  # Consistent loud dynamics
        "patterns": {
            "rhythmic": ["four_on_floor", "syncopated", "breakbeat"]
        }
    },
    "midi_config": {
        "quantization_grid": 32  # Very precise timing
    }
}
```

---

## Pattern Detection

### Basic Pattern Detection

```python
from smt.patterns.detector import PatternDetector

detector = PatternDetector()

# Load melody
notes = tokenizer.midi_processor.load_midi_file("melody.mid")

# Detect patterns
patterns = detector.detect_patterns(notes)

# Print analysis
detector.print_pattern_analysis(notes, patterns)
```

### Custom Pattern Detection

```python
# Sensitive pattern detection
sensitive_config = {
    "min_pattern_length": 2,
    "max_pattern_length": 12,
    "confidence_threshold": 0.5,  # Lower threshold
    "scale_tolerance": 2,
    "sequence_min_repetitions": 2
}

sensitive_detector = PatternDetector(sensitive_config)

# Conservative pattern detection
conservative_config = {
    "min_pattern_length": 4,
    "confidence_threshold": 0.8,  # Higher threshold
    "scale_tolerance": 1
}

conservative_detector = PatternDetector(conservative_config)
```

### Using Pattern Information

```python
patterns = detector.detect_patterns(notes)

# Filter by pattern type
scale_patterns = [p for p in patterns if "scale" in p.pattern_type]
arpeggio_patterns = [p for p in patterns if "arpeggio" in p.pattern_type]

# Get pattern tokens for training
pattern_tokens = detector.get_pattern_tokens(patterns)

# Enhance tokenization with patterns
enhanced_tokens = []
note_index = 0

for pattern in patterns:
    # Add pattern token before the pattern starts
    if pattern.start_index == note_index:
        enhanced_tokens.append(f"PATTERN_{pattern.pattern_type.upper()}")

    # Add regular note tokens
    # ... (implementation depends on specific needs)
```

---

## Training Data Preparation

### Batch Processing

```python
import glob
import json
from pathlib import Path

def prepare_training_dataset(midi_dir, output_file):
    """Prepare training dataset from MIDI files."""

    tokenizer = SmartMelodyTokenizer()
    dataset = []

    midi_files = list(Path(midi_dir).glob("*.mid"))

    for i, midi_file in enumerate(midi_files):
        try:
            # Encode MIDI file
            result = tokenizer.encode_midi_file(str(midi_file))

            # Quality filtering
            metadata = result['metadata']
            if (metadata['num_notes'] >= 10 and  # Minimum length
                metadata['num_notes'] <= 200 and  # Maximum length
                metadata['duration'] <= 64.0 and  # Maximum duration
                metadata['pitch_range']['span'] >= 12):  # Minimum range

                dataset.append({
                    'file': str(midi_file),
                    'tokens': result['token_ids'],
                    'metadata': metadata
                })

                print(f"Processed {i+1}/{len(midi_files)}: {midi_file.name}")
            else:
                print(f"Filtered out: {midi_file.name}")

        except Exception as e:
            print(f"Error processing {midi_file}: {e}")

    # Save dataset
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"Created dataset with {len(dataset)} sequences")
    return dataset

# Usage
dataset = prepare_training_dataset("midi_files/", "training_dataset.json")
```

### Data Augmentation

```python
def augment_melody(notes, transpose_semitones=0, tempo_factor=1.0):
    """Augment melody with transposition and tempo changes."""

    augmented = []
    for note in notes:
        new_note = SMTNote(
            pitch=note.pitch + transpose_semitones,
            start_time=note.start_time * tempo_factor,
            end_time=note.end_time * tempo_factor,
            velocity=note.velocity,
            pitch_name=tokenizer.midi_processor._midi_to_pitch_name(
                note.pitch + transpose_semitones
            ),
            duration_name=note.duration_name,
            dynamic_name=note.dynamic_name
        )
        augmented.append(new_note)

    return augmented

# Create augmented versions
original_notes = tokenizer.midi_processor.load_midi_file("melody.mid")

# Transpose up and down
for transpose in [-2, -1, 1, 2]:  # Transpose by 1-2 semitones
    augmented = augment_melody(original_notes, transpose_semitones=transpose)
    result = tokenizer.encode_notes(augmented, f"augmented_{transpose}")
    # Add to training dataset
```

### Sequence Segmentation

```python
def segment_long_melody(tokens, max_length=512, overlap=64):
    """Segment long token sequences for training."""

    segments = []

    if len(tokens) <= max_length:
        return [tokens]

    start = 0
    while start < len(tokens):
        end = min(start + max_length, len(tokens))
        segment = tokens[start:end]

        # Ensure segment starts and ends properly
        if segment[0] != "[BOS]":
            segment = ["[BOS]"] + segment
        if segment[-1] != "[EOS]":
            segment = segment + ["[EOS]"]

        segments.append(segment)

        # Move start position with overlap
        start += max_length - overlap

        if end == len(tokens):
            break

    return segments
```

---

## Performance Optimization

### Memory-Efficient Processing

```python
def process_large_dataset_streaming(file_list, batch_size=100):
    """Process large datasets in batches to manage memory."""

    tokenizer = SmartMelodyTokenizer()

    for i in range(0, len(file_list), batch_size):
        batch = file_list[i:i + batch_size]

        batch_results = []
        for filepath in batch:
            try:
                result = tokenizer.encode_midi_file(filepath)
                batch_results.append(result['token_ids'])
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

        # Process batch (save, train, etc.)
        yield batch_results

        # Clear memory
        del batch_results
```

### Vocabulary Optimization

```python
# Analyze token frequency to optimize vocabulary
from collections import Counter

def analyze_token_usage(dataset):
    """Analyze token frequency in dataset."""

    all_tokens = []
    for item in dataset:
        all_tokens.extend(item['tokens'])

    token_counts = Counter(all_tokens)

    print(f"Total tokens: {len(all_tokens)}")
    print(f"Unique tokens: {len(token_counts)}")
    print(f"Most common tokens:")

    for token_id, count in token_counts.most_common(20):
        token = tokenizer.vocabulary.decode_token(token_id)
        print(f"  {token}: {count} ({count/len(all_tokens)*100:.1f}%)")

    return token_counts

# Create optimized vocabulary based on usage
def create_optimized_vocabulary(token_counts, min_frequency=10):
    """Create vocabulary with only frequently used tokens."""

    frequent_tokens = [
        token_id for token_id, count in token_counts.items()
        if count >= min_frequency
    ]

    print(f"Reduced vocabulary size: {len(frequent_tokens)}")
    return frequent_tokens
```

### Parallel Processing

```python
import multiprocessing as mp
from functools import partial

def process_midi_file(filepath, config):
    """Process single MIDI file."""
    try:
        tokenizer = SmartMelodyTokenizer(**config)
        return tokenizer.encode_midi_file(filepath)
    except Exception as e:
        return {"error": str(e), "file": filepath}

def parallel_processing(file_list, config, num_processes=4):
    """Process MIDI files in parallel."""

    process_func = partial(process_midi_file, config=config)

    with mp.Pool(num_processes) as pool:
        results = pool.map(process_func, file_list)

    return results
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Error: ModuleNotFoundError: No module named 'smt'
# Solution: Install in development mode
# pip install -e .

# Error: Missing dependencies
# Solution: Install all requirements
# pip install -r requirements.txt
```

#### 2. MIDI File Issues

```python
# Error: No instruments found in MIDI file
# Check if MIDI file has actual note data
notes = tokenizer.midi_processor.load_midi_file("problematic.mid")
if not notes:
    print("MIDI file contains no notes")

# Error: Track index out of range
# Use track 0 or check available tracks
midi_obj = miditoolkit.midi.parser.MidiFile("file.mid")
print(f"Available tracks: {len(midi_obj.instruments)}")
```

#### 3. Memory Issues

```python
# For large files, use streaming processing
def process_large_file(filepath):
    # Process in chunks
    notes = tokenizer.midi_processor.load_midi_file(filepath)

    # Segment if too long
    if len(notes) > 1000:
        segments = segment_melody(notes, max_notes=500)
        for segment in segments:
            result = tokenizer.encode_notes(segment)
            yield result['token_ids']
```

#### 4. Quantization Issues

```python
# Adjust quantization for different music styles
classical_tokenizer = SmartMelodyTokenizer(
    midi_config={"quantization_grid": 32}  # Finer grid
)

electronic_tokenizer = SmartMelodyTokenizer(
    midi_config={"quantization_grid": 16}  # Standard grid
)
```

### Debugging Tools

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Examine tokenization step by step
def debug_tokenization(notes):
    """Debug tokenization process."""

    print(f"Input notes: {len(notes)}")

    # Check quantization
    quantized = tokenizer.midi_processor.quantize_notes(notes)
    print(f"After quantization: {len(quantized)}")

    # Check token creation
    result = tokenizer.encode_notes(quantized)
    print(f"Generated tokens: {len(result['tokens'])}")

    # Show tokens
    tokenizer.print_tokenization_example(result['tokens'])

    return result

# Performance profiling
import time

def profile_encoding(notes):
    """Profile encoding performance."""

    start_time = time.time()
    result = tokenizer.encode_notes(notes)
    end_time = time.time()

    print(f"Encoding took {end_time - start_time:.3f} seconds")
    print(f"Rate: {len(notes) / (end_time - start_time):.1f} notes/second")

    return result
```

### Performance Monitoring

```python
def monitor_tokenizer_performance(tokenizer, test_files):
    """Monitor tokenizer performance across test files."""

    stats = {
        'total_files': 0,
        'successful': 0,
        'errors': 0,
        'total_notes': 0,
        'total_tokens': 0,
        'compression_ratios': []
    }

    for filepath in test_files:
        try:
            result = tokenizer.encode_midi_file(filepath)

            stats['successful'] += 1
            stats['total_notes'] += result['metadata']['num_notes']
            stats['total_tokens'] += result['metadata']['num_tokens']
            stats['compression_ratios'].append(
                result['metadata']['compression_ratio']
            )

        except Exception as e:
            stats['errors'] += 1
            print(f"Error with {filepath}: {e}")

        stats['total_files'] += 1

    # Calculate summary statistics
    if stats['compression_ratios']:
        avg_compression = sum(stats['compression_ratios']) / len(stats['compression_ratios'])
        print(f"Average compression ratio: {avg_compression:.2f}")

    print(f"Success rate: {stats['successful']}/{stats['total_files']}")
    print(f"Total notes processed: {stats['total_notes']}")
    print(f"Total tokens generated: {stats['total_tokens']}")

    return stats
```

---

This guide covers the main use cases for SMT. For more specific questions, refer to the API documentation or create an issue on GitHub.