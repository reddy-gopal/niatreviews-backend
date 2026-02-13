# notifications API views
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationListCreateView(APIView):
    """GET: list notifications for the current user (newest first). ?unread_only=true for unread only."""
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        qs = (
            Notification.objects.filter(recipient=request.user)
            .select_related("actor", "notification_type")
            .order_by("-created_at")
        )
        if request.query_params.get("unread_only", "").lower() in ("true", "1"):
            qs = qs.filter(read_at__isnull=True)
        paginator = NotificationPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = NotificationSerializer(qs, many=True)
        return Response(serializer.data)


class NotificationUnreadCountView(APIView):
    """GET: return { count: number } of unread notifications for current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return Response({"count": count})


class NotificationMarkReadView(APIView):
    """POST: mark a single notification as read. Notification must belong to current user."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(recipient=request.user, id=pk).first()
        if not notification:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    """POST: mark all notifications for current user as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response({"marked": updated})
