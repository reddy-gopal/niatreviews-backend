# Migration: linkedin_profile and campus_id on FoundingEditorProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_founding_editor_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="linkedin_profile",
            field=models.URLField(blank=True, help_text="LinkedIn profile URL", max_length=500),
        ),
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="campus_id",
            field=models.IntegerField(
                blank=True,
                help_text="Default campus for articles; matches campus list in frontend.",
                null=True,
            ),
        ),
    ]
