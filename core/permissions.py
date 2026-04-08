from rest_framework.permissions import BasePermission

from accounts.models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.UserRole.ADMIN
        )


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.UserRole.MODERATOR
        )


class IsFoundingEditor(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.UserRole.VERIFIED_NIAT_STUDENT
        )


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {
                User.UserRole.INTERMEDIATE_STUDENT,
                User.UserRole.NIAT_STUDENT,
            }
        )


class IsVerifiedUser(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and getattr(user, "is_verified", False)
        )


class IsModeratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {
                User.UserRole.MODERATOR,
                User.UserRole.ADMIN,
            }
        )


class IsAuthorOrModerator(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) in {
            User.UserRole.MODERATOR,
            User.UserRole.ADMIN,
        }:
            return True
        return str(getattr(obj, "author_id_id", "")) == str(user.id)
