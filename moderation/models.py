"""
NIATReviews.com — Moderation app.
Featured posts (carousel/home) and generic pending-approval queue for admin workflow.
"""
import uuid
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class FeaturedPost(models.Model):
    """Post promoted to featured (e.g. homepage). Order for display."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        "community.Post",
        on_delete=models.CASCADE,
        related_name="featured_entries",
        db_index=True,
    )
    order = models.PositiveIntegerField(default=0, db_index=True)
    featured_at = models.DateTimeField(auto_now_add=True, db_index=True)
    featured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="featured_posts_set",
    )

    class Meta:
        db_table = "moderation_featured_post"
        ordering = ["order", "-featured_at"]
        verbose_name = "Featured post"
        verbose_name_plural = "Featured posts"

    def __str__(self):
        return f"Featured: {self.post_id} (order={self.order})"


class PendingApprovalQueue(models.Model):
    """
    Generic queue for items needing admin approval (e.g. reported posts, senior applications).
    content_type + object_id point to the item; status and assignee for workflow.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True,
    )
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_review", "In review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_queue_assignments",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_queue_resolutions",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "moderation_pending_approval_queue"
        indexes = [
            models.Index(fields=["status", "content_type"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Pending approval"
        verbose_name_plural = "Pending approvals"

    def __str__(self):
        return f"{self.content_type.model}({self.object_id}) — {self.status}"
