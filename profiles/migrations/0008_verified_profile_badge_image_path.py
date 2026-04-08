from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0007_rename_verified_profile_model_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="verifiedniatstudentprofile",
            name="badge_image_path",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
