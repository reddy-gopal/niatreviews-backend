"""Cursor pagination for posts and comments. Uses created_at + id for stable ordering."""
from rest_framework.pagination import CursorPagination


class PostCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"
    cursor_query_param = "cursor"


class CommentCursorPagination(CursorPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "created_at"
    cursor_query_param = "cursor"
