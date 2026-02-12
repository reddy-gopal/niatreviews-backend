"""
NIATReviews.com — Activity app (optional).
Engagement logs for metrics: post/comment views, optional click events.
Lightweight; can be aggregated or moved to Redis/analytics pipeline at scale.
"""
import uuid
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class EngagementLog(models.Model):
    """
    Generic log entry: user (optional), action, target object.
    Use for view counts, clicks; keep minimal for high write volume.
    Consider async writes or Redis for 2–3k concurrent users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="engagement_logs",
        db_index=True,
    )
    action = models.CharField(max_length=32, db_index=True)  # e.g. "view", "click"
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
    )
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Optional: session or IP for anonymous; store hashed if needed for privacy
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "activity_engagement_log"
        indexes = [
            models.Index(fields=["content_type", "object_id", "action"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Engagement log"
        verbose_name_plural = "Engagement logs"

    def __str__(self):
        return f"{self.action}({self.content_type.model}:{self.object_id})"
