from django.urls import path
from .senior_views import SeniorFollowView, SeniorListView

urlpatterns = [
    path("", SeniorListView.as_view(), name="senior-list"),
    path("<uuid:id>/follow/", SeniorFollowView.as_view(), name="senior-follow"),
]
