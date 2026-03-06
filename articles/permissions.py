from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "moderator"
        )


class IsAuthorOrModerator(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) == "moderator":
            return True
        return str(obj.author_id_id) == str(request.user.id)
