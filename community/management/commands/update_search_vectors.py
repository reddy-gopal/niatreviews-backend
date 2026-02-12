"""
Management command to update search vectors for all posts.
Run this after bulk imports or when switching to PostgreSQL.

Usage:
    python manage.py update_search_vectors
"""
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from django.db import connection
from community.models import Post


class Command(BaseCommand):
    help = "Update search vectors for all posts (PostgreSQL only)"

    def handle(self, *args, **options):
        if "postgresql" not in connection.settings_dict["ENGINE"]:
            self.stdout.write(
                self.style.WARNING(
                    "This command requires PostgreSQL. Current database is not PostgreSQL."
                )
            )
            return

        self.stdout.write("Updating search vectors for all posts...")
        
        # Update search vectors in batches
        batch_size = 500
        total = Post.objects.count()
        updated = 0
        
        for i in range(0, total, batch_size):
            posts = Post.objects.all()[i:i + batch_size]
            for post in posts:
                post.search_vector = (
                    SearchVector("title", weight="A") +
                    SearchVector("description", weight="B")
                )
            
            Post.objects.bulk_update(posts, ["search_vector"], batch_size=batch_size)
            updated += len(posts)
            self.stdout.write(f"Updated {updated}/{total} posts...")
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {updated} post search vectors")
        )
