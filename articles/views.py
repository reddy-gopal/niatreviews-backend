import re
import uuid
import logging
from collections import defaultdict
from django.http import Http404
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, F

from .models import Article, ArticleSuggestion, ArticleUpvote, Category, Subcategory, generate_unique_slug
from accounts.models import FoundingEditorProfile
from .permissions import IsAuthorOrModerator, IsModerator
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    ModerationSerializer,
)

logger = logging.getLogger(__name__)


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
            qs = qs.filter(Q(status="published") | Q(author_id_id=str(user.id)))
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
        if ordering == "upvote_count":
            qs = qs.order_by("-upvote_count", "-updated_at")
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
        if self.action == "create":
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
            if str(instance.author_id_id) != str(request.user.id) and getattr(request.user, "role", None) != "moderator":
                return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    def create(self, request, *args, **kwargs):
        data_for_serializer = dict(request.data)
        logger.error(f"[DEBUG] Original request data: {dict(request.data)}")
        
        if getattr(request.user, "role", None) == "founding_editor":
            try:
                profile = FoundingEditorProfile.objects.get(user=request.user)
                if profile.campus_id is not None:
                    data_for_serializer["campus_id"] = profile.campus_id.id
                    data_for_serializer["campus_name"] = profile.campus_name or ""
                    logger.error(f"[DEBUG] Added founding editor data: campus_id={profile.campus_id.id}, campus_name={profile.campus_name}")
            except FoundingEditorProfile.DoesNotExist:
                logger.error("[DEBUG] FoundingEditorProfile not found")
                pass
        
        logger.error(f"[DEBUG] Final serializer data: {data_for_serializer}")
        
        serializer = ArticleWriteSerializer(data=data_for_serializer, context={"request": request})
        if not serializer.is_valid():
            logger.error(f"[DEBUG] Serializer validation errors: {serializer.errors}")
            debug_data = {}
            for key, value in data_for_serializer.items():
                try:
                    import json
                    json.dumps(value)
                    debug_data[key] = value
                except (TypeError, ValueError):
                    debug_data[key] = str(value)
            
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors,
                'data_received': debug_data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error("[DEBUG] Serializer validation passed")
            
        data = serializer.validated_data
        save_as_draft = data.get("save_as_draft", False)
        article_status = "draft" if save_as_draft else "pending_review"
        slug = generate_unique_slug(data.get("title") or "Draft", instance=None)
        resolved = data.get("_resolved_category")
        campus_id = data.get("campus_id")
        campus_name = data.get("campus_name") or ""
        body_str = (data.get("body") or "").strip() or ""
        images = data.get("images", [])
        if not images:
            images = extract_image_urls_from_html(body_str)
        cover_image = data.get("cover_image", "")
        if not cover_image and images:
            cover_image = images[0] if images else ""
        article = Article(
            author_id=request.user,
            author_username=request.user.username,
            campus_id_id=campus_id,          # FIX: use _id suffix for raw integer FK
            campus_name=campus_name,
            category=data.get("category") or "onboarding-kit",
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
                        data_copy["campus_id"] = profile.campus_id.id
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

        # FIX: handle campus_id separately using _id suffix for raw integer FK
        if "campus_id" in data:
            instance.campus_id_id = data["campus_id"]

        for key in ("campus_name", "category", "title", "excerpt", "body", "cover_image", "is_global_guide", "topic", "club_id", "subcategory", "subcategory_other"):
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
        qs = Article.objects.filter(author_id_id=str(request.user.id)).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

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


def _get_article_for_engagement(article_id, request=None):
    article = get_object_or_404(Article, pk=article_id)
    # Allow access if published, or if the requester is the author/moderator
    if article.status != "published":
        if request is None or not request.user.is_authenticated:
            raise Http404
        if (str(article.author_id_id) != str(request.user.id) and
                getattr(request.user, "role", None) != "moderator"):
            raise Http404
    return article

class ArticleUpvoteView(APIView):
    """POST: toggle upvote. One per user per article. Upsert: create or delete."""
    permission_classes = [IsAuthenticated]

    def post(self, request, article_id):
        article = _get_article_for_engagement(article_id, request)
        user = request.user
        with transaction.atomic():
            upvote = ArticleUpvote.objects.filter(article=article, user=user).first()
            if upvote:
                upvote.delete()
                article.upvote_count = max(0, article.upvote_count - 1)
                article.save(update_fields=["upvote_count"])
                return Response({"upvote_count": article.upvote_count, "upvoted": False})
            ArticleUpvote.objects.create(article=article, user=user)
            article.upvote_count += 1
            article.save(update_fields=["upvote_count"])
            return Response({"upvote_count": article.upvote_count, "upvoted": True})


class ArticleUpvoteStatusView(APIView):
    """GET: upvote count + current user's upvote state."""
    permission_classes = [AllowAny]

    def get(self, request, article_id):
        article = _get_article_for_engagement(article_id, request)
        upvoted = False
        if request.user.is_authenticated:
            upvoted = ArticleUpvote.objects.filter(article=article, user=request.user).exists()
        return Response({
            "upvote_count": article.upvote_count,
            "upvoted": upvoted,
        })


class ArticleSuggestView(APIView):
    """POST: submit a structured suggestion. Auth required. Rate limit per user per article per 24h (no throttling for now)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, article_id):
        article = _get_article_for_engagement(article_id, request)
        type_val = (request.data.get("type") or "").strip()
        content = (request.data.get("content") or "").strip()[:150]
        valid_types = [c[0] for c in ArticleSuggestion._meta.get_field("type").choices]
        if type_val not in valid_types:
            return Response({"type": "Invalid or missing type."}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({"content": "Required (max 150 characters)."}, status=status.HTTP_400_BAD_REQUEST)
        is_anonymous = bool(request.data.get("is_anonymous", False))
        ArticleSuggestion.objects.create(
            article=article,
            user=None if is_anonymous else request.user,
            type=type_val,
            content=content,
            is_anonymous=is_anonymous,
        )
        return Response({"success": True}, status=status.HTTP_201_CREATED)


class ArticleViewIncrementView(APIView):
    """POST: increment view count. Anonymous allowed. Deduplication is client-side (sessionStorage)."""
    permission_classes = [AllowAny]

    def post(self, request, article_id):
        article = _get_article_for_engagement(article_id, request)
        Article.objects.filter(pk=article.pk).update(view_count=F("view_count") + 1)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class ArticleSuggestionsListView(APIView):
    """GET: list suggestions for an article. Author or admin/moderator only."""
    permission_classes = [IsAuthenticated]

    def get(self, request, article_id):
        article = get_object_or_404(Article, pk=article_id)
        is_author = str(article.author_id_id) == str(request.user.id) if article.author_id_id else False
        is_admin = getattr(request.user, "role", None) in ("admin", "moderator")
        if not (is_author or is_admin):
            return Response(status=status.HTTP_403_FORBIDDEN)
        suggestions = ArticleSuggestion.objects.filter(article=article).order_by("-created_at")
        data = [
            {
                "id": str(s.id),
                "type": s.type,
                "content": s.content,
                "is_anonymous": s.is_anonymous,
                "reviewed": s.reviewed,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suggestions
        ]
        return Response(data)


class CampusArticleBreakdownView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            Article.objects
            .filter(status="pending_review")
            .values("campus_name", "author_username")
            .annotate(article_count=Count("id"))
            .order_by("-article_count")
        )
        breakdown = defaultdict(lambda: {"article_count": 0, "authors": []})
        for row in qs:
            campus = row["campus_name"] or "Unknown"
            breakdown[campus]["article_count"] += row["article_count"]
            breakdown[campus]["authors"].append({"username": row["author_username"], "article_count": row["article_count"]})
        return Response(breakdown, status=status.HTTP_200_OK)