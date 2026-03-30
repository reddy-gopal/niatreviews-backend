from rest_framework import serializers
from .models import Article, ClubCampus
from accounts.models import User


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class AuthorArticleCountSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    campus_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "article_count", "campus_name"]

    def get_campus_name(self, obj):
        if hasattr(obj, "founding_editor_profile") and obj.founding_editor_profile.campus_name:
            return obj.founding_editor_profile.campus_name
        
        first_article = obj.articles.filter(campus_name__isnull=False).exclude(campus_name="").first()
        if first_article:
            return first_article.campus_name
        return "Unknown"


class ArticleAdminListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="author_id", read_only=True)
    reviewed_by = AuthorSerializer(source="reviewed_by_id", read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    campus_name = serializers.CharField(read_only=True)
    campus_slug = serializers.SerializerMethodField()
    ai_confident_score = serializers.FloatField(read_only=True)
    ai_feedback = serializers.JSONField(read_only=True)
    ai_reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "slug",
            "title",
            "status",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "created_at",
            "updated_at",
            "category",
            "author",
            "reviewed_by",
            "reviewed_at",
            "campus_name",
            "campus_slug",
            "upvote_count",
            "view_count",
            "ai_generated",
            "featured",
            "ai_confident_score",
            "ai_feedback",
            "ai_reviewed_at",
        ]

    def get_campus_slug(self, obj):
        return getattr(obj.campus_id, "slug", None)


class ArticleAdminDetailSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(source="author_id", read_only=True)
    reviewed_by = AuthorSerializer(source="reviewed_by_id", read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True)
    campus_name = serializers.CharField(read_only=True)
    ai_confident_score = serializers.FloatField(read_only=True)
    ai_feedback = serializers.JSONField(read_only=True)
    ai_reviewed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "slug",
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
            "meta_title",
            "meta_description",
            "meta_keywords",
            "topic",
            "author",
            "reviewed_by",
            "author_username",
            "campus_name",
            "campus_id",
            "upvote_count",
            "view_count",
            "ai_generated",
            "cover_image",
            "images",
            "ai_confident_score",
            "ai_feedback",
            "ai_reviewed_at",
            "reviewed_at",
        ]


class ClubCampusAdminSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="club.name", read_only=True)
    club_slug = serializers.CharField(source="club.slug", read_only=True)
    campus_name = serializers.CharField(source="campus.name", read_only=True)

    class Meta:
        model = ClubCampus
        fields = [
            "id",
            "club",
            "club_name",
            "club_slug",
            "campus",
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
        read_only_fields = [
            "id",
            "created_at",
            "author",           
            "campus_name",      
            "upvote_count",
            "view_count",
        ]