from rest_framework.permissions import BasePermission

class IsHODUser(BasePermission):
    """
    Custom permission to only allow HOD users to access certain views.
    """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='HOD').exists()