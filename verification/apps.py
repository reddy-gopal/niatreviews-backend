from django.apps import AppConfig


class VerificationConfig(AppConfig):
    """Senior verification and approval workflow. Depends on accounts."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "verification"
    verbose_name = "Senior Verification"
    label = "verification"

    def ready(self):
        import verification.signals  # noqa: F401 — sync User.is_verified_senior on SeniorProfile save
