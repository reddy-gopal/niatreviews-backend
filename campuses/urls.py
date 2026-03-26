from django.urls import path
from .views import CampusListView, CampusDetailView

urlpatterns = [
    path("", CampusListView.as_view(), name="campus-list"),
    path("<slug:slug>/", CampusDetailView.as_view(), name="campus-detail"),
]
