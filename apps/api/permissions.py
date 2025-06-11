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