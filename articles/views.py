import re
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, ArticleComment, ArticleHelpful, Category, Subcategory, generate_unique_slug
from accounts.models import FoundingEditorProfile
from .permissions import IsAuthorOrModerator, IsModerator
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    ModerationSerializer,
    ArticleCommentSerializer,
)


def extract_image_urls_from_html(body):
    """Extract all img src URLs from HTML body. Returns list of strings."""
    if not (body and isinstance(body, str)):
        return []
    # Match src="..." or src='...'
    urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
    return [u.strip() for u in urls if u.strip()]


class ArticlePageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ArticleViewSet(viewsets.ModelViewSet):
    pagination_class = ArticlePageNumberPagination
    serializer_class = ArticleListSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Article.objects.all()
        user = self.request.user
        is_moderator = getattr(user, "role", None) == "moderator"

        if not user.is_authenticated:
            qs = qs.filter(status="published")
        elif not is_moderator:
            from django.db.models import Q
            qs = qs.filter(Q(status="published") | Q(author_id=str(user.id)))
        # else moderator sees all

        campus = self.request.query_params.get("campus")
        if campus is not None:
            try:
                qs = qs.filter(campus_id=int(campus))
            except ValueError:
                pass
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        subcategory = self.request.query_params.get("subcategory")
        if subcategory:
            qs = qs.filter(subcategory=subcategory)
        is_global = self.request.query_params.get("is_global_guide")
        if is_global is not None:
            qs = qs.filter(is_global_guide=is_global.lower() in ("true", "1", "yes"))
        featured = self.request.query_params.get("featured")
        if featured is not None:
            qs = qs.filter(featured=featured.lower() in ("true", "1", "yes"))
        if is_moderator:
            status_param = self.request.query_params.get("status")
            if status_param:
                qs = qs.filter(status=status_param)
        topic = self.request.query_params.get("topic")
        if topic:
            qs = qs.filter(topic=topic)

        ordering = self.request.query_params.get("ordering", "updated_at")
        if ordering == "helpful_count":
            qs = qs.order_by("-helpful_count", "-updated_at")
        else:
            qs = qs.order_by("-updated_at")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "create" or self.action == "partial_update" or self.action == "moderate":
            return ArticleDetailSerializer
        return ArticleListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action in ("create", "helpful"):
            return [IsAuthenticated()]
        if self.action in ("partial_update", "destroy"):
            return [IsAuthenticated(), IsAuthorOrModerator()]
        if self.action == "moderate":
            return [IsModerator()]
        if self.action == "pending":
            return [IsModerator()]
        if self.action == "my_articles":
            return [IsAuthenticated()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != "published":
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if str(instance.author_id) != str(request.user.id) and getattr(request.user, "role", None) != "moderator":
                return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data_for_serializer = dict(request.data)
        if getattr(request.user, "role", None) == "founding_editor":
            try:
                profile = FoundingEditorProfile.objects.get(user=request.user)
                if profile.campus_id is not None:
                    data_for_serializer["campus_id"] = profile.campus_id
                    data_for_serializer["campus_name"] = profile.campus_name or ""
            except FoundingEditorProfile.DoesNotExist:
                pass
        serializer = ArticleWriteSerializer(data=data_for_serializer, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        save_as_draft = data.get("save_as_draft", False)
        article_status = "draft" if save_as_draft else "pending_review"
        slug = generate_unique_slug(data.get("title") or "Draft", instance=None)
        resolved = data.get("_resolved_category")
        campus_id = data.get("campus_id")
        campus_name = data.get("campus_name") or ""
        body_str = (data.get("body") or "").strip() or ""
        images = data.get("images")
        if images is None:
            images = extract_image_urls_from_html(body_str)
        if not isinstance(images, list):
            images = list(images) if images else []
        cover_image = (data.get("cover_image") or "").strip()
        if not cover_image and images:
            cover_image = images[0] if images else ""
        article = Article(
            author_id=str(request.user.id),
            author_username=request.user.username,
            campus_id=campus_id,
            campus_name=campus_name,
            category=data.get("category") or "campus-life",
            category_fk=resolved,
            title=(data.get("title") or "").strip() or "Draft",
            slug=slug,
            excerpt=(data.get("excerpt") or "").strip() or "",
            body=body_str,
            cover_image=cover_image,
            images=images,
            status=article_status,
            is_global_guide=data.get("is_global_guide", False),
            topic=data.get("topic") or "",
            club_id=data.get("club_id"),
            subcategory=(data.get("subcategory") or "").strip() or "",
            subcategory_other=(data.get("subcategory_other") or "").strip() or "",
        )
        article.save()
        return Response(ArticleDetailSerializer(article).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        is_moderator = getattr(request.user, "role", None) == "moderator"
        if not is_moderator:
            if instance.status not in ("draft", "pending_review", "rejected"):
                return Response({"detail": "Cannot edit published article."}, status=status.HTTP_400_BAD_REQUEST)
            data_copy = {k: v for k, v in request.data.items() if k in (
                "campus_id", "campus_name", "category", "category_id", "title", "excerpt", "body", "cover_image", "images", "is_global_guide", "topic", "club_id", "subcategory", "subcategory_other"
            )}
            if getattr(request.user, "role", None) == "founding_editor":
                try:
                    profile = FoundingEditorProfile.objects.get(user=request.user)
                    if profile.campus_id is not None:
                        data_copy["campus_id"] = profile.campus_id
                        data_copy["campus_name"] = profile.campus_name or ""
                except FoundingEditorProfile.DoesNotExist:
                    pass
            if instance.status == "rejected":
                instance.status = "pending_review"
                instance.rejection_reason = ""
        else:
            data_copy = dict(request.data)
        serializer = ArticleWriteSerializer(data=data_copy, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        body_str = (data.get("body") or "").strip() if "body" in data else None
        images = data.get("images")
        if images is not None:
            instance.images = list(images) if images else []
            instance.cover_image = (instance.images[0] if instance.images else "") or (instance.cover_image or "")
        elif body_str is not None:
            extracted = extract_image_urls_from_html(body_str)
            if extracted:
                instance.images = extracted
                instance.cover_image = extracted[0] or instance.cover_image or ""
        for key in ("campus_id", "campus_name", "category", "title", "excerpt", "body", "cover_image", "is_global_guide", "topic", "club_id", "subcategory", "subcategory_other"):
            if key in data:
                val = data[key]
                if key in ("subcategory", "subcategory_other"):
                    setattr(instance, key, (val or "").strip() or "")
                elif key != "body" or body_str is None:
                    setattr(instance, key, val)
        if body_str is not None:
            instance.body = body_str
        if "_resolved_category" in data:
            instance.category_fk = data["_resolved_category"]
        if not is_moderator and "status" in request.data:
            # Author may set draft (save draft) or draft -> pending_review (submit for review)
            new_status = request.data.get("status")
            if new_status == "pending_review" and instance.status == "draft":
                instance.status = "pending_review"
            elif new_status == "draft":
                instance.status = "draft"
        elif is_moderator and "status" in data:
            setattr(instance, "status", data["status"])
        instance.save()
        return Response(ArticleDetailSerializer(instance).data)

    @action(detail=True, methods=["post"], permission_classes=[IsModerator])
    def moderate(self, request, pk=None):
        article = self.get_object()
        ser = ModerationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        new_status = data["status"]
        if new_status == "published":
            article.status = "published"
            article.published_at = timezone.now()
            article.reviewed_by_id = str(request.user.id)
            article.reviewed_at = timezone.now()
            article.rejection_reason = ""
        else:
            article.status = "rejected"
            article.rejection_reason = data.get("rejection_reason", "")
            article.reviewed_by_id = str(request.user.id)
            article.reviewed_at = timezone.now()
        if "featured" in data:
            article.featured = data["featured"]
        article.save()
        return Response(ArticleDetailSerializer(article).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def helpful(self, request, pk=None):
        article = self.get_object()
        user_id = str(request.user.id)
        existing = ArticleHelpful.objects.filter(article=article, user_id=user_id).first()
        if existing:
            existing.delete()
            article.helpful_count = max(0, article.helpful_count - 1)
            article.save(update_fields=["helpful_count"])
            return Response({"helpful_count": article.helpful_count, "marked": False})
        ArticleHelpful.objects.create(article=article, user_id=user_id)
        article.helpful_count += 1
        article.save(update_fields=["helpful_count"])
        return Response({"helpful_count": article.helpful_count, "marked": True})

    @action(detail=False, methods=["get"], permission_classes=[IsModerator])
    def pending(self, request):
        qs = Article.objects.filter(status="pending_review").order_by("created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_articles(self, request):
        qs = Article.objects.filter(author_id=str(request.user.id)).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        article = self.get_object()
        if article.status != "published" and not request.user.is_authenticated:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if article.status != "published" and str(article.author_id) != str(request.user.id) and getattr(request.user, "role", None) != "moderator":
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.method == "GET":
            comments = ArticleComment.objects.filter(article=article, is_visible=True)
            serializer = ArticleCommentSerializer(comments, many=True)
            return Response(serializer.data)
        if request.method == "POST":
            if not request.user.is_authenticated:
                return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
            body = (request.data.get("body") or "").strip()
            if not body:
                return Response({"body": "Required."}, status=status.HTTP_400_BAD_REQUEST)
            comment = ArticleComment.objects.create(
                article=article,
                author_id=str(request.user.id),
                author_username=request.user.username,
                body=body[:2000],
            )
            return Response(ArticleCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all().order_by("id")
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class SubcategoryListView(APIView):
    """GET /api/articles/subcategories/?category=club-directory or ?category_id=1. Returns [{ slug, label, requires_other }, ...]."""
    permission_classes = [AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")
        category_id = request.query_params.get("category_id")
        if not category_slug and not category_id:
            return Response([], status=status.HTTP_200_OK)
        try:
            if category_id:
                cat = Category.objects.get(pk=int(category_id))
            else:
                cat = Category.objects.get(slug=category_slug)
        except (Category.DoesNotExist, ValueError, TypeError):
            return Response([], status=status.HTTP_200_OK)
        subs = Subcategory.objects.filter(category=cat).order_by("display_order", "slug")
        data = [{"slug": s.slug, "label": s.label, "requires_other": s.requires_other} for s in subs]
        return Response(data)


class ArticleCommentDestroyView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, article_pk, pk):
        article = Article.objects.filter(pk=article_pk).first()
        if not article:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comment = ArticleComment.objects.filter(article=article, pk=pk).first()
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if str(comment.author_id) != str(request.user.id) and getattr(request.user, "role", None) != "moderator":
            return Response(status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _validate_image_file(file):
    """Validate uploaded file is an image using Pillow. Raises ValueError if invalid."""
    try:
        from PIL import Image
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception as e:
        raise ValueError(f"Invalid or unsupported image: {e}")


class ArticleImageUploadView(APIView):
    """POST: upload an image for use in articles. Saves to media/article/images/. Returns { url }."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        upload_key = "image"
        file = request.FILES.get(upload_key) or request.FILES.get("file")
        if not file:
            return Response(
                {"error": f"Missing file. Send multipart form with key '{upload_key}' or 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not file.content_type or not file.content_type.startswith("image/"):
            return Response(
                {"error": "File must be an image (e.g. image/jpeg, image/png)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            _validate_image_file(file)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        upload_to = getattr(settings, "ARTICLE_IMAGES_UPLOAD_TO", "article/images")
        safe_name = re.sub(r"[^\w.\-]", "_", file.name or "image")[:80]
        path = f"{upload_to}/{uuid.uuid4().hex}_{safe_name}"

        try:
            saved_path = default_storage.save(path, file)
        except Exception as e:
            return Response({"error": f"Save failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        return Response({"url": url}, status=status.HTTP_201_CREATED)
