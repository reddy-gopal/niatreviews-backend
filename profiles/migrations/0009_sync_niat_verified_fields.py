from django.db import migrations, models


def forward_sync_verified_from_niat(apps, schema_editor):
    NiatStudentProfile = apps.get_model("profiles", "NiatStudentProfile")
    VerifiedNiatStudentProfile = apps.get_model("profiles", "VerifiedNiatStudentProfile")

    for niat in NiatStudentProfile.objects.all().iterator():
        verified = VerifiedNiatStudentProfile.objects.filter(user_id=niat.user_id).first()
        if not verified:
            continue
        updated_fields = []
        if hasattr(verified, "student_id_number") and not (verified.student_id_number or "").strip():
            verified.student_id_number = niat.student_id_number or ""
            updated_fields.append("student_id_number")
        if hasattr(verified, "id_card_file") and not getattr(verified, "id_card_file", None):
            verified.id_card_file = niat.id_card_file
            updated_fields.append("id_card_file")
        if updated_fields:
            verified.save(update_fields=updated_fields)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0008_verified_profile_badge_image_path"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="niatstudentprofile",
            name="additional_doc",
        ),
        migrations.AddField(
            model_name="verifiedniatstudentprofile",
            name="id_card_file",
            field=models.FileField(blank=True, upload_to="niat/id_cards/"),
        ),
        migrations.AddField(
            model_name="verifiedniatstudentprofile",
            name="student_id_number",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RunPython(forward_sync_verified_from_niat, noop_reverse),
    ]
