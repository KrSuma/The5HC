"""
Core mixins for The5HC Django application.

This module contains common mixins used across the application to handle
HTMX patterns, organization filtering, and other cross-cutting concerns.
"""
import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import ContextMixin

logger = logging.getLogger(__name__)


class DualTemplateMixin(ContextMixin):
    """
    Mixin to handle HTMX dual template pattern.
    
    This project uses a dual-template pattern for HTMX navigation:
    - Full page template: template_name.html (for direct URL navigation)
    - Content template: template_name_content.html (for HTMX navigation)
    
    This mixin automatically selects the appropriate template based on whether
    the request is an HTMX request, preventing the common bug where features
    work in one navigation method but not the other.
    """
    
    # Allow views to specify a content template explicitly
    content_template_name: Optional[str] = None
    
    def get_template_names(self) -> List[str]:
        """
        Return the appropriate template based on request type.
        
        For HTMX requests, use the content template (without base.html).
        For regular requests, use the full template (extends base.html).
        """
        templates = super().get_template_names()
        
        # Check if this is an HTMX request
        if self.request.headers.get('HX-Request'):
            # If content template is explicitly set, use it
            if self.content_template_name:
                return [self.content_template_name]
            
            # Otherwise, transform regular templates to content templates
            content_templates = []
            for template in templates:
                if template.endswith('.html'):
                    # Replace .html with _content.html
                    content_template = template[:-5] + '_content.html'
                    content_templates.append(content_template)
                else:
                    # Fallback to original if not .html
                    content_templates.append(template)
            
            logger.debug(f"HTMX request - using content templates: {content_templates}")
            return content_templates
        
        logger.debug(f"Regular request - using full templates: {templates}")
        return templates
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add HTMX-related context variables."""
        context = super().get_context_data(**kwargs)
        
        # Add flag to help identify template type in development
        context['is_htmx_request'] = bool(self.request.headers.get('HX-Request'))
        
        # Add current URL for HTMX push-url
        context['current_url'] = self.request.get_full_path()
        
        return context


class HTMXResponseMixin:
    """
    Mixin to handle common HTMX response patterns.
    
    Provides utilities for HTMX-specific responses like redirects,
    triggers, and partial updates.
    """
    
    def htmx_redirect(self, url: str) -> HttpResponse:
        """
        Perform an HTMX redirect.
        
        For HTMX requests, set the HX-Redirect header.
        For regular requests, use standard redirect.
        """
        response = HttpResponse()
        if self.request.headers.get('HX-Request'):
            response['HX-Redirect'] = url
        else:
            response.status_code = 302
            response['Location'] = url
        return response
    
    def htmx_refresh(self) -> HttpResponse:
        """Trigger a full page refresh via HTMX."""
        response = HttpResponse()
        response['HX-Refresh'] = 'true'
        return response
    
    def htmx_trigger(self, event: str, detail: Optional[Dict] = None) -> HttpResponse:
        """
        Trigger a custom HTMX event.
        
        Args:
            event: Name of the event to trigger
            detail: Optional event detail data
        """
        response = HttpResponse()
        if detail:
            import json
            response['HX-Trigger'] = json.dumps({event: detail})
        else:
            response['HX-Trigger'] = event
        return response
    
    def htmx_push_url(self, url: str) -> HttpResponse:
        """Update the browser URL without a full page reload."""
        response = HttpResponse()
        response['HX-Push-Url'] = url
        return response


class OrganizationFilterMixin(LoginRequiredMixin):
    """
    Mixin to filter querysets by the current user's organization.
    
    Ensures data isolation between organizations in the multi-tenant system.
    """
    
    organization_field = 'organization'  # Field name on the model
    user_organization_path = 'trainer_profile.organization'  # Path from user to organization
    
    def get_user_organization(self):
        """Get the current user's organization."""
        try:
            return self.request.user.trainer_profile.organization
        except AttributeError:
            logger.warning(f"User {self.request.user} has no trainer profile")
            return None
    
    def get_queryset(self) -> QuerySet:
        """Filter queryset by user's organization."""
        queryset = super().get_queryset()
        organization = self.get_user_organization()
        
        if organization:
            # Build the filter dynamically based on organization_field
            filter_kwargs = {self.organization_field: organization}
            queryset = queryset.filter(**filter_kwargs)
            logger.debug(f"Filtered queryset by organization: {organization}")
        else:
            # No organization - return empty queryset for safety
            logger.warning(f"No organization for user {self.request.user}, returning empty queryset")
            queryset = queryset.none()
        
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add organization to context."""
        context = super().get_context_data(**kwargs)
        context['user_organization'] = self.get_user_organization()
        return context


class TrainerFilterMixin(OrganizationFilterMixin):
    """
    Mixin to filter querysets by the current trainer.
    
    Extends OrganizationFilterMixin to also filter by trainer,
    ensuring trainers only see their own data.
    """
    
    trainer_field = 'trainer'  # Field name on the model
    
    def get_queryset(self) -> QuerySet:
        """Filter queryset by organization and trainer."""
        # First apply organization filter
        queryset = super().get_queryset()
        
        # Then filter by trainer
        filter_kwargs = {self.trainer_field: self.request.user}
        queryset = queryset.filter(**filter_kwargs)
        logger.debug(f"Filtered queryset by trainer: {self.request.user}")
        
        return queryset


class PermissionMixin:
    """
    Mixin to handle common permission patterns.
    
    Provides utilities for checking ownership and role-based permissions.
    """
    
    owner_field = 'trainer'  # Field that indicates ownership
    
    def check_owner_permission(self, obj) -> bool:
        """Check if the current user owns the object."""
        owner = getattr(obj, self.owner_field, None)
        return owner == self.request.user
    
    def check_organization_permission(self, obj) -> bool:
        """Check if the object belongs to the user's organization."""
        user_org = getattr(self.request.user.trainer_profile, 'organization', None)
        obj_org = getattr(obj, 'organization', None)
        
        # For objects without direct organization field, try via trainer
        if not obj_org and hasattr(obj, 'trainer'):
            trainer = getattr(obj, 'trainer')
            if hasattr(trainer, 'trainer_profile'):
                obj_org = trainer.trainer_profile.organization
        
        return user_org and obj_org and user_org == obj_org
    
    def get_object(self):
        """Get object and check permissions."""
        obj = super().get_object()
        
        # Check both ownership and organization permissions
        if not (self.check_owner_permission(obj) or self.check_organization_permission(obj)):
            logger.warning(
                f"Permission denied for user {self.request.user} on {obj.__class__.__name__} {obj.pk}"
            )
            raise PermissionDenied("이 항목에 대한 접근 권한이 없습니다.")
        
        return obj


