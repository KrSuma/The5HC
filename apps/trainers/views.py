from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

from .models import Trainer, Organization, TrainerInvitation
from .forms import TrainerProfileForm, OrganizationForm, TrainerInvitationForm
from .decorators import requires_trainer, organization_member_required, trainer_role_required, organization_owner_required


@login_required
def trainer_list_view(request):
    """List all trainers in the user's organization."""
    try:
        trainer = request.user.trainer_profile
        organization = trainer.organization
    except Trainer.DoesNotExist:
        # Allow superusers to view all trainers
        if request.user.is_superuser:
            trainer = None
            organization = None
            # For superusers, show all trainers from all organizations
            trainers = Trainer.objects.filter(
                is_active=True
            ).select_related('user', 'organization').order_by('organization__name', 'role', 'user__first_name')
        else:
            messages.error(request, _('You need to have a trainer profile to access this page.'))
            return redirect('accounts:profile')
    else:
        # Get trainers in the same organization
        trainers = Trainer.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('user').order_by('role', 'user__first_name')
    
    # Apply search if provided
    search_query = request.GET.get('search', '')
    if search_query:
        trainers = trainers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(specialties__icontains=search_query)
        )
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/trainer_list_content.html'
    else:
        template = 'trainers/trainer_list.html'
    
    context = {
        'trainers': trainers,
        'organization': organization,
        'search_query': search_query,
        'can_manage': trainer.can_manage_trainers() if trainer else request.user.is_superuser,
        'trainer': trainer,  # Add trainer to context for template checks
    }
    
    return render(request, template, context)


@login_required
def trainer_detail_view(request, pk):
    """Display trainer profile details."""
    trainer = get_object_or_404(
        Trainer.objects.select_related('user', 'organization'),
        pk=pk
    )
    
    # Check if user can view this trainer
    try:
        current_trainer = request.user.trainer_profile
        if trainer.organization != current_trainer.organization:
            messages.error(request, _('You cannot view trainers from other organizations.'))
            return redirect('trainers:list')
    except Trainer.DoesNotExist:
        # If user doesn't have a trainer profile, check if they're superuser
        if request.user.is_superuser:
            # Allow superusers to view any trainer
            current_trainer = None
        else:
            messages.error(request, _('You need to have a trainer profile to access this page.'))
            return redirect('accounts:profile')
    
    # Get trainer statistics with error handling
    try:
        stats = {
            'total_clients': trainer.clients.count(),
            'active_packages': trainer.session_packages.filter(
                remaining_sessions__gt=0,
                expire_date__gte=timezone.now().date()
            ).count(),
            'total_sessions': trainer.sessions.count(),
            'assessments': trainer.assessments_conducted.count(),
        }
    except Exception as e:
        # If there's an error getting stats, use defaults
        print(f"Error getting trainer stats: {e}")
        stats = {
            'total_clients': 0,
            'active_packages': 0,
            'total_sessions': 0,
            'assessments': 0,
        }
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/trainer_detail_content.html'
    else:
        template = 'trainers/trainer_detail.html'
    
    context = {
        'trainer': trainer,
        'stats': stats,
        'is_own_profile': trainer.user == request.user,
        'can_manage': current_trainer.can_manage_trainers() if current_trainer else False,
    }
    
    return render(request, template, context)


