"""Unit tests for Q&A category classifier."""
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.cache import cache

from qa.category_classifier import (
    classify_with_keywords,
    classify_with_groq,
    CategoryClassifier,
    classifier,
)


class TestKeywordFallback(TestCase):
    def test_keyword_fallback(self):
        # "what is the hostel fee" should map to Hostel & Accommodation or Scholarships & Fee
        result = classify_with_keywords("what is the hostel fee")
        self.assertIn(
            result,
            ("Hostel & Accommodation", "Scholarships & Fee"),
            msg=f"Expected Hostel & Accommodation or Scholarships & Fee, got {result!r}",
        )


class TestGroqReturnsTuple(TestCase):
    @patch("qa.category_classifier.settings")
    @patch("groq.Groq")
    def test_groq_returns_tuple(self, mock_groq_class, mock_settings):
        mock_settings.GROQ_API_KEY = "test-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"category": "General", "confidence": 0.8}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_client

        out = classify_with_groq("Is NIAT good?")
        self.assertIsInstance(out, tuple, "classify_with_groq should return a tuple")
        self.assertEqual(len(out), 2, "tuple should have 2 elements")
        self.assertIsInstance(out[0], str, "first element should be str (category)")
        self.assertIsInstance(out[1], float, "second element should be float (confidence)")


class TestCacheHit(TestCase):
    def setUp(self):
        cache.clear()

    def test_cache_hit(self):
        with patch("qa.category_classifier.classify_with_groq") as mock_groq:
            mock_groq.return_value = ("Placements & Career", 0.9)
            c = CategoryClassifier()
            text = "How are placements at NIAT?"
            c.classify(text)
            c.classify(text)
            self.assertEqual(
                mock_groq.call_count,
                1,
                "Groq should be called only once; second call should use cache",
            )


class TestLowConfidenceUsesKeyword(TestCase):
    def setUp(self):
        cache.clear()

    def test_low_confidence_uses_keyword(self):
        with patch("qa.category_classifier.classify_with_groq") as mock_groq:
            mock_groq.return_value = ("General", 0.1)
            result = classifier.classify("What is the hostel fee structure?")
        self.assertEqual(
            result["source"],
            "keyword",
            "When Groq confidence is low (< 0.35), source should be 'keyword'",
        )
        self.assertIn("category", result)
        self.assertIn("confidence", result)
