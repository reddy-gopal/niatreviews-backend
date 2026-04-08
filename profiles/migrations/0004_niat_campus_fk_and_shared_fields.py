import django.utils.timezone
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_campus_data(apps, schema_editor):
    Campus = apps.get_model("campuses", "Campus")
    NiatStudentProfile = apps.get_model("profiles", "NiatStudentProfile")
    for profile in NiatStudentProfile.objects.exclude(campus_name=""):
        campus = Campus.objects.filter(name__iexact=profile.campus_name).first()
        if campus:
            profile.campus = campus
            profile.save(update_fields=["campus"])


class Migration(migrations.Migration):

    dependencies = [
        ("campuses", "0006_campus_google_map_link_and_description"),
        ("profiles", "0003_update_intermediate_profile_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="niatstudentprofile",
            name="linkedin_profile",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="niatstudentprofile",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="niat_profiles",
                to="campuses.campus",
            ),
        ),
        migrations.AddField(
            model_name="niatstudentprofile",
            name="bio",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="niatstudentprofile",
            name="profile_picture",
            field=models.ImageField(blank=True, upload_to="niat/avatars/"),
        ),
        migrations.RunPython(migrate_campus_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="niatstudentprofile",
            name="campus_name",
        ),
        migrations.AddIndex(
            model_name="niatstudentprofile",
            index=models.Index(fields=["campus"], name="profiles_ni_campus_6e4b1b_idx"),
        ),
        migrations.RenameField(
            model_name="foundingeditorprofile",
            old_name="campus_id",
            new_name="campus",
        ),
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name="foundingeditorprofile",
            index=models.Index(fields=["campus"], name="profiles_fo_campus_8a2c91_idx"),
        ),
        migrations.AddIndex(
            model_name="foundingeditorprofile",
            index=models.Index(
                fields=["badge_awarded_at"],
                name="profiles_fo_badge_a_3f7e02_idx",
            ),
        ),
    ]
