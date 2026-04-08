import logging

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import User
from articles.models import Article
from profiles.models import NiatStudentProfile, VerifiedNiatStudentProfile

logger = logging.getLogger("notifications.tasks")

try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    def shared_task(*args, **kwargs):
        bind = kwargs.get("bind", False)

        def decorator(func):
            class _FallbackTaskContext:
                class _Request:
                    retries = 0

                request = _Request()

                @staticmethod
                def retry(exc=None, countdown=None):
                    if exc is not None:
                        raise exc
                    raise RuntimeError("Task retry requested")

            def delay(*delay_args, **delay_kwargs):
                if bind:
                    return func(_FallbackTaskContext(), *delay_args, **delay_kwargs)
                return func(*delay_args, **delay_kwargs)

            func.delay = delay
            return func

        return decorator


def _send(subject, message, recipients):
    if not recipients:
        return
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id):
    logger.info("send_verification_email.start", extra={"user_id": str(user_id)})
    try:
        user = User.objects.filter(pk=user_id).first()
        if not user or not user.email or user.is_verified or not user.email_verification_token:
            return "skipped"
        base_url = getattr(settings, "MAIN_APP_URL", "http://localhost:3000").rstrip("/")
        verify_url = f"{base_url}/verify-email?token={user.email_verification_token}"
        _send(
            "Verify your email",
            f"Hi {user.username},\n\nPlease verify your email address:\n{verify_url}",
            [user.email],
        )
        logger.info("send_verification_email.success", extra={"user_id": str(user_id)})
        return "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("send_verification_email.failure")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def send_write_access_unlocked_email(self, user_id):
    logger.info("send_write_access_unlocked_email.start", extra={"user_id": str(user_id)})
    try:
        user = User.objects.filter(pk=user_id).first()
        if not user or user.role != User.UserRole.VERIFIED_NIAT_STUDENT:
            return "skipped"
        if not user.email:
            logger.warning(
                "send_write_access_unlocked_email.no_email",
                extra={"user_id": str(user_id), "user_role": user.role},
            )
            return "no_email"
        base_url = getattr(settings, "MAIN_APP_URL", "http://localhost:3000").rstrip("/")
        write_access_url = f"{base_url}/write-access"
        _send(
            "You are verified - your writing access is now live",
            (
                f"Hi {user.username},\n\n"
                "Great news! Your NIAT profile has been approved and you are now a Verified NIAT Student.\n\n"
                "Your article writing access is unlocked. We are excited to see your experiences and insights help other students.\n\n"
                "Open your verified experience here:\n"
                f"{write_access_url}\n\n"
                "What happens when you open this link:\n"
                "- If you are already logged in, you will land on Home and see your badge popup.\n"
                "- If you are not logged in, you will be redirected to login first, then automatically sent to Home with the popup open.\n\n"
                "Thank you for contributing to NIAT Insider.\n"
                "Your voice matters.\n\n"
                "- Team NIAT Insider"
            ),
            [user.email],
        )
        logger.info("send_write_access_unlocked_email.success", extra={"user_id": str(user_id)})
        return "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("send_write_access_unlocked_email.failure")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def send_article_status_email(self, article_id, new_status):
    logger.info("send_article_status_email.start", extra={"article_id": str(article_id), "new_status": new_status})
    try:
        article = Article.objects.select_related("author_id").filter(pk=article_id).first()
        if not article or not article.author_id or not article.author_id.email:
            return "skipped"
        _send(
            f"Article status updated: {new_status}",
            f"Hi {article.author_username},\n\nYour article '{article.title}' is now '{new_status}'.",
            [article.author_id.email],
        )
        logger.info("send_article_status_email.success", extra={"article_id": str(article_id), "new_status": new_status})
        return "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("send_article_status_email.failure")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def notify_moderators_new_niat_submission(self, profile_id):
    logger.info("notify_moderators_new_niat_submission.start", extra={"profile_id": str(profile_id)})
    try:
        profile = NiatStudentProfile.objects.select_related("user").filter(pk=profile_id).first()
        if not profile or profile.status != NiatStudentProfile.Status.PENDING:
            return "skipped"
        recipients = list(
            User.objects.filter(role__in=[User.UserRole.MODERATOR, User.UserRole.ADMIN])
            .exclude(email__isnull=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
        _send(
            "New NIAT verification submission",
            f"{profile.user.username} submitted a NIAT profile for review.",
            recipients,
        )
        logger.info("notify_moderators_new_niat_submission.success", extra={"profile_id": str(profile_id)})
        return "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("notify_moderators_new_niat_submission.failure")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def send_niat_rejection_email(self, profile_id):
    logger.info("send_niat_rejection_email.start", extra={"profile_id": str(profile_id)})
    try:
        profile = NiatStudentProfile.objects.select_related("user").filter(pk=profile_id).first()
        if not profile or not profile.user.email or profile.status != NiatStudentProfile.Status.REJECTED:
            return "skipped"
        _send(
            "NIAT profile review update",
            (
                f"Hi {profile.user.username},\n\n"
                "Your NIAT profile submission was rejected.\n"
                f"Reason: {profile.rejection_reason or 'Please update your submission and try again.'}"
            ),
            [profile.user.email],
        )
        logger.info("send_niat_rejection_email.success", extra={"profile_id": str(profile_id)})
        return "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("send_niat_rejection_email.failure")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
