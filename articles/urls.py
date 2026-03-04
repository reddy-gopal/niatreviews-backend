from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, ArticleCommentDestroyView, ArticleImageUploadView, CategoryListView, SubcategoryListView

router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="article-categories"),
    path("subcategories/", SubcategoryListView.as_view(), name="article-subcategories"),
    path("upload_image/", ArticleImageUploadView.as_view(), name="article-upload-image"),
    path("articles/<int:article_pk>/comments/<int:pk>/", ArticleCommentDestroyView.as_view(), name="article-comment-destroy"),
    path("", include(router.urls)),
]
