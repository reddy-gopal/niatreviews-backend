# Generated migration for Post.slug

from django.db import migrations, models


def slugify_title(title):
    """Convert title to a URL-safe slug."""
    import re
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s[:300] or "post"


def populate_post_slugs(apps, schema_editor):
    Post = apps.get_model("community", "Post")
    used = set()
    for post in Post.objects.all():
        base = slugify_title(post.title)
        slug = base
        i = 0
        while slug in used:
            i += 1
            slug = f"{base}-{i}" if len(base) < 290 else f"{base[:290]}-{i}"
        used.add(slug)
        post.slug = slug
        post.save(update_fields=["slug"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0002_alter_category_options_remove_category_order_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="slug",
            field=models.SlugField(db_index=True, max_length=300, null=True, unique=True),
        ),
        migrations.RunPython(populate_post_slugs, noop),
        migrations.AlterField(
            model_name="post",
            name="slug",
            field=models.SlugField(db_index=True, max_length=300, unique=True),
        ),
    ]
