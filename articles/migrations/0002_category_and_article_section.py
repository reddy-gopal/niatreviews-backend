# Category model and Article.category_id FK; seed 6 sections

from django.db import migrations, models
import django.db.models.deletion


SECTION_SEED = [
    ("The Onboarding Kit", "onboarding-kit"),
    ("Survival & Food", "survival-food"),
    ("The Club Directory", "club-directory"),
    ("Career & Wins", "career-wins"),
    ("Local Travel & Hangout Spots", "local-travel"),
    ("Amenities", "amenities"),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("articles", "Category")
    for name, slug in SECTION_SEED:
        Category.objects.get_or_create(slug=slug, defaults={"name": name})


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=80, unique=True)),
            ],
            options={
                "app_label": "articles",
                "db_table": "articles_category",
                "ordering": ["id"],
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.AddField(
            model_name="article",
            name="category_fk",
            field=models.ForeignKey(
                blank=True,
                db_column="category_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="articles.category",
            ),
        ),
        migrations.RunPython(seed_categories, noop),
    ]
