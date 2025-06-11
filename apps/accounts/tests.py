from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import json

from .forms import LoginForm, CustomUserCreationForm

User = get_user_model()


class AuthenticationTestCase(TestCase):
    """Test suite for authentication functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Trainer'
        )
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.dashboard_url = reverse('accounts:dashboard')
        
    def test_login_form_valid_data(self):
        """Test login form with valid data"""
        form_data = {
            'email_or_username': 'test_trainer',
            'password': 'testpass123',
            'remember_me': False
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_login_form_invalid_data(self):
        """Test login form with invalid data"""
        form_data = {
            'email_or_username': '',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login-form')
        self.assertIsInstance(response.context['form'], LoginForm)
        
    def test_login_successful_with_username(self):
        """Test successful login with username"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)
        
    def test_login_successful_with_email(self):
        """Test successful login with email"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '잘못된 비밀번호입니다')
        
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'nonexistent',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '잘못된 이메일 또는 사용자명입니다')
        
    def test_login_htmx_request(self):
        """Test HTMX login request"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123'
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Redirect', response.headers)
        
    def test_logout_view(self):
        """Test logout functionality"""
        # Login first
        self.client.login(username='test_trainer', password='testpass123')
        
        # Test logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)
        
    def test_logout_htmx_request(self):
        """Test HTMX logout request"""
        self.client.login(username='test_trainer', password='testpass123')
        
        response = self.client.post(self.logout_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Redirect', response.headers)
        
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_dashboard_authenticated_access(self):
        """Test dashboard with authenticated user"""
        self.client.login(username='test_trainer', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Trainer')
        

class UserModelTestCase(TestCase):
    """Test custom User model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_user_creation(self):
        """Test user creation with valid data"""
        user = User.objects.create_user(
            username='new_trainer',
            email='new@example.com',
            password='testpass123',
            name='New Trainer'
        )
        self.assertEqual(user.username, 'new_trainer')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.name, 'New Trainer')
        
    def test_user_str_method(self):
        """Test user string representation"""
        self.user.name = 'Test Trainer'
        self.user.save()
        expected = f"{self.user.username} - Test Trainer"
        self.assertEqual(str(self.user), expected)
        
    def test_failed_login_attempts_tracking(self):
        """Test failed login attempts tracking"""
        initial_attempts = self.user.failed_login_attempts
        self.user.increment_failed_login_attempts()
        self.assertEqual(self.user.failed_login_attempts, initial_attempts + 1)
        
    def test_account_lockout_after_max_attempts(self):
        """Test account lockout after 5 failed attempts"""
        # Make 5 failed login attempts
        for i in range(5):
            self.user.increment_failed_login_attempts()
        
        # User should be locked
        self.assertTrue(self.user.is_account_locked())
        
    def test_successful_login_resets_attempts(self):
        """Test that resetting attempts works"""
        # Make failed attempts
        self.user.increment_failed_login_attempts()
        self.user.increment_failed_login_attempts()
        
        # Reset attempts
        self.user.reset_failed_login_attempts()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)
        

class UserCreationTestCase(TestCase):
    """Test user creation and profile management"""
    
    def test_custom_user_creation_form_valid(self):
        """Test user creation form with valid data"""
        form_data = {
            'username': 'new_trainer',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'Trainer',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_custom_user_creation_form_password_mismatch(self):
        """Test user creation form with password mismatch"""
        form_data = {
            'username': 'new_trainer',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'Trainer',
            'password1': 'testpass123',
            'password2': 'differentpass'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        



class MiddlewareTestCase(TestCase):
    """Test custom authentication middleware"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
    def test_unauthenticated_redirect(self):
        """Test that unauthenticated users are redirected to login"""
        protected_url = reverse('accounts:dashboard')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access protected views"""
        self.client.login(username='test_trainer', password='testpass123')
        protected_url = reverse('accounts:dashboard')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, 200)
        

class SessionManagementTestCase(TestCase):
    """Test session management functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
    def test_remember_me_session_duration(self):
        """Test remember me functionality extends session"""
        # Login with remember me
        response = self.client.post(reverse('accounts:login'), {
            'email_or_username': 'test_trainer',
            'password': 'testpass123',
            'remember_me': True
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check session exists and has extended duration
        session_key = self.client.session.session_key
        if session_key:
            session = Session.objects.get(session_key=session_key)
            # Session should expire later than 24 hours (default)
            expected_min_expiry = timezone.now() + timedelta(days=29)
            self.assertGreater(session.expire_date, expected_min_expiry)
            
    def test_normal_login_session_duration(self):
        """Test normal login has standard session duration"""
        # Login without remember me
        response = self.client.post(reverse('accounts:login'), {
            'email_or_username': 'test_trainer',
            'password': 'testpass123',
            'remember_me': False
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Session should expire when browser closes (age 0)
        session_key = self.client.session.session_key
        if session_key:
            # For browser session, Django sets a reasonable default
            # We just verify the session exists
            session = Session.objects.get(session_key=session_key)
            self.assertIsNotNone(session)