"""
NIATReviews.com — Accounts app.
Custom User with UUID PK, roles, verified-senior flag, and phone (with verification).
Must be created first; AUTH_USER_MODEL must point here.
"""
import uuid
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField("email address", blank=True, null=True, unique=True, db_index=True)
    """
    Custom user with UUID primary key for scalability and non-sequential IDs.
    Tracks role and whether the user is a verified NIAT senior (can comment).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Public UUID for the user; use in APIs and foreign keys.",
    )
    class UserRole(models.TextChoices):
        INTERMEDIATE_STUDENT = "intermediate_student", "Intermediate Student"
        NIAT_STUDENT = "niat_student", "NIAT Student"
        VERIFIED_NIAT_STUDENT = "verified_niat_student", "Verified NIAT Student"
        MODERATOR = "moderator", "Moderator"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=24,
        choices=UserRole.choices,
        default=UserRole.INTERMEDIATE_STUDENT,
        db_index=True,
        help_text="User role in the canonical RBAC model.",
    )
    is_verified_senior = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True when verification.SeniorProfile has been approved.",
    )
    # Phone: store E.164 or national format; unique per user when set (null = not set)
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        unique=True,
        help_text="Mobile number (e.g. E.164). Must be verified via OTP.",
    )
    phone_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True after successful phone OTP verification.",
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True once the user's email has been verified.",
    )
    is_onboarded = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True once the user completes onboarding.",
    )
    email_verification_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        help_text="One-time token used to verify the user's email address.",
    )

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["is_verified_senior", "is_active"]),
            models.Index(fields=["phone_verified"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        Normalize optional email so blanks are always stored as NULL.
        This prevents unique conflicts on empty strings and keeps behavior
        consistent across all create/update paths.
        """
        if isinstance(self.email, str):
            normalized = self.email.strip()
            self.email = normalized or None
        super().save(*args, **kwargs)

    @classmethod
    def validate_role_value(cls, value):
        valid_roles = {choice for choice, _label in cls.UserRole.choices}
        if value not in valid_roles:
            raise ValidationError({"role": f"Role must be one of: {', '.join(sorted(valid_roles))}."})


class FoundingEditorProfile(models.Model):
    """
    One-to-one profile for Founding Editors (NIATVerse). Campus, LinkedIn, year joined.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="founding_editor_profile",
        primary_key=True,
    )
    linkedin_profile = models.URLField(max_length=500, blank=True, help_text="LinkedIn profile URL")
    campus_id = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="founding_editors",
        db_column="campus_id",
        help_text="Default campus for articles; matches campus list in frontend.",
    )
    campus_name = models.CharField(max_length=200, blank=True, help_text="Campus display name (e.g. from frontend list).")
    year_joined = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year the student joined (e.g. 2024).",
    )

    class Meta:
        db_table = "accounts_founding_editor_profile"
        verbose_name = "Founding Editor Profile"
        verbose_name_plural = "Founding Editor Profiles"

    def __str__(self):
        return f"Profile of {self.user.username}"
