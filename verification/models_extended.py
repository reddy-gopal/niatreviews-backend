"""
Extended model for detailed senior registration from seniors-frontend.
This stores the comprehensive registration data before admin approval.
"""
import uuid
from django.db import models
from django.conf import settings


class SeniorRegistration(models.Model):
    """
    Detailed senior registration from the seniors-frontend form.
    After admin approval, this creates/updates a SeniorProfile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    full_name = models.CharField(max_length=255)
    call_name = models.CharField(max_length=100)
    college_email = models.EmailField(db_index=True)
    personal_email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Academic Info
    partner_college = models.CharField(max_length=100)
    graduation_year = models.CharField(max_length=4)
    branch = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50)
    current_status = models.CharField(max_length=50)
    
    # Verification
    id_card_image = models.ImageField(upload_to="senior_registrations/id_cards/")
    
    # Engaging Questions
    why_join = models.TextField()
    best_experience = models.TextField()
    advice_to_juniors = models.TextField()
    skills_gained = models.TextField()
    
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
