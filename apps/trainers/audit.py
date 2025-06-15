from typing import Optional, Dict, Any
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpRequest

from .models_audit import AuditLog


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(
    action: str,
    user=None,
    organization=None,
    content_object=None,
    request: Optional[HttpRequest] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Log an action to the audit log.
    
    Args:
        action: The action code (from AuditLog.ACTION_CHOICES)
        user: The user who performed the action
        organization: The organization context
        content_object: The object the action was performed on
        request: The HTTP request (for IP and user agent)
        extra_data: Any additional data to store
    """
    log_data = {
        'action': action,
        'user': user,
        'organization': organization,
        'extra_data': extra_data or {}
    }
    
    # Add object reference if provided
    if content_object:
        log_data['content_type'] = ContentType.objects.get_for_model(content_object)
        log_data['object_id'] = content_object.pk
    
    # Extract request information if available
    if request:
        log_data['ip_address'] = get_client_ip(request)
        log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # Auto-populate user and organization from request if not provided
        if not user and hasattr(request, 'user') and request.user.is_authenticated:
            log_data['user'] = request.user
        
        if not organization and hasattr(request, 'organization'):
            log_data['organization'] = request.organization
    
    # Create the audit log entry
    with transaction.atomic():
        AuditLog.objects.create(**log_data)


# Convenience functions for common actions
def log_client_action(action: str, client, request: HttpRequest, **kwargs):
    """Log a client-related action."""
    log_action(
        action=action,
        content_object=client,
        request=request,
        extra_data={
            'client_name': client.name,
            'client_id': client.id,
            **kwargs
        }
    )


def log_assessment_action(action: str, assessment, request: HttpRequest, **kwargs):
    """Log an assessment-related action."""
    log_action(
        action=action,
        content_object=assessment,
        request=request,
        extra_data={
            'client_name': assessment.client.name,
            'assessment_id': assessment.id,
            'overall_score': assessment.overall_score,
            **kwargs
        }
    )


def log_session_action(action: str, session, request: HttpRequest, **kwargs):
    """Log a session-related action."""
    log_action(
        action=action,
        content_object=session,
        request=request,
        extra_data={
            'client_name': session.client.name,
            'session_date': str(session.session_date),
            'session_cost': float(session.session_cost) if session.session_cost else None,
            **kwargs
        }
    )


def log_trainer_action(action: str, trainer, request: HttpRequest, **kwargs):
    """Log a trainer-related action."""
    log_action(
        action=action,
        content_object=trainer,
        request=request,
        extra_data={
            'trainer_name': trainer.user.get_full_name() or trainer.user.username,
            'trainer_role': trainer.role,
            **kwargs
        }
    )


def log_auth_action(action: str, request: HttpRequest, **kwargs):
    """Log an authentication-related action."""
    log_action(
        action=action,
        request=request,
        extra_data=kwargs
    )