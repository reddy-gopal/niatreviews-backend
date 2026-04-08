from rest_framework.permissions import BasePermission

from accounts.models import User
from core.permissions import IsAdmin, IsAuthorOrModerator, IsModerator, IsModeratorOrAdmin


class CanWriteArticle(BasePermission):
    message = "Only verified NIAT users can write articles."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {
                User.UserRole.VERIFIED_NIAT_STUDENT,
                User.UserRole.MODERATOR,
                User.UserRole.ADMIN,
            }
        )


__all__ = ["IsAdmin", "IsAuthorOrModerator", "IsModerator", "IsModeratorOrAdmin", "CanWriteArticle"]