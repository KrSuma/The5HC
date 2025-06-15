from django.utils import translation

class ForceKoreanMiddleware:
    """Middleware to force Korean language for all requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Force Korean language
        translation.activate('ko')
        request.LANGUAGE_CODE = 'ko'
        
        response = self.get_response(request)
        
        # Ensure the language persists
        response.set_cookie('django_language', 'ko')
        
        return response