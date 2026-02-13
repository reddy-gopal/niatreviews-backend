import re
from django.utils.text import slugify
from rest_framework import serializers
from .models import Category, Tag, Post, Comment, PostVote, CommentUpvote
from accounts.serializers import UserSerializer


def extract_hashtags_from_text(text):
    """Extract unique hashtag words from text (#word). Returns list of lowercase names."""
    if not text:
        return []
    names = re.findall(r"#(\w+)", text, re.UNICODE)
    return list(dict.fromkeys(n.lower().strip() for n in names if n.strip()))


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "created_at"]

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "created_at"]

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False, write_only=True
    )
    slug = serializers.SlugField(required=False, max_length=300)
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "description", "image", "author", "category",
            "tags", "tag_ids", "upvote_count", "downvote_count", "comment_count",
            "is_published", "created_at", "updated_at", "user_vote",
        ]
        read_only_fields = ["upvote_count", "downvote_count", "comment_count"]

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        # Use annotated user_vote from view's get_queryset when present (avoids N+1)
        if hasattr(obj, "user_vote"):
            return obj.user_vote
        vote = PostVote.objects.filter(post_id=obj.id, user=request.user).first()
        return vote.value if vote else None

    def _sync_tags_from_description_and_ids(self, instance, description, tag_ids_list):
        """Merge tags from tag_ids and #hashtags in description."""
        tag_ids = set()
        for t in tag_ids_list or []:
            tag_ids.add(t.id if hasattr(t, "id") else t)
        for name in extract_hashtags_from_text(description or ""):
            slug = (slugify(name)[:50] or "tag").strip() or "tag"
            tag, _ = Tag.objects.get_or_create(
                slug=slug,
                defaults={"name": (name[:50] if name else slug)},
            )
            tag_ids.add(tag.id)
        instance.tags.set(tag_ids)

    def create(self, validated_data):
        request = self.context.get("request")
        tag_ids_list = list(validated_data.pop("tag_ids", []))
        if request and request.user:
            validated_data["author"] = request.user
        if not validated_data.get("slug"):
            base = slugify(validated_data["title"])[:300] or "post"
            slug = base
            i = 0
            while Post.objects.filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}" if len(base) < 290 else f"{base[:290]}-{i}"
            validated_data["slug"] = slug
        instance = super().create(validated_data)
        self._sync_tags_from_description_and_ids(
            instance, instance.description, tag_ids_list
        )
        return instance

    def update(self, instance, validated_data):
        tag_ids_list = validated_data.pop("tag_ids", None)
        if "slug" in validated_data and not validated_data["slug"]:
            validated_data["slug"] = slugify(instance.title)[:300] or "post"
        super().update(instance, validated_data)
        if tag_ids_list is not None:
            self._sync_tags_from_description_and_ids(
                instance, instance.description, list(tag_ids_list)
            )
        else:
            self._sync_tags_from_description_and_ids(
                instance, instance.description, list(instance.tags.values_list("id", flat=True))
            )
        return instance


class CommentMinimalSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "body", "author", "created_at"]

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "parent", "body", "upvote_count", "created_at", "updated_at"]
        read_only_fields = ["upvote_count"]

    def to_representation(self, instance):
        """Output parent as nested object so frontend buildTree works; include post_slug for links."""
        data = super().to_representation(instance)
        if instance.parent_id:
            data["parent"] = CommentMinimalSerializer(instance.parent).data
        else:
            data["parent"] = None
        if instance.post_id:
            data["post_slug"] = getattr(instance.post, "slug", None)
            data["post_title"] = getattr(instance.post, "title", None)
        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        validated_data["author"] = user
        return super().create(validated_data)

class CommentUpvoteSerializer(serializers.ModelSerializer):
    """
    Comment upvote: comment must be the exact comment being upvoted (reply or parent).
    When comment is passed in context (from URL), that is the source of truth; body comment
    is ignored to avoid accidentally upvoting parent instead of reply.
    """
    comment = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False)

    class Meta:
        model = CommentUpvote
        fields = ["id", "comment", "user", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate(self, attrs):
        """Require comment from body when not provided via context (URL)."""
        comment_from_context = self.context.get("comment")
        comment_from_body = attrs.get("comment")
        if comment_from_context is not None:
            attrs["comment"] = comment_from_context
            return attrs
        if not comment_from_body:
            raise serializers.ValidationError(
                {"comment": "Comment is required. Use the exact comment id (reply or parent) you intend to upvote."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else validated_data.get("user")
        comment = validated_data["comment"]
        return CommentUpvote.objects.create(comment=comment, user=user)

