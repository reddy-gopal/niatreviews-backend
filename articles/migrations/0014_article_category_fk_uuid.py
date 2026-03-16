# Step 3 for Category — Article: add category_id_new (category_fk), backfill, drop old FK, rename, add FK to Category.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_article_category_fk_uuid(apps, schema_editor):
    Category = apps.get_model("articles", "Category")
    Article = apps.get_model("articles", "Article")
    mapping = {c.id: c.id_new for c in Category.objects.all()}
    for article in Article.objects.all():
        old_id = article.category_fk_id
        if old_id is not None and old_id in mapping:
            article.category_fk_new = mapping[old_id]
            article.save(update_fields=["category_fk_new"])
    null_new = Article.objects.filter(category_fk_new__isnull=True).exclude(category_fk_id__isnull=True)
    assert null_new.count() == 0, "Article: some rows with category_fk have NULL category_fk_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0013_subcategory_category_id_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="category_fk_new",
            field=models.UUIDField(db_column="category_id_new", null=True),
        ),
        migrations.RunPython(backfill_article_category_fk_uuid, noop),
        migrations.RemoveField(
            model_name="article",
            name="category_fk",
        ),
        migrations.RenameField(
            model_name="article",
            old_name="category_fk_new",
            new_name="category_fk",
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
                to_field="id_new",
            ),
        ),
    ]
