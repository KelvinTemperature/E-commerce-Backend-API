from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows access only to users with role = 'admin'.
    """
    message = 'Access denied. Admin privileges required.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin          # our @property from the User model
        )


class IsRegularUser(BasePermission):
    """
    Allows access only to users with role = 'user'.
    """
    message = 'Access denied. Not a regular user account.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_regular_user   # our @property from the User model
        )


class IsAdminOrReadOnly(BasePermission):
    """
    - Anyone authenticated → can GET (read products)
    - Only admin           → can POST, PUT, DELETE (modify products)
    """
    message = 'Access denied. Admin privileges required to modify products.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') — read-only methods
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True   # any authenticated user can read

        # For POST, PUT, DELETE — must be admin
        return request.user.is_admin