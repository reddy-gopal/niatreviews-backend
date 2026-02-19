"""
Notification signals - create notifications on user actions.
Community-related signals are only registered when the community app is installed.
"""
import logging
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _register_community_signals():
    """Register notification signals for community app (post votes, comments). Only when community is installed."""
    if not apps.is_installed("community"):
        return
    from community.models import Comment, CommentUpvote, PostVote
    from .services import create_notification

    @receiver(post_save, sender=PostVote)
    def notify_post_vote(sender, instance, created, **kwargs):
        if not created:
            return
        post = instance.post
        actor = instance.user
        recipient = post.author
        if instance.value == PostVote.VALUE_UP:
            verb, notification_type_code = "upvoted your post", "post_upvote"
        else:
            verb, notification_type_code = "downvoted your post", "post_downvote"
        create_notification(recipient=recipient, actor=actor, verb=verb, target=post, notification_type_code=notification_type_code)

    @receiver(post_save, sender=Comment)
    def notify_comment_created(sender, instance, created, **kwargs):
        if not created:
            return
        comment = instance
        actor = comment.author
        if comment.parent is None:
            recipient, verb = comment.post.author, "commented on your post"
            notification_type_code, target = "post_comment", comment.post
        else:
            recipient, verb = comment.parent.author, "replied to your comment"
            notification_type_code, target = "comment_reply", comment.parent
        create_notification(recipient=recipient, actor=actor, verb=verb, target=target, notification_type_code=notification_type_code)

    @receiver(post_save, sender=CommentUpvote)
    def notify_comment_upvote(sender, instance, created, **kwargs):
        if not created:
            return
        comment = instance.comment
        create_notification(
            recipient=comment.author,
            actor=instance.user,
            verb="upvoted your comment",
            target=comment,
            notification_type_code="comment_upvote",
        )


_register_community_signals()
