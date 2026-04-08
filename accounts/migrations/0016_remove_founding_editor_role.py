from django.db import migrations, models


def migrate_legacy_founding_editor(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="founding_editor").update(role="verified_niat_student")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_verified_niat_role"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_founding_editor, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("intermediate_student", "Intermediate Student"),
                    ("niat_student", "NIAT Student"),
                    ("verified_niat_student", "Verified NIAT Student"),
                    ("moderator", "Moderator"),
                    ("admin", "Admin"),
                ],
                db_index=True,
                default="intermediate_student",
                help_text="User role in the canonical RBAC model.",
                max_length=24,
            ),
        ),
    ]
