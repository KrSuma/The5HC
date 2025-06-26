"""
Example usage of view mixins in The5HC project.

This file demonstrates how to use the mixins in real-world scenarios.
"""

from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from apps.clients.models import Client
from apps.assessments.models import Assessment
from apps.core.mixins.view_mixins import (
    HtmxResponseMixin,
    OrganizationFilterMixin,
    PermissionRequiredMixin,
    PaginationMixin,
    SearchMixin,
    AuditLogMixin,
)


# Example 1: Client List View with all features
class ClientListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    SearchMixin,
    PaginationMixin,
    HtmxResponseMixin,
    ListView
):
    """
    Client list view with organization filtering, search, and pagination.
    
    Features:
    - Only shows clients from user's organization
    - Searchable by name, email, and phone
    - Paginated with 20 items per page
    - Returns partial template for HTMX requests
    - Requires 'view_client' permission
    """
    model = Client
    template_name = 'clients/client_list.html'
    htmx_template_name = 'clients/client_list_content.html'
    context_object_name = 'clients'
    
    # Permission settings
    permission_required = 'clients.view_client'
    
    # Organization filter settings
    organization_field = 'trainer__organization'
    
    # Search settings
    search_fields = ['name', 'email', 'phone']
    search_query_param = 'q'
    
    # Pagination settings
    paginate_by = 20
    paginate_orphans = 5
    
    def get_queryset(self):
        # The mixins handle filtering automatically
        return super().get_queryset().select_related('trainer')


# Example 2: Assessment Create View with audit logging
class AssessmentCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    AuditLogMixin,
    HtmxResponseMixin,
    CreateView
):
    """
    Create new assessment with automatic audit logging.
    
    Features:
    - Ensures client belongs to user's organization
    - Logs assessment creation for audit trail
    - Returns partial template for HTMX
    - Requires both view and add permissions
    """
    model = Assessment
    template_name = 'assessments/assessment_form.html'
    htmx_template_name = 'assessments/assessment_form_content.html'
    fields = ['client', 'test_date', 'notes']
    success_url = reverse_lazy('assessments:list')
    
    # Permission settings - multiple permissions with 'all' mode
    permission_required = ['assessments.view_assessment', 'assessments.add_assessment']
    permission_mode = 'all'
    
    # Audit settings
    audit_action = 'create'
    audit_message_template = 'Created new assessment for client {client_name}'
    
    def get_form(self):
        form = super().get_form()
        # Filter client choices by organization
        if hasattr(self.request.user, 'trainer_profile'):
            org = self.request.user.trainer_profile.organization
            form.fields['client'].queryset = Client.objects.filter(
                trainer__organization=org
            )
        return form
    
    def get_audit_message(self, **kwargs):
        return self.audit_message_template.format(
            client_name=self.object.client.name
        )


# Example 3: Advanced search with related fields
class AssessmentListView(
    LoginRequiredMixin,
    OrganizationFilterMixin,
    SearchMixin,
    PaginationMixin,
    HtmxResponseMixin,
    ListView
):
    """
    Assessment list with advanced search across related fields.
    
    Features:
    - Search by client name or assessment notes
    - Filter by organization through client relationship
    - Custom search preprocessing
    """
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    htmx_template_name = 'assessments/assessment_list_content.html'
    
    # Organization filter through related model
    organization_field = 'client__trainer__organization'
    
    # Search across related fields
    search_fields = ['client__name', 'notes', 'client__email']
    
    # Pagination
    paginate_by = 15
    max_paginate_by = 100
    
    def get_search_query(self):
        # Custom search query processing
        query = super().get_search_query()
        # Remove special characters that might break the search
        return query.replace('/', '').replace('\\', '')
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'client', 'client__trainer'
        ).order_by('-test_date')


# Example 4: Custom permission logic
class TrainerDashboardView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    HtmxResponseMixin,
    DetailView
):
    """
    Trainer dashboard with custom permission checking.
    
    Features:
    - Custom permission logic beyond Django's permission system
    - HTMX support for dynamic updates
    """
    template_name = 'trainers/dashboard.html'
    htmx_template_name = 'trainers/dashboard_content.html'
    
    def has_permission(self):
        """
        Custom permission: user must have trainer profile and be active.
        """
        if not hasattr(self.request.user, 'trainer_profile'):
            return False
        
        trainer = self.request.user.trainer_profile
        return trainer.is_active and not trainer.is_suspended
    
    def get_object(self):
        return self.request.user.trainer_profile


# Example 5: Combining all mixins
class ComprehensiveClientView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    SearchMixin,
    PaginationMixin,
    AuditLogMixin,
    HtmxResponseMixin,
    ListView
):
    """
    Example showing all mixins working together.
    
    This demonstrates how multiple mixins can be combined to create
    a feature-rich view with minimal code.
    """
    model = Client
    template_name = 'clients/comprehensive_list.html'
    htmx_template_name = 'clients/comprehensive_list_content.html'
    
    # Permission settings
    permission_required = ['clients.view_client', 'clients.export_client']
    permission_mode = 'any'
    permission_denied_message = '클라이언트 목록을 볼 권한이 없습니다.'
    
    # Organization settings
    organization_field = 'trainer__organization'
    allow_superuser_access = True
    
    # Search settings
    search_fields = ['name', 'email', 'phone', 'notes']
    search_use_icontains = True
    
    # Pagination settings
    paginate_by = 25
    page_query_param = 'p'
    
    # Audit settings
    audit_action = 'list_view'
    audit_message_template = 'Viewed client list (page {page})'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add export URL if user has permission
        if self.request.user.has_perm('clients.export_client'):
            context['can_export'] = True
            context['export_url'] = reverse_lazy('clients:export')
        
        return context
    
    def get_audit_message(self, **kwargs):
        page = self.request.GET.get(self.page_query_param, 1)
        return self.audit_message_template.format(page=page)


# Example 6: HTMX-specific response handling
class ClientQuickEditView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    AuditLogMixin,
    HtmxResponseMixin,
    UpdateView
):
    """
    Quick edit view optimized for HTMX interactions.
    
    Features:
    - Different responses based on HTMX trigger
    - Inline editing support
    - Targeted template updates
    """
    model = Client
    fields = ['name', 'email', 'phone']
    template_name = 'clients/quick_edit_form.html'
    
    permission_required = 'clients.change_client'
    audit_action = 'quick_edit'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        if self.is_htmx_request():
            # Return just the updated row for HTMX
            trigger = self.get_htmx_trigger_name()
            
            if trigger == 'save-and-close':
                # Return the display row
                return self.render_htmx_response(
                    'clients/partials/client_row.html',
                    {'client': self.object}
                )
            elif trigger == 'save-and-continue':
                # Return the form again with success message
                context = self.get_context_data(form=form)
                context['success_message'] = '저장되었습니다.'
                return self.render_htmx_response(
                    'clients/quick_edit_form.html',
                    context
                )
        
        return response
    
    def get_queryset(self):
        # Ensure user can only edit clients from their organization
        return super().get_queryset().select_related('trainer')