"""
Senior follow/unfollow API. Only verified seniors can be followed.
List verified seniors for directory (GET /api/seniors/).
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from accounts.serializers import PublicProfileSerializer
from .models import SeniorFollow, SeniorProfile

User = get_user_model()


def error_response(code: str, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    return Response({"code": code, "detail": detail}, status=status_code)


class SeniorListView(APIView):
    """GET: list verified seniors for directory. Optional ?search= filters by username."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = User.objects.filter(is_verified_senior=True, is_active=True).order_by("username")
        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(username__icontains=search)
        serializer = PublicProfileSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class SeniorFollowView(APIView):
    """POST to follow, DELETE to unfollow. Senior is identified by user id (UUID)."""
    permission_classes = [IsAuthenticated]

    def _get_senior_profile(self, senior_id):
        try:
            senior = User.objects.get(pk=senior_id)
        except User.DoesNotExist:
            return None, None
        if not getattr(senior, "is_verified_senior", False):
            return senior, None
        try:
            profile = senior.senior_profile
        except SeniorProfile.DoesNotExist:
            return senior, None
        return senior, profile

    def post(self, request, id):
        senior_id = id
        if str(request.user.id) == str(senior_id):
            return error_response("VALIDATION_ERROR", "You cannot follow yourself.")
        if getattr(request.user, "is_verified_senior", False):
            return Response(
                {"code": "SENIOR_CANNOT_FOLLOW", "detail": "Only prospective students can follow seniors."},
                status=status.HTTP_403_FORBIDDEN,
            )
        senior, profile = self._get_senior_profile(senior_id)
        if senior is None:
            return error_response("NOT_FOUND", "User not found.", status.HTTP_404_NOT_FOUND)
        if not getattr(senior, "is_verified_senior", False):
            return error_response("NOT_VERIFIED", "You can only follow verified seniors.")
        _, created = SeniorFollow.objects.get_or_create(
            follower=request.user,
            senior=senior,
        )
        if not created:
            pass  # already following; still return followed: true and current count
        try:
            profile = senior.senior_profile
            count = profile.follower_count
        except SeniorProfile.DoesNotExist:
            count = SeniorFollow.objects.filter(senior=senior).count()
        return Response({"followed": True, "follower_count": count})

    def delete(self, request, id):
        senior_id = id
        SeniorFollow.objects.filter(
            follower=request.user,
            senior_id=senior_id,
        ).delete()
        try:
            senior = User.objects.get(pk=senior_id)
            profile = senior.senior_profile
            count = profile.follower_count
        except (User.DoesNotExist, SeniorProfile.DoesNotExist):
            count = 0
        return Response({"followed": False, "follower_count": count})
