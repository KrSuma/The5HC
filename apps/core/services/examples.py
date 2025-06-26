"""
Examples showing how to refactor views to use the service layer.

This file demonstrates the before/after pattern for extracting
business logic from views into services.
"""

# =============================================================================
# EXAMPLE 1: Client List View Refactoring
# =============================================================================

# BEFORE: All business logic in the view
"""
@login_required
def client_list_view(request):
    # 100+ lines of business logic mixed with view logic
    clients = Client.objects.filter(trainer__organization=request.organization)
    
    # Complex annotation logic
    clients = clients.annotate(
        calculated_bmi=ExpressionWrapper(
            F('weight') / (F('height') * F('height') / 10000),
            output_field=FloatField()
        )
    )
    # ... more annotations ...
    
    # Complex filtering logic
    if form.is_valid():
        # 50+ lines of filtering code
        pass
    
    # Pagination, rendering, etc.
"""

# AFTER: Using ClientService
from django.views.generic import ListView
from apps.core.mixins import DualTemplateMixin, OrganizationFilterMixin
from apps.core.services import ClientService

class ClientListView(DualTemplateMixin, OrganizationFilterMixin, ListView):
    """Refactored client list view using service layer."""
    template_name = 'clients/client_list.html'
    paginate_by = 20
    context_object_name = 'clients'
    
    def get_queryset(self):
        # Initialize service with user context
        service = ClientService(user=self.request.user)
        
        # Use service to handle complex business logic
        form = ClientSearchForm(self.request.GET)
        if form.is_valid():
            return service.search_and_filter(form.cleaned_data)
        else:
            return service.get_annotated_queryset()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard metrics from service
        service = ClientService(user=self.request.user)
        context['metrics'] = service.get_dashboard_metrics()
        
        return context


# =============================================================================
# EXAMPLE 2: Create Session Package Refactoring
# =============================================================================

# BEFORE: Complex fee calculation in view
"""
@login_required
def create_package_view(request):
    if request.method == 'POST':
        form = SessionPackageForm(request.POST)
        if form.is_valid():
            # Complex fee calculation logic
            gross_amount = form.cleaned_data['total_amount']
            base_amount = gross_amount / Decimal('1.135')
            vat_amount = base_amount * Decimal('0.10')
            card_fee = base_amount * Decimal('0.035')
            
            package = form.save(commit=False)
            package.trainer = request.user
            package.vat_amount = vat_amount
            package.card_fee = card_fee
            package.net_amount = base_amount
            package.save()
            
            # Create audit log
            FeeAuditLog.objects.create(...)
            
            return redirect('success')
"""

# AFTER: Using PaymentService
from django.views.generic import CreateView
from apps.core.services import PaymentService

class SessionPackageCreateView(DualTemplateMixin, FormSuccessMessageMixin, CreateView):
    """Refactored package creation using service layer."""
    model = SessionPackage
    form_class = SessionPackageForm
    template_name = 'sessions/package_form.html'
    success_message = "패키지가 성공적으로 생성되었습니다."
    
    def form_valid(self, form):
        # Use service to handle business logic
        service = PaymentService(user=self.request.user)
        
        package, success = service.create_session_package(form.cleaned_data)
        
        if success:
            self.object = package
            return super().form_valid(form)
        else:
            # Add service errors to form
            for error in service.errors:
                form.add_error(None, error)
            return self.form_invalid(form)


# =============================================================================
# EXAMPLE 3: Using Services in Function-Based Views
# =============================================================================

# If you need to keep function-based views temporarily:
from apps.core.services import ClientService, PaymentService

@login_required
def client_detail_view(request, pk):
    """Example of using service in function-based view."""
    service = ClientService(user=request.user)
    
    # Get client with permission checking
    client = service.get_object(pk)
    if not client:
        messages.error(request, service.get_errors_string())
        return redirect('clients:list')
    
    # Get statistics from service
    stats = service.get_client_statistics(client)
    timeline = service.get_client_timeline(client, limit=20)
    
    context = {
        'client': client,
        'stats': stats,
        'timeline': timeline
    }
    
    # Handle HTMX dual template pattern manually
    template = 'clients/client_detail_content.html' if request.headers.get('HX-Request') else 'clients/client_detail.html'
    
    return render(request, template, context)


# =============================================================================
# EXAMPLE 4: API Views Using Services
# =============================================================================

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class ClientViewSet(viewsets.ModelViewSet):
    """API viewset using service layer."""
    serializer_class = ClientSerializer
    
    def get_queryset(self):
        service = ClientService(user=self.request.user)
        return service.get_annotated_queryset()
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get client statistics endpoint."""
        service = ClientService(user=request.user)
        client = service.get_object(pk)
        
        if not client:
            return Response(
                {'errors': service.errors},
                status=status.HTTP_404_NOT_FOUND
            )
        
        stats = service.get_client_statistics(client)
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export clients data."""
        service = ClientService(user=request.user)
        
        # Apply filters
        queryset = service.search_and_filter(request.query_params)
        export_data = service.export_clients_data(queryset)
        
        return Response(export_data)


# =============================================================================
# EXAMPLE 5: Batch Operations Using Services
# =============================================================================

from django.views.generic import View

class ClientBatchUpdateView(View):
    """Example of batch operations using service."""
    
    def post(self, request):
        service = ClientService(user=request.user)
        
        # Get client IDs from request
        client_ids = request.POST.getlist('client_ids')
        action = request.POST.get('action')
        
        if action == 'mark_inactive':
            # Use service's batch processing
            successful, failed = service.process_batch(
                items=client_ids,
                processor_func=lambda client_id: self._mark_inactive(service, client_id)
            )
            
            messages.success(
                request, 
                f"{successful}명의 고객이 비활성화되었습니다."
            )
            if failed:
                messages.warning(
                    request,
                    f"{failed}명의 고객 처리 중 오류가 발생했습니다."
                )
        
        return redirect('clients:list')
    
    def _mark_inactive(self, service, client_id):
        client = service.get_object(client_id)
        if client:
            client.is_active = False
            service.save_with_audit(client, action='deactivate')


# =============================================================================
# EXAMPLE 6: Testing Services
# =============================================================================

import pytest
from apps.core.services import ClientService, PaymentService

@pytest.mark.django_db
class TestClientService:
    """Example of testing service layer."""
    
    def test_create_client(self, trainer_user):
        service = ClientService(user=trainer_user)
        
        client_data = {
            'name': '테스트 고객',
            'gender': 'M',
            'age': 30,
            'height': 175,
            'weight': 70
        }
        
        client, success = service.create_client(client_data)
        
        assert success is True
        assert client is not None
        assert client.name == '테스트 고객'
        assert client.trainer == trainer_user
    
    def test_create_client_missing_fields(self, trainer_user):
        service = ClientService(user=trainer_user)
        
        # Missing required fields
        client_data = {'name': '테스트 고객'}
        
        client, success = service.create_client(client_data)
        
        assert success is False
        assert client is None
        assert service.has_errors
        assert 'gender는 필수 입력 항목입니다.' in service.errors


# =============================================================================
# Migration Strategy
# =============================================================================
"""
1. Start with high-value views (most complex business logic)
2. Create service methods for specific operations
3. Gradually move logic from views to services
4. Update tests to test services directly
5. Views become thin controllers that coordinate services

Benefits:
- Business logic is reusable across views, APIs, and commands
- Easier to test business logic in isolation
- Views become much simpler and focused on HTTP handling
- Clear separation of concerns
- Easier to maintain and extend
"""