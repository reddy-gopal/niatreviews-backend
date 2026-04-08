from django.db import migrations, models


def migrate_founding_to_verified_niat(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="founding_editor").update(role="verified_niat_student")


def reverse_migrate_founding_to_verified_niat(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="verified_niat_student").update(role="founding_editor")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_user_is_onboarded"),
    ]

    operations = [
        migrations.RunPython(migrate_founding_to_verified_niat, reverse_migrate_founding_to_verified_niat),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("intermediate_student", "Intermediate Student"),
                    ("niat_student", "NIAT Student"),
                    ("verified_niat_student", "Verified NIAT Student"),
                    ("founding_editor", "Founding Editor"),
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
