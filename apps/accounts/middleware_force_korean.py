from django.utils import translation
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ForceKoreanMiddleware:
    """Middleware to force Korean language for all requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info(f"ForceKoreanMiddleware initialized. LANGUAGE_CODE from settings: {settings.LANGUAGE_CODE}")
    
    def __call__(self, request):
        # Force Korean language
        translation.activate('ko')
        request.LANGUAGE_CODE = 'ko'
        
        # Log the activation
        logger.debug(f"Forced Korean language. Current language: {translation.get_language()}")
        
        response = self.get_response(request)
        
        # Ensure the language persists
        response.set_cookie('django_language', 'ko', max_age=365*24*60*60)  # 1 year
        
        return response