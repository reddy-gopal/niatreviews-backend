# notifications API serializers
from rest_framework import serializers
from .models import Notification


def _build_target_url(notification):
    """Build frontend URL for notification target (post or comment). None if not applicable."""
    target = notification.target
    if target is None:
        return None
    # Comment has .post FK; Post has .slug
    if getattr(target, "post", None) is not None:
        return f"/posts/{target.post.slug}/comments/{target.id}"
    if getattr(target, "slug", None) is not None:
        return f"/posts/{target.slug}"
    return None


class NotificationSerializer(serializers.ModelSerializer):
    """Notification for list/detail. Actor summarized for display."""
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    target_url = serializers.SerializerMethodField()

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
            "target_url",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_target_url(self, obj):
        return _build_target_url(obj)
