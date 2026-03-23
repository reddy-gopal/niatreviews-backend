from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0032_alter_subcategory_options_article_meta_description_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="ai_generated",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
