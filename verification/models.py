"""
NIATReviews.com — Verification app.
Senior verification: SeniorProfile holds proof and admin approval state.
Phone verification: PhoneVerification stores OTP and verified_at; User.phone_verified synced via signal.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class PhoneVerification(models.Model):
    """
    OTP-based phone verification. Send code to phone_number; user submits code to verify.
    When verified_at is set and user is set, signal updates User.phone_number and User.phone_verified.
    Store OTP in plain text for dev; use hash in production if needed.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    phone_number = models.CharField(
        max_length=20,
        db_index=True,
        help_text="Mobile number (e.g. E.164) being verified.",
    )
    otp_code = models.CharField(
        max_length=10,
        help_text="OTP sent to phone (hash in production).",
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="OTP valid until this time.",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Set when user successfully submits correct OTP.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="phone_verifications",
        help_text="User claiming this phone; set when logged-in user requests verification.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_phone_verification"
        indexes = [
            models.Index(fields=["phone_number", "expires_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Phone verification"
        verbose_name_plural = "Phone verifications"

    def __str__(self):
        return f"{self.phone_number} — {'verified' if self.verified_at else 'pending'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class SeniorProfile(models.Model):
    """
    Holds senior-specific info and admin approval. One per user applying as senior.
    When status becomes 'approved', set user.is_verified_senior = True (e.g. via signal).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Public UUID for the senior profile.",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="senior_profile",
        help_text="User requesting senior verification.",
    )
    # Proof / display info (customize fields as needed)
    proof_summary = models.TextField(
        blank=True,
        help_text="Summary or link to proof of NIAT senior status.",
    )
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="senior_reviews_given",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "verification_senior_profile"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Senior profile"
        verbose_name_plural = "Senior profiles"

