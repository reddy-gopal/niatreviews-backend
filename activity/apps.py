from django.apps import AppConfig


class ActivityConfig(AppConfig):
    """Optional engagement logs (views, clicks) for metrics and analytics."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity"
    verbose_name = "Activity"
    label = "activity"
