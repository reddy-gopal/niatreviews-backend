# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing Article row

import uuid
from django.db import migrations


def backfill_article_uuid(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    for a in Article.objects.all():
        Article.objects.filter(pk=a.pk).update(id_new=uuid.uuid4())
    null_count = Article.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"Article: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0020_article_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_article_uuid, noop),
    ]
