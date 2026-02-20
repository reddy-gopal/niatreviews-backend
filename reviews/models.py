"""
NIATReviews.com — Reviews app.
Programs, partner colleges, reviews. Senior onboarding review (mandatory on main app).
"""
import uuid
from django.conf import settings
from django.db import models

from .onboarding_constants import (
    FACULTY_SUPPORT_CHOICES,
    LEARNING_BALANCE_CHOICES,
    PLACEMENT_REALITY_CHOICES,
    EXPERIENCE_FEEL_CHOICES,
    FINAL_RECOMMENDATION_CHOICES,
)


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


class SeniorOnboardingReview(models.Model):
    """
    Mandatory onboarding review for approved seniors (one per user).
    Submitted on main app (niatreviews.com) after first magic-login.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="senior_onboarding_review",
        unique=True,
        db_index=True,
    )

    teaching_quality = models.PositiveSmallIntegerField()
    faculty_support_text = models.TextField()
    faculty_support_choice = models.CharField(max_length=32, choices=FACULTY_SUPPORT_CHOICES)

    projects_quality = models.PositiveSmallIntegerField()
    best_project_or_skill = models.TextField()
    learning_balance_choice = models.CharField(max_length=32, choices=LEARNING_BALANCE_CHOICES)

    placement_support = models.PositiveSmallIntegerField()
    job_ready_text = models.TextField()
    placement_reality_choice = models.CharField(max_length=32, choices=PLACEMENT_REALITY_CHOICES)

    overall_satisfaction = models.PositiveSmallIntegerField()
    one_line_experience = models.TextField()
    experience_feel_choice = models.CharField(max_length=32, choices=EXPERIENCE_FEEL_CHOICES)

    recommendation_score = models.PositiveSmallIntegerField()
    who_should_join_text = models.TextField()
    final_recommendation_choice = models.CharField(max_length=32, choices=FINAL_RECOMMENDATION_CHOICES)

    linkedin_profile_url = models.URLField(max_length=512, help_text="LinkedIn profile URL (e.g. https://linkedin.com/in/username)")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_senior_onboarding_review"
        verbose_name = "Senior onboarding review"
        verbose_name_plural = "Senior onboarding reviews"
        constraints = [
            models.CheckConstraint(check=models.Q(teaching_quality__gte=1, teaching_quality__lte=5), name="onb_teaching_1_5"),
            models.CheckConstraint(check=models.Q(projects_quality__gte=1, projects_quality__lte=5), name="onb_projects_1_5"),
            models.CheckConstraint(check=models.Q(placement_support__gte=1, placement_support__lte=5), name="onb_placement_1_5"),
            models.CheckConstraint(check=models.Q(overall_satisfaction__gte=1, overall_satisfaction__lte=5), name="onb_overall_1_5"),
            models.CheckConstraint(check=models.Q(recommendation_score__gte=1, recommendation_score__lte=5), name="onb_recommend_1_5"),
        ]

    def __str__(self):
        return f"Onboarding review by {self.user_id}"
