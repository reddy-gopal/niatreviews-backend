from rest_framework.routers import DefaultRouter
from .admin_views import ArticleAdminViewSet

router = DefaultRouter()
router.register(r"articles", ArticleAdminViewSet, basename="admin-articles")

urlpatterns = router.urls