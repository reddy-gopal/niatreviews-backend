# Generated migration: add subcategory and subcategory_other for Club Directory articles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0002_category_and_article_section"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="subcategory",
            field=models.CharField(blank=True, db_index=True, max_length=80),
        ),
        migrations.AddField(
            model_name="article",
            name="subcategory_other",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
