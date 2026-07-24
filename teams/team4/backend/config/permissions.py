from rest_framework.permissions import BasePermission


class IsTeam4Admin(BasePermission):
    """
    Temporary admin check.

    TODO: Replace with Core-provided is_staff/is_superuser
    when centralized authorization is available.
    """

    def has_permission(self, request, view):
        username = request.headers.get("X-User-Username", "")
        return username == "admin"