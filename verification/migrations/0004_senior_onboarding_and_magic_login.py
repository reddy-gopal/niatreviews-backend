# Senior onboarding fields on SeniorProfile + MagicLoginToken

import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("verification", "0003_seniorregistration"),
    ]

    operations = [
        migrations.AddField(
            model_name="seniorprofile",
            name="review_submitted",
            field=models.BooleanField(db_index=True, default=False, help_text="True when mandatory onboarding review has been submitted."),
        ),
        migrations.AddField(
            model_name="seniorprofile",
            name="onboarding_completed",
            field=models.BooleanField(db_index=True, default=False, help_text="True after senior completes onboarding review."),
        ),
        migrations.CreateModel(
            name="MagicLoginToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("is_used", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.CASCADE, related_name="magic_login_tokens", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "verification_magic_login_token",
                "verbose_name": "Magic login token",
                "verbose_name_plural": "Magic login tokens",
            },
        ),
        migrations.AddIndex(
            model_name="magiclogintoken",
            index=models.Index(fields=["token", "is_used", "expires_at"], name="verification_token_is_us_expires_idx"),
        ),
    ]
