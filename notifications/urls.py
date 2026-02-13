# notifications API URLs
from django.urls import path
from .views import (
    NotificationListCreateView,
    NotificationUnreadCountView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
)

urlpatterns = [
    path("notifications/", NotificationListCreateView.as_view(), name="notification-list"),
    path("notifications/unread_count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/<uuid:pk>/read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
    path("notifications/mark_all_read/", NotificationMarkAllReadView.as_view(), name="notification-mark-all-read"),
]
