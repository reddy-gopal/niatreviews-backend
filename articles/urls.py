from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleViewSet,
    ArticleImageUploadView,
    CategoryListView,
    SubcategoryListView,
    CampusArticleBreakdownView,
    ArticleUpvoteView,
    ArticleUpvoteStatusView,
    ArticleSuggestView,
    ArticleViewIncrementView,
    ArticleSuggestionsListView,
)
router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="article-categories"),
    path("subcategories/", SubcategoryListView.as_view(), name="article-subcategories"),
    path("upload_image/", ArticleImageUploadView.as_view(), name="article-upload-image"),
    path("articles/<int:article_id>/upvote/", ArticleUpvoteView.as_view(), name="article-upvote"),
    path("articles/<int:article_id>/upvote-status/", ArticleUpvoteStatusView.as_view(), name="article-upvote-status"),
    path("articles/<int:article_id>/suggest/", ArticleSuggestView.as_view(), name="article-suggest"),
    path("articles/<int:article_id>/view/", ArticleViewIncrementView.as_view(), name="article-view"),
    path("articles/<int:article_id>/suggestions/", ArticleSuggestionsListView.as_view(), name="article-suggestions-list"),
    path("stats/campus-breakdown/", CampusArticleBreakdownView.as_view()),
    path("", include(router.urls)),
]
