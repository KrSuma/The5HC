from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from decimal import Decimal
import json

from .models import SessionPackage, Session, Payment
from .forms import SessionPackageForm, SessionForm, PaymentForm, SessionSearchForm
from apps.clients.models import Client
from apps.trainers.decorators import requires_trainer, organization_member_required


@login_required
@requires_trainer
@organization_member_required
def session_package_list_view(request):
    """List all session packages with search and filter functionality"""
    # Filter packages by organization
    packages = SessionPackage.objects.filter(
        trainer__organization=request.organization
    ).select_related('client', 'trainer')
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        packages = packages.filter(
            Q(client__name__icontains=search) |
            Q(package_name__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        packages = packages.filter(is_active=True, remaining_sessions__gt=0)
    elif status == 'expired':
        packages = packages.filter(Q(remaining_sessions=0) | Q(is_active=False))
    
    # Pagination
    paginator = Paginator(packages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = packages.aggregate(
        total_packages=Count('id'),
        active_packages=Count('id', filter=Q(is_active=True, remaining_sessions__gt=0)),
        total_revenue=Sum('net_amount'),
        avg_package_value=Avg('total_amount')
    )
    
    # HTMX handling
    if request.headers.get('HX-Request'):
        html = render_to_string(
            'sessions/package_list_partial.html',
            {'page_obj': page_obj, 'request': request}
        )
        return HttpResponse(html)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
        'status': status
    }
    return render(request, 'sessions/package_list.html', context)


@login_required
@requires_trainer
@organization_member_required
def session_package_detail_view(request, pk):
    """View detailed package information with sessions and payments"""
    # Ensure package belongs to the same organization
    package = get_object_or_404(
        SessionPackage.objects.select_related('client', 'trainer'),
        pk=pk,
        trainer__organization=request.organization
    )
    
    # Get related sessions and payments
    sessions = package.sessions.all()[:10]  # Latest 10 sessions
    payments = package.payments.all()[:5]   # Latest 5 payments
    
    context = {
        'package': package,
        'sessions': sessions,
        'payments': payments,
        'total_sessions_count': package.sessions.count(),
        'completed_sessions_count': package.sessions.filter(status='completed').count(),
        'total_payments': package.payments.aggregate(Sum('amount'))['amount__sum'] or 0
    }
    return render(request, 'sessions/package_detail.html', context)


@login_required
@requires_trainer
@organization_member_required
def session_package_add_view(request):
    """Add new session package"""
    client_id = request.GET.get('client')
    
    if request.method == 'POST':
        form = SessionPackageForm(request.POST, user=request.trainer.user)
        if form.is_valid():
            package = form.save(commit=False)
            package.trainer = request.trainer.user
            package.remaining_sessions = package.total_sessions
            package.remaining_credits = package.total_amount
            
            # Set default fee rates
            package.vat_rate = Decimal('0.10')  # 10% VAT
            package.card_fee_rate = Decimal('0.035')  # 3.5% card fee
            package.fee_calculation_method = 'inclusive'
            
            # Save package first without fee calculation
            try:
                package.save()
                # Now calculate fees after package has been saved
                package.calculate_fees(save_audit=True)
                package.save()  # Save again with calculated fees
                messages.success(request, f'"{package.package_name}" 패키지가 성공적으로 생성되었습니다.')
            except Exception as e:
                messages.error(request, f'패키지 저장 중 오류가 발생했습니다: {str(e)}')
                return render(request, 'sessions/package_form.html', {'form': form, 'client_id': client_id})
            
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/sessions/packages/'}
                )
            return redirect('sessions:package_list')
        else:
            # Add form error messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            
            if request.headers.get('HX-Request'):
                html = render_to_string(
                    'sessions/package_form_partial.html',
                    {'form': form, 'client_id': client_id, 'request': request}
                )
                return HttpResponse(html)
    else:
        initial = {}
        if client_id:
            initial['client'] = client_id
        form = SessionPackageForm(initial=initial, user=request.trainer.user)
    
    context = {
        'form': form,
        'client_id': client_id,
    }
    return render(request, 'sessions/package_form.html', context)


@login_required
@requires_trainer
@organization_member_required
def session_list_view(request):
    """List all sessions with search and filter functionality"""
    form = SessionSearchForm(request.GET)
    # Filter sessions by organization
    sessions = Session.objects.filter(
        trainer__organization=request.organization
    ).select_related('client', 'package', 'trainer')
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            sessions = sessions.filter(
                Q(client__name__icontains=search) |
                Q(package__package_name__icontains=search)
            )
        
        status = form.cleaned_data.get('status')
        if status:
            sessions = sessions.filter(status=status)
            
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            sessions = sessions.filter(session_date__gte=date_from)
            
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            sessions = sessions.filter(session_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = sessions.aggregate(
        total_sessions=Count('id'),
        completed_sessions=Count('id', filter=Q(status='completed')),
        total_revenue=Sum('session_cost'),
        avg_session_cost=Avg('session_cost')
    )
    
    # HTMX handling
    if request.headers.get('HX-Request'):
        html = render_to_string(
            'sessions/session_list_partial.html',
            {'page_obj': page_obj, 'request': request}
        )
        return HttpResponse(html)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'stats': stats
    }
    return render(request, 'sessions/session_list.html', context)


@login_required
@requires_trainer
@organization_member_required
def session_add_view(request):
    """Add new session"""
    client_id = request.GET.get('client')
    
    if request.method == 'POST':
        # Get client_id from POST data for form validation
        post_client_id = request.POST.get('client')
        form = SessionForm(request.POST, user=request.user, client_id=post_client_id)
        if form.is_valid():
            session = form.save(commit=False)
            session.trainer = request.user
            
            # Set session cost from package if not already set
            if not session.session_cost:
                session.session_cost = session.package.session_price
            
            # Deduct session from package
            package = session.package
            if package.remaining_sessions > 0:
                package.remaining_sessions -= 1
                package.remaining_credits -= session.session_cost
                package.save()
                
                session.save()
                messages.success(request, '세션이 성공적으로 예약되었습니다.')
                
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        status=204,
                        headers={'HX-Redirect': '/sessions/'}
                    )
                return redirect('sessions:session_list')
            else:
                form.add_error('package', '선택한 패키지에 남은 세션이 없습니다.')
    else:
        form = SessionForm(user=request.user, client_id=client_id)
    
    context = {
        'form': form,
        'client_id': client_id,
    }
    return render(request, 'sessions/session_form.html', context)


