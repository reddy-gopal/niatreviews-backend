from django.apps import AppConfig


class ModerationConfig(AppConfig):
    """Featured posts, admin approval queue. Depends on community (and contenttypes)."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "moderation"
    verbose_name = "Moderation"
    label = "moderation"
