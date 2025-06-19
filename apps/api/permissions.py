"""
Custom permissions for API
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(obj, 'trainer'):
            return obj.trainer == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsTrainerOfClient(permissions.BasePermission):
    """
    Permission to ensure trainer can only access their own clients' data
    """
    def has_object_permission(self, request, view, obj):
        # For assessments, sessions, etc. that have client relationship
        if hasattr(obj, 'client'):
            return obj.client.trainer == request.user
        # For packages that have trainer relationship
        elif hasattr(obj, 'trainer'):
            return obj.trainer == request.user
        # For sessions that have package relationship
        elif hasattr(obj, 'package'):
            return obj.package.trainer == request.user
        
        return False


class BelongsToOrganization(permissions.BasePermission):
    """
    Permission to ensure user belongs to the same organization.
    """
    def has_permission(self, request, view):
        # Check if user has trainer attribute
        if not hasattr(request.user, 'trainer'):
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Get the user's trainer
        if not hasattr(request.user, 'trainer'):
            return False
        
        user_trainer = request.user.trainer
        
        # Check organization membership based on object type
        if hasattr(obj, 'trainer'):
            # For assessments, clients, etc.
            return obj.trainer.organization == user_trainer.organization
        elif hasattr(obj, 'organization'):
            # For direct organization objects
            return obj.organization == user_trainer.organization
        elif hasattr(obj, 'client') and hasattr(obj.client, 'trainer'):
            # For objects related to clients
            return obj.client.trainer.organization == user_trainer.organization
        
        return False