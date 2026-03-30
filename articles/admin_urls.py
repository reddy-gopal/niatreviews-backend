from rest_framework.routers import DefaultRouter
from .admin_views import ArticleAdminViewSet, ClubCampusAdminViewSet

router = DefaultRouter()
router.register(r"articles", ArticleAdminViewSet, basename="admin-articles")
router.register(r"club-chapters", ClubCampusAdminViewSet, basename="admin-club-chapters")

urlpatterns = router.urls