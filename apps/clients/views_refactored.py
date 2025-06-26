"""
Refactored client views using DualTemplateMixin and other core mixins.

This file demonstrates how to convert function-based views to class-based views
with proper mixin usage to handle HTMX dual templates automatically.
"""
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, F, FloatField, ExpressionWrapper, Max, Subquery, OuterRef, Exists
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import csv

from apps.core.mixins import (
    DualTemplateMixin, 
    OrganizationFilterMixin,
    HTMXResponseMixin,
    FormSuccessMessageMixin
)
from apps.trainers.decorators import requires_trainer_mixin
from .models import Client
from .forms import ClientForm, ClientSearchForm
from apps.assessments.models import Assessment
from apps.sessions.models import SessionPackage, Session
from apps.trainers.audit import log_client_action


class ClientListView(DualTemplateMixin, OrganizationFilterMixin, ListView):
    """
    List all clients with search and filter functionality.
    
    This refactored version automatically:
    - Selects the correct template (full vs content) based on HTMX
    - Filters by organization
    - Provides consistent context variables
    """
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10
    organization_field = 'trainer__organization'  # Override for nested filtering
    
    def get_queryset(self):
        """Enhanced queryset with annotations for filtering."""
        # Start with organization-filtered queryset
        queryset = super().get_queryset()
        
        # Add select_related for performance
        queryset = queryset.select_related('trainer')
        
        # Add annotations for filtering
        # Calculate BMI
        queryset = queryset.annotate(
            calculated_bmi=ExpressionWrapper(
                F('weight') / (F('height') * F('height') / 10000),
                output_field=FloatField()
            )
        )
        
        # Get latest assessment score
        latest_assessment = Assessment.objects.filter(
            client=OuterRef('pk')
        ).order_by('-date').values('overall_score')[:1]
        
        queryset = queryset.annotate(
            latest_score=Subquery(latest_assessment)
        )
        
        # Check activity status
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_session = Session.objects.filter(
            client=OuterRef('pk'),
            session_date__gte=thirty_days_ago
        )
        
        recent_assessment = Assessment.objects.filter(
            client=OuterRef('pk'),
            date__gte=thirty_days_ago
        )
        
        queryset = queryset.annotate(
            has_recent_activity=Exists(recent_session) | Exists(recent_assessment)
        )
        
        # Apply search filters
        form = ClientSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(phone__icontains=search)
                )
            
            # Gender filter
            gender = form.cleaned_data.get('gender')
            if gender:
                queryset = queryset.filter(gender=gender)
            
            # Age filters
            age_min = form.cleaned_data.get('age_min')
            if age_min:
                queryset = queryset.filter(age__gte=age_min)
            
            age_max = form.cleaned_data.get('age_max')
            if age_max:
                queryset = queryset.filter(age__lte=age_max)
            
            # BMI range filter
            bmi_range = form.cleaned_data.get('bmi_range')
            if bmi_range:
                if bmi_range == 'underweight':
                    queryset = queryset.filter(calculated_bmi__lt=18.5)
                elif bmi_range == 'normal':
                    queryset = queryset.filter(calculated_bmi__gte=18.5, calculated_bmi__lt=23)
                elif bmi_range == 'overweight':
                    queryset = queryset.filter(calculated_bmi__gte=23, calculated_bmi__lt=25)
                elif bmi_range == 'obese':
                    queryset = queryset.filter(calculated_bmi__gte=25)
            
            # Score range filter
            score_min = form.cleaned_data.get('score_min')
            if score_min is not None:
                queryset = queryset.filter(latest_score__gte=score_min)
            
            score_max = form.cleaned_data.get('score_max')
            if score_max is not None:
                queryset = queryset.filter(latest_score__lte=score_max)
            
            # Activity status filter
            activity_status = form.cleaned_data.get('activity_status')
            if activity_status == 'active':
                queryset = queryset.filter(has_recent_activity=True)
            elif activity_status == 'inactive':
                queryset = queryset.filter(has_recent_activity=False)
            
            # Sort order
            sort_by = form.cleaned_data.get('sort_by', '-created_at')
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add search form and stats to context."""
        context = super().get_context_data(**kwargs)
        
        # Add search form
        context['form'] = ClientSearchForm(self.request.GET)
        
        # Calculate stats
        context['total_clients'] = self.get_queryset().count()
        context['active_clients'] = self.get_queryset().filter(has_recent_activity=True).count()
        
        # Add export URL
        context['export_url'] = reverse_lazy('clients:export') + '?' + self.request.GET.urlencode()
        
        return context


class ClientCreateView(DualTemplateMixin, FormSuccessMessageMixin, OrganizationFilterMixin, CreateView):
    """
    Create a new client.
    
    Automatically handles:
    - Template selection for HTMX
    - Success messages via HTMX trigger or Django messages
    - Organization assignment
    """
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_message = "고객이 성공적으로 등록되었습니다."
    
    def get_form_kwargs(self):
        """Pass trainer to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trainer'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Set trainer and log action."""
        form.instance.trainer = self.request.user
        response = super().form_valid(form)
        
        # Log action
        log_client_action(
            self.request.user,
            'create',
            self.object,
            {'name': self.object.name}
        )
        
        return response
    
    def get_success_url(self):
        """Redirect to client detail."""
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})


