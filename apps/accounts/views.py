from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils.translation import gettext as _

from .forms import LoginForm, CustomUserChangeForm, PasswordResetRequestForm
from .models import User


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Handle user login with HTMX support."""
    if request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('dashboard')
            return response
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            
            # Reset failed login attempts
            user.reset_failed_login_attempts()
            
            # Log the user in
            login(request, user)
            
            # Handle "Remember Me"
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('dashboard')
                response['X-Message'] = _("Welcome, %(name)s!") % {'name': user.name}
                response['X-Message-Type'] = 'success'
                return response
            
            messages.success(request, _("Welcome, %(name)s!") % {'name': user.name})
            return redirect('dashboard')
        else:
            # Handle failed login attempt
            email_or_username = request.POST.get('email_or_username')
            if email_or_username:
                # Try to find the user and increment failed attempts
                if '@' in email_or_username:
                    try:
                        user = User.objects.get(email=email_or_username)
                        user.increment_failed_login_attempts()
                    except User.DoesNotExist:
                        pass
                else:
                    try:
                        user = User.objects.get(username=email_or_username)
                        user.increment_failed_login_attempts()
                    except User.DoesNotExist:
                        pass
            
            if request.headers.get('HX-Request'):
                return render(request, 'registration/login_form.html', {
                    'form': form,
                })
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {
        'form': form,
    })


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """Handle user logout with HTMX support."""
    logout(request)
    
    if request.headers.get('HX-Request'):
        response = HttpResponse()
        response['HX-Redirect'] = reverse('accounts:login')
        response['X-Message'] = _('You have been logged out.')
        response['X-Message-Type'] = 'info'
        return response
    
    messages.info(request, _('You have been logged out.'))
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view."""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['X-Message'] = _('Profile updated successfully.')
                response['X-Message-Type'] = 'success'
                return render(request, 'accounts/profile_form.html', {
                    'form': form,
                    'success': True,
                }, headers=response.headers)
            
            messages.success(request, _('Profile updated successfully.'))
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
    })


