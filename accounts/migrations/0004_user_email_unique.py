# Migration: make email unique on User

from django.db import migrations, models


def empty_email_to_null(apps, schema_editor):
    """Set empty string emails to None so unique constraint can be applied."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(email="").update(email=None)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(empty_email_to_null, noop),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                blank=True,
                db_index=True,
                max_length=254,
                null=True,
                unique=True,
                verbose_name="email address",
            ),
        ),
    ]
