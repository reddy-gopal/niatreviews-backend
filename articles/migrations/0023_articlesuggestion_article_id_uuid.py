# Step 3 for Article — ArticleSuggestion: add article_id_new, backfill, drop old FK, rename, add FK to Article.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_articlesuggestion_article_uuid(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    ArticleSuggestion = apps.get_model("articles", "ArticleSuggestion")
    mapping = {a.id: a.id_new for a in Article.objects.all()}
    for suggestion in ArticleSuggestion.objects.all():
        old_id = suggestion.article_id
        if old_id in mapping:
            suggestion.article_id_new = mapping[old_id]
            suggestion.save(update_fields=["article_id_new"])
    null_new = ArticleSuggestion.objects.filter(article_id_new__isnull=True)
    assert null_new.count() == 0, "ArticleSuggestion: some rows have NULL article_id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0022_articleupvote_article_id_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="articlesuggestion",
            name="article_id_new",
            field=models.UUIDField(db_column="article_id_new", null=True),
        ),
        migrations.RunPython(backfill_articlesuggestion_article_uuid, noop),
        # Drop index before RemoveField so SQLite table remake doesn't reference "article"
        migrations.RemoveIndex(
            model_name="articlesuggestion",
            name="articles_sugg_article_idx",
        ),
        migrations.RemoveField(
            model_name="articlesuggestion",
            name="article",
        ),
        migrations.RenameField(
            model_name="articlesuggestion",
            old_name="article_id_new",
            new_name="article",
        ),
        migrations.AlterField(
            model_name="articlesuggestion",
            name="article",
            field=models.ForeignKey(
                db_column="article_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="suggestions",
                to="articles.article",
                to_field="id_new",
            ),
        ),
        migrations.AddIndex(
            model_name="articlesuggestion",
            index=models.Index(fields=["article"], name="articles_sugg_article_idx"),
        ),
    ]
