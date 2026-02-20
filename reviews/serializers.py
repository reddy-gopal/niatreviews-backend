# reviews API serializers

import re
from rest_framework import serializers

from .models import SeniorOnboardingReview
from .onboarding_constants import (
    ONBOARDING_TEXT_MIN_LENGTH,
    RATING_MIN,
    RATING_MAX,
    FACULTY_SUPPORT_VALUES,
    LEARNING_BALANCE_VALUES,
    PLACEMENT_REALITY_VALUES,
    EXPERIENCE_FEEL_VALUES,
    FINAL_RECOMMENDATION_VALUES,
)


def _validate_rating(value, field_name):
    if value is None:
        raise serializers.ValidationError({field_name: "This field is required."})
    if not (RATING_MIN <= value <= RATING_MAX):
        raise serializers.ValidationError({field_name: f"Must be between {RATING_MIN} and {RATING_MAX}."})
    return value


def _validate_text(value, field_name, min_len=ONBOARDING_TEXT_MIN_LENGTH):
    if not value or not str(value).strip():
        raise serializers.ValidationError({field_name: "This field is required."})
    if len(str(value).strip()) < min_len:
        raise serializers.ValidationError({field_name: f"Must be at least {min_len} characters."})
    return value.strip()


def _validate_choice(value, field_name, allowed):
    if not value or value not in allowed:
        raise serializers.ValidationError({field_name: f"Must be one of: {', '.join(allowed)}."})
    return value


# LinkedIn profile URL: must be https?://...(www.)?linkedin.com/in/<slug>/...
LINKEDIN_PROFILE_RE = re.compile(
    r"^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?",
    re.IGNORECASE,
)


def _validate_linkedin_url(value, field_name="linkedin_profile_url"):
    if not value or not str(value).strip():
        raise serializers.ValidationError({field_name: "This field is required."})
    url = str(value).strip()
    if not LINKEDIN_PROFILE_RE.match(url):
        raise serializers.ValidationError(
            {field_name: "Enter a valid LinkedIn profile URL (e.g. https://linkedin.com/in/yourprofile)"}
        )
    return url


class SeniorOnboardingReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeniorOnboardingReview
        fields = [
            "teaching_quality", "faculty_support_text", "faculty_support_choice",
            "projects_quality", "best_project_or_skill", "learning_balance_choice",
            "placement_support", "job_ready_text", "placement_reality_choice",
            "overall_satisfaction", "one_line_experience", "experience_feel_choice",
            "recommendation_score", "who_should_join_text", "final_recommendation_choice",
            "linkedin_profile_url",
        ]

    def validate_teaching_quality(self, v): return _validate_rating(v, "teaching_quality")
    def validate_faculty_support_text(self, v): return _validate_text(v, "faculty_support_text")
    def validate_faculty_support_choice(self, v): return _validate_choice(v, "faculty_support_choice", FACULTY_SUPPORT_VALUES)
    def validate_projects_quality(self, v): return _validate_rating(v, "projects_quality")
    def validate_best_project_or_skill(self, v): return _validate_text(v, "best_project_or_skill")
    def validate_learning_balance_choice(self, v): return _validate_choice(v, "learning_balance_choice", LEARNING_BALANCE_VALUES)
    def validate_placement_support(self, v): return _validate_rating(v, "placement_support")
    def validate_job_ready_text(self, v): return _validate_text(v, "job_ready_text")
    def validate_placement_reality_choice(self, v): return _validate_choice(v, "placement_reality_choice", PLACEMENT_REALITY_VALUES)
    def validate_overall_satisfaction(self, v): return _validate_rating(v, "overall_satisfaction")
    def validate_one_line_experience(self, v): return _validate_text(v, "one_line_experience")
    def validate_experience_feel_choice(self, v): return _validate_choice(v, "experience_feel_choice", EXPERIENCE_FEEL_VALUES)
    def validate_recommendation_score(self, v): return _validate_rating(v, "recommendation_score")
    def validate_who_should_join_text(self, v): return _validate_text(v, "who_should_join_text")
    def validate_final_recommendation_choice(self, v): return _validate_choice(v, "final_recommendation_choice", FINAL_RECOMMENDATION_VALUES)
    def validate_linkedin_profile_url(self, v): return _validate_linkedin_url(v)
