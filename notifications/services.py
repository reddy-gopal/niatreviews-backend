"""
Notification service layer - handles notification creation logic.
Centralizes business rules: deduplication, no self-notifications, etc.
"""
import logging
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


def create_notification(
    recipient,
    actor,
    verb,
    target=None,
    notification_type_code=None,
):
    """
    Create a notification with business rules applied.
    
    Args:
        recipient: User who receives the notification
        actor: User who performed the action
        verb: Action description (e.g., "upvoted your post")
        target: The object being acted upon (Post, Comment, etc.)
        notification_type_code: Optional NotificationType code
    
    Returns:
        Notification instance or None if not created
    """
    # Rule 1: No self-notifications
    if recipient == actor:
        logger.debug(f"Skipping self-notification: {actor} -> {verb}")
        return None
    
    # Rule 2: Check for duplicate recent notifications (within 5 minutes)
    recent_cutoff = timezone.now() - timedelta(minutes=5)
    content_type = ContentType.objects.get_for_model(target) if target else None
    object_id = target.id if target else None
    
    duplicate = Notification.objects.filter(
        recipient=recipient,
        actor=actor,
        verb=verb,
        content_type=content_type,
        object_id=object_id,
        created_at__gte=recent_cutoff,
    ).exists()
    
    if duplicate:
        logger.debug(f"Skipping duplicate notification: {actor} -> {recipient} ({verb})")
        return None
    
    # Get notification type if code provided
    notification_type = None
    if notification_type_code:
        notification_type = NotificationType.objects.filter(code=notification_type_code).first()
    
    # Create notification
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        notification_type=notification_type,
        content_type=content_type,
        object_id=object_id,
    )
    
    logger.info(f"Created notification: {actor.username} -> {recipient.username} ({verb})")
    return notification


def mark_notification_read(notification_id, user):
    """Mark a notification as read if it belongs to the user."""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
            return True
        return False
    except Notification.DoesNotExist:
        return False


def mark_all_notifications_read(user):
    """Mark all unread notifications as read for a user."""
    count = Notification.objects.filter(
        recipient=user,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    return count


def get_unread_count(user):
    """Get count of unread notifications for a user."""
    return Notification.objects.filter(
        recipient=user,
        read_at__isnull=True,
    ).count()


def cleanup_old_notifications(days=90):
    """Delete notifications older than specified days. Run as periodic task."""
    cutoff = timezone.now() - timedelta(days=days)
    count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info(f"Deleted {count} notifications older than {days} days")
    return count
