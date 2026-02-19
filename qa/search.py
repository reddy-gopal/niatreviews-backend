"""Full-text search for questions (PostgreSQL FTS / SQLite FTS5 / icontains fallback)."""
from django.db import connection
from django.db.models import Prefetch, Q
from .models import Answer, Question


def _answers_prefetch():
    return Prefetch(
        "answers",
        queryset=Answer.objects.order_by("created_at").select_related("author"),
    )


def search_questions(query_string, order_by="-created_at"):
    if not query_string or not query_string.strip():
        return Question.objects.none()
    q = query_string.strip()

    # PostgreSQL: use full-text search with ranking
    if connection.vendor == "postgresql":
        try:
            from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

            search_vector = SearchVector("title", weight="A") + SearchVector("body", weight="B")
            search_query = SearchQuery(q, search_type="websearch")
            qs = (
                Question.objects.select_related("author")
                .prefetch_related(_answers_prefetch())
                .annotate(search_rank=SearchRank(search_vector, search_query))
                .filter(search_rank__gt=0)
            )
            if order_by == "-rank":
                qs = qs.order_by("-search_rank", "-created_at")
            elif order_by == "-created_at":
                qs = qs.order_by("-created_at")
            elif order_by == "-upvote_count":
                qs = qs.order_by("-upvote_count", "-created_at")
            else:
                qs = qs.order_by("-search_rank", "-created_at")
            return qs.distinct()
        except Exception:
            pass  # fall through to FTS5 or icontains fallback

    # SQLite: FTS5 full-text search; fallback to icontains if FTS returns nothing (e.g. index lag)
    if connection.vendor == "sqlite":
        qs = (
            Question.objects.search(q)
            .select_related("author")
            .prefetch_related(_answers_prefetch())
        )
        if order_by == "-upvote_count":
            qs = qs.order_by("-upvote_count", "-created_at")
        else:
            qs = qs.order_by("-created_at")
        # If FTS returned no rows, try icontains fallback (e.g. single-word or partial match)
        if not qs.exists() and q:
            qs = Question.objects.filter(
                Q(title__icontains=q) | Q(body__icontains=q)
            ).select_related("author").prefetch_related(_answers_prefetch())
            if order_by == "-upvote_count":
                qs = qs.order_by("-upvote_count", "-created_at")
            else:
                qs = qs.order_by("-created_at")
        return qs

    # Other DBs or fallback: icontains
    qs = Question.objects.filter(
        Q(title__icontains=q) | Q(body__icontains=q)
    ).select_related("author").prefetch_related(_answers_prefetch())
    if order_by == "-upvote_count":
        qs = qs.order_by("-upvote_count", "-created_at")
    else:
        qs = qs.order_by("-created_at")
    return qs


def suggestion_questions(query_string, limit=10):
    if not query_string or len(query_string.strip()) < 1:
        return Question.objects.none()
    q = query_string.strip()
    limit = min(20, max(1, limit))

    if connection.vendor == "sqlite":
        qs = (
            Question.objects.search(q)
            .select_related("author")
            .prefetch_related(_answers_prefetch())
            .order_by("-created_at")[:limit]
        )
        if not qs.exists() and q:
            return (
                Question.objects.filter(
                    Q(title__icontains=q) | Q(body__icontains=q)
                )
                .select_related("author")
                .prefetch_related(_answers_prefetch())
                .order_by("-created_at")[:limit]
            )
        return qs
    return (
        Question.objects.filter(
            Q(title__icontains=q) | Q(body__icontains=q)
        )
        .select_related("author")
        .prefetch_related(_answers_prefetch())
        .order_by("-created_at")[:limit]
    )
