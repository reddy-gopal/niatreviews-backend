# Generated migration: follow-ups per answer with optional threading (parent)

from django.db import migrations, models
import django.db.models.deletion


def backfill_followup_answer(apps, schema_editor):
    FollowUp = apps.get_model("qa", "FollowUp")
    Answer = apps.get_model("qa", "Answer")
    for fu in FollowUp.objects.filter(answer__isnull=True).select_related("question"):
        first = Answer.objects.filter(question_id=fu.question_id).order_by("created_at").first()
        if first:
            fu.answer_id = first.id
            fu.save(update_fields=["answer_id"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0009_add_search_vector_and_gin_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="followup",
            name="answer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="followups",
                to="qa.answer",
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name="followup",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="replies",
                to="qa.followup",
                db_index=True,
            ),
        ),
        migrations.AddIndex(
            model_name="followup",
            index=models.Index(fields=["answer", "created_at"], name="qa_followup_answer__created_idx"),
        ),
        migrations.RunPython(backfill_followup_answer, noop),
    ]
