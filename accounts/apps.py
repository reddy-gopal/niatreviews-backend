from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """User accounts, roles, and auth. Must load before verification/community."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts"
    label = "accounts"
