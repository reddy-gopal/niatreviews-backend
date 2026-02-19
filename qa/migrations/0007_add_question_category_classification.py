# Generated for Q&A auto category classification.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0006_rename_qa_followup_questio_idx_qa_followup_questio_326938_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="category",
            field=models.CharField(db_index=True, default="General", max_length=80),
        ),
        migrations.AddField(
            model_name="question",
            name="category_confidence",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="question",
            name="category_source",
            field=models.CharField(default="keyword", max_length=20),
        ),
    ]
