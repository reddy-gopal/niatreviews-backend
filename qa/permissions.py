"""Q&A API permissions."""

from rest_framework import permissions


class IsVerifiedSenior(permissions.BasePermission):
    """Allow action only if request.user.is_verified_senior is True."""

    message = "Only verified NIAT seniors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_verified_senior", False) is True
        )


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Read for everyone; create for authenticated; update/delete only for the resource author."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        author = getattr(obj, "author", None)
        return author is not None and author == request.user


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Anyone can read; must be logged in to create or vote."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
