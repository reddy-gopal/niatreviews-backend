from django.utils import timezone
from rest_framework import serializers

from .models import Article, Category, Club, GUIDE_TOPIC_CHOICES, STATUS_CHOICES, Subcategory

def _get_category_slugs():
    """Valid category slugs from DB only (no mock/hardcoded list)."""
    return list(Category.objects.values_list("slug", flat=True))


GUIDE_TOPIC_VALUES = [c[0] for c in GUIDE_TOPIC_CHOICES]


def _validate_subcategory_for_category(cat, attrs, campus_id=None, require_subcategory=False):
    """
    Validate subcategory/subcategory_other using campus-aware scope:
    - Prefer campus-scoped subcategories when present for given category+campus.
    - Fall back to global subcategories (campus=None).
    """
    base_qs = Subcategory.objects.filter(category=cat)
    campus_scoped_exists = bool(campus_id) and base_qs.filter(campus_id=campus_id).exists()
    scoped_qs = (
        base_qs.filter(campus_id=campus_id)
        if campus_scoped_exists
        else base_qs.filter(campus__isnull=True)
    )
    subs = list(scoped_qs.order_by("display_order", "slug"))
    if not subs:
        return
    valid_slugs = {s.slug for s in subs}
    requires_other = {s.slug for s in subs if s.requires_other}
    sub = (attrs.get("subcategory") or "").strip()
    other = (attrs.get("subcategory_other") or "").strip()
    if require_subcategory and not sub:
        raise serializers.ValidationError(
            {"subcategory": f"Please select a subcategory for {cat.name}."}
        )
    if sub and sub not in valid_slugs:
        raise serializers.ValidationError({"subcategory": "Invalid subcategory selection."})
    if sub and sub in requires_other and not other:
        raise serializers.ValidationError(
            {"subcategory_other": "Please specify the name for Others."}
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ClubListSerializer(serializers.ModelSerializer):
    campus_id = serializers.UUIDField(read_only=True)
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    article_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Club
        fields = [
            "id",
            "campus_id",
            "campus_name",
            "name",
            "slug",
            "type",
            "about",
            "open_to_all",
            "member_count",
            "cover_image",
            "article_count",
            "is_active",
            "updated_at",
        ]


class ClubDetailSerializer(serializers.ModelSerializer):
    campus_id = serializers.UUIDField(read_only=True)
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = Club
        fields = [
            "id",
            "campus_id",
            "campus_name",
            "name",
            "slug",
            "type",
            "about",
            "activities",
            "achievements",
            "open_to_all",
            "how_to_join",
            "email",
            "instagram",
            "founded_year",
            "member_count",
            "logo_url",
            "cover_image",
            "verified_at",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ArticleListSerializer(serializers.ModelSerializer):
    updated_days = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "campus_id",
            "campus_name",
            "category",
            "category_id",
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "images",
            "status",
            "featured",
            "upvote_count",
            "view_count",
            "is_global_guide",
            "topic",
            "subcategory",
            "subcategory_other",
            "author_username",
            "published_at",
            "updated_at",
            "updated_days",
        ]

    def get_updated_days(self, obj):
        delta = (timezone.now() - obj.updated_at).days
        return max(0, delta)

    def get_category_id(self, obj):
        return obj.category_fk_id


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + [
            "body",
            "rejection_reason",
            "reviewed_at",
            "created_at",
        ]


class ArticleWriteSerializer(serializers.Serializer):
    campus_id = serializers.UUIDField(allow_null=True, required=False)
    campus_name = serializers.CharField(max_length=200, allow_blank=True, required=False)
    category = serializers.CharField(max_length=50, required=False, allow_blank=True)
    category_id = serializers.CharField(allow_null=True, required=False)  # UUID from Category model
    title = serializers.CharField(max_length=500, allow_blank=True, required=False)
    excerpt = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    body = serializers.CharField(allow_blank=True, required=False)
    cover_image = serializers.URLField(allow_blank=True, required=False)
    images = serializers.ListField(child=serializers.URLField(allow_blank=True), allow_empty=True, required=False)
    is_global_guide = serializers.BooleanField(default=False, required=False)
    topic = serializers.ChoiceField(choices=GUIDE_TOPIC_VALUES, allow_blank=True, required=False)
    subcategory = serializers.CharField(max_length=80, allow_blank=True, required=False)
    subcategory_other = serializers.CharField(max_length=200, allow_blank=True, required=False)
    save_as_draft = serializers.BooleanField(default=False, required=False)

    def validate_cover_image(self, value):
        """Ensure cover_image is either a valid URL or empty"""
        if value and not value.startswith(('http://', 'https://')):
            return ""
        return value

    def validate_images(self, value):
        """Filter out invalid URLs from images list"""
        if not value:
            return []
        valid_images = []
        for img_url in value:
            if img_url and isinstance(img_url, str) and img_url.strip() and img_url.startswith(('http://', 'https://')):
                valid_images.append(img_url.strip())
        return valid_images

    def validate_campus_id(self, value):
        """Normalize empty values to None for optional campus binding."""
        if value == "":
            return None
        return value

    def validate_category_id(self, value):
        """Ensure category_id is a valid UUID string or None."""
        if value is None or value == "":
            return None
        return value

    def validate_category(self, value):
        """Ensure category slug exists in Category table (real data only)."""
        if not (value or "").strip():
            return value
        slug = (value or "").strip()
        valid_slugs = _get_category_slugs()
        if slug not in valid_slugs:
            raise serializers.ValidationError(
                {"category": f"Invalid section. Must be one of: {', '.join(valid_slugs)}."}
            )
        return slug

    def validate(self, attrs):
        is_global = attrs.get("is_global_guide", False)
        campus_id = attrs.get("campus_id")
        request = self.context.get("request")
        is_founding_editor = request and getattr(request.user, "role", None) == "founding_editor"

        if is_global is True:
            if campus_id is not None:
                raise serializers.ValidationError({"campus_id": "Must be null when is_global_guide is True."})
        else:
            if not self.partial and campus_id is None and not attrs.get("save_as_draft") and not is_founding_editor:
                raise serializers.ValidationError({"campus_id": "Please select a campus."})
            if self.partial and "campus_id" in attrs and attrs.get("is_global_guide", True) is False and campus_id is None and not is_founding_editor:
                raise serializers.ValidationError({"campus_id": "Please select a campus."})
        
        save_as_draft = attrs.get("save_as_draft", False)
        body = attrs.get("body", "")
        category_id = attrs.get("category_id")
        category_slug = (attrs.get("category") or "").strip()
        resolved_category = None

        # Resolve category from slug when only category (no category_id) is sent
        if category_slug and category_id is None:
            try:
                cat = Category.objects.get(slug=category_slug)
                attrs["_resolved_category"] = cat
                resolved_category = cat
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category": "Invalid section."})

        if not save_as_draft:
            if len((body or "").strip()) < 100:
                raise serializers.ValidationError({"body": "At least 100 characters required when submitting for review."})
            if not (attrs.get("title") or "").strip():
                raise serializers.ValidationError({"title": "Title is required when submitting for review."})
            if category_id is None and not attrs.get("category"):
                raise serializers.ValidationError({"category_id": "Section is required when submitting for review."})
            if category_id is not None:
                try:
                    cat = Category.objects.get(pk=category_id)
                    attrs["_resolved_category"] = cat
                    attrs["category"] = cat.slug
                    resolved_category = cat
                    _validate_subcategory_for_category(
                        cat, attrs, campus_id=attrs.get("campus_id"), require_subcategory=True
                    )
                except Category.DoesNotExist:
                    raise serializers.ValidationError({"category_id": "Invalid section."})
        elif category_id is not None:
            try:
                cat = Category.objects.get(pk=category_id)
                attrs["_resolved_category"] = cat
                attrs["category"] = cat.slug
                resolved_category = cat
                _validate_subcategory_for_category(
                    cat, attrs, campus_id=attrs.get("campus_id"), require_subcategory=False
                )
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category_id": "Invalid section."})

        if resolved_category is not None and category_id is None:
            _validate_subcategory_for_category(
                resolved_category,
                attrs,
                campus_id=attrs.get("campus_id"),
                require_subcategory=not save_as_draft,
            )

        if resolved_category is None:
            resolved_category = attrs.get("_resolved_category")

        return attrs


class ModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("published", "Published"), ("rejected", "Rejected")])
    rejection_reason = serializers.CharField(allow_blank=True, required=False)
    featured = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if attrs.get("status") == "rejected" and not attrs.get("rejection_reason", "").strip():
            raise serializers.ValidationError({"rejection_reason": "Required when rejecting."})
        return attrs


