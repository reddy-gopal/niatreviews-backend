from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Notification events and delivery history. Ready for Redis/async delivery."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
    verbose_name = "Notifications"
    label = "notifications"
