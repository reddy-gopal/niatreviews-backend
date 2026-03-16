# Point campus_id FK to Campus's primary key (id) now that Campus uses UUID PK.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_founding_editor_profile_campus_uuid"),
        ("campuses", "0004_campus_uuid_primary_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="foundingeditorprofile",
            name="campus_id",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                help_text="Default campus for articles; matches campus list in frontend.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="founding_editors",
                to="campuses.campus",
            ),
        ),
    ]
