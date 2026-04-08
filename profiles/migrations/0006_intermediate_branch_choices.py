from django.db import migrations, models


def normalize_intermediate_branches(apps, schema_editor):
    IntermediateStudentProfile = apps.get_model("profiles", "IntermediateStudentProfile")
    for profile in IntermediateStudentProfile.objects.all().iterator():
        raw = (profile.branch or "").strip()
        upper = raw.upper()
        if upper == "MPC":
            profile.branch = "MPC"
            profile.branch_other = ""
        elif upper == "BIPC":
            profile.branch = "BIPC"
            profile.branch_other = ""
        else:
            profile.branch = "OTHERS"
            profile.branch_other = raw
        profile.save(update_fields=["branch", "branch_other"])


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0005_rename_profiles_fo_campus_8a2c91_idx_profiles_fo_campus__fbfadd_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="intermediatestudentprofile",
            name="branch",
            field=models.CharField(
                choices=[("MPC", "MPC"), ("BIPC", "BIPC"), ("OTHERS", "Others")],
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="intermediatestudentprofile",
            name="branch_other",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(normalize_intermediate_branches, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="intermediatestudentprofile",
            name="branch",
            field=models.CharField(
                choices=[("MPC", "MPC"), ("BIPC", "BIPC"), ("OTHERS", "Others")],
                max_length=20,
            ),
        ),
    ]
