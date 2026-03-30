from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0034_club_campuses_m2m"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="club",
            name="campus",
        ),
    ]

