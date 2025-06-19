from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied

from .models import Trainer


class TrainerContextMiddleware(MiddlewareMixin):
    """
    Middleware to add trainer context to requests.
    
    This middleware:
    1. Adds the current trainer object to the request
    2. Adds the current organization to the request
    3. Handles organization switching for multi-org trainers
    """
    
    def process_request(self, request):
        # Skip middleware for unauthenticated requests
        if not request.user.is_authenticated:
            request.trainer = None
            request.organization = None
            return
        
        # Get the trainer object for the current user
        try:
            trainer = Trainer.objects.select_related('organization').get(user=request.user)
            request.trainer = trainer
            request.organization = trainer.organization
            
            # Check if user is trying to switch organizations
            if 'organization_id' in request.session:
                # Verify user has access to this organization
                org_id = request.session['organization_id']
                if trainer.organization_id == org_id:
                    # User is in their primary organization
                    pass
                else:
                    # For future: Check if user has access to multiple organizations
                    # For now, users only belong to one organization
                    request.session.pop('organization_id', None)
                    
        except Trainer.DoesNotExist:
            # User exists but has no trainer profile
            # This might happen for superusers or during initial setup
            request.trainer = None
            request.organization = None
            
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view to check if view requires trainer access.
        """
        # Check if view has requires_trainer attribute
        if hasattr(view_func, 'requires_trainer') and view_func.requires_trainer:
            # Allow superusers to bypass trainer requirement
            if request.user.is_superuser:
                return None
                
            if not request.trainer:
                raise PermissionDenied("Trainer profile required to access this resource.")
        
        return None