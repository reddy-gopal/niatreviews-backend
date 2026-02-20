"""
Verification API serializers.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import SeniorProfile, PhoneVerification, SeniorRegistration

User = get_user_model()


class SeniorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for SeniorProfile creation and updates.
    """
    class Meta:
        model = SeniorProfile
        fields = [
            "id",
            "user",
            "proof_summary",
            "status",
            "reviewed_by",
            "reviewed_at",
            "admin_notes",
            "review_submitted",
            "onboarding_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_submitted",
            "onboarding_completed",
            "created_at",
            "updated_at",
        ]


class PhoneVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for PhoneVerification.
    """
    class Meta:
        model = PhoneVerification
        fields = [
            "id",
            "phone_number",
            "otp_code",
            "expires_at",
            "verified_at",
            "user",
            "created_at",
        ]
        read_only_fields = ["id", "verified_at", "created_at"]



class SeniorRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed senior registration from seniors-frontend.
    Enforces unique personal_email (must not exist on User or another SeniorRegistration).
    """
    class Meta:
        model = SeniorRegistration
        fields = [
            "id",
            "full_name",
            "call_name",
            "college_email",
            "personal_email",
            "phone",
            "partner_college",
            "graduation_year",
            "branch",
            "student_id",
            "current_status",
            "id_card_image",
            "why_join",
            "best_experience",
            "advice_to_juniors",
            "skills_gained",
            "college_email_verified",
            "phone_verified",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate_personal_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Personal email is required.")
        email = value.strip().lower()
        # Must not already be used by a User
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists. Use a different email or log in."
            )
        # Must not already be used by another SeniorRegistration (any status)
        qs = SeniorRegistration.objects.filter(personal_email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "This email is already registered. Use a different email or check your application status."
            )
        return value.strip()
