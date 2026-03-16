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
        ]

    def get_campus_slug(self, obj):
        return getattr(obj.campus_id, "slug", None)


class ArticleAdminDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="author_id", read_only=True)
    campus_name = serializers.CharField(read_only=True)

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
            "topic",
            "author",
            "author_username",
            "campus_name",
            "campus_id",
            "upvote_count",
            "view_count",
            "cover_image",
            "images",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "author",           
            "campus_name",      
            "upvote_count",
            "view_count",
        ]