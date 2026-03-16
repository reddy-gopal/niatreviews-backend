# Steps 4 & 5 for SeniorFollow — Drop old integer primary key; make UUID column the new primary key.
# No other model has FK to SeniorFollow.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0011_seniorfollow_backfill_uuid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="seniorfollow",
            name="id",
        ),
        migrations.AlterField(
            model_name="seniorfollow",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False, unique=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(
                    model_name="seniorfollow",
                    old_name="id_new",
                    new_name="id",
                ),
                migrations.AlterField(
                    model_name="seniorfollow",
                    name="id",
                    field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