@login_required
def trainer_profile_edit_view(request, pk=None):
    """Edit trainer profile (own profile or managed trainer)."""
    # If no pk provided, edit own profile
    if pk is None:
        try:
            trainer = request.user.trainer_profile
        except Trainer.DoesNotExist:
            messages.error(request, _('You need to have a trainer profile to access this page.'))
            return redirect('accounts:profile')
    else:
        trainer = get_object_or_404(Trainer, pk=pk)
        
        # Check permissions
        try:
            current_trainer = request.user.trainer_profile
            if trainer.organization != current_trainer.organization:
                messages.error(request, _('You cannot edit trainers from other organizations.'))
                return redirect('trainers:list')
            
            # Only owners and seniors can edit other trainers
            if trainer != current_trainer and not current_trainer.can_manage_trainers():
                messages.error(request, _('You do not have permission to edit other trainers.'))
                return redirect('trainers:detail', pk=trainer.pk)
        except Trainer.DoesNotExist:
            messages.error(request, _('You need to have a trainer profile to access this page.'))
            return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = TrainerProfileForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully.'))
            return redirect('trainers:detail', pk=trainer.pk)
    else:
        form = TrainerProfileForm(instance=trainer)
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/trainer_form_content.html'
    else:
        template = 'trainers/trainer_form.html'
    
    context = {
        'form': form,
        'trainer': trainer,
        'is_own_profile': trainer.user == request.user,
    }
    
    return render(request, template, context)


@login_required
def organization_edit_view(request):
    """Edit organization details (owners only)."""
    try:
        trainer = request.user.trainer_profile
        if not trainer.is_owner():
            messages.error(request, _('Only organization owners can edit organization details.'))
            return redirect('trainers:list')
        
        organization = trainer.organization
    except Trainer.DoesNotExist:
        messages.error(request, _('You need to have a trainer profile to access this page.'))
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, _('Organization details updated successfully.'))
            return redirect('trainers:list')
    else:
        form = OrganizationForm(instance=organization)
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/organization_form_content.html'
    else:
        template = 'trainers/organization_form.html'
    
    context = {
        'form': form,
        'organization': organization,
    }
    
    return render(request, template, context)


@login_required
def trainer_invite_view(request):
    """Invite new trainers to the organization."""
    try:
        trainer = request.user.trainer_profile
        if not trainer.can_manage_trainers():
            messages.error(request, _('You do not have permission to invite trainers.'))
            return redirect('trainers:list')
        
        organization = trainer.organization
    except Trainer.DoesNotExist:
        messages.error(request, _('You need to have a trainer profile to access this page.'))
        return redirect('accounts:profile')
    
    # Check if organization can add more trainers
    if not organization.can_add_trainer():
        messages.error(request, _(
            'Your organization has reached the maximum number of trainers (%(max)s).'
        ) % {'max': organization.max_trainers})
        return redirect('trainers:list')
    
    if request.method == 'POST':
        form = TrainerInvitationForm(request.POST, organization=organization)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.organization = organization
            invitation.invited_by = request.user
            invitation.invitation_code = str(uuid.uuid4())
            invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
            invitation.save()
            
            # TODO: Send invitation email
            
            messages.success(request, _(
                'Invitation sent to %(email)s. They have 7 days to accept.'
            ) % {'email': invitation.email})
            return redirect('trainers:list')
    else:
        form = TrainerInvitationForm(organization=organization)
    
    # Get pending invitations
    pending_invitations = TrainerInvitation.objects.filter(
        organization=organization,
        status='pending'
    ).order_by('-created_at')
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/trainer_invite_content.html'
    else:
        template = 'trainers/trainer_invite.html'
    
    context = {
        'form': form,
        'organization': organization,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, template, context)


@login_required
@require_http_methods(["POST"])
def trainer_deactivate_view(request, pk):
    """Deactivate a trainer (owners and seniors only)."""
    trainer_to_deactivate = get_object_or_404(Trainer, pk=pk)
    
    try:
        current_trainer = request.user.trainer_profile
        
        # Check permissions
        if trainer_to_deactivate.organization != current_trainer.organization:
            messages.error(request, _('You cannot deactivate trainers from other organizations.'))
            return redirect('trainers:list')
        
        if not current_trainer.can_manage_trainers():
            messages.error(request, _('You do not have permission to deactivate trainers.'))
            return redirect('trainers:list')
        
        # Cannot deactivate yourself
        if trainer_to_deactivate == current_trainer:
            messages.error(request, _('You cannot deactivate yourself.'))
            return redirect('trainers:detail', pk=trainer_to_deactivate.pk)
        
        # Cannot deactivate the only owner
        if trainer_to_deactivate.is_owner():
            owner_count = Trainer.objects.filter(
                organization=trainer_to_deactivate.organization,
                role='owner',
                is_active=True
            ).count()
            if owner_count == 1:
                messages.error(request, _('Cannot deactivate the only owner of the organization.'))
                return redirect('trainers:detail', pk=trainer_to_deactivate.pk)
        
        # Deactivate the trainer
        trainer_to_deactivate.deactivate()
        messages.success(request, _(
            '%(name)s has been deactivated.'
        ) % {'name': trainer_to_deactivate.get_display_name()})
        
    except Trainer.DoesNotExist:
        messages.error(request, _('You need to have a trainer profile to access this page.'))
        return redirect('accounts:profile')
    
    return redirect('trainers:list')


