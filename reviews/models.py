"""
NIATReviews.com — Reviews app (scaffold for future).
Programs, partner colleges, and reviews. Expand when moving beyond community-only.
"""
import uuid
from django.conf import settings
from django.db import models


class Program(models.Model):
    """NIAT program (e.g. B.Tech, M.Tech). For future review targeting."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_program"
        ordering = ["name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self):
        return self.name


class PartnerCollege(models.Model):
    """Partner college. Can offer multiple programs (M2M)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    programs = models.ManyToManyField(
        Program,
        related_name="partner_colleges",
        blank=True,
        db_table="reviews_partner_college_programs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_partner_college"
        ordering = ["name"]
        verbose_name = "Partner college"
        verbose_name_plural = "Partner colleges"

    def __str__(self):
        return self.name


class Review(models.Model):
    """
    Future: user review of a program at a partner college.
    Scaffold only; expand with rating, body, moderation when needed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    partner_college = models.ForeignKey(
        PartnerCollege,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    # Placeholder for future fields: rating, body, is_approved, etc.
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_review"
        indexes = [
            models.Index(fields=["program", "partner_college"]),
        ]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"Review({self.author_id}, {self.program_id}, {self.partner_college_id})"
