"""
Unit tests for SMT Vocabulary functionality.
"""

import unittest
import tempfile
import os
import json
from smt.core.vocabulary import SMTVocabulary


class TestSMTVocabulary(unittest.TestCase):
    """Test cases for SMTVocabulary class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.vocab = SMTVocabulary()

    def test_vocabulary_creation(self):
        """Test basic vocabulary creation."""
        self.assertIsInstance(self.vocab.vocab, list)
        self.assertGreater(len(self.vocab.vocab), 0)
        self.assertIsInstance(self.vocab.token_to_id, dict)
        self.assertIsInstance(self.vocab.id_to_token, dict)

    def test_special_tokens(self):
        """Test that special tokens are properly included."""
        special_tokens = ["[PAD]", "[BOS]", "[EOS]", "[MASK]", "[UNK]", "[SEP]"]

        for token in special_tokens:
            self.assertIn(token, self.vocab.vocab)
            self.assertIn(token, self.vocab.token_to_id)

    def test_structural_tokens(self):
        """Test structural tokens are included."""
        structural_tokens = ["BAR", "PHRASE_START", "PHRASE_END"]

        for token in structural_tokens:
            self.assertIn(token, self.vocab.vocab)

    def test_note_tokens_format(self):
        """Test that note tokens follow correct format."""
        note_tokens = [token for token in self.vocab.vocab if token.startswith("NOTE_")]

        self.assertGreater(len(note_tokens), 0)

        # Check format: NOTE_{pitch}_{duration}_{dynamic}
        for token in note_tokens[:10]:  # Test first 10
            parts = token.split("_")
            self.assertEqual(len(parts), 4)
            self.assertEqual(parts[0], "NOTE")
            # Pitch should contain note name and octave
            self.assertTrue(any(note in parts[1] for note in ['C', 'D', 'E', 'F', 'G', 'A', 'B']))

    def test_rest_tokens(self):
        """Test rest tokens are properly formatted."""
        rest_tokens = [token for token in self.vocab.vocab if token.startswith("REST_")]

        self.assertGreater(len(rest_tokens), 0)

        for token in rest_tokens:
            parts = token.split("_")
            self.assertGreaterEqual(len(parts), 2)  # Allow for dotted durations with underscores
            self.assertEqual(parts[0], "REST")

    def test_pattern_tokens(self):
        """Test pattern tokens are included."""
        pattern_tokens = [token for token in self.vocab.vocab if token.startswith("PATTERN_")]

        self.assertGreater(len(pattern_tokens), 0)

    def test_encode_decode_consistency(self):
        """Test that encoding and decoding are consistent."""
        test_tokens = ["[BOS]", "BAR", "NOTE_C4_quarter_mf", "[EOS]"]

        for token in test_tokens:
            if token in self.vocab.token_to_id:
                token_id = self.vocab.encode_token(token)
                decoded_token = self.vocab.decode_token(token_id)
                self.assertEqual(token, decoded_token)

    def test_encode_unknown_token(self):
        """Test encoding of unknown tokens."""
        unknown_token = "UNKNOWN_TOKEN_12345"
        token_id = self.vocab.encode_token(unknown_token)
        expected_id = self.vocab.token_to_id["[UNK]"]
        self.assertEqual(token_id, expected_id)

    def test_encode_decode_token_lists(self):
        """Test encoding and decoding token lists."""
        test_tokens = ["[BOS]", "BAR", "NOTE_C4_quarter_mf", "[EOS]"]

        # Filter tokens that exist in vocabulary
        valid_tokens = [token for token in test_tokens if token in self.vocab.token_to_id]

        if valid_tokens:
            token_ids = self.vocab.encode_tokens(valid_tokens)
            decoded_tokens = self.vocab.decode_tokens(token_ids)
            self.assertEqual(valid_tokens, decoded_tokens)

    def test_vocabulary_size_property(self):
        """Test vocabulary size property."""
        self.assertEqual(self.vocab.size, len(self.vocab.vocab))
        self.assertGreater(self.vocab.size, 100)  # Should have reasonable size

    def test_get_special_tokens(self):
        """Test get_special_tokens method."""
        special_tokens = self.vocab.get_special_tokens()
        self.assertIsInstance(special_tokens, dict)
        self.assertIn("[PAD]", special_tokens)
        self.assertIn("[BOS]", special_tokens)
        self.assertIn("[EOS]", special_tokens)

    def test_save_load_vocabulary(self):
        """Test saving and loading vocabulary."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Save vocabulary
            self.vocab.save(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))

            # Load into new vocabulary
            new_vocab = SMTVocabulary()
            new_vocab.load(tmp_path)

            # Compare vocabularies
            self.assertEqual(self.vocab.vocab, new_vocab.vocab)
            self.assertEqual(self.vocab.token_to_id, new_vocab.token_to_id)
            self.assertEqual(self.vocab.size, new_vocab.size)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_custom_config_vocabulary(self):
        """Test vocabulary creation with custom configuration."""
        custom_config = {
            "pitch_range": {"min_octave": 4, "max_octave": 5},
            "durations": ["quarter", "half"],
            "dynamics": ["mf", "f"],
            "patterns": {
                "scales": ["scale_up"]
            }
        }

        custom_vocab = SMTVocabulary(custom_config)

        # Should have fewer tokens due to restricted config
        self.assertLess(custom_vocab.size, self.vocab.size)

        # Check that custom restrictions are applied
        note_tokens = [token for token in custom_vocab.vocab if token.startswith("NOTE_")]

        # All note tokens should only use specified durations and dynamics
        for token in note_tokens[:10]:
            parts = token.split("_")
            if len(parts) >= 4:
                duration = parts[2]
                dynamic = parts[3]
                self.assertIn(duration, ["quarter", "half"])
                self.assertIn(dynamic, ["mf", "f"])

    def test_vocabulary_json_format(self):
        """Test that saved vocabulary follows correct JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            self.vocab.save(tmp_path)

            # Load and check JSON structure
            with open(tmp_path, 'r') as f:
                data = json.load(f)

            required_keys = ["vocab", "token_to_id", "id_to_token", "config", "size"]
            for key in required_keys:
                self.assertIn(key, data)

            self.assertEqual(data["size"], len(data["vocab"]))
            self.assertEqual(len(data["token_to_id"]), len(data["vocab"]))

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_print_sample_tokens(self):
        """Test print_sample_tokens method doesn't crash."""
        # This method prints to stdout, so we just test it doesn't raise an exception
        try:
            self.vocab.print_sample_tokens(10)
        except Exception as e:
            self.fail(f"print_sample_tokens raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()