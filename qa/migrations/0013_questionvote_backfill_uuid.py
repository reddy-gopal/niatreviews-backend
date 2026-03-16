# Step 2 — RunPython data migration to assign uuid.uuid4() to every existing QuestionVote row

import uuid
from django.db import migrations


def backfill_questionvote_uuid(apps, schema_editor):
    QuestionVote = apps.get_model("qa", "QuestionVote")
    for v in QuestionVote.objects.all():
        QuestionVote.objects.filter(pk=v.pk).update(id_new=uuid.uuid4())
    null_count = QuestionVote.objects.filter(id_new__isnull=True).count()
    assert null_count == 0, f"QuestionVote: {null_count} row(s) still have NULL id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0012_questionvote_add_uuid_id_new"),
    ]

    operations = [
        migrations.RunPython(backfill_questionvote_uuid, noop),
    ]
