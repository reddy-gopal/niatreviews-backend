from django.apps import AppConfig


class CommunityConfig(AppConfig):
    """Posts, threaded comments, upvotes, tags, categories. Depends on accounts, verification."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "community"
    verbose_name = "Community"
    label = "community"

    def ready(self):
        import community.signals
