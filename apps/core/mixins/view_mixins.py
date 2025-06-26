"""
View mixins for The5HC project.

This module provides reusable mixins for Django views to handle common
functionality in a composable way.
"""

import logging
from typing import Any, Dict, Optional, List, Type
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, QuerySet, Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic.base import ContextMixin

logger = logging.getLogger(__name__)


class HtmxResponseMixin:
    """
    Mixin to handle HTMX requests and responses.
    
    This mixin provides methods to detect HTMX requests and return appropriate
    responses (partial templates for HTMX, full templates for regular requests).
    
    Usage:
        class MyView(HtmxResponseMixin, TemplateView):
            template_name = 'myapp/myview.html'
            htmx_template_name = 'myapp/myview_content.html'
            
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                # Your context logic here
                return context
                
    The mixin will automatically use htmx_template_name for HTMX requests
    if it's defined, otherwise it falls back to template_name.
    """
    
    htmx_template_name: Optional[str] = None
    
    def is_htmx_request(self, request: Optional[HttpRequest] = None) -> bool:
        """Check if the current request is an HTMX request."""
        request = request or getattr(self, 'request', None)
        if not request:
            return False
        return request.headers.get('HX-Request', '').lower() == 'true'
    
    def get_template_names(self) -> List[str]:
        """
        Return template name based on whether it's an HTMX request.
        
        For HTMX requests, tries htmx_template_name first, then falls back
        to the regular template_name.
        """
        if hasattr(super(), 'get_template_names'):
            template_names = super().get_template_names()
        else:
            template_names = [self.template_name] if hasattr(self, 'template_name') else []
        
        if self.is_htmx_request() and self.htmx_template_name:
            return [self.htmx_template_name]
        
        return template_names
    
    def render_htmx_response(self, template_name: str, context: Dict[str, Any],
                           status: int = 200) -> HttpResponse:
        """Render a response specifically for HTMX requests."""
        return render(self.request, template_name, context, status=status)
    
    def get_htmx_trigger_name(self) -> Optional[str]:
        """Get the name of the element that triggered the HTMX request."""
        return self.request.headers.get('HX-Trigger-Name')
    
    def get_htmx_target(self) -> Optional[str]:
        """Get the ID of the target element for the HTMX request."""
        return self.request.headers.get('HX-Target')


