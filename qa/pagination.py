from rest_framework.pagination import CursorPagination


class QuestionCursorPagination(CursorPagination):
    """Cursor pagination for question list. Returns only questions (results) with next/previous cursors."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    # Unique ordering required for stable cursors (id breaks ties on same created_at)
    ordering = ["-created_at", "id"]
    cursor_query_param = "cursor"


class FollowUpCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ["created_at", "id"]
    cursor_query_param = "cursor"
