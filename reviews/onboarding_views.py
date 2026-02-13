"""Senior onboarding review API (main app only)."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from verification.models import SeniorProfile
from .models import SeniorOnboardingReview
from .permissions import IsApprovedSenior
from .serializers import SeniorOnboardingReviewSerializer


class OnboardingStatusView(APIView):
    """GET /api/senior/onboarding/status/ — returns review_submitted for current senior."""

    permission_classes = [IsApprovedSenior]

    def get(self, request):
        profile = request.user.senior_profile
        submitted = SeniorOnboardingReview.objects.filter(user=request.user).exists()
        return Response({
            "review_submitted": submitted,
            "onboarding_completed": profile.onboarding_completed,
        })


class OnboardingReviewSubmitView(APIView):
    """POST /api/senior/onboarding/review/ — create onboarding review, set flags on SeniorProfile."""

    permission_classes = [IsApprovedSenior]

    def post(self, request):
        if SeniorOnboardingReview.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "You have already submitted your onboarding review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SeniorOnboardingReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        profile = request.user.senior_profile
        profile.review_submitted = True
        profile.onboarding_completed = True
        profile.save(update_fields=["review_submitted", "onboarding_completed", "updated_at"])
        return Response(
            {"status": "submitted"},
            status=status.HTTP_201_CREATED,
        )