class OrganizationFilterMixin:
    """
    Mixin to filter querysets by organization based on the current user.
    
    This mixin ensures that users only see data from their own organization
    in multi-tenant setups.
    
    Usage:
        class ClientListView(OrganizationFilterMixin, ListView):
            model = Client
            organization_field = 'organization'  # Field name on the model
            allow_superuser_access = True  # Superusers see all data
            
    For related models:
        class AssessmentListView(OrganizationFilterMixin, ListView):
            model = Assessment
            organization_field = 'client__trainer__organization'
    """
    
    organization_field: str = 'organization'
    allow_superuser_access: bool = True
    organization_required: bool = True
    
    def get_organization(self) -> Optional[Model]:
        """Get the current user's organization."""
        if not hasattr(self, 'request') or not self.request.user.is_authenticated:
            return None
            
        user = self.request.user
        
        # Handle superuser access
        if user.is_superuser and self.allow_superuser_access:
            # For superusers, we might want to filter by a specific org
            # This could come from a query parameter or session
            org_id = self.request.GET.get('organization_id')
            if org_id:
                from apps.trainers.models import Organization
                try:
                    return Organization.objects.get(pk=org_id)
                except Organization.DoesNotExist:
                    pass
            return None  # Superuser sees all if no specific org requested
        
        # Get organization from user's trainer profile
        if hasattr(user, 'trainer_profile'):
            return user.trainer_profile.organization
        
        return None
    
    def get_queryset(self) -> QuerySet:
        """Filter queryset by organization."""
        queryset = super().get_queryset()
        
        organization = self.get_organization()
        
        # If superuser and no specific org, return all
        if (self.request.user.is_superuser and 
            self.allow_superuser_access and 
            organization is None):
            return queryset
        
        # If organization is required but not found, return empty queryset
        if self.organization_required and organization is None:
            return queryset.none()
        
        # Filter by organization if we have one
        if organization:
            filter_kwargs = {self.organization_field: organization}
            return queryset.filter(**filter_kwargs)
        
        return queryset
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add organization to context."""
        context = super().get_context_data(**kwargs)
        context['current_organization'] = self.get_organization()
        return context


class PermissionRequiredMixin(AccessMixin):
    """
    Enhanced permission checking mixin with better error handling.
    
    This mixin extends Django's permission checking with organization-aware
    permissions and better error messages.
    
    Usage:
        class MyView(PermissionRequiredMixin, View):
            permission_required = 'myapp.view_mymodel'
            # or multiple permissions
            permission_required = ['myapp.view_mymodel', 'myapp.change_mymodel']
            permission_mode = 'any'  # 'all' or 'any'
            
            def has_permission(self):
                # Custom permission logic
                return self.request.user.trainer_profile.is_active
    """
    
    permission_required = None
    permission_mode: str = 'all'  # 'all' or 'any'
    raise_exception: bool = True
    permission_denied_message: str = '이 작업을 수행할 권한이 없습니다.'
    
    def get_permission_required(self) -> List[str]:
        """Get the required permissions."""
        if self.permission_required is None:
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} is missing the permission_required attribute.'
            )
        
        if isinstance(self.permission_required, str):
            return [self.permission_required]
        
        return list(self.permission_required)
    
    def has_permission(self) -> bool:
        """
        Check if the user has the required permissions.
        
        Override this method for custom permission logic.
        """
        perms = self.get_permission_required()
        
        if self.permission_mode == 'any':
            return any(self.request.user.has_perm(perm) for perm in perms)
        else:
            return self.request.user.has_perms(perms)
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching the request."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not self.has_permission():
            logger.warning(
                f"Permission denied for user {request.user} on {self.__class__.__name__}"
            )
            if self.raise_exception:
                raise PermissionDenied(self.permission_denied_message)
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)


class PaginationMixin:
    """
    Mixin to add pagination to list views.
    
    This mixin provides consistent pagination across the application with
    customizable page sizes and query parameter names.
    
    Usage:
        class MyListView(PaginationMixin, ListView):
            model = MyModel
            paginate_by = 20
            paginate_orphans = 5
            page_query_param = 'page'
            
            def get_paginate_by(self, queryset):
                # Allow dynamic page size from query params
                return self.request.GET.get('page_size', self.paginate_by)
    """
    
    paginate_by: int = 10
    paginate_orphans: int = 0
    page_query_param: str = 'page'
    max_paginate_by: int = 100
    
    def get_paginate_by(self, queryset: QuerySet) -> int:
        """Get the number of items per page."""
        if hasattr(super(), 'get_paginate_by'):
            paginate_by = super().get_paginate_by(queryset)
        else:
            paginate_by = self.paginate_by
        
        # Allow page size from query params
        if self.request.GET.get('page_size'):
            try:
                page_size = int(self.request.GET.get('page_size'))
                # Enforce maximum page size
                return min(page_size, self.max_paginate_by)
            except (ValueError, TypeError):
                pass
        
        return paginate_by
    
    def paginate_queryset(self, queryset: QuerySet, page_size: int) -> tuple:
        """Paginate the queryset."""
        paginator = Paginator(queryset, page_size, orphans=self.paginate_orphans)
        page_number = self.request.GET.get(self.page_query_param, 1)
        
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        
        return (paginator, page, page.object_list, page.has_other_pages())
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add pagination context."""
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'paginator') and self.paginator:
            context.update({
                'paginator': self.paginator,
                'page_obj': getattr(self, 'page_obj', None),
                'is_paginated': getattr(self, 'is_paginated', False),
                'page_query_param': self.page_query_param,
            })
        
        return context


