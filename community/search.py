"""
Full-text search utilities for community posts using PostgreSQL FTS.
Provides scalable search with ranking, filtering, and caching support.
SQLite-safe: postgres imports are lazy so suggestions/trending work without PostgreSQL.
"""
from django.db.models import Q
from .models import Post, Tag, Category


def search_posts(
    query_string,
    category_slug=None,
    tag_slug=None,
    date_from=None,
    date_to=None,
    order_by="-rank",
):
    """
    Full-text search on Post model with PostgreSQL FTS.
    
    Args:
        query_string: Search query string
        category_slug: Filter by category slug
        tag_slug: Filter by tag slug
        date_from: Filter posts created after this date
        date_to: Filter posts created before this date
        order_by: Sort order (default: -rank for relevance)
    
    Returns:
        QuerySet of Post objects with search_rank annotation
    """
    if not query_string or not query_string.strip():
        return Post.objects.none()
    
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    
    # Create search vector from title (weight A) and description (weight B)
    search_vector = SearchVector("title", weight="A") + SearchVector(
        "description", weight="B"
    )
    
    # Create search query
    search_query = SearchQuery(query_string, search_type="websearch")
    
    # Base queryset with published posts
    qs = (
        Post.objects.filter(is_published=True)
        .select_related("author", "category")
        .prefetch_related("tags")
    )
    
    # Apply filters
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    
    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)
    
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    
    # Apply search with ranking
    qs = qs.annotate(
        search_rank=SearchRank(search_vector, search_query)
    ).filter(search_rank__gt=0)
    
    # Order by relevance or other criteria
    if order_by == "-rank":
        qs = qs.order_by("-search_rank", "-created_at")
    elif order_by == "-created_at":
        qs = qs.order_by("-created_at")
    elif order_by == "-upvote_count":
        qs = qs.order_by("-upvote_count", "-created_at")
    else:
        qs = qs.order_by("-search_rank", "-created_at")
    
    return qs.distinct()


def search_posts_simple(query_string):
    """
    Simple fallback search using icontains for SQLite compatibility.
    Use this when PostgreSQL FTS is not available.
    """
    if not query_string or not query_string.strip():
        return Post.objects.none()
    
    return (
        Post.objects.filter(
            Q(title__icontains=query_string) | Q(description__icontains=query_string),
            is_published=True,
        )
        .select_related("author", "category")
        .prefetch_related("tags")
        .order_by("-created_at")
        .distinct()
    )


def get_search_suggestions(query_string, limit=7):
    """
    Get search suggestions based on partial query.
    Returns matching tags, categories, and posts. Single character match allowed.
    """
    if not query_string or not query_string.strip():
        return {"tags": [], "categories": [], "posts": []}
    
    tags = list(
        Tag.objects.filter(name__icontains=query_string)
        .values("name", "slug")[:limit]
    )
    
    categories = list(
        Category.objects.filter(name__icontains=query_string)
        .values("name", "slug")[:limit]
    )
    
    # Get matching posts by title
    posts = list(
        Post.objects.filter(
            title__icontains=query_string,
            is_published=True
        )
        .values("id", "title", "slug")
        .order_by("-created_at")[:limit]
    )
    
    return {"tags": tags, "categories": categories, "posts": posts}


def get_trending_searches(limit=10):
    """
    Get trending search terms.
    In production, this would query a search analytics table.
    For now, returns popular tags.
    """
    from django.db.models import Count
    
    return list(
        Tag.objects.annotate(post_count=Count("posts"))
        .filter(post_count__gt=0)
        .order_by("-post_count")
        .values("name", "slug", "post_count")[:limit]
    )
