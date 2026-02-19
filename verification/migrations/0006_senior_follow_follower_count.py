# Generated manually for SeniorFollow and follower_count on SeniorProfile

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("verification", "0005_rename_verification_token_is_us_expires_idx_verificatio_token_4a3528_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="seniorprofile",
            name="follower_count",
            field=models.PositiveIntegerField(db_index=True, default=0, help_text="Denormalized count of users following this senior."),
        ),
        migrations.CreateModel(
            name="SeniorFollow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("follower", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="following_seniors", to=settings.AUTH_USER_MODEL, db_index=True)),
                ("senior", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="followers", to=settings.AUTH_USER_MODEL, db_index=True)),
            ],
            options={
                "db_table": "verification_senior_follow",
            },
        ),
        migrations.AddIndex(
            model_name="seniorfollow",
            index=models.Index(fields=["senior", "created_at"], name="verificatio_senior__idx"),
        ),
        migrations.AddConstraint(
            model_name="seniorfollow",
            constraint=models.UniqueConstraint(fields=("follower", "senior"), name="verification_senior_follow_unique"),
        ),
    ]
