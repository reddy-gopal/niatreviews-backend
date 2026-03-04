from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_founding_editor_profile_simplify"),
    ]

    operations = [
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="campus_name",
            field=models.CharField(blank=True, help_text="Campus display name (e.g. from frontend list).", max_length=200),
        ),
    ]
