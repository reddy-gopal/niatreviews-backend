"""Magic login (passwordless) for approved seniors."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import MagicLoginToken


class MagicLoginView(APIView):
    """
    GET /api/auth/magic-login/?token=<uuid>
    Validates token, ensures senior is approved, returns JWT + redirect path.
    The token can be used multiple times (e.g. open link, come back, use again)
    and always redirects to setup if password not set. It is invalidated only
    after the user successfully completes account setup (sets password).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        token_value = request.query_params.get("token")
        if not token_value:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ml = MagicLoginToken.objects.get(token=token_value)
        except MagicLoginToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or expired link."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if ml.is_used:
            return Response(
                {"detail": "This link has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ml.is_expired:
            return Response(
                {"detail": "This link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = ml.user
        if not hasattr(user, "senior_profile"):
            return Response(
                {"detail": "Invalid account."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user.senior_profile.status != "approved":
            return Response(
                {"detail": "Your senior account is not yet approved."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Token is not marked used here; it stays valid until they complete account setup (set password).
        refresh = RefreshToken.for_user(user)
        needs_password_set = not user.has_usable_password()
        if needs_password_set:
            redirect = "/auth/setup"
        elif not user.senior_profile.review_submitted:
            redirect = "/onboarding/review"
        else:
            redirect = "/"
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "redirect": redirect,
            "needs_password_set": needs_password_set,
        })