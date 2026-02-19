from django.db.models import OuterRef, Subquery
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination

from .models import QuestionVote
from .search import search_questions, suggestion_questions
from .serializers import QuestionListSerializer


class QuestionSearchPagination(CursorPagination):
    page_size = 20
    ordering = "-created_at"
    cursor_query_param = "cursor"


def _annotate_user_vote(qs, user):
    if not user or not user.is_authenticated:
        return qs
    my_vote = QuestionVote.objects.filter(
        question=OuterRef("pk"),
        user=user,
    ).values("value")[:1]
    return qs.annotate(user_vote=Subquery(my_vote))


@api_view(["GET"])
@permission_classes([AllowAny])
def search_questions_view(request):
    """GET /api/questions/search/?q=...&order_by=-rank|-created_at|-upvote_count"""
    q = request.query_params.get("q", "").strip()
    order_by = request.query_params.get("order_by", "-rank")
    qs = search_questions(q, order_by=order_by)
    qs = _annotate_user_vote(qs, request.user)
    paginator = QuestionSearchPagination()
    page = paginator.paginate_queryset(qs, request)
    if page is not None:
        serializer = QuestionListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
    serializer = QuestionListSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_suggestions_view(request):
    """GET /api/questions/search/suggestions/?q=..."""
    q = request.query_params.get("q", "").strip()
    limit = min(20, int(request.query_params.get("limit", 10)))
    qs = suggestion_questions(q, limit=limit)
    qs = _annotate_user_vote(qs, request.user)
    serializer = QuestionListSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)
