from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.template.loader import render_to_string
import csv

from .models import Client
from .forms import ClientForm, ClientSearchForm
from apps.assessments.models import Assessment
from apps.sessions.models import SessionPackage, Session
from apps.trainers.decorators import requires_trainer, organization_member_required
from apps.trainers.audit import log_client_action


@login_required
@requires_trainer
@organization_member_required
def client_list_view(request):
    """List all clients with search and filter functionality."""
    form = ClientSearchForm(request.GET)
    # Filter clients by organization
    clients = Client.objects.filter(
        trainer__organization=request.organization
    ).select_related('trainer')
    
    # Apply search filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            clients = clients.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        gender = form.cleaned_data.get('gender')
        if gender:
            clients = clients.filter(gender=gender)
        
        age_min = form.cleaned_data.get('age_min')
        if age_min:
            clients = clients.filter(age__gte=age_min)
        
        age_max = form.cleaned_data.get('age_max')
        if age_max:
            clients = clients.filter(age__lte=age_max)
    
    # Order by most recent
    clients = clients.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(clients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add statistics
    for client in page_obj:
        client.assessment_count = client.assessments.count()
        client.active_packages = client.session_packages.filter(is_active=True).count()
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_count': paginator.count,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'clients/client_list_partial.html', context)
    
    return render(request, 'clients/client_list.html', context)


@login_required
@requires_trainer
@organization_member_required
def client_detail_view(request, pk):
    """Display detailed information about a client."""
    # Ensure client belongs to the same organization
    client = get_object_or_404(
        Client, 
        pk=pk, 
        trainer__organization=request.organization
    )
    
    # Get related data
    assessments = client.assessments.order_by('-date')[:5]
    active_packages = client.session_packages.filter(is_active=True)
    recent_sessions = client.sessions.order_by('-session_date')[:10]
    
    context = {
        'client': client,
        'assessments': assessments,
        'active_packages': active_packages,
        'recent_sessions': recent_sessions,
        'total_assessments': client.assessments.count(),
        'total_sessions': client.sessions.count(),
        'completed_sessions': client.sessions.filter(status='completed').count(),
    }
    
    # Check if this is an HTMX navigation request (navbar click)
    # HX-Target will be #main-content for navbar navigation
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        return render(request, 'clients/client_detail_content.html', context)
    
    return render(request, 'clients/client_detail.html', context)


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["GET", "POST"])
def client_add_view(request):
    """Add a new client."""
    if request.method == 'POST':
        form = ClientForm(request.POST, trainer=request.trainer)
        if form.is_valid():
            client = form.save()
            
            # Log the action
            log_client_action('client_created', client, request)
            
            # Send notification
            from apps.trainers.notifications import notify_client_added
            notify_client_added(request.trainer, client)
            
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('clients:detail', kwargs={'pk': client.pk})
                response['X-Message'] = f"{client.name}님이 등록되었습니다."
                response['X-Message-Type'] = 'success'
                return response
            
            messages.success(request, f"{client.name}님이 등록되었습니다.")
            return redirect('clients:detail', pk=client.pk)
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'clients/client_form_partial.html', {
                    'form': form,
                    'action': 'add',
                })
    else:
        form = ClientForm(trainer=request.trainer)
    
    # Check if this is an HTMX navigation request (navbar click)
    # HX-Target will be #main-content for navbar navigation
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        return render(request, 'clients/client_form_content.html', {
            'form': form,
            'action': 'add',
        })
    
    return render(request, 'clients/client_form.html', {
        'form': form,
        'action': 'add',
    })


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["GET", "POST"])
def client_edit_view(request, pk):
    """Edit an existing client."""
    # Ensure client belongs to the same organization
    client = get_object_or_404(
        Client, 
        pk=pk, 
        trainer__organization=request.organization
    )
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client, trainer=request.trainer)
        if form.is_valid():
            client = form.save()
            
            # Log the action
            log_client_action('client_updated', client, request)
            
            if request.headers.get('HX-Request'):
                # For HTMX requests, redirect to the detail page
                response = HttpResponse(status=204)
                response['HX-Redirect'] = reverse('clients:detail', kwargs={'pk': client.pk})
                return response
            
            messages.success(request, "회원 정보가 수정되었습니다.")
            return redirect('clients:detail', pk=client.pk)
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'clients/client_form_partial.html', {
                    'form': form,
                    'client': client,
                    'action': 'edit',
                })
    else:
        form = ClientForm(instance=client, trainer=request.trainer)
    
    # Check if this is an HTMX navigation request (navbar click)
    # HX-Target will be #main-content for navbar navigation
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        return render(request, 'clients/client_form_content.html', {
            'form': form,
            'client': client,
            'action': 'edit',
        })
    
    return render(request, 'clients/client_form.html', {
        'form': form,
        'client': client,
        'action': 'edit',
    })


