# PostVote model and Post.downvote_count; PostUpvote retained for data migration

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("community", "0003_post_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="downvote_count",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.CreateModel(
            name="PostVote",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("value", models.SmallIntegerField(choices=[(1, "upvote"), (-1, "downvote")], db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="community.post", db_index=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="post_votes", to=settings.AUTH_USER_MODEL, db_index=True)),
            ],
            options={
                "db_table": "community_post_vote",
                "verbose_name": "Post vote",
                "verbose_name_plural": "Post votes",
            },
        ),
        migrations.AddConstraint(
            model_name="postvote",
            constraint=models.UniqueConstraint(fields=("post", "user"), name="community_post_vote_unique_user_post"),
        ),
        migrations.AddConstraint(
            model_name="postvote",
            constraint=models.CheckConstraint(check=models.Q(("value__in", [1, -1])), name="community_post_vote_value_check"),
        ),
        migrations.AddIndex(
            model_name="postvote",
            index=models.Index(fields=["post", "user"], name="community_p_post_id_idx"),
        ),
        migrations.AddIndex(
            model_name="postvote",
            index=models.Index(fields=["post", "value"], name="community_p_post_val_idx"),
        ),
    ]
