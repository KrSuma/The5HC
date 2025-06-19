from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def debug_trainer_view(request):
    """Debug view to check trainer setup"""
    data = {
        'user': str(request.user),
        'user_id': request.user.id,
        'is_authenticated': request.user.is_authenticated,
        'has_trainer_attr': hasattr(request, 'trainer'),
        'trainer': str(request.trainer) if hasattr(request, 'trainer') else None,
        'has_organization_attr': hasattr(request, 'organization'),
        'organization': str(request.organization) if hasattr(request, 'organization') else None,
    }
    
    try:
        trainer = request.user.trainer_profile
        data['trainer_profile_exists'] = True
        data['trainer_id'] = trainer.id
        data['trainer_organization'] = str(trainer.organization)
        data['trainer_role'] = trainer.role
    except:
        data['trainer_profile_exists'] = False
        
    return JsonResponse(data)