# Subcategory model: scalable, admin-managed subcategories per category

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0004_article_images"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subcategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80)),
                ("label", models.CharField(help_text="Display name", max_length=120)),
                (
                    "requires_other",
                    models.BooleanField(
                        default=False,
                        help_text="If True, subcategory_other is required (e.g. 'Others' with custom name)",
                    ),
                ),
                (
                    "display_order",
                    models.PositiveSmallIntegerField(default=0, help_text="Order in lists (lower first)"),
                ),
                (
                    "category",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="articles.category",
                    ),
                ),
            ],
            options={
                "ordering": ["category", "display_order", "slug"],
                "db_table": "articles_subcategory",
                "verbose_name_plural": "Subcategories",
            },
        ),
        migrations.AddConstraint(
            model_name="subcategory",
            constraint=models.UniqueConstraint(fields=("category", "slug"), name="articles_subcategory_category_slug_uniq"),
        ),
    ]
