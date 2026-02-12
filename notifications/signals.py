"""
Notification signals - automatically create notifications on user actions.
Triggered by community app signals (post votes, comments, etc.)
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from community.models import PostVote, Comment, CommentUpvote
from .services import create_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PostVote)
def notify_post_vote(sender, instance, created, **kwargs):
    """Notify post author when someone votes on their post."""
    if not created:
        # Vote was updated (changed from upvote to downvote or vice versa)
        # We could handle this differently, but for now, skip
        return
    
    post = instance.post
    actor = instance.user
    recipient = post.author
    
    # Determine verb based on vote value
    if instance.value == PostVote.VALUE_UP:
        verb = "upvoted your post"
        notification_type_code = "post_upvote"
    else:
        verb = "downvoted your post"
        notification_type_code = "post_downvote"
    
    create_notification(
        recipient=recipient,
        actor=actor,
        verb=verb,
        target=post,
        notification_type_code=notification_type_code,
    )


@receiver(post_save, sender=Comment)
def notify_comment_created(sender, instance, created, **kwargs):
    """
    Notify when someone comments on a post or replies to a comment.
    - If top-level comment: notify post author
    - If reply: notify parent comment author
    """
    if not created:
        return
    
    comment = instance
    actor = comment.author
    
    if comment.parent is None:
        # Top-level comment on post
        recipient = comment.post.author
        verb = "commented on your post"
        notification_type_code = "post_comment"
        target = comment.post
    else:
        # Reply to another comment
        recipient = comment.parent.author
        verb = "replied to your comment"
        notification_type_code = "comment_reply"
        target = comment.parent
    
    create_notification(
        recipient=recipient,
        actor=actor,
        verb=verb,
        target=target,
        notification_type_code=notification_type_code,
    )


@receiver(post_save, sender=CommentUpvote)
def notify_comment_upvote(sender, instance, created, **kwargs):
    """Notify comment author when someone upvotes their comment."""
    if not created:
        return
    
    comment = instance.comment
    actor = instance.user
    recipient = comment.author
    
    create_notification(
        recipient=recipient,
        actor=actor,
        verb="upvoted your comment",
        target=comment,
        notification_type_code="comment_upvote",
    )
