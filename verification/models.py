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

    # Senior onboarding (mandatory on main app after first login)
    review_submitted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True when mandatory onboarding review has been submitted.",
    )
    onboarding_completed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True after senior completes onboarding review.",
    )
    follower_count = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Denormalized count of users following this senior.",
    )

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



class SeniorRegistration(models.Model):
    """
    Detailed senior registration from the seniors-frontend form.
    Stores comprehensive application data before admin approval.
    After approval, admin can create a User account and SeniorProfile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    full_name = models.CharField(max_length=255, help_text="Full legal name")
    call_name = models.CharField(max_length=100, help_text="Preferred name or nickname")
    college_email = models.EmailField(db_index=True, help_text="College email address")
    personal_email = models.EmailField(help_text="Personal email for notifications")
    phone = models.CharField(max_length=20, help_text="Phone number")
    
    # Academic Info
    partner_college = models.CharField(max_length=100, help_text="Partner college name")
    graduation_year = models.CharField(max_length=4, help_text="Expected graduation year")
    branch = models.CharField(max_length=100, help_text="Branch/Department")
    student_id = models.CharField(max_length=50, help_text="Student ID number")
    current_status = models.CharField(max_length=50, help_text="Current status (Student/Intern)")
    
    # Verification
    id_card_image = models.ImageField(
        upload_to="senior_registrations/id_cards/",
        help_text="College ID card image"
    )
    
    # Engaging Questions
    why_join = models.TextField(help_text="Why they want to join as a mentor")
    best_experience = models.TextField(help_text="Best experience at NIAT")
    advice_to_juniors = models.TextField(help_text="Advice for junior students")
    skills_gained = models.TextField(help_text="Key skills gained")
    
    # Verification Status
    college_email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Admin Review
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="senior_registrations_reviewed"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Linked User (created after approval)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="senior_registration",
        help_text="User account created/linked after approval"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "verification_senior_registration"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["college_email"]),
        ]
        verbose_name = "Senior Registration"
        verbose_name_plural = "Senior Registrations"
    
    def __str__(self):
        return f"{self.full_name} ({self.college_email}) - {self.status}"


class MagicLoginToken(models.Model):
    """
    Passwordless magic link login for approved seniors.
    Single-use, expires in 30 minutes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="magic_login_tokens",
        db_index=True,
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_magic_login_token"
        indexes = [models.Index(fields=["token", "is_used", "expires_at"])]
        verbose_name = "Magic login token"
        verbose_name_plural = "Magic login tokens"

    def __str__(self):
        return f"MagicLogin({self.user_id}, used={self.is_used})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class SeniorFollow(models.Model):
    """User follows a verified senior. Unique (follower, senior)."""
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_seniors",
        db_index=True,
    )
    senior = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_senior_follow"
        constraints = [
            models.UniqueConstraint(fields=["follower", "senior"], name="verification_senior_follow_unique"),
        ]
        indexes = [models.Index(fields=["senior", "created_at"])]

    def __str__(self):
        return f"{self.follower_id} -> {self.senior_id}"
