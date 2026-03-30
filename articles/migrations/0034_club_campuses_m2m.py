from django.db import migrations, models
from django.utils.text import slugify


def backfill_club_campuses(apps, schema_editor):
    Club = apps.get_model("articles", "Club")
    for club in Club.objects.all().iterator():
        campus_id = getattr(club, "campus_id", None)
        if campus_id:
            club.campuses.add(campus_id)


def make_slugs_globally_unique(apps, schema_editor):
    Club = apps.get_model("articles", "Club")
    seen = set()
    for club in Club.objects.all().order_by("id").iterator():
        base = slugify(club.slug or club.name or f"club-{club.id}")[:120] or f"club-{club.id}"
        candidate = base
        i = 2
        while candidate in seen:
            suffix = f"-{i}"
            candidate = f"{base[:120 - len(suffix)]}{suffix}"
            i += 1
        if club.slug != candidate:
            club.slug = candidate
            club.save(update_fields=["slug"])
        seen.add(candidate)


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0033_article_ai_generated"),
    ]

    operations = [
        migrations.AddField(
            model_name="club",
            name="campuses",
            field=models.ManyToManyField(blank=True, related_name="clubs", to="campuses.campus"),
        ),
        migrations.RunPython(backfill_club_campuses, migrations.RunPython.noop),
        migrations.RunPython(make_slugs_globally_unique, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="club",
            name="articles_club_campus_slug_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="club",
            name="articles_club_campus_name_uniq",
        ),
        migrations.RemoveIndex(
            model_name="club",
            name="art_club_campus_active_idx",
        ),
        migrations.AlterModelOptions(
            name="club",
            options={"ordering": ["name"]},
        ),
        migrations.AlterField(
            model_name="club",
            name="slug",
            field=models.SlugField(max_length=120, unique=True),
        ),
    ]

