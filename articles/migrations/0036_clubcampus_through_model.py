from django.db import migrations, models


def backfill_club_chapters(apps, schema_editor):
    Club = apps.get_model("articles", "Club")
    ClubCampus = apps.get_model("articles", "ClubCampus")
    for club in Club.objects.all().iterator():
        campuses = list(club.campuses.all())
        for campus in campuses:
            ClubCampus.objects.get_or_create(
                club=club,
                campus=campus,
                defaults={
                    "member_count": getattr(club, "member_count", 0) or 0,
                    "open_to_all": getattr(club, "open_to_all", True),
                    "chapter_description": getattr(club, "about", "") or "",
                    "contact_email": getattr(club, "email", "") or "",
                    "is_active": getattr(club, "is_active", True),
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0035_remove_club_campus_fk"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClubCampus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("member_count", models.PositiveIntegerField(default=0)),
                ("open_to_all", models.BooleanField(default=True)),
                ("president_name", models.CharField(blank=True, max_length=255)),
                ("president_email", models.EmailField(blank=True, max_length=254)),
                ("president_photo", models.ImageField(blank=True, null=True, upload_to="club_leaders/")),
                ("vice_president_name", models.CharField(blank=True, max_length=255)),
                ("vice_president_email", models.EmailField(blank=True, max_length=254)),
                ("vice_president_photo", models.ImageField(blank=True, null=True, upload_to="club_leaders/")),
                ("chapter_description", models.TextField(blank=True)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campus", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="club_chapters", to="campuses.campus")),
                ("club", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="campus_chapters", to="articles.club")),
            ],
            options={
                "db_table": "articles_club_campus",
                "ordering": ["club__name"],
                "unique_together": {("club", "campus")},
            },
        ),
        migrations.RunPython(backfill_club_chapters, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            # Changing M2M `through` cannot be emitted as a DB ALTER by Django.
            # We keep DB ops as-is and only update migration state so future
            # migrations/models know `club.campuses` uses ClubCampus.
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="club",
                    name="campuses",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="clubs",
                        through="articles.ClubCampus",
                        to="campuses.campus",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="club",
            name="member_count",
        ),
        migrations.RemoveField(
            model_name="club",
            name="open_to_all",
        ),
        migrations.RemoveField(
            model_name="club",
            name="email",
        ),
    ]

