"""
NIATReviews.com — Notifications app.
Event-style notifications (recipient, actor, verb, target object) with read flag.
Delivery log for email/push; scalable — can move to Redis/queue for high volume.
"""
import uuid
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotificationType(models.Model):
    """
    Registry of notification types (e.g. comment_reply, post_upvote).
    Used for templating and filtering; optional for simple setups.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    # Optional: template keys for email/push
    email_template = models.CharField(max_length=255, blank=True)
    push_template = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification_type"
        verbose_name = "Notification type"
        verbose_name_plural = "Notification types"

    def __str__(self):
        return self.name


class Notification(models.Model):
    """
    In-app notification: recipient, actor (who did it), verb, optional target object.
    Indexed for fast "unread for user" and pagination. Ready to mirror to Redis for real-time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications_acted",
        db_index=True,
    )
    verb = models.CharField(max_length=64, db_index=True) 
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.UUIDField(null=True, blank=True, db_index=True)
    target = GenericForeignKey("content_type", "object_id")

    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notifications_notification"
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "read_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.verb} -> {self.recipient_id}"


class NotificationDelivery(models.Model):
    """
    Log of delivery attempts (email, push). Links to Notification for idempotency.
    Enables retries and analytics; can be moved to async worker.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="deliveries",
        db_index=True,
    )
    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("push", "Push"),
        ("in_app", "In-app"),
    ]
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, db_index=True)
    # Optional: external id for push/email provider
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification_delivery"
        indexes = [
            models.Index(fields=["notification", "channel"]),
            models.Index(fields=["sent_at"]),
        ]
        verbose_name = "Notification delivery"
        verbose_name_plural = "Notification deliveries"

    def __str__(self):
        return f"{self.channel}({self.notification_id})"
