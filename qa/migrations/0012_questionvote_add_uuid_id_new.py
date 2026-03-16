# Step 1 — Add new UUID column (nullable, not PK yet) for QuestionVote

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0011_rename_qa_followup_answer__created_idx_qa_followup_answer__7340cc_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionvote",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
