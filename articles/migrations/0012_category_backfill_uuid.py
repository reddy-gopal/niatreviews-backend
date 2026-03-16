# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing Category row

import uuid
from django.db import migrations


def backfill_category_uuid(apps, schema_editor):
    Category = apps.get_model("articles", "Category")
    for c in Category.objects.all():
        Category.objects.filter(pk=c.pk).update(id_new=uuid.uuid4())
    null_count = Category.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"Category: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0011_category_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_category_uuid, noop),
    ]
