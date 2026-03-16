# Steps 4 & 5 for Subcategory — Drop old integer primary key; make UUID column the new primary key.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0018_subcategory_backfill_uuid"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subcategory",
            name="id",
        ),
        migrations.AlterField(
            model_name="subcategory",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False, unique=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameField(
                    model_name="subcategory",
                    old_name="id_new",
                    new_name="id",
                ),
                migrations.AlterField(
                    model_name="subcategory",
                    name="id",
                    field=models.UUIDField(db_column="id_new", editable=False, primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
