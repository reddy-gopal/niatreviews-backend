from django.urls import path
from .views import (
    ForgotPasswordRequestView,
    ForgotPasswordVerifyView,
    ForgotPasswordResetConfirmView,
    UsernameAvailabilityView,
    ChangePhoneRequestOtpView,
    ChangePhoneConfirmView,
)

urlpatterns = []

urlpatterns += [
    path("forgot-password/request/", ForgotPasswordRequestView.as_view(), name="forgot-password-request"),
    path("forgot-password/verify/", ForgotPasswordVerifyView.as_view(), name="forgot-password-verify"),
    path("forgot-password/reset-confirm/", ForgotPasswordResetConfirmView.as_view(), name="forgot-password-reset-confirm"),
    path("username-available/", UsernameAvailabilityView.as_view(), name="username-available"),
    path("change-phone/request-otp/", ChangePhoneRequestOtpView.as_view(), name="change-phone-request-otp"),
    path("change-phone/confirm/", ChangePhoneConfirmView.as_view(), name="change-phone-confirm"),
]
