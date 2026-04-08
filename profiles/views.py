from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from accounts.models import User
from core.permissions import IsModeratorOrAdmin, IsVerifiedUser
from notifications.tasks import notify_moderators_new_niat_submission
import logging

from .models import VerifiedNiatStudentProfile, IntermediateStudentProfile, NiatStudentProfile
from .serializers import (
    VerifiedNiatStudentProfileSerializer,
    IntermediateStudentProfileSerializer,
    NiatStudentProfileReadSerializer,
    NiatStudentProfileWriteSerializer,
)

logger = logging.getLogger("profiles.views")


class IntermediateStudentProfileUpsertView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedUser]

    def post(self, request):
        profile = getattr(request.user, "intermediate_profile", None)
        serializer = IntermediateStudentProfileSerializer(instance=profile, data=request.data, partial=profile is not None)
        serializer.is_valid(raise_exception=True)
        if profile is None:
            serializer.save(user=request.user)
        else:
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK if profile else status.HTTP_201_CREATED)


class NiatStudentProfileUpsertView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # NIAT approval notifications are email-driven, so ensure we always have one.
        if not (request.user.email or "").strip():
            return Response(
                {"email": "Email is required before submitting NIAT profile for verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        existing = getattr(request.user, "niat_profile", None)
        serializer = NiatStudentProfileWriteSerializer(
            instance=existing,
            data=request.data,
            partial=existing is not None,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        if profile.status == NiatStudentProfile.Status.PENDING:
            notify_moderators_new_niat_submission.delay(str(profile.id))
        read_serializer = NiatStudentProfileReadSerializer(profile)
        return Response(read_serializer.data, status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED)


class NiatStudentProfileDetailView(generics.RetrieveAPIView):
    queryset = NiatStudentProfile.objects.select_related("user", "reviewed_by", "campus").all()
    serializer_class = NiatStudentProfileReadSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        badge = None
        if role == User.UserRole.INTERMEDIATE_STUDENT:
            profile = getattr(request.user, "intermediate_profile", None)
            serializer = IntermediateStudentProfileSerializer(profile) if profile else None
        elif role == User.UserRole.NIAT_STUDENT:
            profile = getattr(request.user, "niat_profile", None)
            serializer = NiatStudentProfileReadSerializer(profile) if profile else None
        elif role == User.UserRole.VERIFIED_NIAT_STUDENT:
            profile = getattr(request.user, "verified_niat_profile", None)
            serializer = VerifiedNiatStudentProfileSerializer(profile) if profile else None
            if profile is not None and profile.badge_awarded_at is not None:
                badge = {
                    "type": "verified_niat_student",
                    "awarded_at": profile.badge_awarded_at.isoformat(),
                }
        else:
            profile = None
            serializer = None

        return Response(
            {
                "user": {
                    "id": str(request.user.id),
                    "username": request.user.username,
                    "phone": request.user.phone_number,
                },
                "role": role,
                "is_onboarded": request.user.is_onboarded,
                "profile": serializer.data if serializer else None,
                "badge": badge,
            }
        )


class PublicBadgeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        logger.info("public_badge.request", extra={"username": username})
        user = User.objects.filter(username=username).first()
        if not user or user.role != User.UserRole.VERIFIED_NIAT_STUDENT:
            logger.warning("public_badge.user_not_found_or_not_verified", extra={"username": username})
            return Response({"detail": "Badge not found."}, status=status.HTTP_404_NOT_FOUND)

        profile = getattr(user, "verified_niat_profile", None)
        if not profile or not profile.badge_awarded_at:
            logger.warning(
                "public_badge.profile_missing_or_unawarded",
                extra={"username": username, "user_id": str(user.id)},
            )
            return Response({"detail": "Badge not found."}, status=status.HTTP_404_NOT_FOUND)

        public_base = getattr(settings, "MAIN_APP_URL", "").rstrip("/")
        badge_page_url = f"{public_base}/badge/{user.username}" if public_base else None
        month_year = profile.badge_awarded_at.strftime("%B %Y")
        caption = (
            f"I am now a Verified NIAT Student on NIAT Insider ({month_year}). "
            "Proud to share authentic student experiences."
        )

        try:
            profile_picture_url = request.build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None
        except ValueError:
            profile_picture_url = None

        name = (user.get_full_name() or user.username).strip()
        niat_profile = getattr(user, "niat_profile", None)
        student_id = (profile.student_id_number or "").strip()
        if not student_id and niat_profile:
            student_id = (niat_profile.student_id_number or "").strip()

        logger.info(
            "public_badge.response",
            extra={"username": username, "user_id": str(user.id)},
        )

        return Response(
            {
                "username": user.username,
                "name": name,
                "role": "Verified NIAT Student",
                "campus": (profile.campus_name or (profile.campus.name if profile.campus_id else "NIAT Campus")).strip(),
                "program": "NIAT Insider",
                "batch": str(profile.year_joined or profile.badge_awarded_at.year if profile.badge_awarded_at else "2026"),
                "studentId": student_id or "N/A",
                "credentialId": f"NIAT-{profile.id:06d}",
                "issuedDate": profile.badge_awarded_at.isoformat(),
                "profilePictureUrl": profile_picture_url,
                "awarded_at": profile.badge_awarded_at.isoformat(),
                "badge_page_url": badge_page_url,
                "caption": caption,
            }
        )
