from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def requires_trainer(view_func):
    """
    Decorator to ensure user has a trainer profile.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'trainer') or not request.trainer:
            messages.error(request, "트레이너 프로필이 필요합니다.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    
    # Mark the view as requiring trainer
    wrapped_view.requires_trainer = True
    return wrapped_view


def trainer_role_required(*allowed_roles):
    """
    Decorator to check if trainer has one of the allowed roles.
    
    Usage:
        @trainer_role_required('owner', 'senior')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @requires_trainer
        def wrapped_view(request, *args, **kwargs):
            if not request.trainer:
                raise PermissionDenied("트레이너 프로필이 필요합니다.")
                
            if request.trainer.role not in allowed_roles:
                raise PermissionDenied(f"권한이 없습니다. 필요한 권한: {', '.join(allowed_roles)}")
                
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def organization_owner_required(view_func):
    """
    Decorator to ensure user is the organization owner.
    """
    @wraps(view_func)
    @requires_trainer
    def wrapped_view(request, *args, **kwargs):
        if not request.trainer or request.trainer.role != 'owner':
            raise PermissionDenied("조직 소유자만 접근할 수 있습니다.")
        return view_func(request, *args, **kwargs)
    return wrapped_view


def can_manage_trainers(view_func):
    """
    Decorator to check if user can manage other trainers.
    Only owners and senior trainers can manage others.
    """
    return trainer_role_required('owner', 'senior')(view_func)


def organization_member_required(view_func):
    """
    Decorator to ensure user belongs to an organization.
    """
    @wraps(view_func)
    @requires_trainer
    def wrapped_view(request, *args, **kwargs):
        if not request.organization:
            messages.error(request, "조직에 소속되어 있지 않습니다.")
            return redirect('trainers:list')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def trainer_is_active_required(view_func):
    """
    Decorator to ensure trainer is active.
    """
    @wraps(view_func)
    @requires_trainer
    def wrapped_view(request, *args, **kwargs):
        if not request.trainer.is_active:
            messages.error(request, "비활성화된 트레이너입니다.")
            return redirect('accounts:logout')
        return view_func(request, *args, **kwargs)
    return wrapped_view