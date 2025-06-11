from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class AuthenticationMiddleware:
    """Custom authentication middleware to handle login redirects."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that don't require authentication
        self.exempt_urls = [
            reverse('accounts:login'),
            reverse('accounts:password_reset'),
            '/admin/',
            '/static/',
            '/media/',
            '/api/',  # API endpoints handle their own authentication
        ]
    
    def __call__(self, request):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Check if current path requires authentication
            path = request.path_info
            
            # Allow access to exempt URLs
            for exempt_url in self.exempt_urls:
                if path.startswith(exempt_url):
                    return self.get_response(request)
            
            # For HTMX requests, return a redirect header
            if request.headers.get('HX-Request'):
                from django.http import HttpResponse
                response = HttpResponse()
                response['HX-Redirect'] = reverse('accounts:login')
                return response
            
            # For normal requests, redirect to login
            return redirect('accounts:login')
        
        response = self.get_response(request)
        return response