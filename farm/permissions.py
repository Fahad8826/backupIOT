from rest_framework import permissions

class IsAdminOrFarmManager(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow admin and farm managers full access
        return request.user.is_authenticated and (
            request.user.role == 'admin' or
            request.user.role == 'user'
        )

class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'OPERATOR'