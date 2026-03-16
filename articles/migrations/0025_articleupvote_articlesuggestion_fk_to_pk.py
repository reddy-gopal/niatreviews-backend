# Point ArticleUpvote.article and ArticleSuggestion.article to Article's primary key.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0024_article_uuid_primary_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="articleupvote",
            name="article",
            field=models.ForeignKey(
                db_column="article_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="upvotes",
                to="articles.article",
            ),
        ),
        migrations.AlterField(
            model_name="articlesuggestion",
            name="article",
            field=models.ForeignKey(
                db_column="article_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="suggestions",
                to="articles.article",
            ),
        ),
    ]
