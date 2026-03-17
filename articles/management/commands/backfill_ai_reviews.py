"""
Backfill AI review for articles that are pending_review but have no ai_feedback.
Run: python manage.py backfill_ai_reviews
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from articles.models import Article

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Gemini AI review for all pending_review articles that have no ai_feedback yet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print which articles would be reviewed, do not call Gemini.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        qs = Article.objects.filter(status="pending_review", ai_feedback__isnull=True)
        count = qs.count()
        self.stdout.write(f"Found {count} article(s) in pending_review with no AI feedback.")
        if count == 0:
            return

        if dry_run:
            for a in qs:
                self.stdout.write(f"  Would review: {a.id} — {a.title[:60]}")
            self.stdout.write("Run without --dry-run to perform reviews.")
            return

        from articles.ai_review import review_article_with_gemini

        done = 0
        failed = 0
        for article in qs:
            try:
                self.stdout.write(f"Reviewing {article.id} — {article.title[:50]}…")
                result = review_article_with_gemini(article)
                article.ai_confident_score = result["confidence_score"]
                article.ai_feedback = result
                article.ai_reviewed_at = timezone.now()
                article.save(update_fields=["ai_confident_score", "ai_feedback", "ai_reviewed_at"])
                done += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ {result.get('status_recommendation', '?')}"))
            except Exception as e:
                failed += 1
                logger.exception("AI review failed for %s", article.id)
                self.stdout.write(self.style.ERROR(f"  ✗ {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Reviewed: {done}, failed: {failed}."))
