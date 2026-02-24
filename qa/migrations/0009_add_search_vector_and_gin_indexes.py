# Generated for PostgreSQL full-text search (search_vector + GinIndexes).

from django.db import migrations
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Migration(migrations.Migration):

    dependencies = [
        ("qa", "0008_multiple_answers_per_question"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="search_vector",
            field=SearchVectorField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="question",
            index=GinIndex(fields=["search_vector"], name="question_search_vector_gin_idx"),
        ),
        migrations.AddIndex(
            model_name="question",
            index=GinIndex(
                fields=["title"],
                name="question_title_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