class SearchMixin:
    """
    Mixin to add search functionality to list views.
    
    This mixin provides a consistent search interface across list views with
    configurable search fields and query parameter names.
    
    Usage:
        class ClientListView(SearchMixin, ListView):
            model = Client
            search_fields = ['name', 'email', 'phone']
            search_query_param = 'q'
            
        # For related field search:
        class AssessmentListView(SearchMixin, ListView):
            model = Assessment
            search_fields = ['client__name', 'notes']
            
        # For custom search logic:
        class MyView(SearchMixin, ListView):
            def get_search_query(self):
                # Custom query processing
                return super().get_search_query().strip().lower()
    """
    
    search_fields: List[str] = []
    search_query_param: str = 'search'
    search_use_icontains: bool = True
    
    def get_search_query(self) -> str:
        """Get the search query from request parameters."""
        return self.request.GET.get(self.search_query_param, '').strip()
    
    def get_search_fields(self) -> List[str]:
        """Get the fields to search in."""
        return self.search_fields
    
    def apply_search(self, queryset: QuerySet) -> QuerySet:
        """Apply search filtering to the queryset."""
        search_query = self.get_search_query()
        if not search_query:
            return queryset
        
        search_fields = self.get_search_fields()
        if not search_fields:
            return queryset
        
        # Build Q objects for each search field
        q_objects = Q()
        lookup_type = 'icontains' if self.search_use_icontains else 'contains'
        
        for field in search_fields:
            lookup = f'{field}__{lookup_type}'
            q_objects |= Q(**{lookup: search_query})
        
        return queryset.filter(q_objects)
    
    def get_queryset(self) -> QuerySet:
        """Get queryset with search applied."""
        queryset = super().get_queryset()
        return self.apply_search(queryset)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add search context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.get_search_query(),
            'search_query_param': self.search_query_param,
            'search_fields': self.get_search_fields(),
        })
        return context


class AuditLogMixin:
    """
    Mixin to log view actions for audit trails.
    
    This mixin automatically logs actions performed in views, useful for
    compliance and debugging.
    
    Usage:
        class ClientUpdateView(AuditLogMixin, UpdateView):
            model = Client
            audit_action = 'update'
            audit_message_template = 'Updated client: {object}'
            
            def get_audit_message(self, **kwargs):
                return f"Updated client {self.object.name} fields: {', '.join(self.get_form().changed_data)}"
    """
    
    audit_action: str = 'view'
    audit_log_model: Optional[Type[Model]] = None
    audit_message_template: str = '{action} {object}'
    
    def get_audit_action(self) -> str:
        """Get the action to log."""
        return self.audit_action
    
    def get_audit_object(self) -> Optional[Model]:
        """Get the object being acted upon."""
        return getattr(self, 'object', None)
    
    def get_audit_message(self, **kwargs: Any) -> str:
        """Build the audit log message."""
        action = self.get_audit_action()
        obj = self.get_audit_object()
        
        if hasattr(self, 'audit_message_template'):
            return self.audit_message_template.format(
                action=action,
                object=obj,
                user=self.request.user,
                **kwargs
            )
        
        return f"{action} {obj}"
    
    def create_audit_log(self, **extra_data: Any) -> None:
        """Create an audit log entry."""
        if not hasattr(self, 'request'):
            return
        
        message = self.get_audit_message(**extra_data)
        
        # Log to Python logger
        logger.info(
            f"Audit: {message}",
            extra={
                'user': self.request.user.id,
                'ip_address': self.get_client_ip(),
                'action': self.get_audit_action(),
                'object': str(self.get_audit_object()),
                'timestamp': timezone.now().isoformat(),
                **extra_data
            }
        )
        
        # If audit model is specified, create database entry
        if self.audit_log_model:
            try:
                self.audit_log_model.objects.create(
                    user=self.request.user,
                    action=self.get_audit_action(),
                    message=message,
                    ip_address=self.get_client_ip(),
                    object_id=getattr(self.get_audit_object(), 'pk', None),
                    **extra_data
                )
            except Exception as e:
                logger.error(f"Failed to create audit log: {e}")
    
    def get_client_ip(self) -> str:
        """Get the client's IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def dispatch(self, request, *args, **kwargs):
        """Log the action and dispatch the request."""
        response = super().dispatch(request, *args, **kwargs)
        
        # Only log successful responses
        if response.status_code < 400:
            self.create_audit_log()
        
        return response