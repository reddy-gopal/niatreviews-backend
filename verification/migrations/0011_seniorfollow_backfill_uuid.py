# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing SeniorFollow row

import uuid
from django.db import migrations


def backfill_seniorfollow_uuid(apps, schema_editor):
    SeniorFollow = apps.get_model("verification", "SeniorFollow")
    for s in SeniorFollow.objects.all():
        SeniorFollow.objects.filter(pk=s.pk).update(id_new=uuid.uuid4())
    null_count = SeniorFollow.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"SeniorFollow: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0010_seniorfollow_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_seniorfollow_uuid, noop),
    ]
