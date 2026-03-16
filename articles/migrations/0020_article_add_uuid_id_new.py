# Step 1 — Add new UUID column (nullable, not PK yet) for Article

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0019_subcategory_uuid_primary_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