@login_required
@require_http_methods(["POST"])
def invitation_cancel_view(request, pk):
    """Cancel a pending invitation."""
    invitation = get_object_or_404(TrainerInvitation, pk=pk)
    
    try:
        trainer = request.user.trainer_profile
        
        # Check permissions
        if invitation.organization != trainer.organization:
            messages.error(request, _('You cannot cancel invitations from other organizations.'))
            return redirect('trainers:invite')
        
        if not trainer.can_manage_trainers():
            messages.error(request, _('You do not have permission to cancel invitations.'))
            return redirect('trainers:invite')
        
        if invitation.status != 'pending':
            messages.error(request, _('This invitation has already been %(status)s.') % {
                'status': invitation.get_status_display()
            })
            return redirect('trainers:invite')
        
        # Cancel the invitation
        invitation.status = 'expired'
        invitation.save()
        
        messages.success(request, _('Invitation cancelled successfully.'))
        
    except Trainer.DoesNotExist:
        messages.error(request, _('You need to have a trainer profile to access this page.'))
        return redirect('accounts:profile')
    
    return redirect('trainers:invite')


@login_required
@requires_trainer
def organization_switch_view(request):
    """
    Handle organization switching for trainers who belong to multiple organizations.
    Note: Currently, trainers only belong to one organization, but this is for future expansion.
    """
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer_id')
        
        # For now, since we have OneToOne relationship, just verify it's the same trainer
        if str(request.trainer.id) == trainer_id:
            # Store in session for future multi-trainer support
            request.session['current_trainer_id'] = int(trainer_id)
            messages.success(request, _('Successfully switched account.'))
        else:
            messages.error(request, _('You do not have access to that account.'))
        
        # Redirect to dashboard
        return redirect('accounts:dashboard')
    
    # For now, show only the current organization
    organizations = [request.organization]
    
    context = {
        'organizations': organizations,
        'current_organization': request.organization,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'trainers/organization_switch_partial.html', context)
    
    return render(request, 'trainers/organization_switch.html', context)


