from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("articles", "0029_subcategory_campus_and_article_indexes"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="article",
            name="club_id",
        ),
    ]

