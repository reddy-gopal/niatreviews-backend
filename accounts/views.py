import re
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import FoundingEditorProfile
from .serializers import (
    ProfileSerializer,
    PublicProfileSerializer,
    SeniorsSetupSerializer,
    FoundingEditorProfileSerializer,
)
from verification.models import MagicLoginToken

User = get_user_model()


def _get_user_by_phone(phone: str):
    """Return user with this phone (exact or digits-only match), or None."""
    phone = (phone or "").strip()
    if not phone:
        return None
    user = User.objects.filter(phone_number=phone).first()
    if user:
        return user
    digits = re.sub(r"\D", "", phone)
    if digits:
        return User.objects.filter(phone_number=digits).first()
    return None


class RegisterView(APIView):
    """Prospective students: phone required (verified via OTP on frontend), email optional.
    When source=niatverse (NIATVerse / campus app), user is created with role founding_editor."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        email = (request.data.get("email") or "").strip() or None
        password = request.data.get("password", "")
        source = (request.data.get("source") or "").strip().lower()
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
        if source == "niatverse":
            user.role = "founding_editor"
        user.save(update_fields=["phone_number", "phone_verified", "email", "role"])
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
        serializer = ProfileSerializer(user, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


def _verify_otp_for_phone(phone: str, code: str):
    """Verify OTP via MSG91. Returns (True, dummy_key) or (False, None)."""
    from verification.msg91_client import is_configured as msg91_configured, verify_otp as msg91_verify_otp

    if not msg91_configured():
        return False, None
    ok, _ = msg91_verify_otp(phone, code)
    return (True, "ok") if ok else (False, None)


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


class PhoneLoginView(APIView):
    """
    POST /api/auth/login/phone/
    Body: { "phone": "+91...", "code": "123456" }
    Verifies OTP via MSG91, finds user by phone, returns JWT access and refresh.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        code = (request.data.get("code") or "").strip()
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
        valid, _ = _verify_otp_for_phone(phone, code)
        if not valid:
            return Response(
                {"detail": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = _get_user_by_phone(phone)
        if not user:
            return Response(
                {"detail": "No account with this phone number. Please register first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return Response(
                {"detail": "This account has been deactivated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class PhonePasswordLoginView(APIView):
    """
    POST /api/auth/login/phone-password/
    Body: { "phone": "9876543210", "password": "..." }
    Finds user by phone, validates password, returns JWT access and refresh.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = (request.data.get("phone") or "").strip()
        password = request.data.get("password") or ""
        if not phone:
            return Response(
                {"detail": "Mobile number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return Response(
                {"detail": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = _get_user_by_phone(phone)
        if not user:
            return Response(
                {"detail": "No account with this mobile number. Please register first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return Response(
                {"detail": "This account has been deactivated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.check_password(password):
            return Response(
                {"detail": "Invalid mobile number or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


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


class FoundingEditorProfileView(APIView):
    """
    GET /api/auth/me/profile/ — return current user's Founding Editor profile (college details).
    PATCH /api/auth/me/profile/ — update profile. Only for users with role founding_editor.
    Profile is created on first GET if missing.
    """
    permission_classes = [IsAuthenticated]

    def _get_or_create_profile(self, user):
        if user.role != "founding_editor":
            return None
        profile, _ = FoundingEditorProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self._get_or_create_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Founding Editor profile is only for users with role founding_editor."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = FoundingEditorProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = self._get_or_create_profile(request.user)
        if profile is None:
            return Response(
                {"detail": "Founding Editor profile is only for users with role founding_editor."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = FoundingEditorProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class UserProfileByUsernameView(APIView):
    """GET: public profile by username for /api/users/<username>/."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"code": "NOT_FOUND", "detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PublicProfileSerializer(user, context={"request": request})
        return Response(serializer.data)
