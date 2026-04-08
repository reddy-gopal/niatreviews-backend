from django.urls import path

from .views import ApproveNiatProfileView, RejectNiatProfileView

urlpatterns = [
    path("niat-profiles/<int:id>/approve/", ApproveNiatProfileView.as_view(), name="moderation-niat-approve"),
    path("niat-profiles/<int:id>/reject/", RejectNiatProfileView.as_view(), name="moderation-niat-reject"),
]
