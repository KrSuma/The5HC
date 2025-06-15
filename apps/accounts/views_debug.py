from django.http import JsonResponse
from django.conf import settings
from django.utils import translation

def debug_language(request):
    """Debug view to check language settings"""
    return JsonResponse({
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
        'USE_I18N': settings.USE_I18N,
        'USE_L10N': settings.USE_L10N,
        'LANGUAGES': settings.LANGUAGES,
        'LOCALE_PATHS': [str(p) for p in settings.LOCALE_PATHS],
        'current_language': translation.get_language(),
        'middleware': settings.MIDDLEWARE,
        'is_production': not settings.DEBUG,
    })