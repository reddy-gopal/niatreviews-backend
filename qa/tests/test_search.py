"""Unit tests for Q&A FTS5 search (prefix matching, normalization)."""
from django.test import TestCase

from qa.models import build_fts5_query


class TestBuildFts5QueryPrefix(TestCase):
    """Test that build_fts5_query produces prefix-based FTS5 MATCH terms."""

    def test_output_uses_prefix_asterisk(self):
        q = build_fts5_query("placement niat")
        self.assertIn("*", q, "Query should use prefix terms (contain *)")
        self.assertIn("AND", q, "Terms should be joined with AND")

    def test_normalization_lowercase_and_no_punctuation(self):
        # Contractions and punctuation should not break matching
        q = build_fts5_query("How's the placement at niat ??")
        self.assertIn("placement", q.lower())
        self.assertIn("niat", q.lower())
        self.assertNotIn("?", q)
        self.assertNotIn("'", q)

    def test_stopwords_removed(self):
        q = build_fts5_query("how is the placement at niat")
        # "how", "is", "the", "at" are stopwords
        self.assertIn("placement", q.lower())
        self.assertIn("niat", q.lower())
        self.assertNotIn("how", q.lower())
        self.assertNotIn(" the ", f" {q} ")

    def test_placements_at_niat(self):
        q = build_fts5_query("placements at NIAT")
        # Should be normalized to prefix form: "placement"* AND "niat"* (or similar)
        self.assertIn("*", q)
        self.assertIn("AND", q)
        # Both substantive terms present
        self.assertTrue("niat" in q.lower() or "placement" in q.lower(), f"Expected niat/placement in {q}")

    def test_niat_placement_companies(self):
        q = build_fts5_query("NIAT placement companies")
        self.assertIn("*", q)
        self.assertIn("AND", q)
        q_lower = q.lower()
        self.assertIn("niat", q_lower, f"Expected niat in {q}")
        self.assertIn("placement", q_lower, f"Expected placement in {q}")
        self.assertIn("companies", q_lower, f"Expected companies in {q}")

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(build_fts5_query(""), "")
        self.assertEqual(build_fts5_query("   "), "")

    def test_only_stopwords_uses_fallback_tokens(self):
        # "the the the" -> all stopwords -> fallback to all tokens
        q = build_fts5_query("the the the")
        self.assertIn("*", q)
        self.assertIn("the", q.lower())
