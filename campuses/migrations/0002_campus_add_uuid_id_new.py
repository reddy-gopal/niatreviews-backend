# Step 1 — Add new UUID column (nullable, not PK yet) for Campus

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campuses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="campus",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
