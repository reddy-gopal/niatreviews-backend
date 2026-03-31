import logging
import os
import requests
from django.conf import settings
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Article
from campuses.models import Campus

logger = logging.getLogger(__name__)
NEXT_BASE_URL = os.environ.get("NEXT_BASE_URL", "").rstrip("/")
REVALIDATION_SECRET = os.environ.get("REVALIDATION_SECRET", "")


def _revalidate_paths(paths: list[str]) -> None:
    if not NEXT_BASE_URL or not REVALIDATION_SECRET:
        return
    try:
        requests.post(
            f"{NEXT_BASE_URL}/api/revalidate",
            json={"secret": REVALIDATION_SECRET, "paths": paths},
            timeout=5,
        )
        logger.info("Revalidated paths: %s", paths)
    except requests.exceptions.RequestException as e:
        logger.warning("Revalidation failed for paths %s: %s", paths, e)


def _sync_ai_review_enabled():
    """
    Synchronous AI review during request/response is disabled by default.
    Enable only if explicitly needed via settings.ENABLE_SYNC_AI_REVIEW = True.
    """
    return bool(getattr(settings, "ENABLE_SYNC_AI_REVIEW", False))


def _run_ai_review_and_assign(instance):
    """Call Gemini and set ai_confident_score, ai_feedback, ai_reviewed_at on instance."""
    from .ai_review import is_ai_review_skipped, review_article_with_gemini
    if is_ai_review_skipped():
        return
    try:
        logger.info("Running AI review for article %s", instance.pk)
        result = review_article_with_gemini(instance)
        instance.ai_confident_score = result["confidence_score"]
        instance.ai_feedback = result
        instance.ai_reviewed_at = timezone.now()
        logger.info(
            "AI review complete for article %s — score: %s, recommendation: %s",
            instance.pk, result["confidence_score"], result["status_recommendation"],
        )
    except Exception as e:
        logger.error("AI review failed for article %s, saving without score: %s", instance.pk, e)
        instance.ai_confident_score = None
        instance.ai_feedback = None


@receiver(pre_save, sender=Article)
def trigger_ai_review_on_pending(sender, instance, **kwargs):
    """
    When an existing article is saved with status pending_review and no AI feedback yet,
    run Gemini review and attach result to this save.
    New articles are handled in post_save (trigger_ai_review_after_create).
    """
    if not _sync_ai_review_enabled():
        return

    if not instance.pk:
        return  # new article: handled in post_save

    try:
        previous = Article.objects.get(pk=instance.pk)
    except Article.DoesNotExist:
        return

    if instance.status != "pending_review" or previous.ai_feedback:
        return

    _run_ai_review_and_assign(instance)


@receiver(post_save, sender=Article)
def trigger_ai_review_after_create(sender, instance, created, **kwargs):
    """
    When an article is first created with status pending_review, run AI review
    and save the result (pre_save skips new articles because pk is not set yet).
    """
    if not _sync_ai_review_enabled():
        return

    if not created or instance.status != "pending_review" or instance.ai_feedback:
        return

    _run_ai_review_and_assign(instance)
    instance.save(update_fields=["ai_confident_score", "ai_feedback", "ai_reviewed_at"])


@receiver(post_save, sender=Article)
def revalidate_article_page(sender, instance, **kwargs):
    if instance.campus_id is None or instance.slug is None:
        return
    if instance.campus_id.slug is None:
        return
    paths = [
        f"/campus/{instance.campus_id.slug}/article/{instance.slug}",
        f"/campus/{instance.campus_id.slug}",
        f"/campus/{instance.campus_id.slug}/articles",
    ]
    _revalidate_paths(paths)


@receiver(post_delete, sender=Article)
def revalidate_deleted_article_page(sender, instance, **kwargs):
    if instance.campus_id is None or instance.slug is None:
        return
    if instance.campus_id.slug is None:
        return
    paths = [
        f"/campus/{instance.campus_id.slug}/article/{instance.slug}",
        f"/campus/{instance.campus_id.slug}",
        f"/campus/{instance.campus_id.slug}/articles",
    ]
    _revalidate_paths(paths)


@receiver(post_save, sender=Campus)
def revalidate_campus_page(sender, instance, **kwargs):
    if instance.slug is None:
        return
    paths = [f"/campus/{instance.slug}", "/campuses"]
    _revalidate_paths(paths)