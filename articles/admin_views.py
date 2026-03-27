from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.utils import timezone

from .models import Article
from accounts.models import User
from .admin_serializers import (
    ArticleAdminListSerializer,
    ArticleAdminDetailSerializer,
    AuthorArticleCountSerializer,
)
from .permissions import IsAdmin


class ArticleAdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ArticleAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = ArticleAdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category", "campus_id", "author_id", "featured", "is_global_guide", "ai_generated"]
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

    @action(detail=False, methods=["get"], url_path="authors")
    def authors(self, request):
        authors = (
            User.objects.filter(articles__isnull=False, articles__ai_generated=False)
            .prefetch_related("founding_editor_profile", "articles")
            .annotate(article_count=Count("id"))
            .order_by("-article_count", "username")
        )
        serializer = AuthorArticleCountSerializer(authors, many=True)
        return Response(serializer.data)