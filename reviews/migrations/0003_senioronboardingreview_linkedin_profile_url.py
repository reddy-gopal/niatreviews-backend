# Add LinkedIn profile URL to senior onboarding review

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0002_senior_onboarding_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="senioronboardingreview",
            name="linkedin_profile_url",
            field=models.URLField(
                help_text="LinkedIn profile URL (e.g. https://linkedin.com/in/username)",
                max_length=512,
                default="",
            ),
        ),
    ]
