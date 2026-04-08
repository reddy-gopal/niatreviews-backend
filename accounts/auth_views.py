import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from audit.models import ActionType
from audit.utils import log_action

logger = logging.getLogger(__name__)

try:
    from django_ratelimit.decorators import ratelimit
except ImportError:  # pragma: no cover - fallback for environments missing the package
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )


def set_access_cookie(response, access_token):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 60 * 24,
        path="/",
    )


def clear_auth_cookies(response):
    response.delete_cookie("access_token", path="/", samesite="None")
    response.delete_cookie("refresh_token", path="/", samesite="None")


def send_verification_email_sync(user):
    if not user.email or not user.email_verification_token:
        return
    base_url = getattr(settings, "MAIN_APP_URL", "http://localhost:3000").rstrip("/")
    verify_url = f"{base_url}/verify-email?token={user.email_verification_token}"
    send_mail(
        "Verify your email",
        (
            f"Hi {user.username},\n\n"
            f"Please verify your email address to continue onboarding:\n{verify_url}\n\n"
            "If you did not create this account, you can ignore this email."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


class RoleAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["user_id"] = str(user.id)
        return token


class RateLimitedTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleAwareTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def _client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _is_rate_limited(self, request):
        key = f"login_rate_limit:{self._client_ip(request)}"
        count = cache.get(key, 0)
        if count >= 5:
            return True
        cache.set(key, count + 1, timeout=60)
        return False

    def _log_failed_login(self, request):
        class LoginAttempt:
            def __init__(self):
                self.pk = uuid.uuid4()

        username = (request.data.get("username") or "").strip()
        user = User.objects.filter(username__iexact=username).first() if username else None
        try:
            log_action(
                actor=None,
                action=ActionType.LOGIN_FAILED,
                entity=user or LoginAttempt(),
                target_user=user,
                metadata={"username": username},
                request=request,
            )
        except Exception:  # pragma: no cover
            logger.exception("Failed to write audit log for login failure")

    def post(self, request, *args, **kwargs):
        if self._is_rate_limited(request):
            self._log_failed_login(request)
            return Response(
                {"error": {"code": "RATE_LIMITED", "message": "Too many login attempts. Please try again later."}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            self._log_failed_login(request)
            return response

        refresh = response.data.pop("refresh", None)
        access = response.data.get("access")
        if access:
            set_access_cookie(response, access)
        if refresh:
            set_refresh_cookie(response, refresh)
        return response


class TokenRefreshCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_value = request.COOKIES.get("refresh_token")
        if not token_value:
            return Response({"detail": "Refresh token cookie is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(token_value)
        except Exception:
            return Response({"detail": "Refresh token is invalid."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = refresh.access_token
        access_token["role"] = request.user.role if getattr(request, "user", None) and request.user.is_authenticated else refresh.get("role")
        access_token["user_id"] = str(request.user.id) if getattr(request, "user", None) and request.user.is_authenticated else refresh.get("user_id")

        response = Response({"access": str(access_token)}, status=status.HTTP_200_OK)
        set_access_cookie(response, str(access_token))

        if getattr(settings, "SIMPLE_JWT", {}).get("ROTATE_REFRESH_TOKENS", False):
            try:
                refresh.blacklist()
            except Exception:
                pass
            new_refresh = RefreshToken.for_user(User.objects.get(pk=refresh["user_id"]))
            new_refresh["role"] = refresh.get("role")
            new_refresh["user_id"] = refresh.get("user_id")
            set_refresh_cookie(response, str(new_refresh))

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_value = request.COOKIES.get("refresh_token")
        if token_value and getattr(settings, "SIMPLE_JWT", {}).get("BLACKLIST_AFTER_ROTATION", False):
            try:
                RefreshToken(token_value).blacklist()
            except Exception:
                pass

        response = Response({"detail": "logged out"}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_value = request.data.get("token")
        if not token_value:
            return Response({"detail": "Verification token is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email_verification_token=token_value).first()
        if not user:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = True
        user.email_verification_token = None
        user.save(update_fields=["is_verified", "email_verification_token"])
        return Response({"detail": "Email verified successfully.", "verified_at": timezone.now().isoformat()})
