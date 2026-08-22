import unittest
import os
import tempfile
from parser import parse_resume, parse_txt
from screener import clean_json_response
from config import Config

class TestConfig(unittest.TestCase):
    def test_provider_mapping(self):
        """Test that get_available_provider behaves predictably."""
        # Save original keys to restore later
        orig_gemini = Config.GEMINI_API_KEY
        orig_openai = Config.OPENAI_API_KEY
        
        try:
            # Set mock key
            Config.GEMINI_API_KEY = "mock_gemini_key"
            provider, key = Config.get_available_provider()
            self.assertEqual(provider, "gemini")
            self.assertEqual(key, "mock_gemini_key")
            
            # Remove keys
            Config.GEMINI_API_KEY = None
            Config.OPENAI_API_KEY = None
            Config.ANTHROPIC_API_KEY = None
            Config.GROQ_API_KEY = None
            provider, key = Config.get_available_provider()
            self.assertIsNone(provider)
            self.assertIsNone(key)
        finally:
            # Restore
            Config.GEMINI_API_KEY = orig_gemini
            Config.OPENAI_API_KEY = orig_openai

class TestParser(unittest.TestCase):
    def test_parse_txt(self):
        """Test that plain text parser extracts content correctly."""
        # Create a temporary txt file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as temp:
            temp.write("Candidate Name: John Doe\nSkills: Python, SQL")
            temp_path = temp.name

        try:
            content = parse_resume(temp_path)
            self.assertIn("John Doe", content)
            self.assertIn("Skills: Python, SQL", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_unsupported_format(self):
        """Test that parser raises error for unsupported extensions."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False, mode="w") as temp:
            temp_path = temp.name
        try:
            with self.assertRaises(ValueError):
                parse_resume(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

class TestScreener(unittest.TestCase):
    def test_clean_json_response_raw(self):
        """Test cleaning of raw JSON response string."""
        raw_json = '{"candidate_name": "Test Candidate", "relevance_score": 90}'
        cleaned = clean_json_response(raw_json)
        self.assertEqual(cleaned, raw_json)

    def test_clean_json_response_markdown(self):
        """Test cleaning of markdown code block wrapped JSON."""
        markdown_json = '```json\n{"candidate_name": "Test Candidate", "relevance_score": 90}\n```'
        cleaned = clean_json_response(markdown_json)
        expected = '{"candidate_name": "Test Candidate", "relevance_score": 90}'
        self.assertEqual(cleaned, expected)

if __name__ == "__main__":
    unittest.main()
