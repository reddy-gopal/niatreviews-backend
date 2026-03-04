# Generated migration: add multi-image support (images JSONField)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0003_article_subcategory"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="images",
            field=models.JSONField(blank=True, default=list, help_text="List of image URLs from the article body"),
        ),
    ]
