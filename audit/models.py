import uuid

from django.conf import settings
from django.db import models


class ActionType(models.TextChoices):
    ROLE_CHANGED = "role_changed", "Role Changed"
    NIAT_APPROVED = "niat_approved", "NIAT Approved"
    NIAT_REJECTED = "niat_rejected", "NIAT Rejected"
    ARTICLE_SUBMITTED = "article_submitted", "Article Submitted"
    ARTICLE_APPROVED = "article_approved", "Article Approved"
    ARTICLE_REJECTED = "article_rejected", "Article Rejected"
    ARTICLE_PUBLISHED = "article_published", "Article Published"
    LOGIN_FAILED = "login_failed", "Login Failed"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100, choices=ActionType.choices)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]
