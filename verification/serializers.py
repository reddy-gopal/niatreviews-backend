"""
Verification API serializers.
"""
from rest_framework import serializers
from .models import SeniorProfile, PhoneVerification, SeniorRegistration


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
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "reviewed_by",
            "reviewed_at",
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