@login_required
@requires_trainer
@organization_member_required
@require_http_methods(["DELETE"])
def client_delete_view(request, pk):
    """Delete a client."""
    # Ensure client belongs to the same organization
    client = get_object_or_404(
        Client, 
        pk=pk, 
        trainer__organization=request.organization
    )
    name = client.name
    
    # Log the action before deletion
    log_client_action('client_deleted', client, request)
    
    client.delete()
    
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Redirect'] = reverse('clients:list')
        response['X-Message'] = f"{name}님이 삭제되었습니다."
        response['X-Message-Type'] = 'info'
        return response
    
    messages.info(request, f"{name}님이 삭제되었습니다.")
    return redirect('clients:list')


@login_required
@requires_trainer
@organization_member_required
def client_export_view(request):
    """Export client list to CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="clients.csv"'
    
    # Add BOM for proper Korean encoding in Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(['이름', '나이', '성별', '키(cm)', '몸무게(kg)', 'BMI', '이메일', '전화번호', '등록일', '담당 트레이너'])
    
    # Export all clients in the organization
    clients = Client.objects.filter(
        trainer__organization=request.organization
    ).select_related('trainer__user').order_by('name')
    for client in clients:
        writer.writerow([
            client.name,
            client.age,
            client.get_gender_display(),
            client.height,
            client.weight,
            client.bmi if client.bmi else '',
            client.email or '',
            client.phone or '',
            client.created_at.strftime('%Y-%m-%d'),
            client.trainer.user.get_full_name() or client.trainer.user.username,
        ])
    
    return response


# HTMX validation endpoints
@login_required
@requires_trainer
@require_http_methods(["POST"])
def validate_client_name(request):
    """Validate client name via HTMX."""
    name = request.POST.get('name', '').strip()
    
    if not name:
        return HttpResponse('<div class="text-red-500 text-sm mt-1">이름을 입력해주세요.</div>')
    
    if len(name) < 2:
        return HttpResponse('<div class="text-red-500 text-sm mt-1">이름은 최소 2자 이상이어야 합니다.</div>')
    
    # Check for duplicate names within organization (warning only)
    existing = Client.objects.filter(
        trainer__organization=request.organization, 
        name=name
    ).exists()
    if existing:
        return HttpResponse('<div class="text-yellow-500 text-sm mt-1">동일한 이름의 회원이 이미 있습니다.</div>')
    
    return HttpResponse('')


@login_required
@requires_trainer
@require_http_methods(["POST"])
def validate_client_email(request):
    """Validate client email via HTMX."""
    email = request.POST.get('email', '').strip()
    
    if not email:
        return HttpResponse('')  # Email is optional
    
    # Basic email validation is handled by the form field
    # Check for duplicates within organization
    existing = Client.objects.filter(
        trainer__organization=request.organization, 
        email=email
    ).exclude(pk=request.POST.get('client_id')).exists()
    
    if existing:
        return HttpResponse('<div class="text-red-500 text-sm mt-1">이미 등록된 이메일입니다.</div>')
    
    return HttpResponse('')


@login_required
@requires_trainer
@require_http_methods(["POST"])
def validate_client_phone(request):
    """Validate client phone via HTMX."""
    phone = request.POST.get('phone', '').strip()
    
    if not phone:
        return HttpResponse('')  # Phone is optional
    
    # Remove non-digits for validation
    cleaned_phone = ''.join(filter(str.isdigit, phone))
    
    if len(cleaned_phone) not in [10, 11]:
        return HttpResponse('<div class="text-red-500 text-sm mt-1">올바른 전화번호 형식이 아닙니다.</div>')
    
    return HttpResponse('')
