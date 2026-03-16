# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing Campus row

import uuid
from django.db import migrations


def backfill_campus_uuid(apps, schema_editor):
    Campus = apps.get_model("campuses", "Campus")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id FROM campuses")
        rows = cursor.fetchall()
    for (old_id,) in rows:
        Campus.objects.filter(pk=old_id).update(id_new=uuid.uuid4())
    # Verification: no row must have NULL id_new
    null_count = Campus.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"Campus: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("campuses", "0002_campus_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_campus_uuid, noop),
    ]
