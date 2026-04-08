import os

from rest_framework import serializers

from campuses.models import Campus
from .models import VerifiedNiatStudentProfile, IntermediateStudentProfile, NiatStudentProfile


ALLOWED_PROFILE_FILE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_PROFILE_FILE_SIZE = 5 * 1024 * 1024


def validate_profile_file(value):
    if not value:
        return value
    ext = os.path.splitext(value.name or "")[1].lower()
    if ext not in ALLOWED_PROFILE_FILE_EXTENSIONS:
        raise serializers.ValidationError("Only pdf, jpg, jpeg, and png files are allowed.")
    if value.size > MAX_PROFILE_FILE_SIZE:
        raise serializers.ValidationError("File size must be 5MB or less.")
    return value


class IntermediateStudentProfileSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        branch = attrs.get("branch")
        branch_other = (attrs.get("branch_other") or "").strip()
        if branch == IntermediateStudentProfile.Branch.OTHERS and not branch_other:
            raise serializers.ValidationError({"branch_other": "Please specify your branch."})
        if branch in (IntermediateStudentProfile.Branch.MPC, IntermediateStudentProfile.Branch.BIPC):
            attrs["branch_other"] = ""
        else:
            attrs["branch_other"] = branch_other
        return attrs

    class Meta:
        model = IntermediateStudentProfile
        fields = ["id", "college_name", "branch", "branch_other", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class NiatStudentProfileReadSerializer(serializers.ModelSerializer):
    reviewed_by_username = serializers.SerializerMethodField()
    campus = serializers.SerializerMethodField()

    class Meta:
        model = NiatStudentProfile
        fields = [
            "id",
            "student_id_number",
            "campus",
            "id_card_file",
            "linkedin_profile",
            "bio",
            "profile_picture",
            "status",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_reviewed_by_username(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by_id else None

    def get_campus(self, obj):
        if obj.campus_id is None:
            return None
        return {"id": str(obj.campus_id), "name": obj.campus.name}


class NiatStudentProfileWriteSerializer(serializers.ModelSerializer):
    campus = serializers.PrimaryKeyRelatedField(
        queryset=Campus.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = NiatStudentProfile
        fields = [
            "student_id_number",
            "campus",
            "id_card_file",
            "linkedin_profile",
            "bio",
            "profile_picture",
        ]

    def validate_id_card_file(self, value):
        return validate_profile_file(value)

    def validate_profile_picture(self, value):
        return validate_profile_file(value)

    def create(self, validated_data):
        user = self.context["request"].user
        profile, created = NiatStudentProfile.objects.get_or_create(
            user=user,
            defaults=validated_data,
        )
        if created:
            return profile
        return self.update(profile, validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if instance.status == NiatStudentProfile.Status.REJECTED:
            instance.status = NiatStudentProfile.Status.PENDING
            instance.reviewed_by = None
            instance.reviewed_at = None
            instance.rejection_reason = ""
        instance.save()
        return instance


class VerifiedNiatStudentProfileSerializer(serializers.ModelSerializer):
    campus = serializers.SerializerMethodField()

    class Meta:
        model = VerifiedNiatStudentProfile
        fields = [
            "id",
            "student_id_number",
            "bio",
            "badge_awarded_at",
            "id_card_file",
            "profile_picture",
            "linkedin_profile",
            "campus",
            "campus_name",
            "year_joined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "badge_awarded_at",
            "campus",
            "campus_name",
            "created_at",
            "updated_at",
        ]

    def get_campus(self, obj):
        if obj.campus_id is None:
            return None
        return {"id": str(obj.campus_id), "name": obj.campus.name}
