from django.urls import path
from .views import CampusListView

urlpatterns = [
    path("", CampusListView.as_view(), name="campus-list"),
]
