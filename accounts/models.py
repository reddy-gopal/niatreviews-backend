"""
NIATReviews.com — Accounts app.
Custom User with UUID PK, roles, verified-senior flag, and phone (with verification).
Must be created first; AUTH_USER_MODEL must point here.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
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
    ROLE_CHOICES = [
        ("student", "Student"),
        ("senior", "Senior"),
        ("admin", "Admin"),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="student",
        db_index=True,
        help_text="User role; seniors can be verified separately.",
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

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_verified_senior", "is_active"]),
            models.Index(fields=["phone_verified"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username
