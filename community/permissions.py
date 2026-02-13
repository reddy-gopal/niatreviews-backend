"""Community API permissions."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Read-only for everyone; create for authenticated; update/delete only for the author.
    Use for Post and Comment.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        author = getattr(obj, "author", None)
        return author is not None and author == request.user


class SeniorMustCompleteOnboarding(permissions.BasePermission):
    """
    Block approved seniors who have not submitted the mandatory onboarding review
    from accessing community endpoints. They must complete onboarding first.
    """

    message = "Please complete your onboarding review before accessing the community."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True  # Let IsAuthenticatedOrReadOnly handle anonymous
        if not hasattr(request.user, "senior_profile"):
            return True
        if request.user.senior_profile.status != "approved":
            return True
        return request.user.senior_profile.review_submitted
