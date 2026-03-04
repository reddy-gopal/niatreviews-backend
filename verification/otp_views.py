"""
OTP request/verify via MSG91 only. No demo OTP.
Phone: MSG91 sends and verifies. When for=register, reject if phone already registered.
"""
import logging
import re
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SeniorRegistration
from .msg91_client import (
    is_configured as msg91_configured,
    send_otp as msg91_send_otp,
    verify_otp as msg91_verify_otp,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _phone_already_registered(phone: str) -> bool:
    """True if a user exists with this phone (exact or digits-only match)."""
    if not phone or not phone.strip():
        return False
    if User.objects.filter(phone_number=phone.strip()).exists():
        return True
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return False
    return User.objects.filter(phone_number=digits).exists()


class OTPRequestView(APIView):
    """
    POST /api/verification/otp/request/
    Body: { "phone": "+919876543210" } or { "email": "..." }
    Optional: "for": "register" | "login" — register: reject if already registered;
    login: reject if not registered (send OTP only for existing accounts).
    Phone: MSG91 sends OTP. Email: not configured (501).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        phone = (request.data.get("phone") or "").strip()
        otp_for = (request.data.get("for") or "").strip().lower()
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
        if phone:
            if not msg91_configured():
                return Response(
                    {"detail": "OTP is not configured. Contact support."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            if otp_for == "register" and _phone_already_registered(phone):
                return Response(
                    {
                        "detail": "This phone number is already registered. Log in or use a different number.",
                        "code": "PHONE_ALREADY_REGISTERED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if otp_for == "login" and not _phone_already_registered(phone):
                return Response(
                    {
                        "detail": "No account with this phone number. Please register first.",
                        "code": "PHONE_NOT_REGISTERED",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ok, msg = msg91_send_otp(phone, template_params=request.data.get("template_params"))
            if ok:
                return Response({"message": msg or "OTP sent."})
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        # Email OTP not implemented
        return Response(
            {"detail": "Email OTP is not available. Use phone number."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class OTPVerifyView(APIView):
    """
    POST /api/verification/otp/verify/
    Body: { "phone": "...", "code": "123456" } or { "email": "...", "code": "..." }
    Phone: MSG91 verifies. Email: not implemented (501).
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
        if phone:
            if not msg91_configured():
                return Response(
                    {"detail": "OTP verification is not configured."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            ok, _ = msg91_verify_otp(phone, code)
            if ok:
                return Response({"verified": True})
            return Response(
                {"detail": "Invalid or expired code.", "verified": False},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"detail": "Email OTP is not available. Use phone number."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
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
