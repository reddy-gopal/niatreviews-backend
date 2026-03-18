import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("campuses", "0005_alter_campus_id"),
        ("articles", "0028_backfill_article_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="subcategory",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subcategories",
                to="campuses.campus",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="subcategory",
            unique_together={("category", "campus", "slug")},
        ),
        migrations.AddIndex(
            model_name="article",
            index=models.Index(
                fields=["campus_id", "category", "subcategory", "status"],
                name="art_camp_cat_sub_st_idx",
            ),
        ),
    ]