@login_required
@requires_trainer
@organization_owner_required
def organization_dashboard_view(request):
    """
    Organization dashboard showing comprehensive metrics and analytics.
    Only accessible to organization owners.
    """
    organization = request.organization
    
    # Get all trainers in the organization
    trainers = organization.trainers.filter(is_active=True).select_related('user')
    
    # Get organization-wide statistics
    from apps.clients.models import Client
    from apps.assessments.models import Assessment
    from apps.sessions.models import SessionPackage, Session, Payment
    from django.db.models import Count, Sum, Q, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Client statistics
    total_clients = Client.objects.filter(
        trainer__organization=organization
    ).count()
    
    # For now, consider all clients as active
    # TODO: Add is_active field to Client model if needed
    active_clients = Client.objects.filter(
        trainer__organization=organization
    ).count()
    
    new_clients_this_month = Client.objects.filter(
        trainer__organization=organization,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Assessment statistics
    total_assessments = Assessment.objects.filter(
        client__trainer__organization=organization
    ).count()
    
    assessments_this_month = Assessment.objects.filter(
        client__trainer__organization=organization,
        created_at__gte=thirty_days_ago
    ).count()
    
    avg_assessment_score = Assessment.objects.filter(
        client__trainer__organization=organization
    ).aggregate(avg_score=Avg('overall_score'))['avg_score'] or 0
    
    # Session and revenue statistics
    total_revenue = Payment.objects.filter(
        package__trainer__organization=organization
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_this_month = Payment.objects.filter(
        package__trainer__organization=organization,
        payment_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    active_packages = SessionPackage.objects.filter(
        trainer__organization=organization,
        is_active=True
    ).count()
    
    sessions_this_month = Session.objects.filter(
        package__trainer__organization=organization,
        session_date__gte=thirty_days_ago
    ).count()
    
    # Trainer performance metrics
    trainer_stats = []
    for trainer in trainers:
        stats = {
            'trainer': trainer,
            'client_count': Client.objects.filter(trainer=trainer).count(),
            'assessment_count': Assessment.objects.filter(client__trainer=trainer).count(),
            'revenue_this_month': Payment.objects.filter(
                package__trainer=trainer,
                payment_date__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'sessions_this_month': Session.objects.filter(
                package__trainer=trainer,
                session_date__gte=thirty_days_ago
            ).count(),
        }
        trainer_stats.append(stats)
    
    # Sort trainers by revenue
    trainer_stats.sort(key=lambda x: x['revenue_this_month'], reverse=True)
    
    # Get recent activities
    from apps.trainers.models_audit import AuditLog
    recent_activities = AuditLog.objects.filter(
        organization=organization
    ).select_related('user', 'content_type').order_by('-created_at')[:20]
    
    context = {
        'organization': organization,
        'total_trainers': trainers.count(),
        'total_clients': total_clients,
        'active_clients': active_clients,
        'new_clients_this_month': new_clients_this_month,
        'total_assessments': total_assessments,
        'assessments_this_month': assessments_this_month,
        'avg_assessment_score': round(avg_assessment_score, 1),
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'active_packages': active_packages,
        'sessions_this_month': sessions_this_month,
        'trainer_stats': trainer_stats,
        'recent_activities': recent_activities,
        'thirty_days_ago': thirty_days_ago,
        'today': today,
    }
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/organization_dashboard_content.html'
    else:
        template = 'trainers/organization_dashboard.html'
    
    return render(request, template, context)


@login_required
@requires_trainer
def trainer_analytics_view(request, pk=None):
    """
    Show detailed analytics for a specific trainer.
    If no pk provided, show analytics for the current trainer.
    """
    # Determine which trainer to show analytics for
    if pk:
        trainer = get_object_or_404(Trainer, pk=pk)
        # Check permissions - only same org trainers can view
        if trainer.organization != request.organization:
            messages.error(request, _('You cannot view analytics for trainers from other organizations.'))
            return redirect('trainers:list')
    else:
        trainer = request.trainer
    
    # Import required models
    from apps.clients.models import Client
    from apps.assessments.models import Assessment
    from apps.sessions.models import SessionPackage, Session, Payment
    from django.db.models import Count, Sum, Q, Avg
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    # Time ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    one_year_ago = today - timedelta(days=365)
    
    # Client metrics
    total_clients = Client.objects.filter(trainer=trainer).count()
    active_clients = Client.objects.filter(trainer=trainer, is_active=True).count()
    new_clients_30d = Client.objects.filter(
        trainer=trainer,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Assessment metrics
    total_assessments = Assessment.objects.filter(client__trainer=trainer).count()
    assessments_30d = Assessment.objects.filter(
        client__trainer=trainer,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Average scores by category
    avg_scores = Assessment.objects.filter(
        client__trainer=trainer
    ).aggregate(
        avg_overall=Avg('overall_score'),
        avg_strength=Avg('strength_score'),
        avg_mobility=Avg('mobility_score'),
        avg_balance=Avg('balance_score'),
        avg_cardio=Avg('cardio_score')
    )
    
    # Session metrics
    total_sessions = Session.objects.filter(
        session_package__trainer=trainer
    ).count()
    sessions_30d = Session.objects.filter(
        session_package__trainer=trainer,
        session_date__gte=thirty_days_ago
    ).count()
    
    # Revenue metrics
    total_revenue = Payment.objects.filter(
        session_package__trainer=trainer
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_30d = Payment.objects.filter(
        session_package__trainer=trainer,
        payment_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_90d = Payment.objects.filter(
        session_package__trainer=trainer,
        payment_date__gte=ninety_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Monthly revenue trend (last 12 months)
    monthly_revenue = []
    for i in range(12):
        start_date = today.replace(day=1) - timedelta(days=i*30)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_revenue = Payment.objects.filter(
            session_package__trainer=trainer,
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_revenue.append({
            'month': start_date.strftime('%Y-%m'),
            'revenue': month_revenue
        })
    
    monthly_revenue.reverse()
    
    # Client retention rate
    clients_90d_ago = Client.objects.filter(
        trainer=trainer,
        created_at__lte=ninety_days_ago
    ).values_list('id', flat=True)
    
    if clients_90d_ago:
        retained_clients = Session.objects.filter(
            session_package__trainer=trainer,
            session_package__client__in=clients_90d_ago,
            session_date__gte=thirty_days_ago
        ).values('session_package__client').distinct().count()
        
        retention_rate = (retained_clients / len(clients_90d_ago)) * 100
    else:
        retention_rate = 0
    
    # Top clients by revenue
    top_clients = Payment.objects.filter(
        session_package__trainer=trainer,
        payment_date__gte=ninety_days_ago
    ).values(
        'session_package__client__id',
        'session_package__client__name'
    ).annotate(
        total_revenue=Sum('amount')
    ).order_by('-total_revenue')[:5]
    
    # Recent activity
    from apps.trainers.models_audit import AuditLog
    recent_activities = AuditLog.objects.filter(
        user=trainer.user
    ).select_related('content_type').order_by('-created_at')[:10]
    
    context = {
        'trainer': trainer,
        'is_own_profile': trainer == request.trainer,
        'can_view_revenue': trainer == request.trainer or request.trainer.role in ['owner', 'senior'],
        
        # Client metrics
        'total_clients': total_clients,
        'active_clients': active_clients,
        'new_clients_30d': new_clients_30d,
        
        # Assessment metrics
        'total_assessments': total_assessments,
        'assessments_30d': assessments_30d,
        'avg_scores': avg_scores,
        
        # Session metrics
        'total_sessions': total_sessions,
        'sessions_30d': sessions_30d,
        
        # Revenue metrics
        'total_revenue': total_revenue,
        'revenue_30d': revenue_30d,
        'revenue_90d': revenue_90d,
        'monthly_revenue_json': json.dumps(monthly_revenue),
        
        # Other metrics
        'retention_rate': round(retention_rate, 1),
        'top_clients': top_clients,
        'recent_activities': recent_activities,
    }
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/trainer_analytics_content.html'
    else:
        template = 'trainers/trainer_analytics.html'
    
    return render(request, template, context)


@login_required
def notification_list_view(request):
    """
    List all notifications for the current user.
    """
    from .models_notification import Notification
    
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    # Mark viewed notifications as read
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        messages.success(request, _('All notifications marked as read.'))
        return redirect('trainers:notifications')
    
    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
    }
    
    # Check for HTMX request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        template = 'trainers/notification_list_content.html'
    else:
        template = 'trainers/notification_list.html'
    
    return render(request, template, context)


@login_required
@require_http_methods(["POST"])
def notification_mark_read_view(request, pk):
    """
    Mark a single notification as read.
    """
    from .models_notification import Notification
    
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('HX-Request'):
        # Return updated notification HTML
        return render(request, 'trainers/notification_item.html', {
            'notification': notification
        })
    
    return redirect('trainers:notifications')


@login_required
def notification_badge_view(request):
    """
    Return notification badge count for navbar.
    """
    from .models_notification import Notification
    
    unread_count = Notification.get_unread_count(request.user)
    
    return render(request, 'trainers/notification_badge.html', {
        'unread_count': unread_count
    })
