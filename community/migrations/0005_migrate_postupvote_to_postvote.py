# Data migration: copy PostUpvote to PostVote, recalc Post counts, then drop PostUpvote data

from django.db import migrations


def copy_upvotes_to_postvote(apps, schema_editor):
    PostUpvote = apps.get_model("community", "PostUpvote")
    PostVote = apps.get_model("community", "PostVote")
    Post = apps.get_model("community", "Post")
    for up in PostUpvote.objects.all():
        PostVote.objects.get_or_create(
            post_id=up.post_id,
            user_id=up.user_id,
            defaults={"value": 1},
        )
    # Recalc all post counts from PostVote
    for post in Post.objects.all():
        up = PostVote.objects.filter(post_id=post.id, value=1).count()
        down = PostVote.objects.filter(post_id=post.id, value=-1).count()
        post.upvote_count = up
        post.downvote_count = down
        post.save(update_fields=["upvote_count", "downvote_count"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0004_postvote_and_downvote_count"),
    ]

    operations = [
        migrations.RunPython(copy_upvotes_to_postvote, noop),
    ]
