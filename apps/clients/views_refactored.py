"""
Refactored client views using the service layer.
This demonstrates how to use the new service layer infrastructure.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
import csv

from apps.core.services import ClientService
from .models import Client
from .forms import ClientForm, ClientSearchForm
from apps.trainers.decorators import requires_trainer, organization_member_required


@login_required
@requires_trainer
@organization_member_required
def client_list_view_refactored(request):
    """
    Refactored client list view using the ClientService.
    This demonstrates the service layer pattern.
    """
    # Initialize service with user context
    service = ClientService(user=request.user)
    
    # Get form data
    form = ClientSearchForm(request.GET)
    filters = {}
    
    if form.is_valid():
        # Build filters from form data
        filters = {
            'search': form.cleaned_data.get('search'),
            'gender': form.cleaned_data.get('gender'),
            'age_min': form.cleaned_data.get('age_min'),
            'age_max': form.cleaned_data.get('age_max'),
            'bmi_range': form.cleaned_data.get('bmi_range'),
            'has_medical_conditions': form.cleaned_data.get('has_medical_conditions'),
            'activity_status': form.cleaned_data.get('activity_status'),
            'latest_score_range': form.cleaned_data.get('latest_score_range'),
            'sort_by': form.cleaned_data.get('sort_by', '-created_at'),
        }
        
        # Clean up empty values
        filters = {k: v for k, v in filters.items() if v}
    
    # Use service to get filtered clients
    clients = service.search_and_filter(filters)
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        # Use service method for export
        export_data = service.export_clients_data(clients)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clients.csv"'
        
        if export_data:
            writer = csv.DictWriter(response, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
        
        return response
    
    # Pagination
    paginator = Paginator(clients, 20)
    page = request.GET.get('page')
    clients_page = paginator.get_page(page)
    
    # Get dashboard metrics using service
    metrics = service.get_dashboard_metrics()
    
    context = {
        'clients': clients_page,
        'form': form,
        'total_count': paginator.count,
        'metrics': metrics,
        'page_title': '고객 관리',
    }
    
    # Handle HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'clients/client_list_content.html', context)
    
    return render(request, 'clients/client_list.html', context)


@login_required
@requires_trainer
@organization_member_required
def client_detail_view_refactored(request, pk):
    """
    Refactored client detail view using the ClientService.
    """
    service = ClientService(user=request.user)
    
    # Get client using service
    client = service.get_object(pk)
    if not client:
        messages.error(request, "고객을 찾을 수 없습니다.")
        return redirect('clients:client_list')
    
    # Get client statistics using service
    stats = service.get_client_statistics(client)
    
    # Get client timeline
    timeline = service.get_client_timeline(client, limit=10)
    
    context = {
        'client': client,
        'stats': stats,
        'timeline': timeline,
        'page_title': f'{client.name} - 고객 정보',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'clients/client_detail_content.html', context)
    
    return render(request, 'clients/client_detail.html', context)


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["GET", "POST"])
def client_add_view_refactored(request):
    """
    Refactored client add view using the ClientService.
    """
    service = ClientService(user=request.user)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, user=request.user)
        if form.is_valid():
            # Use service to create client
            client_data = form.cleaned_data
            client, success = service.create_client(client_data)
            
            if success:
                messages.success(request, f"고객 '{client.name}'이(가) 등록되었습니다.")
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        status=204,
                        headers={'HX-Redirect': reverse('clients:client_detail', kwargs={'pk': client.pk})}
                    )
                return redirect('clients:client_detail', pk=client.pk)
            else:
                # Add service errors to form
                for error in service.errors:
                    form.add_error(None, error)
    else:
        form = ClientForm(user=request.user)
    
    context = {
        'form': form,
        'page_title': '고객 등록',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'clients/client_form_content.html', context)
    
    return render(request, 'clients/client_form.html', context)


@login_required  
@requires_trainer
@organization_member_required
@require_http_methods(["GET", "POST"])
def client_edit_view_refactored(request, pk):
    """
    Refactored client edit view using the ClientService.
    """
    service = ClientService(user=request.user)
    
    # Get client using service
    client = service.get_object(pk)
    if not client:
        messages.error(request, "고객을 찾을 수 없습니다.")
        return redirect('clients:client_list')
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client, user=request.user)
        if form.is_valid():
            # Use service to update client
            success = service.update_client(client, form.cleaned_data)
            
            if success:
                messages.success(request, f"고객 '{client.name}'의 정보가 수정되었습니다.")
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        status=204,
                        headers={'HX-Redirect': reverse('clients:client_detail', kwargs={'pk': client.pk})}
                    )
                return redirect('clients:client_detail', pk=client.pk)
            else:
                # Add service errors to form
                for error in service.errors:
                    form.add_error(None, error)
    else:
        form = ClientForm(instance=client, user=request.user)
    
    context = {
        'form': form,
        'client': client,
        'page_title': f'{client.name} - 정보 수정',
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'clients/client_form_content.html', context)
    
    return render(request, 'clients/client_form.html', context)


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["DELETE"])
def client_delete_view_refactored(request, pk):
    """
    Refactored client delete view using the ClientService.
    """
    service = ClientService(user=request.user)
    
    # Get client using service
    client = service.get_object(pk)
    if not client:
        return JsonResponse({'error': '고객을 찾을 수 없습니다.'}, status=404)
    
    # Check if client can be deleted
    if hasattr(client, 'assessments') and client.assessments.exists():
        return JsonResponse({'error': '평가 기록이 있는 고객은 삭제할 수 없습니다.'}, status=400)
    
    if hasattr(client, 'session_packages') and client.session_packages.exists():
        return JsonResponse({'error': '세션 패키지가 있는 고객은 삭제할 수 없습니다.'}, status=400)
    
    # Delete using service (includes audit logging)
    client_name = client.name
    success = service.delete(client)
    
    if success:
        messages.success(request, f"고객 '{client_name}'이(가) 삭제되었습니다.")
        return HttpResponse(status=204, headers={'HX-Redirect': reverse('clients:client_list')})
    else:
        return JsonResponse({'error': service.get_errors_string()}, status=400)