class FormSuccessMessageMixin:
    """
    Mixin to handle success messages for forms.
    
    Provides consistent success message handling with HTMX support.
    """
    
    success_message = ""
    
    def get_success_message(self, cleaned_data: Dict[str, Any]) -> str:
        """Get the success message, allowing for dynamic messages."""
        if self.success_message and '%' in self.success_message:
            return self.success_message % cleaned_data
        return self.success_message
    
    def form_valid(self, form):
        """Add success message on form validation."""
        response = super().form_valid(form)
        
        message = self.get_success_message(form.cleaned_data)
        if message:
            # For HTMX requests, trigger a notification event
            if self.request.headers.get('HX-Request'):
                # Ensure response allows headers to be set
                if not hasattr(response, '__setitem__'):
                    # If response doesn't support headers (like HttpResponseRedirect),
                    # create a new response
                    from django.http import HttpResponse
                    new_response = HttpResponse()
                    new_response['HX-Redirect'] = response.url if hasattr(response, 'url') else '/'
                    response = new_response
                
                import json
                response['HX-Trigger-After-Settle'] = json.dumps({
                    'showNotification': message
                })
            else:
                # For regular requests, use Django messages
                from django.contrib import messages
                messages.success(self.request, message)
        
        return response


class CacheMixin:
    """
    Mixin to handle caching for expensive operations.
    
    Provides utilities for caching view results and invalidating cache.
    """
    
    cache_timeout = 300  # 5 minutes default
    cache_key_prefix = None
    
    def get_cache_key(self, **kwargs) -> str:
        """Generate a cache key for the current request."""
        from django.core.cache import cache
        
        prefix = self.cache_key_prefix or self.__class__.__name__
        user_id = self.request.user.id if self.request.user.is_authenticated else 'anonymous'
        
        # Include relevant kwargs in cache key
        key_parts = [prefix, str(user_id)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache."""
        from django.core.cache import cache
        return cache.get(cache_key)
    
    def set_cached_data(self, cache_key: str, data: Any) -> None:
        """Set data in cache."""
        from django.core.cache import cache
        cache.set(cache_key, data, self.cache_timeout)
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries matching pattern."""
        from django.core.cache import cache
        
        if pattern:
            # Django's default cache doesn't support pattern deletion
            # This would need a Redis cache backend
            logger.info(f"Cache invalidation for pattern {pattern} requires Redis backend")
        else:
            cache.clear()


# Convenience class combining common mixins
class BaseViewMixin(DualTemplateMixin, HTMXResponseMixin, PermissionMixin):
    """Base mixin combining commonly used mixins."""
    pass


# Organization-filtered view mixin
class OrganizationViewMixin(OrganizationFilterMixin, BaseViewMixin):
    """Mixin for views that need organization filtering."""
    pass


# Trainer-filtered view mixin  
class TrainerViewMixin(TrainerFilterMixin, BaseViewMixin):
    """Mixin for views that need trainer filtering."""
    pass