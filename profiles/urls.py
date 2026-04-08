from django.urls import path

from .views import (
    IntermediateStudentProfileUpsertView,
    MyProfileView,
    NiatStudentProfileDetailView,
    NiatStudentProfileUpsertView,
    PublicBadgeView,
)

urlpatterns = [
    path("intermediate/", IntermediateStudentProfileUpsertView.as_view(), name="profiles-intermediate-upsert"),
    path("niat/", NiatStudentProfileUpsertView.as_view(), name="profiles-niat-upsert"),
    path("niat/<int:pk>/", NiatStudentProfileDetailView.as_view(), name="profiles-niat-detail"),
    path("me/", MyProfileView.as_view(), name="profiles-me"),
    path("badge/<str:username>/", PublicBadgeView.as_view(), name="profiles-badge-public"),
]
