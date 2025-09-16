# SMT API Documentation

## Table of Contents
- [SmartMelodyTokenizer](#smartmelodytokenizer)
- [SMTVocabulary](#smtvocabulary)
- [MIDIProcessor](#midiprocessor)
- [PatternDetector](#patterndetector)
- [SMTNote](#smtnote)
- [Configuration Options](#configuration-options)
- [Examples](#examples)

---

## SmartMelodyTokenizer

The main tokenizer class for converting between MIDI files and SMT tokens.

### Constructor

```python
SmartMelodyTokenizer(vocab_config=None, midi_config=None)
```

**Parameters:**
- `vocab_config` (Dict, optional): Configuration for vocabulary building
- `midi_config` (Dict, optional): Configuration for MIDI processing

**Example:**
```python
tokenizer = SmartMelodyTokenizer()

# Custom configuration
custom_vocab = {
    "pitch_range": {"min_octave": 4, "max_octave": 6},
    "durations": ["eighth", "quarter", "half"],
    "dynamics": ["p", "mf", "f"]
}
tokenizer = SmartMelodyTokenizer(vocab_config=custom_vocab)
```

### Methods

#### `encode_midi_file(filepath, track_index=0)`

Encode a MIDI file to SMT tokens.

**Parameters:**
- `filepath` (str): Path to MIDI file
- `track_index` (int): Which track to use (default: 0)

**Returns:**
- `Dict`: Encoding result with keys:
  - `tokens` (List[str]): Token strings
  - `token_ids` (List[int]): Token IDs
  - `metadata` (Dict): Encoding metadata
  - `notes` (List[SMTNote]): Processed notes

**Example:**
```python
result = tokenizer.encode_midi_file("melody.mid")
print(f"Encoded {result['metadata']['num_notes']} notes")
print(f"Tokens: {result['tokens'][:5]}...")
```

#### `encode_notes(notes, source_info="")`

Encode a list of SMTNote objects to tokens.

**Parameters:**
- `notes` (List[SMTNote]): Notes to encode
- `source_info` (str): Source information for metadata

**Returns:**
- `Dict`: Same format as `encode_midi_file`

**Example:**
```python
from smt.utils.midi_utils import SMTNote

notes = [
    SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),
    SMTNote(62, 1.0, 2.0, 80, "D4", "quarter", "mf")
]
result = tokenizer.encode_notes(notes)
```

#### `decode_tokens(tokens, output_filepath=None)`

Decode SMT tokens back to notes.

**Parameters:**
- `tokens` (Union[List[str], List[int]]): Token strings or IDs
- `output_filepath` (str, optional): Save MIDI file

**Returns:**
- `List[SMTNote]`: Decoded notes

**Example:**
```python
tokens = ["[BOS]", "BAR", "NOTE_C4_quarter_mf", "[EOS]"]
notes = tokenizer.decode_tokens(tokens, "output.mid")
```

#### `generate_sample_tokens(style="simple")`

Generate sample token sequences for testing.

**Parameters:**
- `style` (str): Style type ("simple", "scale", "arpeggio")

**Returns:**
- `List[str]`: Sample tokens

**Example:**
```python
tokens = tokenizer.generate_sample_tokens("scale")
```

#### `print_tokenization_example(tokens)`

Print a visual representation of tokenization.

**Parameters:**
- `tokens` (List[str]): Tokens to visualize

**Example:**
```python
tokenizer.print_tokenization_example(tokens)
```

### Properties

- `vocabulary`: SMTVocabulary instance
- `midi_processor`: MIDIProcessor instance

---

## SMTVocabulary

Manages the tokenizer vocabulary.

### Constructor

```python
SMTVocabulary(config=None)
```

**Parameters:**
- `config` (Dict, optional): Vocabulary configuration

### Methods

#### `encode_token(token)` / `decode_token(token_id)`

Convert between tokens and IDs.

**Example:**
```python
vocab = SMTVocabulary()
token_id = vocab.encode_token("NOTE_C4_quarter_mf")
token = vocab.decode_token(token_id)
```

#### `encode_tokens(tokens)` / `decode_tokens(token_ids)`

Convert token lists.

#### `save(filepath)` / `load(filepath)`

Save/load vocabulary to/from JSON.

**Example:**
```python
vocab.save("my_vocabulary.json")
new_vocab = SMTVocabulary()
new_vocab.load("my_vocabulary.json")
```

#### `print_sample_tokens(n=20)`

Print sample tokens for inspection.

### Properties

- `size`: Vocabulary size
- `vocab`: List of all tokens
- `token_to_id`: Dict mapping tokens to IDs
- `id_to_token`: Dict mapping IDs to tokens

---

## MIDIProcessor

Handles MIDI file I/O and note processing.

### Constructor

```python
MIDIProcessor(ticks_per_beat=480)
```

### Methods

#### `load_midi_file(filepath, track_index=0)`

Load MIDI file and extract notes.

**Returns:**
- `List[SMTNote]`: Extracted notes

#### `save_midi_file(notes, filepath, tempo=120)`

Save notes to MIDI file.

**Parameters:**
- `notes` (List[SMTNote]): Notes to save
- `filepath` (str): Output path
- `tempo` (int): Tempo in BPM

#### `quantize_notes(notes, grid=16)`

Quantize note timings to grid.

**Parameters:**
- `notes` (List[SMTNote]): Notes to quantize
- `grid` (int): Grid divisions (16 = 16th notes)

#### `print_melody_info(notes, max_notes=10)`

Print human-readable melody information.

#### `get_melody_statistics(notes)`

Get detailed melody statistics.

**Returns:**
- `Dict`: Statistics including pitch range, duration info, etc.

---

## PatternDetector

Detects musical patterns in melodies.

### Constructor

```python
PatternDetector(config=None)
```

### Methods

#### `detect_patterns(notes)`

Detect all patterns in a melody.

**Parameters:**
- `notes` (List[SMTNote]): Notes to analyze

**Returns:**
- `List[MusicalPattern]`: Detected patterns

**Example:**
```python
detector = PatternDetector()
patterns = detector.detect_patterns(notes)
for pattern in patterns:
    print(f"{pattern.pattern_type}: {pattern.description}")
```

#### `get_pattern_tokens(patterns)`

Convert patterns to SMT tokens.

#### `print_pattern_analysis(notes, patterns)`

Print detailed pattern analysis.

---

## SMTNote

Internal note representation.

### Attributes

- `pitch` (int): MIDI pitch (0-127)
- `start_time` (float): Start time in beats
- `end_time` (float): End time in beats
- `velocity` (int): MIDI velocity (0-127)
- `pitch_name` (str): Human-readable pitch (e.g., "C4")
- `duration_name` (str): Human-readable duration (e.g., "quarter")
- `dynamic_name` (str): Human-readable dynamic (e.g., "mf")

**Example:**
```python
note = SMTNote(
    pitch=60,
    start_time=0.0,
    end_time=1.0,
    velocity=80,
    pitch_name="C4",
    duration_name="quarter",
    dynamic_name="mf"
)
```

---

## Configuration Options

### Vocabulary Configuration

```python
vocab_config = {
    "pitch_range": {
        "min_octave": 3,        # Minimum octave
        "max_octave": 6,        # Maximum octave
        "include_accidentals": True  # Include sharp/flat notes
    },
    "durations": [              # Available durations
        "sixteenth", "eighth", "quarter",
        "half", "whole", "dotted_quarter"
    ],
    "dynamics": [               # Available dynamics
        "pp", "p", "mp", "mf", "f", "ff"
    ],
    "patterns": {               # Pattern types to include
        "scales": ["scale_up", "scale_down"],
        "intervals": ["step", "skip", "leap"],
        "arpeggios": ["arpeggio_major", "arpeggio_minor"]
    },
    "max_vocab_size": 2000      # Maximum vocabulary size
}
```

### MIDI Configuration

```python
midi_config = {
    "quantization_grid": 16,    # 16th note quantization
    "min_rest_duration": 0.25,  # Minimum rest duration (beats)
    "max_bars": 32,             # Maximum melody length
    "beats_per_bar": 4.0        # Time signature (4/4)
}
```

### Pattern Detection Configuration

```python
pattern_config = {
    "min_pattern_length": 3,        # Minimum notes in pattern
    "max_pattern_length": 8,        # Maximum notes in pattern
    "scale_tolerance": 1,           # Tolerance for scale detection
    "arpeggio_tolerance": 2,        # Tolerance for arpeggio detection
    "sequence_min_repetitions": 2,  # Minimum sequence repetitions
    "confidence_threshold": 0.7     # Minimum confidence for patterns
}
```

---

## Examples

### Complete Workflow

```python
from smt import SmartMelodyTokenizer

# Initialize with custom config
vocab_config = {
    "pitch_range": {"min_octave": 4, "max_octave": 6},
    "durations": ["eighth", "quarter", "half"],
    "dynamics": ["p", "mf", "f"]
}

tokenizer = SmartMelodyTokenizer(vocab_config=vocab_config)

# Encode MIDI file
result = tokenizer.encode_midi_file("input.mid")

# Show results
print(f"Vocabulary size: {tokenizer.vocabulary.size}")
print(f"Encoded {result['metadata']['num_notes']} notes")
print(f"Generated {len(result['tokens'])} tokens")
print(f"Compression ratio: {result['metadata']['compression_ratio']:.2f}")

# Decode and save
notes = tokenizer.decode_tokens(result['tokens'], "output.mid")
print(f"Decoded {len(notes)} notes")
```

### Pattern Analysis

```python
from smt import SmartMelodyTokenizer
from smt.patterns.detector import PatternDetector

tokenizer = SmartMelodyTokenizer()
detector = PatternDetector()

# Load and analyze
notes = tokenizer.midi_processor.load_midi_file("melody.mid")
patterns = detector.detect_patterns(notes)

# Show analysis
detector.print_pattern_analysis(notes, patterns)

# Get pattern tokens
pattern_tokens = detector.get_pattern_tokens(patterns)
print(f"Pattern tokens: {pattern_tokens}")
```

### Training Data Preparation

```python
import glob
from smt import SmartMelodyTokenizer

tokenizer = SmartMelodyTokenizer()
training_data = []

for midi_file in glob.glob("dataset/*.mid"):
    try:
        result = tokenizer.encode_midi_file(midi_file)

        # Filter by quality criteria
        if (result['metadata']['num_notes'] >= 10 and
            result['metadata']['duration'] <= 32.0):

            training_data.append({
                "file": midi_file,
                "tokens": result['token_ids'],
                "metadata": result['metadata']
            })

    except Exception as e:
        print(f"Error processing {midi_file}: {e}")

print(f"Prepared {len(training_data)} training sequences")
```

### Custom Vocabulary

```python
from smt.core.vocabulary import SMTVocabulary

# Create genre-specific vocabulary
jazz_config = {
    "pitch_range": {"min_octave": 3, "max_octave": 7},
    "durations": [
        "eighth", "quarter", "half",
        "dotted_eighth", "dotted_quarter"  # Jazz swing rhythms
    ],
    "dynamics": ["pp", "p", "mp", "mf", "f", "ff"],
    "patterns": {
        "scales": ["scale_up", "scale_down", "chromatic_up"],
        "intervals": ["step", "skip", "leap", "octave"],
        "jazz": ["bebop_scale", "blue_note", "tritone_sub"]
    }
}

jazz_vocab = SMTVocabulary(jazz_config)
jazz_vocab.save("jazz_vocabulary.json")
print(f"Jazz vocabulary: {jazz_vocab.size} tokens")
```

---

## Error Handling

SMT includes comprehensive error handling:

```python
from smt import SmartMelodyTokenizer

tokenizer = SmartMelodyTokenizer()

try:
    result = tokenizer.encode_midi_file("nonexistent.mid")
except FileNotFoundError:
    print("MIDI file not found")
except Exception as e:
    print(f"Encoding error: {e}")

try:
    notes = tokenizer.decode_tokens(["INVALID_TOKEN"])
except Exception as e:
    print(f"Decoding error: {e}")
```

---

## Performance Tips

1. **Use appropriate quantization**: Higher grid values (32, 64) for precise timing, lower values (8, 16) for general use.

2. **Optimize vocabulary size**: Smaller vocabularies train faster but may lose expressiveness.

3. **Batch processing**: Process multiple files in batches for better performance.

4. **Memory management**: Use streaming for large datasets.

```python
# Memory-efficient processing
def process_large_dataset(file_list):
    for filepath in file_list:
        result = tokenizer.encode_midi_file(filepath)
        yield result['token_ids']
        # Memory is freed after each yield
```