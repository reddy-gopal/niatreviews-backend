# Migration: FoundingEditorProfile (one-to-one with User)

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_email_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="FoundingEditorProfile",
            fields=[
                ("user", models.OneToOneField(
                    on_delete=models.CASCADE,
                    primary_key=True,
                    related_name="founding_editor_profile",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("college_name", models.CharField(blank=True, max_length=255)),
                ("college_city", models.CharField(blank=True, max_length=100)),
                ("college_state", models.CharField(blank=True, max_length=100)),
                ("degree", models.CharField(blank=True, help_text="e.g. B.Tech, B.E.", max_length=100)),
                ("branch", models.CharField(blank=True, help_text="e.g. CSE, ECE", max_length=100)),
                ("year_of_passing", models.CharField(blank=True, help_text="e.g. 2025", max_length=20)),
            ],
            options={
                "db_table": "accounts_founding_editor_profile",
                "verbose_name": "Founding Editor Profile",
                "verbose_name_plural": "Founding Editor Profiles",
            },
        ),
    ]
