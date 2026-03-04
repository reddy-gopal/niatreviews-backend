# Migration: Simplify FoundingEditorProfile to campus_id, linkedin_profile, year_joined

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_founding_editor_linkedin_campus"),
    ]

    operations = [
        migrations.RemoveField(model_name="foundingeditorprofile", name="college_name"),
        migrations.RemoveField(model_name="foundingeditorprofile", name="college_city"),
        migrations.RemoveField(model_name="foundingeditorprofile", name="college_state"),
        migrations.RemoveField(model_name="foundingeditorprofile", name="degree"),
        migrations.RemoveField(model_name="foundingeditorprofile", name="branch"),
        migrations.RemoveField(model_name="foundingeditorprofile", name="year_of_passing"),
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="year_joined",
            field=models.IntegerField(
                blank=True,
                help_text="Year the student joined (e.g. 2024).",
                null=True,
            ),
        ),
    ]
