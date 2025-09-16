"""
SMT Basic Usage Examples
========================

This file demonstrates basic usage of the Smart Melody Tokenizer.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smt import SmartMelodyTokenizer


def example_1_basic_tokenization():
    """Example 1: Basic tokenization workflow."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Tokenization")
    print("=" * 60)

    # Initialize tokenizer
    tokenizer = SmartMelodyTokenizer()

    print(f"SMT Vocabulary size: {tokenizer.vocabulary.size}")
    print(f"Special tokens: {tokenizer.vocabulary.get_special_tokens()}")

    # Generate sample tokens
    print("\\nGenerating sample melody tokens...")
    sample_tokens = tokenizer.generate_sample_tokens("simple")

    # Show tokenization
    tokenizer.print_tokenization_example(sample_tokens)

    # Decode back to notes
    print("\\nDecoding tokens back to notes...")
    notes = tokenizer.decode_tokens(sample_tokens)

    if notes:
        tokenizer.midi_processor.print_melody_info(notes)

        # Save as MIDI file
        output_file = "basic_example.mid"
        tokenizer.midi_processor.save_midi_file(notes, output_file)
        print(f"\\nSaved decoded melody to: {output_file}")
    else:
        print("No notes decoded!")


def example_2_different_styles():
    """Example 2: Different melody styles."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 2: Different Melody Styles")
    print("=" * 60)

    tokenizer = SmartMelodyTokenizer()

    styles = ["simple", "scale", "arpeggio"]

    for style in styles:
        print(f"\\n--- {style.upper()} STYLE ---")
        tokens = tokenizer.generate_sample_tokens(style)

        # Show just the musical tokens (skip BOS/EOS)
        music_tokens = [t for t in tokens if not t.startswith("[")]
        print(f"Tokens: {music_tokens}")

        # Decode and save
        notes = tokenizer.decode_tokens(tokens)
        if notes:
            output_file = f"{style}_example.mid"
            tokenizer.midi_processor.save_midi_file(notes, output_file)
            print(f"Saved to: {output_file}")


def example_3_vocabulary_exploration():
    """Example 3: Explore the vocabulary structure."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 3: Vocabulary Exploration")
    print("=" * 60)

    tokenizer = SmartMelodyTokenizer()

    # Show sample tokens from different categories
    tokenizer.vocabulary.print_sample_tokens()

    # Show specific token types
    all_tokens = tokenizer.vocabulary.vocab

    print(f"\\nToken categories in vocabulary:")
    categories = {
        "Special": [t for t in all_tokens if t.startswith("[")],
        "Structural": [t for t in all_tokens if t in ["BAR", "PHRASE_START", "PHRASE_END"]],
        "Notes": [t for t in all_tokens if t.startswith("NOTE_")],
        "Rests": [t for t in all_tokens if t.startswith("REST_")],
        "Patterns": [t for t in all_tokens if t.startswith("PATTERN_")],
        "Control": [t for t in all_tokens if t.startswith(("TEMPO_", "KEY_", "TIME_", "STYLE_"))]
    }

    for category, tokens in categories.items():
        print(f"  {category:12s}: {len(tokens):4d} tokens")
        if tokens:
            print(f"    Examples: {tokens[:3]}")


def example_4_encoding_decoding_cycle():
    """Example 4: Full encoding/decoding cycle."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 4: Encoding/Decoding Cycle")
    print("=" * 60)

    tokenizer = SmartMelodyTokenizer()

    # Create a test melody manually
    from smt.utils.midi_utils import SMTNote

    test_melody = [
        SMTNote(60, 0.0, 1.0, 80, "C4", "quarter", "mf"),  # C4 quarter
        SMTNote(62, 1.0, 2.0, 75, "D4", "quarter", "mf"),  # D4 quarter
        SMTNote(64, 2.0, 3.0, 85, "E4", "quarter", "mf"),  # E4 quarter
        SMTNote(65, 3.0, 4.0, 80, "F4", "quarter", "mf"),  # F4 quarter
        SMTNote(67, 4.0, 6.0, 90, "G4", "half", "f"),      # G4 half
    ]

    print(f"Original melody: {len(test_melody)} notes")

    # Encode to tokens
    result = tokenizer.encode_notes(test_melody, "test_melody")

    print(f"\\nEncoding result:")
    print(f"  Original notes: {result['metadata']['num_notes']}")
    print(f"  Generated tokens: {result['metadata']['num_tokens']}")
    print(f"  Compression ratio: {result['metadata']['compression_ratio']:.2f}")

    print(f"\\nTokens: {result['tokens']}")

    # Decode back
    decoded_notes = tokenizer.decode_tokens(result['tokens'])

    print(f"\\nDecoded: {len(decoded_notes)} notes")

    # Compare original vs decoded
    print("\\nComparison:")
    for i, (orig, decoded) in enumerate(zip(test_melody, decoded_notes)):
        print(f"  Note {i+1}: {orig.pitch_name} -> {decoded.pitch_name} "
              f"({orig.duration_name} -> {decoded.duration_name})")

    # Save both versions
    tokenizer.midi_processor.save_midi_file(test_melody, "original_melody.mid")
    tokenizer.midi_processor.save_midi_file(decoded_notes, "decoded_melody.mid")

    print("\\nSaved original_melody.mid and decoded_melody.mid for comparison")


def example_5_token_statistics():
    """Example 5: Token usage statistics."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 5: Token Statistics")
    print("=" * 60)

    tokenizer = SmartMelodyTokenizer()

    # Generate multiple melodies and analyze token usage
    styles = ["simple", "scale", "arpeggio"]
    all_tokens = []

    for style in styles:
        tokens = tokenizer.generate_sample_tokens(style)
        all_tokens.extend(tokens)

    # Count token frequencies
    from collections import Counter
    token_counts = Counter(all_tokens)

    print(f"Token usage across {len(styles)} sample melodies:")
    print(f"Total tokens generated: {len(all_tokens)}")
    print(f"Unique tokens used: {len(token_counts)}")

    print("\\nMost common tokens:")
    for token, count in token_counts.most_common(10):
        print(f"  {token:25s}: {count} times")

    # Analyze token types
    token_types = {}
    for token in token_counts:
        if token.startswith("["):
            token_type = "Special"
        elif token == "BAR":
            token_type = "Structural"
        elif token.startswith("NOTE_"):
            token_type = "Note"
        elif token.startswith("REST_"):
            token_type = "Rest"
        elif token.startswith("PATTERN_"):
            token_type = "Pattern"
        else:
            token_type = "Other"

        token_types[token_type] = token_types.get(token_type, 0) + token_counts[token]

    print("\\nToken type distribution:")
    for token_type, count in sorted(token_types.items()):
        percentage = (count / len(all_tokens)) * 100
        print(f"  {token_type:12s}: {count:3d} ({percentage:5.1f}%)")


if __name__ == "__main__":
    print("SMT - Smart Melody Tokenizer - Basic Usage Examples")
    print("=" * 60)

    try:
        example_1_basic_tokenization()
        example_2_different_styles()
        example_3_vocabulary_exploration()
        example_4_encoding_decoding_cycle()
        example_5_token_statistics()

        print("\\n" + "=" * 60)
        print("All examples completed successfully!")
        print("Check the generated MIDI files to hear the results.")
        print("=" * 60)

    except Exception as e:
        print(f"\\nError running examples: {e}")
        import traceback
        traceback.print_exc()