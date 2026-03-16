# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing Subcategory row

import uuid
from django.db import migrations


def backfill_subcategory_uuid(apps, schema_editor):
    Subcategory = apps.get_model("articles", "Subcategory")
    for s in Subcategory.objects.all():
        Subcategory.objects.filter(pk=s.pk).update(id_new=uuid.uuid4())
    null_count = Subcategory.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"Subcategory: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0017_subcategory_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_subcategory_uuid, noop),
    ]
