"""Senior onboarding URLs. Mount at api/senior/."""

from django.urls import path
from .onboarding_views import OnboardingStatusView, OnboardingReviewSubmitView

urlpatterns = [
    path("onboarding/status/", OnboardingStatusView.as_view(), name="senior-onboarding-status"),
    path("onboarding/review/", OnboardingReviewSubmitView.as_view(), name="senior-onboarding-review-submit"),
]
