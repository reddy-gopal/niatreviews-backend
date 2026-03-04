# Generated manually for Campus directory

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Campus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("short_name", models.CharField(blank=True, max_length=100, null=True)),
                ("location", models.CharField(max_length=200)),
                ("state", models.CharField(max_length=100)),
                ("image_url", models.URLField(max_length=500)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("is_deemed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "campuses",
                "ordering": ["name"],
                "verbose_name_plural": "Campuses",
            },
        ),
    ]
