"""
Follow-up thread under answered questions. Only question author can create.
Edit: follow-up author. Delete: follow-up author OR answer author OR staff.
"""
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Answer, FollowUp, Question
from .pagination import FollowUpCursorPagination
from .serializers import FollowUpSerializer


def error_response(code: str, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    return Response({"code": code, "detail": detail}, status=status_code)


def get_question_by_slug(slug):
    return (
        Question.objects.filter(slug=slug)
        .select_related("author")
        .prefetch_related(Prefetch("answers", queryset=Answer.objects.order_by("created_at").select_related("author")))
        .first()
    )


class FollowUpListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FollowUpCursorPagination

    def get(self, request, slug):
        question = get_question_by_slug(slug)
        if not question:
            return error_response("NOT_FOUND", "Question not found.", status.HTTP_404_NOT_FOUND)
        qs = FollowUp.objects.filter(question=question).select_related("author").order_by("created_at", "id")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = FollowUpSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        serializer = FollowUpSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, slug):
        if not request.user.is_authenticated:
            return error_response("UNAUTHORIZED", "Authentication required.", status.HTTP_401_UNAUTHORIZED)
        question = get_question_by_slug(slug)
        if not question:
            return error_response("NOT_FOUND", "Question not found.", status.HTTP_404_NOT_FOUND)
        if not question.answers.exists():
            return error_response("NO_ANSWER_YET", "At least one answer must exist before posting a follow-up.")
        if question.author_id != request.user.id:
            return error_response("FORBIDDEN", "Only the question author can post follow-ups.", status.HTTP_403_FORBIDDEN)
        body = (request.data.get("body") or "").strip()
        if not body:
            return error_response("VALIDATION_ERROR", "Body may not be blank.")
        followup = FollowUp.objects.create(question=question, author=request.user, body=body)
        serializer = FollowUpSerializer(followup, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FollowUpDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _get_followup(self, slug, pk):
        question = get_question_by_slug(slug)
        if not question:
            return None, None, "NOT_FOUND"
        try:
            followup = FollowUp.objects.select_related("author", "question").get(pk=pk, question=question)
        except FollowUp.DoesNotExist:
            return question, None, "NOT_FOUND"
        return question, followup, None

    def get(self, request, slug, pk):
        question, followup, err = self._get_followup(slug, pk)
        if err:
            return error_response("NOT_FOUND", "Follow-up not found.", status.HTTP_404_NOT_FOUND)
        serializer = FollowUpSerializer(followup, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, slug, pk):
        if not request.user.is_authenticated:
            return error_response("UNAUTHORIZED", "Authentication required.", status.HTTP_401_UNAUTHORIZED)
        question, followup, err = self._get_followup(slug, pk)
        if err:
            return error_response("NOT_FOUND", "Follow-up not found.", status.HTTP_404_NOT_FOUND)
        if followup.author_id != request.user.id:
            return error_response("FORBIDDEN", "Only the follow-up author can edit it.", status.HTTP_403_FORBIDDEN)
        body = request.data.get("body")
        if body is not None:
            body = body.strip()
            if not body:
                return error_response("VALIDATION_ERROR", "Body may not be blank.")
            followup.body = body
            followup.save(update_fields=["body", "updated_at"])
        serializer = FollowUpSerializer(followup, context={"request": request})
        return Response(serializer.data)

    def delete(self, request, slug, pk):
        if not request.user.is_authenticated:
            return error_response("UNAUTHORIZED", "Authentication required.", status.HTTP_401_UNAUTHORIZED)
        question, followup, err = self._get_followup(slug, pk)
        if err:
            return error_response("NOT_FOUND", "Follow-up not found.", status.HTTP_404_NOT_FOUND)
        answer_author_ids = list(question.answers.values_list("author_id", flat=True))
        can_delete = (
            followup.author_id == request.user.id
            or request.user.id in answer_author_ids
            or getattr(request.user, "is_staff", False)
        )
        if not can_delete:
            return error_response("FORBIDDEN", "You cannot delete this follow-up.", status.HTTP_403_FORBIDDEN)
        followup.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
