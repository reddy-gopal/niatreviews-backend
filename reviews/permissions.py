"""Custom permissions for reviews app."""

from rest_framework import permissions


class IsApprovedSenior(permissions.BasePermission):
    """Allow only authenticated users with an approved SeniorProfile."""

    message = "Only approved NIAT seniors can access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, "senior_profile"):
            return False
        return request.user.senior_profile.status == "approved"
