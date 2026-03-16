# Point Subcategory.category and Article.category_fk to Category's primary key.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0015_category_uuid_primary_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subcategory",
            name="category",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subcategories",
                to="articles.category",
            ),
        ),
        migrations.AlterField(
            model_name="article",
            name="category_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="category_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="articles.category",
            ),
        ),
    ]
