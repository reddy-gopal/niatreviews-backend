# Generated manually for multiple answers per question

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0007_add_question_category_classification"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="answers",
                to="qa.question",
                db_index=True,
            ),
        ),
        migrations.AddConstraint(
            model_name="answer",
            constraint=models.UniqueConstraint(
                fields=("question", "author"),
                name="qa_answer_one_per_senior_per_question",
            ),
        ),
    ]
