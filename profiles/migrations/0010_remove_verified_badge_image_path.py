from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0009_sync_niat_verified_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="verifiedniatstudentprofile",
            name="badge_image_path",
        ),
    ]

