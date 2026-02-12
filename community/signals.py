import logging

from django.db.models import F
from django.db.models.functions import Greatest
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Post, Comment, PostVote, CommentUpvote

logger = logging.getLogger(__name__)


def _recalc_post_vote_counts(post_id):
    """Recalc upvote_count and downvote_count from PostVote for a single post. Production-safe."""
    from .models import PostVote
    up = PostVote.objects.filter(post_id=post_id, value=PostVote.VALUE_UP).count()
    down = PostVote.objects.filter(post_id=post_id, value=PostVote.VALUE_DOWN).count()
    Post.objects.filter(id=post_id).update(upvote_count=up, downvote_count=down)


@receiver(post_save, sender=PostVote)
def post_vote_save_recalc(sender, instance, created, **kwargs):
    _recalc_post_vote_counts(instance.post_id)


@receiver(post_delete, sender=PostVote)
def post_vote_delete_recalc(sender, instance, **kwargs):
    _recalc_post_vote_counts(instance.post_id)




@receiver(post_save, sender=CommentUpvote)
def increase_comment_upvote_count(sender, instance, created, **kwargs):
    if created:
        comment_id = instance.comment_id
        logger.debug(
            "Comment upvote signal: incrementing upvote_count for comment_id=%s only (not parent)",
            comment_id,
        )
        Comment.objects.filter(id=comment_id).update(
            upvote_count=F("upvote_count") + 1
        )


@receiver(post_delete, sender=CommentUpvote)
def decrease_comment_upvote_count(sender, instance, **kwargs):
    comment_id = instance.comment_id
    logger.debug(
        "Comment upvote signal: decrementing upvote_count for comment_id=%s only",
        comment_id,
    )
    Comment.objects.filter(id=comment_id).update(
        upvote_count=Greatest(F("upvote_count") - 1, 0)
    )


@receiver(post_save, sender=Comment)
def increase_post_comment_count(sender, instance, created, **kwargs):
   
    if created and instance.parent is None:
        Post.objects.filter(id=instance.post_id).update(
            comment_count=F("comment_count") + 1
        )


@receiver(post_delete, sender=Comment)
def decrease_post_comment_count(sender, instance, **kwargs):

    if instance.parent is None:
        Post.objects.filter(id=instance.post_id).update(
            comment_count=Greatest(F("comment_count") - 1, 0)
        )
