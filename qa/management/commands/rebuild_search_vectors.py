"""
Rebuild search_vector for all Question records (PostgreSQL full-text search).
Usage: python manage.py rebuild_search_vectors
"""
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector

from qa.models import Question


class Command(BaseCommand):
    help = "Rebuild search vectors for all questions"

    def handle(self, *args, **options):
        updated = Question.objects.update(
            search_vector=SearchVector("title", weight="A", config="english")
            + SearchVector("body", weight="B", config="english")
        )
        self.stdout.write(self.style.SUCCESS(f"Rebuilt search vectors for {updated} question(s)."))
