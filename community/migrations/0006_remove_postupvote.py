# Remove deprecated PostUpvote model; PostVote is the source of truth

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0005_migrate_postupvote_to_postvote"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PostUpvote",
        ),
    ]
