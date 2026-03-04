from django.utils import timezone
from rest_framework import serializers

from .models import Article, ArticleComment, Category, CATEGORY_CHOICES, GUIDE_TOPIC_CHOICES, STATUS_CHOICES, Subcategory

CATEGORY_VALUES = [c[0] for c in CATEGORY_CHOICES]
GUIDE_TOPIC_VALUES = [c[0] for c in GUIDE_TOPIC_CHOICES]


def _validate_subcategory_for_category(cat, attrs, require_subcategory=False):
    """Validate subcategory and subcategory_other against Subcategory model for the given category."""
    subs = list(Subcategory.objects.filter(category=cat).order_by("display_order", "slug"))
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
            "helpful_count",
            "is_global_guide",
            "topic",
            "club_id",
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
    comments_count = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + [
            "body",
            "rejection_reason",
            "reviewed_at",
            "created_at",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return ArticleComment.objects.filter(article=obj, is_visible=True).count()


class ArticleWriteSerializer(serializers.Serializer):
    campus_id = serializers.IntegerField(allow_null=True, required=False)
    campus_name = serializers.CharField(max_length=200, allow_blank=True, required=False)
    category = serializers.ChoiceField(choices=CATEGORY_VALUES, required=False)
    category_id = serializers.IntegerField(allow_null=True, required=False)
    title = serializers.CharField(max_length=500, allow_blank=True, required=False)
    excerpt = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    body = serializers.CharField(allow_blank=True, required=False)
    cover_image = serializers.URLField(allow_blank=True, required=False)
    images = serializers.ListField(child=serializers.URLField(allow_blank=True), allow_empty=True, required=False)
    is_global_guide = serializers.BooleanField(default=False, required=False)
    topic = serializers.ChoiceField(choices=GUIDE_TOPIC_VALUES, allow_blank=True, required=False)
    club_id = serializers.IntegerField(allow_null=True, required=False)
    subcategory = serializers.CharField(max_length=80, allow_blank=True, required=False)
    subcategory_other = serializers.CharField(max_length=200, allow_blank=True, required=False)
    save_as_draft = serializers.BooleanField(default=False, required=False)

    def validate(self, attrs):
        is_global = attrs.get("is_global_guide", False)
        campus_id = attrs.get("campus_id")
        campus_name = attrs.get("campus_name", "")
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
                    _validate_subcategory_for_category(cat, attrs, require_subcategory=True)
                except Category.DoesNotExist:
                    raise serializers.ValidationError({"category_id": "Invalid section."})
        elif category_id is not None:
            try:
                cat = Category.objects.get(pk=category_id)
                attrs["_resolved_category"] = cat
                attrs["category"] = cat.slug
                _validate_subcategory_for_category(cat, attrs, require_subcategory=False)
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category_id": "Invalid section."})
        return attrs


class ModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[("published", "Published"), ("rejected", "Rejected")])
    rejection_reason = serializers.CharField(allow_blank=True, required=False)
    featured = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if attrs.get("status") == "rejected" and not attrs.get("rejection_reason", "").strip():
            raise serializers.ValidationError({"rejection_reason": "Required when rejecting."})
        return attrs


class ArticleCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleComment
        fields = ["id", "author_username", "body", "created_at"]
