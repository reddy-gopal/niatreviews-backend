"""Unit tests for Q&A search (PostgreSQL full-text search)."""
from django.test import TestCase

from qa.search import search_questions, suggestion_questions


class TestSearchQuestions(TestCase):
    """Smoke tests for search_questions and suggestion_questions (no DB FTS required for empty query)."""

    def test_search_questions_empty_query_returns_none(self):
        qs = search_questions("")
        self.assertEqual(qs.count(), 0)
        qs = search_questions("   ")
        self.assertEqual(qs.count(), 0)

    def test_suggestion_questions_empty_query_returns_none(self):
        qs = suggestion_questions("")
        self.assertEqual(list(qs), [])
        qs = suggestion_questions("   ")
        self.assertEqual(list(qs), [])
