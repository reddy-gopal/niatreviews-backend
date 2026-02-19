"""
Demo OTP and registration status API for senior registration flow.
Use DEMO_OTP_CODE in development; replace with real SMS/email integration in production.
"""
import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SeniorRegistration

logger = logging.getLogger(__name__)

# Demo OTP: accept this code when DEMO_OTP_ENABLED is True (e.g. in dev)
DEMO_OTP_CODE = getattr(settings, "DEMO_OTP_CODE", "123456")
DEMO_OTP_ACCEPT_ALSO = ("000000",)  # common test code
CACHE_PREFIX = "verification_otp"
CACHE_TTL = 600  # 10 minutes


def _demo_otp_enabled():
    return getattr(settings, "DEMO_OTP_ENABLED", settings.DEBUG)


def _otp_key(channel: str, value: str) -> str:
    """Cache key for OTP (value normalized to lowercase for email)."""
    normalized = value.strip().lower() if channel == "email" else value.strip()
    return f"{CACHE_PREFIX}:{channel}:{normalized}"


class OTPRequestView(APIView):
    """
    POST /api/verification/otp/request/
    Body: { "email": "user@example.com" } or { "phone": "+919876543210" }
    In demo mode: stores fixed OTP (123456); in production, send via email/SMS.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        if email and phone:
            return Response(
                {"detail": "Provide either email or phone, not both."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not email and not phone:
            return Response(
                {"detail": "Provide email or phone."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email:
            channel, value = "email", email
        else:
            channel, value = "phone", phone

        if _demo_otp_enabled():
            code = DEMO_OTP_CODE
            cache.set(_otp_key(channel, value), code, CACHE_TTL)
            logger.info("Demo OTP stored for %s (code=%s)", value[:3] + "***", code)
            return Response({"message": "OTP sent. Use demo code 123456."})
        # Production: generate code, send via email/SMS, store in cache
        # TODO: integrate with your SMS/email provider
        return Response(
            {"detail": "OTP sending not configured. Use demo mode."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class OTPVerifyView(APIView):
    """
    POST /api/verification/otp/verify/
    Body: { "email": "..." or "phone": "...", "code": "123456" }
    Returns { "verified": true } on success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        code = (request.data.get("code") or "").strip()
        if email and phone:
            return Response(
                {"detail": "Provide either email or phone, not both."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not email and not phone:
            return Response(
                {"detail": "Provide email or phone."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code:
            return Response(
                {"detail": "Provide code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if email:
            channel, value = "email", email
        else:
            channel, value = "phone", phone

        key = _otp_key(channel, value)
        stored = cache.get(key) if not _demo_otp_enabled() else DEMO_OTP_CODE
        if _demo_otp_enabled():
            accepted = code == DEMO_OTP_CODE or code in DEMO_OTP_ACCEPT_ALSO
        else:
            accepted = stored and stored == code
        if accepted:
            cache.delete(key)
            return Response({"verified": True})
        return Response(
            {"detail": "Invalid or expired code.", "verified": False},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SeniorRegistrationStatusView(APIView):
    """
    GET /api/verification/senior/registration-status/?email=applicant@example.com
    Returns application status for the given personal email (no auth).
    Only returns status; no PII beyond what the user provides.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        email = (request.query_params.get("email") or "").strip().lower()
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reg = SeniorRegistration.objects.filter(personal_email__iexact=email).order_by("-created_at").first()
        if not reg:
            return Response({"status": "not_found"})
        return Response({"status": reg.status})
