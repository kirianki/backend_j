import logging
from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()
logger = logging.getLogger(__name__)

class BaseRolePermission(permissions.BasePermission):
    """
    Base permission class for role-based access.
    """
    required_role = None  # Set this in child classes

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            logger.debug(f"User: {request.user.username}, Role: {request.user.role}")
            if request.user.role == self.required_role:
                return True
            logger.warning(f"User: {request.user.username} attempted unauthorized access to {view}.")
        return False

class IsOverallAdmin(BaseRolePermission):
    required_role = User.Role.OVERALL_ADMIN

class IsSectorAdmin(BaseRolePermission):
    required_role = User.Role.SECTOR_ADMIN

class IsServiceProvider(BaseRolePermission):
    required_role = User.Role.SERVICE_PROVIDER

class IsClient(BaseRolePermission):
    required_role = User.Role.CLIENT

class IsOwner(permissions.BasePermission):
    """
    Object-level permission: Only allow owners to modify their own objects.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        possible_owners = ['user', 'owner', 'created_by']
        owner = next((getattr(obj, attr, None) for attr in possible_owners if hasattr(obj, attr)), None)
        if owner and owner == request.user:
            logger.debug(f"User {request.user.username} is owner of {obj}.")
            return True

        logger.warning(f"Unauthorized access attempt by {request.user.username} on {obj}.")
        return False
