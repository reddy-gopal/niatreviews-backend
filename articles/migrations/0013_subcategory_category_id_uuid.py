# Step 3 for Category — Subcategory: add category_id_new, backfill, drop old FK, rename, add FK to Category.id_new

import django.db.models.deletion
from django.db import migrations, models


def backfill_subcategory_category_uuid(apps, schema_editor):
    Category = apps.get_model("articles", "Category")
    Subcategory = apps.get_model("articles", "Subcategory")
    mapping = {c.id: c.id_new for c in Category.objects.all()}
    for sub in Subcategory.objects.all():
        old_id = sub.category_id
        if old_id in mapping:
            sub.category_id_new = mapping[old_id]
            sub.save(update_fields=["category_id_new"])
    null_new = Subcategory.objects.filter(category_id_new__isnull=True)
    assert null_new.count() == 0, "Subcategory: some rows have NULL category_id_new"


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0012_category_backfill_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="subcategory",
            name="category_id_new",
            field=models.UUIDField(db_column="category_id_new", null=True),
        ),
        migrations.RunPython(backfill_subcategory_category_uuid, noop),
        # Drop unique_together before RemoveField so SQLite table remake doesn't reference "category"
        migrations.AlterUniqueTogether(
            name="subcategory",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="subcategory",
            name="category",
        ),
        migrations.RenameField(
            model_name="subcategory",
            old_name="category_id_new",
            new_name="category",
        ),
        migrations.AlterField(
            model_name="subcategory",
            name="category",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subcategories",
                to="articles.category",
                to_field="id_new",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="subcategory",
            unique_together={("category", "slug")},
        ),
    ]
