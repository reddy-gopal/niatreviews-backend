# accounts API serializers
from rest_framework import serializers
from .models import User


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
