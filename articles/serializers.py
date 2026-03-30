from django.utils import timezone
from rest_framework import serializers

from accounts.models import FoundingEditorProfile
from .models import Article, Category, Club, ClubCampus, GUIDE_TOPIC_CHOICES, STATUS_CHOICES, Subcategory

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
    # club-directory subcategories are dynamic from Club table (campus-scoped via M2M)
    if cat.slug == "club-directory":
        sub = (attrs.get("subcategory") or "").strip()
        if require_subcategory and not sub:
            raise serializers.ValidationError(
                {"subcategory": f"Please select a subcategory for {cat.name}."}
            )
        if not sub:
            return
        if not campus_id:
            raise serializers.ValidationError(
                {"campus_id": "Please select a campus for club-directory articles."}
            )
        exists = ClubCampus.objects.filter(
            club__slug=sub,
            campus_id=campus_id,
            is_active=True,
            club__is_active=True,
        ).exists()
        if not exists:
            raise serializers.ValidationError(
                {"subcategory": "This club does not have an active chapter at the selected campus."}
            )
        return

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
    objective = serializers.CharField(source="about", read_only=True)
    campus_id = serializers.SerializerMethodField()
    campus_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    open_to_all = serializers.SerializerMethodField()
    president_name = serializers.SerializerMethodField()
    vice_president_name = serializers.SerializerMethodField()
    chapter_description = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    chapter_is_active = serializers.SerializerMethodField()
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
            "objective",
            "about",
            "member_count",
            "open_to_all",
            "president_name",
            "vice_president_name",
            "chapter_description",
            "contact_email",
            "chapter_is_active",
            "cover_image",
            "article_count",
            "is_active",
            "updated_at",
        ]

    def _current_chapter(self, obj):
        chapter_list = getattr(obj, "current_chapter", None)
        if chapter_list:
            return chapter_list[0]
        return None

    def get_member_count(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.member_count if chapter else 0

    def get_campus_id(self, obj):
        chapter = self._current_chapter(obj)
        return str(chapter.campus_id) if chapter else None

    def get_campus_name(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.campus.name if chapter else ""

    def get_open_to_all(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.open_to_all if chapter else False

    def get_president_name(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.president_name if chapter else ""

    def get_vice_president_name(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.vice_president_name if chapter else ""

    def get_chapter_description(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.chapter_description if chapter else ""

    def get_contact_email(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.contact_email if chapter else ""

    def get_chapter_is_active(self, obj):
        chapter = self._current_chapter(obj)
        return chapter.is_active if chapter else False


class ClubCampusSerializer(serializers.ModelSerializer):
    campus_id = serializers.UUIDField(source="campus.id", read_only=True)
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = ClubCampus
        fields = [
            "campus_id",
            "campus_name",
            "member_count",
            "open_to_all",
            "president_name",
            "president_email",
            "president_photo",
            "vice_president_name",
            "vice_president_email",
            "vice_president_photo",
            "chapter_description",
            "contact_email",
            "is_active",
            "updated_at",
        ]


class ClubDetailSerializer(serializers.ModelSerializer):
    campus_chapters = ClubCampusSerializer(many=True, read_only=True)
    objective = serializers.CharField(source="about", read_only=True)

    class Meta:
        model = Club
        fields = [
            "id",
            "name",
            "slug",
            "type",
            "objective",
            "about",
            "activities",
            "achievements",
            "how_to_join",
            "instagram",
            "founded_year",
            "logo_url",
            "cover_image",
            "verified_at",
            "is_active",
            "campus_chapters",
            "created_at",
            "updated_at",
        ]


class ArticleListSerializer(serializers.ModelSerializer):
    updated_days = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    author_linkedin_profile = serializers.SerializerMethodField()

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
            "meta_title",
            "meta_description",
            "meta_keywords",
            "author_username",
            "author_linkedin_profile",
            "published_at",
            "updated_at",
            "updated_days",
        ]

    def get_updated_days(self, obj):
        delta = (timezone.now() - obj.updated_at).days
        return max(0, delta)

    def get_category_id(self, obj):
        return obj.category_fk_id

    def get_author_linkedin_profile(self, obj):
        linkedin = (
            FoundingEditorProfile.objects
            .filter(user__username=obj.author_username)
            .values_list("linkedin_profile", flat=True)
            .first()
        )
        if not linkedin:
            return None
        value = str(linkedin).strip()
        return value or None


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
    meta_title = serializers.CharField(max_length=255, allow_blank=True, required=False)
    meta_description = serializers.CharField(allow_blank=True, required=False)
    meta_keywords = serializers.ListField(
        child=serializers.CharField(max_length=120, allow_blank=False),
        allow_empty=True,
        required=False,
    )
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

    def validate_meta_keywords(self, value):
        """Normalize keywords: trim, drop empties, deduplicate (case-insensitive), cap count."""
        if not value:
            return []
        normalized = []
        seen = set()
        for item in value:
            kw = (item or "").strip()
            if not kw:
                continue
            key = kw.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(kw)
        return normalized[:25]

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


