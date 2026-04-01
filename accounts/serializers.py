# accounts API serializers
from rest_framework import serializers
from .models import User, FoundingEditorProfile


def _get_senior_follower_count(user):
    try:
        return user.senior_profile.follower_count
    except Exception:
        return 0


def _get_is_followed_by_me(request, user):
    if not request or not request.user.is_authenticated:
        return None
    from verification.models import SeniorFollow
    return SeniorFollow.objects.filter(follower=request.user, senior=user).exists()


class UserSerializer(serializers.ModelSerializer):
    """Minimal user for nesting in Post/Comment etc."""
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_verified_senior", "phone_verified"]
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    """Profile for GET/PATCH /api/auth/me/. Only allow updating safe fields."""
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_verified_senior", "phone_number", "phone_verified"]
        read_only_fields = ["id", "role", "is_verified_senior", "phone_verified"]

    def validate_username(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")
        if value.lower() == "me":
            raise serializers.ValidationError("This username is reserved.")
        request = self.context.get("request")
        current_user = getattr(request, "user", None)
        qs = User.objects.filter(username__iexact=value)
        if current_user is not None and getattr(current_user, "pk", None):
            qs = qs.exclude(pk=current_user.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value


class PublicProfileSerializer(serializers.ModelSerializer):
    """Public profile for GET /api/users/<username>/ (no email/phone). Includes follower_count, is_followed_by_me for seniors."""
    follower_count = serializers.SerializerMethodField()
    is_followed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "is_verified_senior", "follower_count", "is_followed_by_me"]
        read_only_fields = fields

    def get_follower_count(self, obj):
        return _get_senior_follower_count(obj)

    def get_is_followed_by_me(self, obj):
        return _get_is_followed_by_me(self.context.get("request"), obj)


class AuthorProfileSerializer(serializers.ModelSerializer):
    """Public author profile with optional Founding Editor metadata."""
    follower_count = serializers.SerializerMethodField()
    is_followed_by_me = serializers.SerializerMethodField()
    linkedin_profile = serializers.SerializerMethodField()
    campus_id = serializers.SerializerMethodField()
    campus_name = serializers.SerializerMethodField()
    year_joined = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "is_verified_senior",
            "follower_count",
            "is_followed_by_me",
            "linkedin_profile",
            "campus_id",
            "campus_name",
            "year_joined",
        ]
        read_only_fields = fields

    def get_follower_count(self, obj):
        return _get_senior_follower_count(obj)

    def get_is_followed_by_me(self, obj):
        return _get_is_followed_by_me(self.context.get("request"), obj)

    def _get_fe_profile(self, obj):
        try:
            return obj.founding_editor_profile
        except FoundingEditorProfile.DoesNotExist:
            return None

    def get_linkedin_profile(self, obj):
        profile = self._get_fe_profile(obj)
        return profile.linkedin_profile if profile else ""

    def get_campus_id(self, obj):
        profile = self._get_fe_profile(obj)
        if not profile or profile.campus_id is None:
            return None
        return str(profile.campus_id_id)

    def get_campus_name(self, obj):
        profile = self._get_fe_profile(obj)
        return profile.campus_name if profile else ""

    def get_year_joined(self, obj):
        profile = self._get_fe_profile(obj)
        return profile.year_joined if profile else None


class FoundingEditorProfileSerializer(serializers.ModelSerializer):
    """GET/PATCH current user's Founding Editor profile (campus, LinkedIn, year_joined)."""
    class Meta:
        model = FoundingEditorProfile
        fields = ["linkedin_profile", "campus_id", "campus_name", "year_joined"]


class ModeratorAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "role", "date_joined", "last_login"]


class ModeratorAssignSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False, allow_blank=False)
    phone_number = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        provided = [
            "user_id" in attrs,
            bool(attrs.get("username")),
            bool(attrs.get("email")),
            bool(attrs.get("phone_number")),
        ]
        if sum(provided) == 0:
            raise serializers.ValidationError(
                "Provide one identifier: user_id, username, email, or phone_number."
            )
        return attrs


class ModeratorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active"]


class SeniorsSetupSerializer(serializers.Serializer):
    """First-time setup for approved seniors (set username and password after magic link)."""
    username = serializers.CharField(max_length=150, required=False, allow_blank=False)
    password = serializers.CharField(style={"input_type": "password"}, write_only=True, min_length=8)

    def validate_username(self, value):
        value = (value or "").strip()
        if not value:
            return value
        if value.lower() == "me":
            raise serializers.ValidationError("This username is reserved.")
        if User.objects.filter(username__iexact=value).exclude(pk=self.context["user"].pk).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value
