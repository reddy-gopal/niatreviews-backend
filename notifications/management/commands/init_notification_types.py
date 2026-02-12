"""
Management command to initialize notification types.
Run: python manage.py init_notification_types
"""
from django.core.management.base import BaseCommand
from notifications.models import NotificationType


class Command(BaseCommand):
    help = "Initialize notification types in the database"

    def handle(self, *args, **options):
        notification_types = [
            {
                "code": "post_upvote",
                "name": "Post Upvote",
                "description": "Someone upvoted your post",
            },
            {
                "code": "post_downvote",
                "name": "Post Downvote",
                "description": "Someone downvoted your post",
            },
            {
                "code": "post_comment",
                "name": "Post Comment",
                "description": "Someone commented on your post",
            },
            {
                "code": "comment_upvote",
                "name": "Comment Upvote",
                "description": "Someone upvoted your comment",
            },
            {
                "code": "comment_reply",
                "name": "Comment Reply",
                "description": "Someone replied to your comment",
            },
        ]

        created_count = 0
        updated_count = 0

        for nt_data in notification_types:
            nt, created = NotificationType.objects.update_or_create(
                code=nt_data["code"],
                defaults={
                    "name": nt_data["name"],
                    "description": nt_data["description"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created notification type: {nt.code}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated notification type: {nt.code}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created: {created_count}, Updated: {updated_count}"
            )
        )
