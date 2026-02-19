"""
Verification API URLs.
"""
from django.urls import path
from .views import (
    SeniorProfileCreateAPIView,
    SeniorProfileDetailAPIView,
    PhoneVerificationCreateAPIView,
    SeniorRegistrationCreateAPIView,
    SeniorRegistrationListAPIView,
)
from .otp_views import OTPRequestView, OTPVerifyView, SeniorRegistrationStatusView

urlpatterns = [
    # Demo OTP (seniors-frontend registration)
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("senior/registration-status/", SeniorRegistrationStatusView.as_view(), name="senior-registration-status"),
    #
    # Senior verification (simple - for authenticated users)
    path(
        "senior/apply/",
        SeniorProfileCreateAPIView.as_view(),
        name="senior-apply"
    ),
    path(
        "senior/profile/",
        SeniorProfileDetailAPIView.as_view(),
        name="senior-profile"
    ),
    
    # Senior registration (detailed - from seniors-frontend, no auth required)
    path(
        "senior/register/",
        SeniorRegistrationCreateAPIView.as_view(),
        name="senior-register"
    ),
    path(
        "senior/registrations/",
        SeniorRegistrationListAPIView.as_view(),
        name="senior-registrations-list"
    ),
    
    # Phone verification
    path(
        "phone/request/",
        PhoneVerificationCreateAPIView.as_view(),
        name="phone-verification-request"
    ),
]
