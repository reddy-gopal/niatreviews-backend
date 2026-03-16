# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing AnswerVote row

import uuid
from django.db import migrations


def backfill_answervote_uuid(apps, schema_editor):
    AnswerVote = apps.get_model("qa", "AnswerVote")
    for v in AnswerVote.objects.all():
        AnswerVote.objects.filter(pk=v.pk).update(id_new=uuid.uuid4())
    null_count = AnswerVote.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"AnswerVote: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0015_answervote_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_answervote_uuid, noop),
    ]
