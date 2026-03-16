# Step 3 for Campus — FoundingEditorProfile: add campus_id_new, backfill, drop old FK, rename, add FK to Campus.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_founding_editor_campus_uuid(apps, schema_editor):
    Campus = apps.get_model("campuses", "Campus")
    FoundingEditorProfile = apps.get_model("accounts", "FoundingEditorProfile")
    # Build old_id -> new_uuid mapping from Campus
    mapping = {c.id: c.id_new for c in Campus.objects.all()}
    for profile in FoundingEditorProfile.objects.all():
        old_campus_id = profile.campus_id_id  # raw FK value before we drop it
        if old_campus_id is not None and old_campus_id in mapping:
            profile.campus_id_new = mapping[old_campus_id]
            profile.save(update_fields=["campus_id_new"])
    # Verification: every non-null old campus_id should now have campus_id_new set
    null_new = FoundingEditorProfile.objects.filter(campus_id_new__isnull=True).exclude(campus_id_id__isnull=True)
    assert null_new.count() == 0, "FoundingEditorProfile: some rows with campus_id have NULL campus_id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_remove_user_accounts_us_email_74c8d6_idx_and_more"),
        ("campuses", "0003_campus_backfill_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="foundingeditorprofile",
            name="campus_id_new",
            field=models.UUIDField(db_column="campus_id_new", null=True),
        ),
        migrations.RunPython(backfill_founding_editor_campus_uuid, noop),
        migrations.RemoveField(
            model_name="foundingeditorprofile",
            name="campus_id",
        ),
        migrations.RenameField(
            model_name="foundingeditorprofile",
            old_name="campus_id_new",
            new_name="campus_id",
        ),
        migrations.AlterField(
            model_name="foundingeditorprofile",
            name="campus_id",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                help_text="Default campus for articles; matches campus list in frontend.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="founding_editors",
                to="campuses.campus",
                to_field="id_new",
            ),
        ),
    ]
