# Step 1 — Add new UUID column (nullable, not PK yet) for SeniorFollow

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0009_remove_phoneverification"),
    ]

    operations = [
        migrations.AddField(
            model_name="seniorfollow",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
