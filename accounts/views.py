from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import ProfileSerializer, PublicProfileSerializer, SeniorsSetupSerializer
from verification.models import MagicLoginToken

User = get_user_model()


class RegisterView(APIView):
    """Prospective students: phone required (verified via OTP on frontend), email optional."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        email = (request.data.get("email") or "").strip() or None
        password = request.data.get("password", "")
        if not username or not phone or not password:
            return Response(
                {"detail": "Username, phone and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"username": "A user with that username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(phone_number=phone).exists():
            return Response(
                {"phone": "A user with that phone number already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email and User.objects.filter(email__iexact=email).exists():
            return Response(
                {"email": "A user with that email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(
            username=username,
            email=email or None,
            password=password,
        )
        user.phone_number = phone
        user.phone_verified = True  # Frontend verified via OTP before submit
        if not email:
            user.email = None  # Keep email null when not provided
        user.save(update_fields=["phone_number", "phone_verified", "email"])
        return Response(
            {"id": str(user.id), "username": user.username, "email": user.email or "", "phone": user.phone_number},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """GET and PATCH current user profile. Requires authentication."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        data = dict(serializer.data)
        data["needs_password_set"] = not request.user.has_usable_password()
        return Response(data)

    def patch(self, request):
        user = request.user
        # First-time setup: allow setting username and password when no usable password
        if not user.has_usable_password():
            setup = SeniorsSetupSerializer(data=request.data, context={"user": user})
            if setup.is_valid():
                if setup.validated_data.get("username"):
                    user.username = setup.validated_data["username"].strip()
                user.set_password(setup.validated_data["password"])
                user.save(update_fields=["username", "password"])
                # Invalidate all magic login tokens for this user; link is single-use after setup.
                MagicLoginToken.objects.filter(user=user).update(is_used=True)
                return Response(ProfileSerializer(user).data)
            return Response(setup.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


def _verify_otp_for_phone(phone: str, code: str):
    """Reuse verification OTP logic. Returns (True, None) if valid, (False, detail) otherwise."""
    from django.core.cache import cache
    from django.conf import settings
    key = f"verification_otp:phone:{phone.strip()}"
    demo_enabled = getattr(settings, "DEMO_OTP_ENABLED", settings.DEBUG)
    demo_code = getattr(settings, "DEMO_OTP_CODE", "123456")
    if demo_enabled:
        if code == demo_code or code in ("000000",):
            return True, key
        return False, None
    stored = cache.get(key)
    if stored and stored == code:
        return True, key
    return False, None


class ForgotPasswordResetView(APIView):
    """
    POST /api/auth/forgot-password/reset/
    Body: { "phone": "+91...", "code": "123456", "new_password": "..." }
    Verifies OTP then sets password for the user with that phone.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.core.cache import cache
        phone = (request.data.get("phone") or "").strip()
        code = (request.data.get("code") or "").strip()
        new_password = (request.data.get("new_password") or "").strip()
        if not phone:
            return Response(
                {"detail": "Phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code:
            return Response(
                {"detail": "Verification code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not new_password or len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        valid, cache_key = _verify_otp_for_phone(phone, code)
        if not valid:
            return Response(
                {"detail": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.filter(phone_number=phone).first()
        if not user:
            return Response(
                {"detail": "No account found with this phone number."},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.set_password(new_password)
        user.save(update_fields=["password"])
        if cache_key:
            cache.delete(cache_key)
        return Response({"detail": "Password has been reset. You can log in now."})


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Body: { "current_password": "...", "new_password": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current = (request.data.get("current_password") or "").strip()
        new_password = (request.data.get("new_password") or "").strip()
        if not current:
            return Response(
                {"current_password": "Current password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not new_password or len(new_password) < 8:
            return Response(
                {"new_password": "New password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if not user.check_password(current):
            return Response(
                {"current_password": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": "Password has been updated."})


class DeleteAccountView(APIView):
    """
    POST /api/auth/delete-account/
    Body: { "password": "..." } — confirm with current password.
    Deactivates the account (is_active=False); optionally can delete later.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = (request.data.get("password") or "").strip()
        if not password:
            return Response(
                {"password": "Password is required to confirm account deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if not user.check_password(password):
            return Response(
                {"password": "Password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"detail": "Your account has been deactivated."})


class UserProfileByUsernameView(APIView):
    """GET: public profile by username for /api/users/<username>/."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"code": "NOT_FOUND", "detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicProfileSerializer(user, context={"request": request})
        return Response(serializer.data)
