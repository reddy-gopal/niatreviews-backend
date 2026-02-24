"""PostgreSQL full-text search for questions (search_vector + trigram fallback)."""
from django.db.models import F, Prefetch, Q
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchHeadline,
    TrigramSimilarity,
)

from .models import Answer, Question


def _answers_prefetch():
    return Prefetch(
        "answers",
        queryset=Answer.objects.order_by("created_at").select_related("author"),
    )


def _trigram_fallback(q, order_by):
    """Fallback when FTS returns no results: trigram similarity on title, then icontains."""
    qs = (
        Question.objects.select_related("author")
        .prefetch_related(_answers_prefetch())
        .annotate(similarity=TrigramSimilarity("title", q))
        .filter(similarity__gte=0.15)
        .order_by("-similarity", "-created_at")
    )
    if qs.exists():
        return qs
    qs = Question.objects.filter(
        Q(title__icontains=q) | Q(body__icontains=q)
    ).select_related("author").prefetch_related(_answers_prefetch())
    if order_by == "-upvote_count":
        qs = qs.order_by("-upvote_count", "-created_at")
    else:
        qs = qs.order_by("-created_at")
    return qs


def search_questions(query_string, order_by="-rank"):
    q = (query_string or "").strip()
    if not q:
        return Question.objects.none()

    search_query = SearchQuery(q, search_type="websearch", config="english")
    qs = (
        Question.objects.select_related("author")
        .prefetch_related(_answers_prefetch())
        .filter(search_vector=search_query)
        .annotate(
            rank=SearchRank(
                F("search_vector"),
                search_query,
                weights=[0.1, 0.2, 0.4, 1.0],
                normalization=2,
                cover_density=True,
            ),
            headline=SearchHeadline(
                "body",
                search_query,
                config="english",
                start_sel="<mark>",
                stop_sel="</mark>",
                max_words=50,
                min_words=15,
                max_fragments=3,
            ),
            title_headline=SearchHeadline(
                "title",
                search_query,
                config="english",
                start_sel="<mark>",
                stop_sel="</mark>",
            ),
        )
        .filter(rank__gte=0.01)
    )
    if order_by == "-rank":
        qs = qs.order_by("-rank", "-created_at")
    elif order_by == "-created_at":
        qs = qs.order_by("-created_at")
    elif order_by == "-upvote_count":
        qs = qs.order_by("-upvote_count", "-created_at")
    else:
        qs = qs.order_by("-rank", "-created_at")

    if not qs.exists():
        return _trigram_fallback(q, order_by)
    return qs


def suggestion_questions(query_string, limit=10):
    q = (query_string or "").strip()
    if not q:
        return Question.objects.none()
    limit = min(20, max(1, limit))

    search_query = SearchQuery(q, search_type="websearch", config="english")
    qs = (
        Question.objects.select_related("author")
        .prefetch_related(_answers_prefetch())
        .filter(search_vector=search_query)
        .annotate(
            rank=SearchRank(
                F("search_vector"),
                search_query,
                weights=[0.1, 0.2, 0.4, 1.0],
                normalization=2,
                cover_density=True,
            ),
        )
        .order_by("-rank", "-created_at")[:limit]
    )
    if qs.exists():
        return qs
    qs = (
        Question.objects.select_related("author")
        .prefetch_related(_answers_prefetch())
        .annotate(similarity=TrigramSimilarity("title", q))
        .filter(similarity__gte=0.1)
        .order_by("-similarity", "-created_at")[:limit]
    )
    return qs
