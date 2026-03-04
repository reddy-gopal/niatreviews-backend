# Seed default subcategories for club-directory and amenities

from django.db import migrations


def seed_subcategories(apps, schema_editor):
    Category = apps.get_model("articles", "Category")
    Subcategory = apps.get_model("articles", "Subcategory")

    club_dir = Category.objects.filter(slug="club-directory").first()
    if club_dir:
        for order, (slug, label) in enumerate(
            [
                ("media-club", "Media Club"),
                ("coding-club", "Coding Club"),
                ("design-club", "Design Club"),
                ("robotics-club", "Robotics Club"),
                ("sports-club", "Sports Club"),
                ("cultural-club", "Cultural Club"),
                ("others", "Others"),
            ]
        ):
            Subcategory.objects.get_or_create(
                category=club_dir,
                slug=slug,
                defaults={"label": label, "requires_other": slug == "others", "display_order": order},
            )

    amenities = Category.objects.filter(slug="amenities").first()
    if amenities:
        for order, (slug, label) in enumerate(
            [
                ("library", "Library"),
                ("sports-and-ground", "Sports and Ground"),
                ("cafeteria", "Cafeteria"),
                ("labs", "Labs"),
                ("hostel", "Hostel"),
                ("transport", "Transport"),
                ("others", "Others"),
            ]
        ):
            Subcategory.objects.get_or_create(
                category=amenities,
                slug=slug,
                defaults={"label": label, "requires_other": slug == "others", "display_order": order},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0005_subcategory"),
    ]

    operations = [
        migrations.RunPython(seed_subcategories, noop),
    ]
