from django.conf import settings
from django.db import models
from django.utils import timezone


class IntermediateStudentProfile(models.Model):
    class Branch(models.TextChoices):
        MPC = "MPC", "MPC"
        BIPC = "BIPC", "BIPC"
        OTHERS = "OTHERS", "Others"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="intermediate_profile",
    )
    college_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=20, choices=Branch.choices)
    branch_other = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Intermediate profile for {self.user.username}"


class NiatStudentProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="niat_profile",
    )
    student_id_number = models.CharField(max_length=100)
    campus = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="niat_profiles",
        db_column="campus_id",
    )
    id_card_file = models.FileField(upload_to="niat/id_cards/")
    linkedin_profile = models.URLField(max_length=500, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="niat/avatars/", blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="niat_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["campus"]),
        ]

    def __str__(self):
        return f"NIAT profile for {self.user.username} ({self.status})"

    def promote_to_verified_niat_student(self) -> "VerifiedNiatStudentProfile":
        """
        Promotes this NIAT student to Verified NIAT Student.
        - Creates or updates VerifiedNiatStudentProfile
        - Copies collected NIAT details into VerifiedNiatStudentProfile
        - Sets user.role = verified_niat_student
        MUST be called inside transaction.atomic()
        """
        from accounts.models import User  # avoid circular import

        assert self.status == self.Status.APPROVED, (
            "promote_to_verified_niat_student called on non-approved profile"
        )

        verified_profile, created = VerifiedNiatStudentProfile.objects.get_or_create(
            user=self.user,
            defaults={
                "student_id_number": self.student_id_number,
                "campus": self.campus,
                "id_card_file": self.id_card_file,
                "linkedin_profile": self.linkedin_profile,
                "bio": self.bio,
                "profile_picture": self.profile_picture,
            },
        )

        if not created:
            verified_profile.student_id_number = self.student_id_number
            verified_profile.campus = self.campus
            verified_profile.id_card_file = self.id_card_file
            verified_profile.linkedin_profile = self.linkedin_profile
            verified_profile.bio = self.bio
            if self.profile_picture:
                verified_profile.profile_picture = self.profile_picture
            verified_profile.save(update_fields=[
                "student_id_number",
                "campus",
                "id_card_file",
                "linkedin_profile",
                "bio",
                "profile_picture",
                "updated_at",
            ])

        self.user.role = User.UserRole.VERIFIED_NIAT_STUDENT
        self.user.save(update_fields=["role"])

        return verified_profile


class VerifiedNiatStudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verified_niat_profile",
    )
    student_id_number = models.CharField(max_length=100, blank=True)
    campus = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_niat_profiles",
        db_column="campus_id",
    )
    bio = models.TextField(blank=True)
    id_card_file = models.FileField(upload_to="niat/id_cards/", blank=True)
    profile_picture = models.ImageField(
        upload_to="founding/avatars/", blank=True
    )
    linkedin_profile = models.URLField(max_length=500, blank=True)
    badge_awarded_at = models.DateTimeField(auto_now_add=True)
    campus_name = models.CharField(
        max_length=200, blank=True, editable=False
    )
    year_joined = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_verified_niat_student_profile"
        indexes = [
            models.Index(fields=["campus"]),
            models.Index(fields=["badge_awarded_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.campus_id:
            self.campus_name = self.campus.name
        else:
            self.campus_name = ""
        super().save(*args, **kwargs)

    def __str__(self):
        awarded = (
            timezone.localtime(self.badge_awarded_at).date().isoformat()
            if self.badge_awarded_at
            else "pending"
        )
        return f"Verified NIAT profile for {self.user.username} ({awarded})"
