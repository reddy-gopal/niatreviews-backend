"""
Search API views with caching, pagination, and filtering.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connection

from .search import (
    search_posts,
    search_posts_simple,
    get_search_suggestions,
    get_trending_searches,
)
from .serializers import PostSerializer
from .pagination import PostCursorPagination


def is_postgres():
    """Check if database is PostgreSQL."""
    return "postgresql" in connection.settings_dict["ENGINE"]


@api_view(["GET"])
@permission_classes([AllowAny])
def search_posts_view(request):
    """
    Search posts with full-text search, filtering, and pagination.
    
    Query params:
        q: Search query string (required)
        category: Filter by category slug
        tag: Filter by tag slug
        date_from: Filter by date (YYYY-MM-DD)
        date_to: Filter by date (YYYY-MM-DD)
        order_by: Sort order (-rank, -created_at, -upvote_count)
        page: Page number for pagination
        limit: Results per page (default: 20, max: 50)
    
    Returns:
        {
            "count": total_results,
            "next": next_page_url,
            "previous": prev_page_url,
            "results": [post_objects],
            "query": search_query,
            "filters": applied_filters
        }
    """
    query_string = request.query_params.get("q", "").strip()
    
    if not query_string:
        return Response(
            {
                "detail": "Search query 'q' parameter is required.",
                "count": 0,
                "results": [],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Get filter parameters
    category_slug = request.query_params.get("category")
    tag_slug = request.query_params.get("tag")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    order_by = request.query_params.get("order_by", "-rank")
    
    # Build cache key
    cache_key = f"search:{query_string}:{category_slug}:{tag_slug}:{date_from}:{date_to}:{order_by}"
    
    # Try to get from cache (5 minutes)
    cached_result = cache.get(cache_key)
    if cached_result and not request.user.is_authenticated:
        # Use cache for anonymous users only
        paginator = PostCursorPagination()
        page = paginator.paginate_queryset(cached_result, request)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={"request": request})
            response_data = paginator.get_paginated_response(serializer.data).data
            response_data["query"] = query_string
            response_data["cached"] = True
            return Response(response_data)
    
    # Perform search
    if is_postgres():
        posts = search_posts(
            query_string=query_string,
            category_slug=category_slug,
            tag_slug=tag_slug,
            date_from=date_from,
            date_to=date_to,
            order_by=order_by,
        )
    else:
        # Fallback to simple search for SQLite
        posts = search_posts_simple(query_string)
        if category_slug:
            posts = posts.filter(category__slug=category_slug)
        if tag_slug:
            posts = posts.filter(tags__slug=tag_slug)
    
    # Cache results for anonymous users
    if not request.user.is_authenticated:
        cache.set(cache_key, list(posts), 300)  # 5 minutes
    
    # Paginate results
    paginator = PostCursorPagination()
    page = paginator.paginate_queryset(posts, request)
    
    if page is not None:
        serializer = PostSerializer(page, many=True, context={"request": request})
        response_data = paginator.get_paginated_response(serializer.data).data
        response_data["query"] = query_string
        response_data["filters"] = {
            "category": category_slug,
            "tag": tag_slug,
            "date_from": date_from,
            "date_to": date_to,
            "order_by": order_by,
        }
        return Response(response_data)
    
    # No pagination
    serializer = PostSerializer(posts, many=True, context={"request": request})
    return Response(
        {
            "count": len(serializer.data),
            "results": serializer.data,
            "query": query_string,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def search_suggestions_view(request):
    """
    Get search suggestions for autocomplete.
    
    Query params:
        q: Partial search query (min 2 chars)
        limit: Max suggestions (default: 5)
    
    Returns:
        {
            "tags": [{name, slug}, ...],
            "categories": [{name, slug}, ...],
            "posts": [{id, title, slug}, ...]
        }
    """
    query_string = request.query_params.get("q", "").strip()
    limit = int(request.query_params.get("limit", 5))
    
    if len(query_string) < 2:
        return Response({"tags": [], "categories": [], "posts": []})
    
    # Build cache key
    cache_key = f"search_suggestions:{query_string}:{limit}"
    
    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
    
    # Get suggestions
    suggestions = get_search_suggestions(query_string, limit=limit)
    
    # Cache for 5 minutes
    cache.set(cache_key, suggestions, 300)
    
    return Response(suggestions)


@api_view(["GET"])
@permission_classes([AllowAny])
def trending_searches_view(request):
    """
    Get trending search terms/topics.
    
    Query params:
        limit: Max results (default: 10)
    
    Returns:
        {
            "trending": [{name, slug, post_count}, ...]
        }
    """
    limit = int(request.query_params.get("limit", 10))
    
    # Build cache key
    cache_key = f"trending_searches:{limit}"
    
    # Try cache first (15 minutes)
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
    
    # Get trending
    trending = get_trending_searches(limit=limit)
    result = {"trending": trending}
    
    # Cache for 15 minutes
    cache.set(cache_key, result, 900)
    
    return Response(result)
