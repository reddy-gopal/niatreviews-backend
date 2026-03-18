from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleViewSet,
    ClubViewSet,
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
router.register(r"clubs", ClubViewSet, basename="club")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="article-categories"),
    path("subcategories/", SubcategoryListView.as_view(), name="article-subcategories"),
    path("upload_image/", ArticleImageUploadView.as_view(), name="article-upload-image"),
    path("articles/<str:article_id>/upvote/", ArticleUpvoteView.as_view(), name="article-upvote"),
    path("articles/<str:article_id>/upvote-status/", ArticleUpvoteStatusView.as_view(), name="article-upvote-status"),
    path("articles/<str:article_id>/suggest/", ArticleSuggestView.as_view(), name="article-suggest"),
    path("articles/<str:article_id>/view/", ArticleViewIncrementView.as_view(), name="article-view"),
    path("articles/<str:article_id>/suggestions/", ArticleSuggestionsListView.as_view(), name="article-suggestions-list"),
    path("stats/campus-breakdown/", CampusArticleBreakdownView.as_view()),
    path("admin/", include("articles.admin_urls")),
    path("", include(router.urls)),
]