@login_required
def session_complete_view(request, pk):
    """Mark session as completed"""
    session = get_object_or_404(Session, pk=pk, trainer=request.user)
    
    if request.method == 'POST':
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        messages.success(request, '세션이 완료로 표시되었습니다.')
        
        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
        return redirect('sessions:session_list')
    
    return render(request, 'sessions/session_confirm_complete.html', {
        'session': session
    })


@login_required
def payment_add_view(request):
    """Add new payment"""
    client_id = request.GET.get('client')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.trainer = request.user
            payment.save()
            
            messages.success(request, '결제가 성공적으로 기록되었습니다.')
            
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/sessions/packages/'}
                )
            return redirect('sessions:package_list')
    else:
        initial = {}
        if client_id:
            initial['client'] = client_id
        form = PaymentForm(initial=initial, user=request.user)
    
    context = {
        'form': form,
        'client_id': client_id,
    }
    return render(request, 'sessions/payment_form.html', context)


@login_required
@require_http_methods(["GET"])
def get_client_packages_ajax(request):
    """AJAX endpoint to get packages for a specific client"""
    client_id = request.GET.get('client_id')
    if not client_id:
        return JsonResponse({'packages': []})
    
    packages = SessionPackage.objects.filter(
        client_id=client_id,
        trainer=request.user,
        is_active=True,
        remaining_sessions__gt=0
    ).values('id', 'package_name', 'session_price', 'remaining_sessions')
    
    return JsonResponse({'packages': list(packages)})


@login_required
@require_http_methods(["GET"])
def calculate_package_fees_ajax(request):
    """AJAX endpoint to calculate package fees"""
    try:
        total_amount = Decimal(request.GET.get('total_amount', '0'))
        vat_rate = Decimal(request.GET.get('vat_rate', '0.10'))
        card_fee_rate = Decimal(request.GET.get('card_fee_rate', '0.035'))
        method = request.GET.get('method', 'inclusive')
        
        if method == 'inclusive':
            gross = int(total_amount)
            total_fee_rate = vat_rate + card_fee_rate
            net = int(gross / (1 + total_fee_rate))
            vat = int(net * vat_rate)
            card_fee = int(net * card_fee_rate)
            
            # Adjust for rounding
            total_fees = vat + card_fee
            if gross - net != total_fees:
                card_fee += gross - net - total_fees
        else:
            net = int(total_amount)
            vat = int(net * vat_rate)
            card_fee = int(net * card_fee_rate)
            gross = net + vat + card_fee
        
        return JsonResponse({
            'gross_amount': gross,
            'vat_amount': vat,
            'card_fee_amount': card_fee,
            'net_amount': net,
            'total_fee_rate': float(vat_rate + card_fee_rate) * 100
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def session_calendar_view(request):
    """Calendar view for sessions"""
    # Get current month's sessions
    today = timezone.now().date()
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = today.month
        year = today.year
    
    # Get sessions for the month
    sessions = Session.objects.filter(
        trainer=request.user,
        session_date__year=year,
        session_date__month=month
    ).select_related('client', 'package')
    
    # Group sessions by date
    sessions_by_date = {}
    for session in sessions:
        date_str = session.session_date.strftime('%Y-%m-%d')
        if date_str not in sessions_by_date:
            sessions_by_date[date_str] = []
        sessions_by_date[date_str].append(session)
    
    context = {
        'sessions_by_date': json.dumps(sessions_by_date, default=str),
        'current_month': month,
        'current_year': year,
        'today': today.strftime('%Y-%m-%d')
    }
    return render(request, 'sessions/session_calendar.html', context)
