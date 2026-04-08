import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0006_intermediate_branch_choices"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="FoundingEditorProfile",
            new_name="VerifiedNiatStudentProfile",
        ),
        migrations.AlterModelTable(
            name="verifiedniatstudentprofile",
            table="profiles_verified_niat_student_profile",
        ),
        migrations.AlterField(
            model_name="verifiedniatstudentprofile",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_niat_profiles",
                to="campuses.campus",
            ),
        ),
        migrations.AlterField(
            model_name="verifiedniatstudentprofile",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="verified_niat_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
