"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import (
    RegisterView,
    MeView,
    FoundingEditorProfileView,
    UserProfileByUsernameView,
    AuthorProfileWithArticlesView,
    ForgotPasswordResetView,
    ChangePasswordView,
    DeleteAccountView,
    PhoneLoginView,
    PhonePasswordLoginView,
    ModeratorAdminListCreateView,
    ModeratorAdminDetailView,
)
from verification.magic_login_views import MagicLoginView
from qa.dashboard_views import SeniorDashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/forgot-password/reset/", ForgotPasswordResetView.as_view(), name="forgot-password-reset"),
    path("api/auth/login/phone/", PhoneLoginView.as_view(), name="login-phone"),
    path("api/auth/login/phone-password/", PhonePasswordLoginView.as_view(), name="login-phone-password"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/auth/me/profile/", FoundingEditorProfileView.as_view(), name="me-profile"),
    path("api/auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("api/auth/delete-account/", DeleteAccountView.as_view(), name="delete-account"),
    path("api/auth/magic-login/", MagicLoginView.as_view(), name="magic-login"),
    path("api/users/<str:username>/", UserProfileByUsernameView.as_view(), name="user-profile-by-username"),
    path("api/authors/<str:username>/", AuthorProfileWithArticlesView.as_view(), name="author-profile-with-articles"),
    path("api/admin/moderators/", ModeratorAdminListCreateView.as_view(), name="admin-moderators-list-create"),
    path("api/admin/moderators/<uuid:moderator_id>/", ModeratorAdminDetailView.as_view(), name="admin-moderator-detail"),
    path("api/", include("qa.urls")),
    path("api/dashboard/senior/", SeniorDashboardView.as_view(), name="dashboard-senior"),
    path("api/", include("notifications.urls")),
    path("api/verification/", include("verification.urls")),
    path("api/seniors/", include("verification.senior_urls")),
    path("api/senior/", include("reviews.onboarding_urls")),
    path("api/articles/", include("articles.urls")),
    path("api/campuses/", include("campuses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
