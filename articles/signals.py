import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Article

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Article)
def trigger_ai_review_on_pending(sender, instance, **kwargs):
    """
    Automatically run Gemini review when an article is in pending_review
    and has no AI feedback yet. Once a review is saved, it is never overwritten.
    Runs synchronously; use run_ai_review_daemon for automatic backfill of
    articles that are already pending without feedback.
    """
    if not instance.pk:
        return  # new article, skip

    try:
        previous = Article.objects.get(pk=instance.pk)
    except Article.DoesNotExist:
        return

    # Only run when status is pending_review and there is no existing review
    if instance.status != "pending_review" or previous.ai_feedback:
        return

    # Run the review
    try:
        from .ai_review import review_article_with_gemini
        logger.info(f"Running AI review for article {instance.pk}")
        result = review_article_with_gemini(instance)

        instance.ai_confident_score = result["confidence_score"]
        instance.ai_feedback = result
        instance.ai_reviewed_at = timezone.now()

        logger.info(
            f"AI review complete for article {instance.pk} — "
            f"score: {result['confidence_score']}, "
            f"recommendation: {result['status_recommendation']}"
        )

    except Exception as e:
        # Never block the save if Gemini fails
        logger.error(f"AI review failed for article {instance.pk}, saving without score: {e}")
        instance.ai_confident_score = None
        instance.ai_feedback = None