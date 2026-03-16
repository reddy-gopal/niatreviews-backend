# Step 3 for Article — ArticleUpvote: add article_id_new, backfill, drop old FK, rename, add FK to Article.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_articleupvote_article_uuid(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    ArticleUpvote = apps.get_model("articles", "ArticleUpvote")
    mapping = {a.id: a.id_new for a in Article.objects.all()}
    for upvote in ArticleUpvote.objects.all():
        old_id = upvote.article_id
        if old_id in mapping:
            upvote.article_id_new = mapping[old_id]
            upvote.save(update_fields=["article_id_new"])
    null_new = ArticleUpvote.objects.filter(article_id_new__isnull=True)
    assert null_new.count() == 0, "ArticleUpvote: some rows have NULL article_id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0021_article_backfill_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="articleupvote",
            name="article_id_new",
            field=models.UUIDField(db_column="article_id_new", null=True),
        ),
        migrations.RunPython(backfill_articleupvote_article_uuid, noop),
        # Drop constraint and index before RemoveField so SQLite table remake doesn't reference "article"
        migrations.RemoveConstraint(
            model_name="articleupvote",
            name="articles_articleupvote_article_user_uniq",
        ),
        migrations.RemoveIndex(
            model_name="articleupvote",
            name="articles_upv_article_user_idx",
        ),
        migrations.RemoveField(
            model_name="articleupvote",
            name="article",
        ),
        migrations.RenameField(
            model_name="articleupvote",
            old_name="article_id_new",
            new_name="article",
        ),
        migrations.AlterField(
            model_name="articleupvote",
            name="article",
            field=models.ForeignKey(
                db_column="article_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="upvotes",
                to="articles.article",
                to_field="id_new",
            ),
        ),
        migrations.AddIndex(
            model_name="articleupvote",
            index=models.Index(fields=["article", "user"], name="articles_upv_article_user_idx"),
        ),
        migrations.AddConstraint(
            model_name="articleupvote",
            constraint=models.UniqueConstraint(fields=("article", "user"), name="articles_articleupvote_article_user_uniq"),
        ),
    ]