class ClientUpdateView(DualTemplateMixin, FormSuccessMessageMixin, OrganizationFilterMixin, UpdateView):
    """
    Update an existing client.
    
    Includes permission checking via OrganizationFilterMixin.
    """
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_message = "고객 정보가 성공적으로 수정되었습니다."
    organization_field = 'trainer__organization'
    
    def get_form_kwargs(self):
        """Pass trainer to form."""
        kwargs = super().get_form_kwargs()
        kwargs['trainer'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Log update action."""
        # Get changed fields
        changed_fields = []
        if form.has_changed():
            changed_fields = form.changed_data
        
        response = super().form_valid(form)
        
        # Log action
        log_client_action(
            self.request.user,
            'update',
            self.object,
            {'changed_fields': changed_fields}
        )
        
        return response
    
    def get_success_url(self):
        """Redirect to client detail."""
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})


class ClientDetailView(DualTemplateMixin, OrganizationFilterMixin, DetailView):
    """
    Display client details with related data.
    
    Automatically uses correct template based on HTMX request.
    """
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    organization_field = 'trainer__organization'
    
    def get_context_data(self, **kwargs):
        """Add related data to context."""
        context = super().get_context_data(**kwargs)
        
        # Recent assessments
        context['recent_assessments'] = Assessment.objects.filter(
            client=self.object
        ).order_by('-date')[:5]
        
        # Active packages
        context['active_packages'] = SessionPackage.objects.filter(
            client=self.object,
            is_active=True
        ).order_by('-created_at')
        
        # Recent sessions
        context['recent_sessions'] = Session.objects.filter(
            client=self.object
        ).order_by('-session_date')[:10]
        
        # Stats
        context['total_assessments'] = Assessment.objects.filter(client=self.object).count()
        context['total_sessions'] = Session.objects.filter(client=self.object).count()
        
        return context


class ClientDeleteView(DualTemplateMixin, HTMXResponseMixin, OrganizationFilterMixin, DeleteView):
    """
    Delete a client with HTMX support.
    
    Uses HTMXResponseMixin for proper redirect handling.
    """
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')
    organization_field = 'trainer__organization'
    
    def delete(self, request, *args, **kwargs):
        """Log deletion and handle HTMX response."""
        self.object = self.get_object()
        
        # Log action before deletion
        log_client_action(
            request.user,
            'delete',
            self.object,
            {'name': self.object.name}
        )
        
        # Delete the object
        self.object.delete()
        
        # Use HTMX-aware redirect
        return self.htmx_redirect(self.get_success_url())


class ClientExportView(OrganizationFilterMixin, ListView):
    """
    Export clients to CSV.
    
    This view doesn't need DualTemplateMixin as it returns CSV.
    """
    model = Client
    organization_field = 'trainer__organization'
    
    def get_queryset(self):
        """Apply same filters as list view."""
        # Reuse the filtering logic from ClientListView
        list_view = ClientListView()
        list_view.request = self.request
        return list_view.get_queryset()
    
    def render_to_response(self, context):
        """Generate CSV response."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="clients.csv"'
        
        # Add BOM for Excel Korean support
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            '이름', '성별', '나이', '키(cm)', '체중(kg)', 'BMI', 
            '이메일', '전화번호', '최근 점수', '활동 상태', '등록일'
        ])
        
        for client in self.get_queryset():
            writer.writerow([
                client.name,
                client.get_gender_display(),
                client.age,
                client.height,
                client.weight,
                f"{client.calculated_bmi:.1f}" if hasattr(client, 'calculated_bmi') else '',
                client.email,
                client.phone,
                f"{client.latest_score:.1f}점" if client.latest_score else '-',
                '활동중' if getattr(client, 'has_recent_activity', False) else '비활동',
                client.created_at.strftime('%Y-%m-%d')
            ])
        
        return response


# URL configuration example for urls.py:
"""
from django.urls import path
from . import views_refactored as views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('add/', views.ClientCreateView.as_view(), name='add'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    path('export/', views.ClientExportView.as_view(), name='export'),
]
"""