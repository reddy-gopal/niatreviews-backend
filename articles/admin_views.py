from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Article
from .admin_serializers import ArticleAdminListSerializer, ArticleAdminDetailSerializer
from .permissions import IsAdmin


class ArticleAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category", "campus_id", "featured", "is_global_guide"]
    search_fields = ["title", "author_username", "campus_name"]
    ordering_fields = ["created_at", "updated_at", "upvote_count", "view_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Article.objects.select_related(
            "author_id",
            "campus_id",
            "category_fk",
            "reviewed_by_id",
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleAdminListSerializer
        return ArticleAdminDetailSerializer

    def perform_create(self, serializer):
        campus_id = self.request.data.get("campus_id")
        extra = {}

        if campus_id:
            from campuses.models import Campus
            try:
                campus = Campus.objects.get(id=campus_id)
                extra["campus_id"] = campus
                extra["campus_name"] = campus.name
            except Campus.DoesNotExist:
                pass

        serializer.save(**extra)

    def perform_update(self, serializer):
        campus_id = self.request.data.get("campus_id")
        extra = {}

        if campus_id:
            from campuses.models import Campus
            try:
                campus = Campus.objects.get(id=campus_id)
                extra["campus_id"] = campus
                extra["campus_name"] = campus.name
            except Campus.DoesNotExist:
                pass

        new_status = self.request.data.get("status")
        if new_status in ("published", "rejected"):
            extra["reviewed_by_id"] = self.request.user
            extra["reviewed_at"] = timezone.now()

        if new_status == "published" and not serializer.instance.published_at:
            extra["published_at"] = timezone.now()

        serializer.save(**extra)

    def perform_destroy(self, instance):
        instance.delete()