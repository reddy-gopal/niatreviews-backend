import uuid
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from .models import Answer, FollowUp, Question

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Minimal user for FollowUp author and similar nesting."""
    class Meta:
        model = User
        fields = ["id", "username", "is_verified_senior"]
        read_only_fields = fields


class FollowUpSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = FollowUp
        fields = ["id", "author", "body", "created_at", "updated_at", "can_edit", "can_delete"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_can_edit(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and obj.author_id == user.id

    def get_can_delete(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        answer = getattr(obj.question, "answer", None)
        answer_author_id = answer.author_id if answer else None
        return user.id in [obj.author_id, answer_author_id] or getattr(user, "is_staff", False)


class AnswerSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            "id",
            "body",
            "author",
            "upvote_count",
            "downvote_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["upvote_count", "downvote_count", "created_at", "updated_at"]

    def get_author(self, obj):
        return {
            "username": obj.author.username,
            "is_verified_senior": getattr(obj.author, "is_verified_senior", False),
        }


class QuestionListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    has_answer = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "slug",
            "title",
            "category",
            "author",
            "is_answered",
            "upvote_count",
            "downvote_count",
            "view_count",
            "created_at",
            "has_answer",
            "user_vote",
            "answer",
        ]

    def get_author(self, obj):
        return {"username": obj.author.username, "id": str(obj.author.id)}

    def get_has_answer(self, obj):
        return obj.is_answered

    def get_user_vote(self, obj):
        vote = getattr(obj, "user_vote", None)
        return vote

    def get_answer(self, obj):
        if not obj.is_answered:
            return None
        try:
            a = obj.answer
            data = AnswerSerializer(a).data
            if self.context.get("request") and self.context["request"].user.is_authenticated:
                vote = a.votes.filter(user=self.context["request"].user).first()
                data["user_vote"] = vote.value if vote else None
            else:
                data["user_vote"] = None
            return data
        except Answer.DoesNotExist:
            return None


class QuestionDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    followups = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "slug",
            "title",
            "body",
            "category",
            "author",
            "is_answered",
            "upvote_count",
            "downvote_count",
            "view_count",
            "is_faq",
            "faq_order",
            "created_at",
            "updated_at",
            "answer",
            "user_vote",
            "followups",
        ]

    def get_followups(self, obj):
        followups = getattr(obj, "followups_prefetched", None) or obj.followups.all()
        return FollowUpSerializer(followups, many=True, context=self.context).data

    def get_author(self, obj):
        return {"username": obj.author.username, "id": str(obj.author.id)}

    def get_answer(self, obj):
        try:
            a = obj.answer
            data = AnswerSerializer(a).data
            if self.context.get("request") and self.context["request"].user.is_authenticated:
                vote = a.votes.filter(user=self.context["request"].user).first()
                data["user_vote"] = vote.value if vote else None
            else:
                data["user_vote"] = None
            return data
        except Answer.DoesNotExist:
            return None

    def get_user_vote(self, obj):
        return getattr(obj, "user_vote", None)


class FAQSerializer(QuestionDetailSerializer):
    """Same as QuestionDetailSerializer; used for /api/faqs/ (always includes answer)."""
    pass


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["title", "body", "slug"]
        read_only_fields = ["slug"]

    def create(self, validated_data):
        title = validated_data.get("title", "")
        base = slugify(title)[:300] or "question"
        slug = base
        while Question.objects.filter(slug=slug).exists():
            slug = f"{base}-{uuid.uuid4().hex[:8]}"
        validated_data["slug"] = slug
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)
