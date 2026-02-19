# Generated manually for FollowUp model

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("qa", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FollowUp",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="followups", to=settings.AUTH_USER_MODEL, db_index=True)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="followups", to="qa.question", db_index=True)),
            ],
            options={
                "db_table": "qa_followup",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="followup",
            index=models.Index(fields=["question", "created_at"], name="qa_followup_questio_idx"),
        ),
    ]
