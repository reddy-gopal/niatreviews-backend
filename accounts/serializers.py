# accounts API serializers
from rest_framework import serializers
from .models import User


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
        read_only_fields = ["id", "username", "role", "is_verified_senior", "phone_verified"]


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
