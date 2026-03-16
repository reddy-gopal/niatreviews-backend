# Step 3 for Campus — Article: add campus_id_new, backfill, drop old FK, rename, add FK to Campus.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_article_campus_uuid(apps, schema_editor):
    Campus = apps.get_model("campuses", "Campus")
    Article = apps.get_model("articles", "Article")
    mapping = {c.id: c.id_new for c in Campus.objects.all()}
    for article in Article.objects.all():
        old_campus_id = article.campus_id_id
        if old_campus_id is not None and old_campus_id in mapping:
            article.campus_id_new = mapping[old_campus_id]
            article.save(update_fields=["campus_id_new"])
    null_new = Article.objects.filter(campus_id_new__isnull=True).exclude(campus_id_id__isnull=True)
    assert null_new.count() == 0, "Article: some rows with campus_id have NULL campus_id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0008_engagement_upvote_suggestion_view"),
        ("campuses", "0003_campus_backfill_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="campus_id_new",
            field=models.UUIDField(db_column="campus_id_new", null=True),
        ),
        migrations.RunPython(backfill_article_campus_uuid, noop),
        migrations.RemoveField(
            model_name="article",
            name="campus_id",
        ),
        migrations.RenameField(
            model_name="article",
            old_name="campus_id_new",
            new_name="campus_id",
        ),
        migrations.AlterField(
            model_name="article",
            name="campus_id",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="campuses.campus",
                to_field="id_new",
            ),
        ),
    ]
