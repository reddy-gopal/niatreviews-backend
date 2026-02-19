"""
Feed of answers from seniors the current user follows.
GET /api/feed/answers/ — cursor-paginated, authenticated only.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from verification.models import SeniorFollow

from .models import Answer
from .pagination import QuestionCursorPagination
from .serializers import AnswerSerializer


class FeedAnswersView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = QuestionCursorPagination

    def get(self, request):
        following_senior_ids = SeniorFollow.objects.filter(
            follower=request.user
        ).values_list("senior_id", flat=True)
        qs = (
            Answer.objects.filter(author_id__in=following_senior_ids)
            .select_related("question", "author")
            .order_by("-created_at")
        )
        paginator = self.pagination_class()
        paginator.ordering = "-created_at"
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = AnswerSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)
        serializer = AnswerSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
