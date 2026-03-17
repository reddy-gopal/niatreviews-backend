from rest_framework import serializers
from .models import Article
from accounts.models import User


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ArticleAdminListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="author_id", read_only=True)
    campus_name = serializers.CharField(read_only=True)
    campus_slug = serializers.SerializerMethodField()
    ai_confident_score = serializers.FloatField(read_only=True)
    ai_feedback = serializers.JSONField(read_only=True)
    ai_reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "status",
            "created_at",
            "updated_at",
            "category",
            "author",
            "campus_name",
            "campus_slug",
            "upvote_count",
            "view_count",
            "featured",
            "ai_confident_score",
            "ai_feedback",
            "ai_reviewed_at",
        ]

    def get_campus_slug(self, obj):
        return getattr(obj.campus_id, "slug", None)


class ArticleAdminDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="author_id", read_only=True)
    campus_name = serializers.CharField(read_only=True)
    ai_confident_score = serializers.FloatField(read_only=True)
    ai_feedback = serializers.JSONField(read_only=True)
    ai_reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "body",
            "excerpt",
            "status",
            "rejection_reason",
            "featured",
            "created_at",
            "updated_at",
            "category",
            "category_fk",
            "subcategory",
            "subcategory_other",
            "topic",
            "author",
            "author_username",
            "campus_name",
            "campus_id",
            "upvote_count",
            "view_count",
            "cover_image",
            "images",
            "ai_confident_score",
            "ai_feedback",
            "ai_reviewed_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "author",           
            "campus_name",      
            "upvote_count",
            "view_count",
        ]