"""
Daemon that automatically runs Gemini AI review for articles in pending_review
that have no ai_feedback. Run once (e.g. in a separate process or systemd);
it loops every interval and processes one batch per run.

  python manage.py run_ai_review_daemon
  python manage.py run_ai_review_daemon --interval 300 --batch 5

Reviews are saved to the article; once saved, they are never overwritten.
"""
import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from articles.models import Article

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Daemon: automatically run Gemini review for pending_review articles with no AI feedback."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Seconds between each run (default: 60).",
        )
        parser.add_argument(
            "--batch",
            type=int,
            default=3,
            help="Max articles to review per run (default: 3).",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run once and exit (no daemon loop).",
        )

    def handle(self, *args, **options):
        interval = max(10, options["interval"])
        batch = max(1, options["batch"])
        once = options["once"]

        from articles.ai_review import review_article_with_gemini

        self.stdout.write(
            self.style.SUCCESS(
                f"AI review daemon started (interval={interval}s, batch={batch}). "
                "Ctrl+C to stop."
            )
        )

        while True:
            try:
                qs = Article.objects.filter(
                    status="pending_review", ai_feedback__isnull=True
                )[:batch]
                articles = list(qs)
                if not articles:
                    if once:
                        self.stdout.write("No articles to review. Exiting.")
                        return
                    time.sleep(interval)
                    continue

                for article in articles:
                    try:
                        self.stdout.write(
                            f"Reviewing {article.id} — {article.title[:50]}…"
                        )
                        result = review_article_with_gemini(article)
                        article.ai_confident_score = result["confidence_score"]
                        article.ai_feedback = result
                        article.ai_reviewed_at = timezone.now()
                        article.save(
                            update_fields=[
                                "ai_confident_score",
                                "ai_feedback",
                                "ai_reviewed_at",
                            ]
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ {result.get('status_recommendation', '?')}"
                            )
                        )
                    except Exception as e:
                        logger.exception("AI review failed for %s", article.id)
                        self.stdout.write(self.style.ERROR(f"  ✗ {e}"))

                if once:
                    self.stdout.write("Run once complete. Exiting.")
                    return

            except KeyboardInterrupt:
                self.stdout.write("\nStopped.")
                return

            time.sleep(interval)
