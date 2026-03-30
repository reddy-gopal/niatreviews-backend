from django.db import migrations, models


def copy_about_to_objective(apps, schema_editor):
    Club = apps.get_model("articles", "Club")
    for club in Club.objects.all():
        about = getattr(club, "about", "") or ""
        if about and not getattr(club, "objective", ""):
            club.objective = about
            club.save(update_fields=["objective"])


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0036_clubcampus_through_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="club",
            name="objective",
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(copy_about_to_objective, migrations.RunPython.noop),
        migrations.AddField(
            model_name="clubcampus",
            name="instagram",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="clubcampus",
            name="linkedin",
            field=models.URLField(blank=True),
        ),
        migrations.RemoveField(
            model_name="club",
            name="about",
        ),
        migrations.RemoveField(
            model_name="club",
            name="achievements",
        ),
        migrations.RemoveField(
            model_name="club",
            name="activities",
        ),
        migrations.RemoveField(
            model_name="club",
            name="founded_year",
        ),
        migrations.RemoveField(
            model_name="club",
            name="how_to_join",
        ),
        migrations.RemoveField(
            model_name="club",
            name="instagram",
        ),
        migrations.RemoveField(
            model_name="club",
            name="type",
        ),
        migrations.RemoveField(
            model_name="club",
            name="verified_at",
        ),
        migrations.SeparateDatabaseAndState(
            # Some DB states (especially SQLite dev DBs) may not have this index
            # physically present even though migration state includes it.
            # Keep state aligned without executing a failing DROP INDEX.
            database_operations=[],
            state_operations=[
                migrations.RemoveIndex(
                    model_name="club",
                    name="art_club_type_active_idx",
                ),
            ],
        ),
    ]

