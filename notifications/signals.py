"""
Notification signals - create notifications on user actions (Q&A).
"""
import logging
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _register_qa_signals():
    """Notify seniors when a prospective asks a question; notify question author when a senior answers."""
    if not apps.is_installed("qa"):
        return
    from qa.models import Question, Answer
    from .services import create_notification

    User = get_user_model()

    @receiver(post_save, sender=Question)
    def notify_seniors_new_question(sender, instance, created, **kwargs):
        if not created:
            return
        question = instance
        author = question.author
        if getattr(author, "is_verified_senior", False):
            return
        seniors = User.objects.filter(
            is_verified_senior=True, is_active=True
        ).exclude(pk=author.pk)
        verb = "asked a question"
        for recipient in seniors:
            create_notification(
                recipient=recipient,
                actor=author,
                verb=verb,
                target=question,
                notification_type_code="qa_question_asked",
            )

    @receiver(post_save, sender=Answer)
    def notify_author_answer_posted(sender, instance, created, **kwargs):
        if not created:
            return
        answer = instance
        question = answer.question
        recipient = question.author
        create_notification(
            recipient=recipient,
            actor=answer.author,
            verb="answered your question",
            target=question,
            notification_type_code="qa_answer",
        )


_register_qa_signals()
