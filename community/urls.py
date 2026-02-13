from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    TagViewSet,
    PostViewSet,
    CommentViewSet,
    CommentUpvoteViewSet,
)
from .search_views import (
    search_posts_view,
    search_suggestions_view,
    trending_searches_view,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"tags", TagViewSet)
router.register(r"posts", PostViewSet)
router.register(r"comments", CommentViewSet)
router.register(r"comment-upvotes", CommentUpvoteViewSet)

urlpatterns = [
    path("search/", search_posts_view),
    path("search/suggestions/", search_suggestions_view),
    path("search/trending/", trending_searches_view),
    path("", include(router.urls)),
]