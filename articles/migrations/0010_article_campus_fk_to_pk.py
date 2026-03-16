# Point Article.campus_id FK to Campus's primary key (id) now that Campus uses UUID PK.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0009_article_campus_id_uuid"),
        ("campuses", "0004_campus_uuid_primary_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="campus_id",
            field=models.ForeignKey(
                blank=True,
                db_column="campus_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="campuses.campus",
            ),
        ),
    ]
