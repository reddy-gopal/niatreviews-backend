import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import ActionType
from audit.utils import log_action
from core.permissions import IsModeratorOrAdmin
from notifications.models import Notification
from notifications.tasks import (
    send_niat_rejection_email,
    send_write_access_unlocked_email,
)
from profiles.models import NiatStudentProfile

logger = logging.getLogger("moderation.views")


class ApproveNiatProfileView(APIView):
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request, id):
        profile = NiatStudentProfile.objects.select_related("user").filter(pk=id).first()
        if not profile:
            return Response({"detail": "NIAT profile not found."}, status=status.HTTP_404_NOT_FOUND)
        if profile.status == NiatStudentProfile.Status.APPROVED:
            return Response({"detail": "NIAT profile is already approved."}, status=status.HTTP_409_CONFLICT)

        user = profile.user
        with transaction.atomic():
            profile.status = NiatStudentProfile.Status.APPROVED
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.rejection_reason = ""
            profile.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )
            verified_profile = profile.promote_to_verified_niat_student()
            log_action(
                actor=request.user,
                action=ActionType.NIAT_APPROVED,
                entity=profile,
                target_user=profile.user,
                metadata={"verified_profile_id": str(verified_profile.pk)},
                request=request,
            )

        profile.delete()
        send_write_access_unlocked_email.delay(str(user.id))
        logger.info(
            "approval_email_queued",
            extra={"user_id": str(user.id), "user_email": user.email or "NO_EMAIL", "user_role": user.role},
        )
        Notification.objects.create(
            recipient=user,
            actor=request.user,
            verb="niat_approved",
        )
        return Response({"status": profile.status, "user_role": user.role}, status=status.HTTP_200_OK)


class RejectNiatProfileView(APIView):
    permission_classes = [IsModeratorOrAdmin]

    def post(self, request, id):
        reason = (request.data.get("rejection_reason") or "").strip()
        if len(reason) < 10:
            return Response(
                {"rejection_reason": "Rejection reason must be at least 10 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = NiatStudentProfile.objects.select_related("user").filter(pk=id).first()
        if not profile:
            return Response({"detail": "NIAT profile not found."}, status=status.HTTP_404_NOT_FOUND)

        profile.status = NiatStudentProfile.Status.REJECTED
        profile.reviewed_by = request.user
        profile.reviewed_at = timezone.now()
        profile.rejection_reason = reason
        profile.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"])

        log_action(
            actor=request.user,
            action=ActionType.NIAT_REJECTED,
            entity=profile,
            target_user=profile.user,
            metadata={"rejection_reason": reason},
            request=request,
        )
        send_niat_rejection_email.delay(profile.pk)
        return Response({"status": profile.status, "rejection_reason": profile.rejection_reason}, status=status.HTTP_200_OK)