@require_http_methods(["GET", "POST"])
def password_reset_request_view(request):
    """Handle password reset requests."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # TODO: Implement email sending logic
            
            if request.headers.get('HX-Request'):
                return render(request, 'registration/password_reset_done.html', {
                    'email': email,
                })
            
            messages.success(request, _("Password reset link has been sent to %(email)s.") % {'email': email})
            return render(request, 'registration/password_reset_done.html', {
                'email': email,
            })
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'registration/password_reset_form.html', {
        'form': form,
    })


@login_required
def dashboard_view(request):
    """Main dashboard view with comprehensive analytics."""
    from django.db.models import Count, Sum, Q, Avg
    from datetime import datetime, timedelta
    from django.utils import timezone
    from apps.clients.models import Client
    from apps.sessions.models import SessionPackage, Session, Payment
    from apps.assessments.models import Assessment
    
    # Date ranges for analytics
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    this_week_start = today - timedelta(days=today.weekday())
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # Basic counts
    total_clients = request.user.clients.count()
    active_packages = request.user.session_packages.filter(is_active=True).count()
    
    # Session statistics
    sessions_this_month = request.user.sessions.filter(
        session_date__gte=this_month_start
    ).count()
    
    completed_sessions_this_month = request.user.sessions.filter(
        session_date__gte=this_month_start,
        status='completed'
    ).count()
    
    # Revenue statistics  
    revenue_this_month = Payment.objects.filter(
        package__trainer=request.user,
        payment_date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    # Convert Decimal to int for JavaScript
    revenue_this_month = int(revenue_this_month)
    
    revenue_last_month = Payment.objects.filter(
        package__trainer=request.user,
        payment_date__gte=last_month_start,
        payment_date__lt=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    # Convert Decimal to int for JavaScript
    revenue_last_month = int(revenue_last_month)
    
    # Client growth statistics
    new_clients_this_month = request.user.clients.filter(
        created_at__gte=this_month_start
    ).count()
    
    new_clients_this_week = request.user.clients.filter(
        created_at__gte=this_week_start
    ).count()
    
    # Assessment statistics
    assessments_this_month = Assessment.objects.filter(
        client__trainer=request.user,
        date__gte=this_month_start
    ).count()
    
    avg_score_this_month = Assessment.objects.filter(
        client__trainer=request.user,
        date__gte=this_month_start,
        overall_score__isnull=False
    ).aggregate(avg=Avg('overall_score'))['avg'] or 0
    
    # Package statistics
    package_stats = SessionPackage.objects.filter(
        trainer=request.user
    ).aggregate(
        total_value=Sum('total_amount'),
        avg_value=Avg('total_amount'),
        total_sessions_sold=Sum('total_sessions')
    )
    
    # Weekly session data for chart (last 7 weeks)
    weekly_sessions = []
    for i in range(7):
        week_start = today - timedelta(weeks=i, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_sessions = request.user.sessions.filter(
            session_date__gte=week_start,
            session_date__lte=week_end
        ).count()
        weekly_sessions.append({
            'week': f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
            'sessions': week_sessions
        })
    weekly_sessions.reverse()
    
    # Monthly revenue data for chart (last 6 months)
    monthly_revenue = []
    for i in range(6):
        # Calculate the month start date by going back i months
        year = this_month_start.year
        month = this_month_start.month - i
        if month <= 0:
            year -= 1
            month += 12
        month_start = this_month_start.replace(year=year, month=month, day=1)
        
        # Calculate month end
        if i == 0:
            month_end = today
        else:
            # Get the first day of next month
            if month == 12:
                next_month_start = month_start.replace(year=year + 1, month=1, day=1)
            else:
                next_month_start = month_start.replace(month=month + 1, day=1)
            # Last day of current month is day before first day of next month
            month_end = next_month_start - timedelta(days=1)
        
        month_revenue = Payment.objects.filter(
            package__trainer=request.user,
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%Y년 %m월'),
            'revenue': int(month_revenue)  # Convert to int for JavaScript
        })
        
        # Debug logging
        print(f"DEBUG: Month {month_start.strftime('%Y-%m')}: Revenue = {month_revenue}")
        
    monthly_revenue.reverse()
    
    # Debug: Print final monthly revenue data
    print("DEBUG: Final monthly_revenue data:")
    for item in monthly_revenue:
        print(f"  {item['month']}: {item['revenue']}")
    
    # Package status distribution (active vs inactive)
    package_distribution = SessionPackage.objects.filter(
        trainer=request.user
    ).values('is_active').annotate(count=Count('id'))
    
    # Recent activities (mixed recent items)
    recent_activities = []
    
    # Recent clients
    for client in request.user.clients.order_by('-created_at')[:3]:
        recent_activities.append({
            'type': 'client_added',
            'title': f"새 회원 등록: {client.name}",
            'date': client.created_at,
            'icon': 'user-plus',
            'color': 'blue',
            'url': f"/clients/{client.id}/"
        })
    
    # Recent sessions
    for session in request.user.sessions.order_by('-session_date')[:3]:
        recent_activities.append({
            'type': 'session',
            'title': f"세션: {session.client.name}",
            'date': timezone.make_aware(datetime.combine(session.session_date, session.session_time if session.session_time else datetime.min.time())),
            'icon': 'calendar',
            'color': 'green',
            'status': session.status
        })
    
    # Recent assessments
    for assessment in Assessment.objects.filter(client__trainer=request.user).order_by('-date')[:3]:
        recent_activities.append({
            'type': 'assessment',
            'title': f"평가 완료: {assessment.client.name}",
            'date': timezone.make_aware(datetime.combine(assessment.date, datetime.min.time())),
            'icon': 'clipboard-check',
            'color': 'purple',
            'score': assessment.overall_score
        })
    
    # Sort by date and limit
    recent_activities = sorted(recent_activities, key=lambda x: x['date'], reverse=True)[:8]
    
    # Calculate growth percentages
    revenue_growth = 0
    if revenue_last_month > 0:
        revenue_growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
    
    context = {
        'user': request.user,
        'recent_clients': request.user.clients.order_by('-created_at')[:5],
        'recent_sessions': request.user.sessions.order_by('-session_date')[:5],
        
        # Enhanced analytics data
        'total_clients': total_clients,
        'active_packages': active_packages,
        'sessions_this_month': sessions_this_month,
        'completed_sessions_this_month': completed_sessions_this_month,
        'revenue_this_month': revenue_this_month,
        'revenue_last_month': revenue_last_month,
        'revenue_growth': revenue_growth,
        'new_clients_this_month': new_clients_this_month,
        'new_clients_this_week': new_clients_this_week,
        'assessments_this_month': assessments_this_month,
        'avg_score_this_month': avg_score_this_month,
        'package_stats': package_stats,
        'weekly_sessions': weekly_sessions,
        'monthly_revenue': monthly_revenue,
        'package_distribution': package_distribution,
        'recent_activities': recent_activities,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'dashboard/dashboard_content.html', context)
    
    return render(request, 'dashboard/dashboard.html', context)
