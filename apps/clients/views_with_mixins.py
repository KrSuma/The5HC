"""
Client views using both service layer and view mixins.
This demonstrates the full refactoring approach.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
import csv

from apps.core.services import ClientService
from apps.core.mixins import (
    HtmxResponseMixin, 
    OrganizationFilterMixin,
    PermissionRequiredMixin,
    PaginationMixin,
    SearchMixin,
    AuditLogMixin
)
from .models import Client
from .forms import ClientForm, ClientSearchForm
from apps.trainers.decorators import requires_trainer


class ClientListViewWithMixins(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    SearchMixin,
    PaginationMixin,
    HtmxResponseMixin,
    ListView
):
    """
    Client list view using all our new mixins and service layer.
    This is a fully refactored class-based view.
    """
    model = Client
    template_name = 'clients/client_list.html'
    htmx_template_name = 'clients/client_list_content.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    # Permission mixin settings
    permission_required = 'clients.view_client'
    permission_check_mode = 'any'  # Allow if user has trainer role
    
    # Organization filter mixin settings
    organization_field = 'trainer__organization'
    
    # Search mixin settings
    search_fields = ['name', 'email', 'phone']
    search_form_class = ClientSearchForm
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
    
    def setup(self, request, *args, **kwargs):
        """Initialize the service layer."""
        super().setup(request, *args, **kwargs)
        self.service = ClientService(user=request.user)
    
    def get_queryset(self):
        """Use service layer for getting queryset with filters."""
        # Get form data
        form = ClientSearchForm(self.request.GET)
        filters = {}
        
        if form.is_valid():
            filters = {k: v for k, v in form.cleaned_data.items() if v}
        
        # Use service to get filtered queryset
        return self.service.search_and_filter(filters)
    
    def get_context_data(self, **kwargs):
        """Add metrics to context using service."""
        context = super().get_context_data(**kwargs)
        context['metrics'] = self.service.get_dashboard_metrics()
        context['page_title'] = '고객 관리'
        context['form'] = ClientSearchForm(self.request.GET)
        return context
    
    def render_to_response(self, context, **response_kwargs):
        """Handle CSV export."""
        if self.request.GET.get('export') == 'csv':
            return self.export_csv()
        return super().render_to_response(context, **response_kwargs)
    
    def export_csv(self):
        """Export clients to CSV using service."""
        queryset = self.get_queryset()
        export_data = self.service.export_clients_data(queryset)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clients.csv"'
        
        if export_data:
            writer = csv.DictWriter(response, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
        
        return response


class ClientDetailViewWithMixins(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    HtmxResponseMixin,
    AuditLogMixin,
    DetailView
):
    """
    Client detail view using mixins and service layer.
    """
    model = Client
    template_name = 'clients/client_detail.html'
    htmx_template_name = 'clients/client_detail_content.html'
    context_object_name = 'client'
    
    # Permission settings
    permission_required = 'clients.view_client'
    
    # Organization filter settings
    organization_field = 'trainer__organization'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
    
    def setup(self, request, *args, **kwargs):
        """Initialize the service layer."""
        super().setup(request, *args, **kwargs)
        self.service = ClientService(user=request.user)
    
    def get_context_data(self, **kwargs):
        """Add statistics and timeline using service."""
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # Use service methods
        context['stats'] = self.service.get_client_statistics(client)
        context['timeline'] = self.service.get_client_timeline(client, limit=10)
        context['page_title'] = f'{client.name} - 고객 정보'
        
        return context


class ClientCreateViewWithMixins(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    HtmxResponseMixin,
    AuditLogMixin,
    CreateView
):
    """
    Client create view using mixins and service layer.
    """
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    htmx_template_name = 'clients/client_form_content.html'
    
    # Permission settings
    permission_required = 'clients.add_client'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
    
    def setup(self, request, *args, **kwargs):
        """Initialize the service layer."""
        super().setup(request, *args, **kwargs)
        self.service = ClientService(user=request.user)
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Use service layer to create client."""
        client_data = form.cleaned_data
        client, success = self.service.create_client(client_data)
        
        if success:
            messages.success(self.request, f"고객 '{client.name}'이(가) 등록되었습니다.")
            
            # Log action using audit mixin
            self.log_action(client, 'create', {'name': client.name})
            
            if self.request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': reverse_lazy('clients:client_detail', kwargs={'pk': client.pk})}
                )
            
            self.object = client
            return super().form_valid(form)
        else:
            # Add service errors to form
            for error in self.service.errors:
                form.add_error(None, error)
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect to client detail page."""
        return reverse_lazy('clients:client_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """Add page title."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = '고객 등록'
        return context


class ClientUpdateViewWithMixins(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    HtmxResponseMixin,
    AuditLogMixin,
    UpdateView
):
    """
    Client update view using mixins and service layer.
    """
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    htmx_template_name = 'clients/client_form_content.html'
    context_object_name = 'client'
    
    # Permission settings
    permission_required = 'clients.change_client'
    
    # Organization filter settings
    organization_field = 'trainer__organization'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
    
    def setup(self, request, *args, **kwargs):
        """Initialize the service layer."""
        super().setup(request, *args, **kwargs)
        self.service = ClientService(user=request.user)
    
    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Use service layer to update client."""
        client = self.object
        success = self.service.update_client(client, form.cleaned_data)
        
        if success:
            messages.success(self.request, f"고객 '{client.name}'의 정보가 수정되었습니다.")
            
            # Log action using audit mixin
            self.log_action(client, 'update', form.changed_data)
            
            if self.request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': reverse_lazy('clients:client_detail', kwargs={'pk': client.pk})}
                )
            
            return super().form_valid(form)
        else:
            # Add service errors to form
            for error in self.service.errors:
                form.add_error(None, error)
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect to client detail page."""
        return reverse_lazy('clients:client_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        """Add page title."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.name} - 정보 수정'
        return context


class ClientDeleteViewWithMixins(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    OrganizationFilterMixin,
    AuditLogMixin,
    DeleteView
):
    """
    Client delete view using mixins and service layer.
    """
    model = Client
    
    # Permission settings
    permission_required = 'clients.delete_client'
    
    # Organization filter settings
    organization_field = 'trainer__organization'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
    
    def setup(self, request, *args, **kwargs):
        """Initialize the service layer."""
        super().setup(request, *args, **kwargs)
        self.service = ClientService(user=request.user)
    
    def delete(self, request, *args, **kwargs):
        """Handle delete with validation."""
        self.object = self.get_object()
        
        # Check if client can be deleted
        if hasattr(self.object, 'assessments') and self.object.assessments.exists():
            return JsonResponse({'error': '평가 기록이 있는 고객은 삭제할 수 없습니다.'}, status=400)
        
        if hasattr(self.object, 'session_packages') and self.object.session_packages.exists():
            return JsonResponse({'error': '세션 패키지가 있는 고객은 삭제할 수 없습니다.'}, status=400)
        
        # Log before deletion
        client_name = self.object.name
        self.log_action(self.object, 'delete', {'name': client_name})
        
        # Delete using service
        success = self.service.delete(self.object)
        
        if success:
            messages.success(request, f"고객 '{client_name}'이(가) 삭제되었습니다.")
            return HttpResponse(status=204, headers={'HX-Redirect': reverse_lazy('clients:client_list')})
        else:
            return JsonResponse({'error': self.service.get_errors_string()}, status=400)