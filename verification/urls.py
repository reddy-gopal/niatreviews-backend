"""
Verification API URLs.
"""
from django.urls import path
from .views import (
    SeniorProfileCreateAPIView,
    SeniorProfileDetailAPIView,
    SeniorRegistrationCreateAPIView,
    SeniorRegistrationListAPIView,
)
from .otp_views import OTPRequestView, OTPVerifyView, SeniorRegistrationStatusView

urlpatterns = [
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("senior/registration-status/", SeniorRegistrationStatusView.as_view(), name="senior-registration-status"),
    path("senior/apply/", SeniorProfileCreateAPIView.as_view(), name="senior-apply"),
    path("senior/profile/", SeniorProfileDetailAPIView.as_view(), name="senior-profile"),
    path("senior/register/", SeniorRegistrationCreateAPIView.as_view(), name="senior-register"),
    path("senior/registrations/", SeniorRegistrationListAPIView.as_view(), name="senior-registrations-list"),
]
