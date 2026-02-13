# Senior onboarding review model

import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeniorOnboardingReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("teaching_quality", models.PositiveSmallIntegerField()),
                ("faculty_support_text", models.TextField()),
                ("faculty_support_choice", models.CharField(choices=[("very_helpful", "Very helpful"), ("average", "Average"), ("not_supportive", "Not supportive")], max_length=32)),
                ("projects_quality", models.PositiveSmallIntegerField()),
                ("best_project_or_skill", models.TextField()),
                ("learning_balance_choice", models.CharField(choices=[("practical_focused", "Practical focused"), ("balanced", "Balanced"), ("too_theoretical", "Too theoretical")], max_length=32)),
                ("placement_support", models.PositiveSmallIntegerField()),
                ("job_ready_text", models.TextField()),
                ("placement_reality_choice", models.CharField(choices=[("very_promising", "Very promising"), ("decent_needs_improvement", "Decent, needs improvement"), ("not_as_expected", "Not as expected")], max_length=32)),
                ("overall_satisfaction", models.PositiveSmallIntegerField()),
                ("one_line_experience", models.TextField()),
                ("experience_feel_choice", models.CharField(choices=[("positive", "Positive"), ("mixed", "Mixed"), ("stressful", "Stressful")], max_length=32)),
                ("recommendation_score", models.PositiveSmallIntegerField()),
                ("who_should_join_text", models.TextField()),
                ("final_recommendation_choice", models.CharField(choices=[("yes_definitely", "Yes, definitely"), ("yes_serious_students_only", "Yes, serious students only"), ("no_better_options", "No, better options elsewhere")], max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=models.CASCADE, related_name="senior_onboarding_review", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "reviews_senior_onboarding_review",
                "verbose_name": "Senior onboarding review",
                "verbose_name_plural": "Senior onboarding reviews",
            },
        ),
        migrations.AddConstraint(model_name="senioronboardingreview", constraint=models.CheckConstraint(check=models.Q(teaching_quality__gte=1, teaching_quality__lte=5), name="onb_teaching_1_5")),
        migrations.AddConstraint(model_name="senioronboardingreview", constraint=models.CheckConstraint(check=models.Q(projects_quality__gte=1, projects_quality__lte=5), name="onb_projects_1_5")),
        migrations.AddConstraint(model_name="senioronboardingreview", constraint=models.CheckConstraint(check=models.Q(placement_support__gte=1, placement_support__lte=5), name="onb_placement_1_5")),
        migrations.AddConstraint(model_name="senioronboardingreview", constraint=models.CheckConstraint(check=models.Q(overall_satisfaction__gte=1, overall_satisfaction__lte=5), name="onb_overall_1_5")),
        migrations.AddConstraint(model_name="senioronboardingreview", constraint=models.CheckConstraint(check=models.Q(recommendation_score__gte=1, recommendation_score__lte=5), name="onb_recommend_1_5")),
    ]
