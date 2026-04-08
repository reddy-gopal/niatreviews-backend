from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0002_copy_accounts_founding_profiles"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="intermediatestudentprofile",
            name="city",
        ),
        migrations.RemoveField(
            model_name="intermediatestudentprofile",
            name="grade",
        ),
        migrations.RemoveField(
            model_name="intermediatestudentprofile",
            name="school_name",
        ),
        migrations.AddField(
            model_name="intermediatestudentprofile",
            name="branch",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="intermediatestudentprofile",
            name="college_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
    ]

