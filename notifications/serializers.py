# notifications API serializers
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Notification for list/detail. Actor summarized for display."""
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "actor",
            "actor_username",
            "verb",
            "notification_type",
            "content_type",
            "object_id",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
