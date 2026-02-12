# notifications API views
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
    """GET: list notifications for the current user (newest first). Requires auth."""
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        qs = (
            Notification.objects.filter(recipient=request.user)
            .select_related("actor", "notification_type")
            .order_by("-created_at")
        )
        paginator = NotificationPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = NotificationSerializer(qs, many=True)
        return Response(serializer.data)
