# Step 1 — Add new UUID column (nullable, not PK yet) for Subcategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0016_category_fk_to_pk"),
    ]

    operations = [
        migrations.AddField(
            model_name="subcategory",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
