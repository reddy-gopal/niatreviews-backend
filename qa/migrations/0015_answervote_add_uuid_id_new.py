# Step 1 — Add new UUID column (nullable, not PK yet) for AnswerVote

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0014_questionvote_uuid_primary_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="answervote",
            name="id_new",
            field=models.UUIDField(db_column="id_new", editable=False, null=True, unique=True),
        ),
    ]
