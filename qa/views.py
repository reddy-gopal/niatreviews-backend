import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OuterRef, Subquery
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes

from .models import Question, Answer, QuestionVote, AnswerVote
from .category_classifier import CATEGORIES
from .permissions import IsAuthorOrReadOnly, IsVerifiedSenior


def _user_is_verified_senior(user):
    """True if user is a verified senior (flag or approved SeniorProfile). Syncs flag if stale."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_verified_senior", False):
        return True
    try:
        profile = user.senior_profile
        if getattr(profile, "status", None) == "approved":
            user.is_verified_senior = True
            user.save(update_fields=["is_verified_senior"])
            return True
    except ObjectDoesNotExist:
        pass
    return False
from .serializers import (
    QuestionListSerializer,
    QuestionDetailSerializer,
    QuestionCreateUpdateSerializer,
    AnswerSerializer,
    FAQSerializer,
)
from .pagination import QuestionCursorPagination

logger = logging.getLogger(__name__)

VALUE_UP = 1


@api_view(["GET"])
@permission_classes([AllowAny])
def question_categories_view(request):
    """GET /api/questions/categories/ — return list of question categories (from classifier)."""
    return Response({"categories": list(CATEGORIES)})


VALUE_DOWN = -1


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.select_related(
        "author", "answer", "answer__author"
    ).order_by("-created_at")
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    pagination_class = QuestionCursorPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_permissions(self):
        # Answer/vote actions: only need to be authenticated; answer() enforces verified senior / answer author
        if self.action in ("answer", "answer_upvote", "answer_downvote"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticatedOrReadOnly(), IsAuthorOrReadOnly()]

    def get_serializer_class(self):
        if self.action == "list":
            return QuestionListSerializer
        if self.action in ("create", "update", "partial_update"):
            return QuestionCreateUpdateSerializer
        return QuestionDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("followups", "followups__author")
        answered = self.request.query_params.get("answered")
        if answered == "true":
            qs = qs.filter(is_answered=True)
        elif answered == "false":
            qs = qs.filter(is_answered=False)
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(author_id=author)
        answer_author = self.request.query_params.get("answer_author")
        if answer_author:
            qs = qs.filter(is_answered=True, answer__author_id=answer_author)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        if self.request.user.is_authenticated:
            my_vote = QuestionVote.objects.filter(
                question=OuterRef("pk"),
                user=self.request.user,
            ).values("value")[:1]
            qs = qs.annotate(user_vote=Subquery(my_vote))
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _ensure_can_edit_or_delete(self, question):
        """Raise 403 if question already has an answer (only author can edit/delete before answer)."""
        if question.is_answered:
            raise PermissionDenied(
                "Cannot edit or delete this question after a senior has answered."
            )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_can_edit_or_delete(instance)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_can_edit_or_delete(instance)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_can_edit_or_delete(instance)
        return super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Question.objects.filter(pk=instance.pk).update(view_count=instance.view_count + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _vote_response_question(self, question, user):
        vote = QuestionVote.objects.filter(question=question, user=user).first()
        question.refresh_from_db()
        return {
            "upvote_count": question.upvote_count,
            "downvote_count": question.downvote_count,
            "user_vote": vote.value if vote else None,
        }

    @action(detail=True, methods=["post", "delete"], url_path="upvote")
    def upvote(self, request, slug=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        question = self.get_object()
        if request.method == "POST":
            QuestionVote.objects.update_or_create(
                question=question,
                user=request.user,
                defaults={"value": VALUE_UP},
            )
        else:
            QuestionVote.objects.filter(question=question, user=request.user).delete()
        return Response(self._vote_response_question(question, request.user))

    @action(detail=True, methods=["post", "delete"], url_path="downvote")
    def downvote(self, request, slug=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        question = self.get_object()
        if request.method == "POST":
            QuestionVote.objects.update_or_create(
                question=question,
                user=request.user,
                defaults={"value": VALUE_DOWN},
            )
        else:
            QuestionVote.objects.filter(question=question, user=request.user).delete()
        return Response(self._vote_response_question(question, request.user))

    @action(detail=True, methods=["get", "post", "patch", "delete"], url_path="answer")
    def answer(self, request, slug=None):
        question = self.get_object()
        if request.method == "GET":
            try:
                ans = question.answer
                ser = AnswerSerializer(ans)
                data = ser.data
                if request.user.is_authenticated:
                    v = ans.votes.filter(user=request.user).first()
                    data["user_vote"] = v.value if v else None
                else:
                    data["user_vote"] = None
                return Response(data)
            except Answer.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            if not _user_is_verified_senior(request.user):
                return Response(
                    {"detail": "Only verified NIAT seniors can answer questions."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if hasattr(question, "answer"):
                return Response(
                    {"detail": "This question already has an answer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            body = request.data.get("body") or ""
            if not body.strip():
                return Response(
                    {"body": ["This field may not be blank."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ans = Answer.objects.create(
                question=question,
                author=request.user,
                body=body.strip(),
            )
            return Response(AnswerSerializer(ans).data, status=status.HTTP_201_CREATED)

        try:
            ans = question.answer
        except Answer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if ans.author != request.user:
            return Response(
                {"detail": "You can only edit or delete your own answer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "PATCH":
            body = request.data.get("body")
            if body is not None:
                ans.body = body.strip()
                ans.save(update_fields=["body", "updated_at"])
            return Response(AnswerSerializer(ans).data)

        if request.method == "DELETE":
            ans.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post", "delete"], url_path="answer/upvote")
    def answer_upvote(self, request, slug=None):
        return self._answer_vote(request, slug, VALUE_UP, "upvote")

    @action(detail=True, methods=["post", "delete"], url_path="answer/downvote")
    def answer_downvote(self, request, slug=None):
        return self._answer_vote(request, slug, VALUE_DOWN, "downvote")

    def _answer_vote(self, request, slug, value, label):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        question = self.get_object()
        try:
            ans = question.answer
        except Answer.DoesNotExist:
            return Response(
                {"detail": "No answer to vote on."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if request.method == "POST":
            AnswerVote.objects.update_or_create(
                answer=ans,
                user=request.user,
                defaults={"value": value},
            )
        else:
            AnswerVote.objects.filter(answer=ans, user=request.user).delete()
        ans.refresh_from_db()
        data = AnswerSerializer(ans).data
        v = ans.votes.filter(user=request.user).first()
        data["user_vote"] = v.value if v else None
        return Response(data)


class FAQListView(APIView):
    """GET /api/faqs/ — list questions with is_faq=True, ordered by faq_order."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            Question.objects.filter(is_faq=True)
            .select_related("author")
            .prefetch_related("answer")
            .order_by("faq_order", "-created_at")
        )
        if request.user.is_authenticated:
            my_vote = QuestionVote.objects.filter(
                question=OuterRef("pk"),
                user=request.user,
            ).values("value")[:1]
            qs = qs.annotate(user_vote=Subquery(my_vote))
        serializer = FAQSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
