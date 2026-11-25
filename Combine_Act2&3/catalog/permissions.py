from rest_framework.permissions import SAFE_METHODS, BasePermission


class StaffWriteOrReadOnly(BasePermission):
    """Anyone can browse; only an active staff account can change products."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(
            request.user and request.user.is_authenticated
            and request.user.is_active and request.user.is_staff
        )
