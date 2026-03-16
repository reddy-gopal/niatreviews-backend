# Step 1 — Add new UUID column (nullable, not PK yet) for Category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0010_article_campus_fk_to_pk"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
