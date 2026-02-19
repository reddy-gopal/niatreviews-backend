"""
Re-run category classification for all existing questions.
Usage: python manage.py reclassify_questions
Use after improving keyword/LLM logic so existing rows get updated categories.
"""
from django.core.management.base import BaseCommand

from qa.models import Question
from qa.category_classifier import classifier


class Command(BaseCommand):
    help = "Reclassify all questions with current classifier (category, confidence, source)."

    def handle(self, *args, **options):
        updated = 0
        for q in Question.objects.iterator():
            text = f"{q.title}\n{q.body or ''}".strip()
            result = classifier.classify(text)
            q.category = result.get("category", "General")
            q.category_confidence = result.get("confidence", 0.0)
            q.category_source = result.get("source", "keyword")
            q.save(update_fields=["category", "category_confidence", "category_source"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Reclassified {updated} questions."))
