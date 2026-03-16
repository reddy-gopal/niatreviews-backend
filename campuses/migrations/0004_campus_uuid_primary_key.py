# Steps 4 & 5 — Drop old integer primary key; make UUID column the new primary key.
# State: rename id_new -> id with db_column="id_new" so FKs to campuses.id_new remain valid.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campuses", "0003_campus_backfill_uuid"),
        ("accounts", "0010_founding_editor_profile_campus_uuid"),
        ("articles", "0009_article_campus_id_uuid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="campus",
            name="id",
        ),
        migrations.AlterField(
            model_name="campus",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False, unique=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(
                    model_name="campus",
                    old_name="id_new",
                    new_name="id",
                ),
                migrations.AlterField(
                    model_name="campus",
                    name="id",
                    field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
