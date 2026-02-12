"""
Migration to add search vector field and GIN index for PostgreSQL FTS.
This migration is safe to run on SQLite (will be skipped).
"""
from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0006_remove_postupvote'),
    ]

    operations = [
        # Enable trigram extension for similarity search (PostgreSQL only)
        TrigramExtension(),
        
        # Add search_vector field (PostgreSQL only, ignored on SQLite)
        migrations.AddField(
            model_name='post',
            name='search_vector',
            field=SearchVectorField(null=True, blank=True),
        ),
        
        # Add GIN index on search_vector for fast FTS (PostgreSQL only)
        migrations.AddIndex(
            model_name='post',
            index=GinIndex(fields=['search_vector'], name='community_post_search_vector_idx'),
        ),
    ]
