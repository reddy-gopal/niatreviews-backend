from django.urls import path
from .auth_views import LogoutView
from .views import (
    ForgotPasswordRequestView,
    ForgotPasswordVerifyView,
    ForgotPasswordResetConfirmView,
    UsernameAvailabilityView,
    ChangePhoneRequestOtpView,
    ChangePhoneConfirmView,
    OnboardingRoleView,
    OnboardingCompleteView,
)

urlpatterns = []

urlpatterns += [
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("onboarding/role/", OnboardingRoleView.as_view(), name="onboarding-role"),
    path("onboarding/complete/", OnboardingCompleteView.as_view(), name="onboarding-complete"),
    path("forgot-password/request/", ForgotPasswordRequestView.as_view(), name="forgot-password-request"),
    path("forgot-password/verify/", ForgotPasswordVerifyView.as_view(), name="forgot-password-verify"),
    path("forgot-password/reset-confirm/", ForgotPasswordResetConfirmView.as_view(), name="forgot-password-reset-confirm"),
    path("username-available/", UsernameAvailabilityView.as_view(), name="username-available"),
    path("change-phone/request-otp/", ChangePhoneRequestOtpView.as_view(), name="change-phone-request-otp"),
    path("change-phone/confirm/", ChangePhoneConfirmView.as_view(), name="change-phone-confirm"),
]
