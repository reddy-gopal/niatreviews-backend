"""Tests for magic login and senior onboarding flow."""

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from verification.models import SeniorProfile, MagicLoginToken
from reviews.models import SeniorOnboardingReview
from reviews.onboarding_views import OnboardingStatusView, OnboardingReviewSubmitView
from reviews.serializers import SeniorOnboardingReviewSerializer


def _valid_payload():
    return {
        "teaching_quality": 4,
        "faculty_support_text": "Faculty were very supportive and approachable.",
        "faculty_support_choice": "very_helpful",
        "projects_quality": 5,
        "best_project_or_skill": "Built a full-stack project with React and Django.",
        "learning_balance_choice": "balanced",
        "placement_support": 4,
        "job_ready_text": "Placement cell provided good training and mock interviews.",
        "placement_reality_choice": "very_promising",
        "overall_satisfaction": 4,
        "one_line_experience": "Challenging but rewarding; great peer and faculty support.",
        "experience_feel_choice": "positive",
        "recommendation_score": 5,
        "who_should_join_text": "Serious students who want hands-on technical exposure.",
        "final_recommendation_choice": "yes_definitely",
        "linkedin_profile_url": "https://www.linkedin.com/in/testprofile",
    }


class MagicLoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="senior1", email="s@example.com", password="x", role="senior")
        self.profile = SeniorProfile.objects.create(user=self.user, status="approved", proof_summary="Ok")

    def test_magic_login_success_redirects_to_onboarding(self):
        ml = MagicLoginToken.objects.create(user=self.user, expires_at=timezone.now() + timedelta(minutes=30))
        r = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        self.assertEqual(r.data["redirect"], "/onboarding/review")
        ml.refresh_from_db()
        self.assertFalse(ml.is_used)  # Token stays valid until account setup (set password)

    def test_magic_login_after_onboarding_redirects_to_community(self):
        self.profile.review_submitted = True
        self.profile.save()
        ml = MagicLoginToken.objects.create(user=self.user, expires_at=timezone.now() + timedelta(minutes=30))
        r = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["redirect"], "/")

    def test_magic_login_expired_returns_400(self):
        ml = MagicLoginToken.objects.create(user=self.user, expires_at=timezone.now() - timedelta(minutes=1))
        r = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", r.data["detail"].lower())

    def test_magic_login_works_multiple_times_until_setup(self):
        ml = MagicLoginToken.objects.create(user=self.user, expires_at=timezone.now() + timedelta(hours=48))
        r1 = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        r2 = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        ml.refresh_from_db()
        self.assertFalse(ml.is_used)

    def test_magic_login_after_setup_returns_400(self):
        self.user.set_password("newpass")
        self.user.save(update_fields=["password"])
        ml = MagicLoginToken.objects.create(user=self.user, expires_at=timezone.now() + timedelta(hours=48))
        # Simulate setup completion: mark tokens used (as MeView does after set_password)
        MagicLoginToken.objects.filter(user=self.user).update(is_used=True)
        r = self.client.get(reverse("magic-login"), {"token": str(ml.token)})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been used", r.data["detail"].lower())

    def test_magic_login_invalid_token_returns_404(self):
        r = self.client.get(reverse("magic-login"), {"token": "00000000-0000-0000-0000-000000000000"})
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class OnboardingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="senior1", email="s@example.com", password="x", role="senior")
        self.profile = SeniorProfile.objects.create(user=self.user, status="approved", proof_summary="Ok")

    def test_status_not_submitted(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get(reverse("senior-onboarding-status"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.data["review_submitted"])

    def test_submit_success(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.post(reverse("senior-onboarding-review-submit"), _valid_payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.review_submitted)
        self.assertTrue(self.profile.onboarding_completed)
        self.assertTrue(SeniorOnboardingReview.objects.filter(user=self.user).exists())

    def test_submit_duplicate_400(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("senior-onboarding-review-submit"), _valid_payload(), format="json")
        r = self.client.post(reverse("senior-onboarding-review-submit"), _valid_payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_requires_approved_senior(self):
        other = User.objects.create_user(username="student1", email="x@example.com", password="x", role="student")
        self.client.force_authenticate(user=other)
        r = self.client.post(reverse("senior-onboarding-review-submit"), _valid_payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
