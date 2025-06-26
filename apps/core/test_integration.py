"""
Integration tests for core mixins in a real Django environment.
"""
from django.test import TestCase, Client
from django.urls import path, include
from django.views.generic import TemplateView, CreateView
from django import forms
from django.http import HttpResponse

from apps.core.mixins import (
    DualTemplateMixin, 
    HTMXResponseMixin,
    FormSuccessMessageMixin
)


# Test form
class TestForm(forms.Form):
    name = forms.CharField()


# Test views
class TestDualTemplateView(DualTemplateMixin, TemplateView):
    template_name = 'test/test.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # Simulate rendering with template name
        template_names = self.get_template_names()
        return HttpResponse(f"Template: {template_names[0]}, HTMX: {context['is_htmx_request']}")


class TestFormView(DualTemplateMixin, FormSuccessMessageMixin, CreateView):
    template_name = 'test/form.html'
    form_class = TestForm
    success_message = "Successfully saved %(name)s!"
    
    def form_valid(self, form):
        # Don't actually save, just return success response
        self.object = None
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/success/'


# Test URLs
urlpatterns = [
    path('test/', TestDualTemplateView.as_view(), name='test'),
    path('form/', TestFormView.as_view(), name='form'),
]


class MixinIntegrationTest(TestCase):
    """Test mixins in a real Django view context."""
    
    def setUp(self):
        self.client = Client()
        # Temporarily add test URLs
        import apps.core.test_integration
        self.urls = 'apps.core.test_integration'
    
    def test_dual_template_regular_request(self):
        """Test regular request uses full template."""
        with self.settings(ROOT_URLCONF=self.urls):
            response = self.client.get('/test/')
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            self.assertIn('Template: test/test.html', content)
            self.assertIn('HTMX: False', content)
    
    def test_dual_template_htmx_request(self):
        """Test HTMX request uses content template."""
        with self.settings(ROOT_URLCONF=self.urls):
            response = self.client.get('/test/', HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            self.assertIn('Template: test/test_content.html', content)
            self.assertIn('HTMX: True', content)
    
    def test_form_success_message_htmx(self):
        """Test form success message with HTMX."""
        with self.settings(ROOT_URLCONF=self.urls):
            response = self.client.post(
                '/form/',
                {'name': 'TestUser'},
                HTTP_HX_REQUEST='true'
            )
            # Check for redirect with HTMX trigger
            self.assertTrue(
                'HX-Trigger-After-Settle' in response or
                'HX-Redirect' in response
            )
    
    def test_htmx_response_mixin(self):
        """Test HTMXResponseMixin methods work correctly."""
        mixin = HTMXResponseMixin()
        
        # Test redirect
        mixin.request = self.client.get('/').wsgi_request
        response = mixin.htmx_redirect('/new/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/new/')
        
        # Test HTMX redirect
        mixin.request = self.client.get('/', HTTP_HX_REQUEST='true').wsgi_request
        response = mixin.htmx_redirect('/new/')
        self.assertEqual(response['HX-Redirect'], '/new/')
        
        # Test refresh
        response = mixin.htmx_refresh()
        self.assertEqual(response['HX-Refresh'], 'true')
        
        # Test trigger
        response = mixin.htmx_trigger('test-event')
        self.assertEqual(response['HX-Trigger'], 'test-event')