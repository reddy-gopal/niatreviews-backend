import uuid
from django.db import migrations
from django.utils.text import slugify


def backfill_article_slugs(apps, schema_editor):
    Article = apps.get_model("articles", "Article")
    queryset = Article.objects.all().only("id", "title", "slug")
    for article in queryset.iterator():
        current_slug = (article.slug or "").strip()
        if current_slug:
            continue
        base = slugify(article.title or "article")[:500] or "article"
        slug = f"{base}-{uuid.uuid4().hex[:8]}"
        while Article.objects.filter(slug=slug).exclude(pk=article.pk).exists():
            slug = f"{base}-{uuid.uuid4().hex[:8]}"
        article.slug = slug
        article.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0027_club_and_article_club_fk"),
    ]

    operations = [
        migrations.RunPython(backfill_article_slugs, migrations.RunPython.noop),
    ]

