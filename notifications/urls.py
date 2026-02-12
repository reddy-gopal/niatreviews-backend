# notifications API URLs
from django.urls import path
from .views import NotificationListCreateView

urlpatterns = [
    path("notifications/", NotificationListCreateView.as_view(), name="notification-list"),
]
