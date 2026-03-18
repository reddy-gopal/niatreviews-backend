from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campuses", "0005_alter_campus_id"),
        ("articles", "0026_article_ai_confident_score_article_ai_feedback_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Club",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(max_length=120)),
                ("type", models.CharField(choices=[("Coding", "Coding"), ("Cultural", "Cultural"), ("Sports", "Sports"), ("Literary", "Literary"), ("Robotics", "Robotics"), ("Social", "Social"), ("Music", "Music"), ("Dance", "Dance"), ("NIAT Circle", "NIAT Circle")], db_index=True, max_length=40)),
                ("about", models.TextField(blank=True)),
                ("activities", models.TextField(blank=True)),
                ("achievements", models.TextField(blank=True)),
                ("open_to_all", models.BooleanField(default=True)),
                ("how_to_join", models.TextField(blank=True)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("instagram", models.CharField(blank=True, max_length=120)),
                ("founded_year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("member_count", models.PositiveIntegerField(default=0)),
                ("logo_url", models.URLField(blank=True)),
                ("cover_image", models.URLField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("verified_at", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "campus",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="clubs",
                        to="campuses.campus",
                    ),
                ),
            ],
            options={
                "db_table": "articles_club",
                "ordering": ["campus", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="club",
            index=models.Index(fields=["campus", "is_active"], name="art_club_campus_active_idx"),
        ),
        migrations.AddIndex(
            model_name="club",
            index=models.Index(fields=["type", "is_active"], name="art_club_type_active_idx"),
        ),
        migrations.AddConstraint(
            model_name="club",
            constraint=models.UniqueConstraint(fields=("campus", "slug"), name="articles_club_campus_slug_uniq"),
        ),
        migrations.AddConstraint(
            model_name="club",
            constraint=models.UniqueConstraint(fields=("campus", "name"), name="articles_club_campus_name_uniq"),
        ),
        migrations.AlterField(
            model_name="article",
            name="club_id",
            field=models.ForeignKey(blank=True, db_column="club_id", null=True, on_delete=models.deletion.SET_NULL, related_name="articles", to="articles.club"),
        ),
    ]
