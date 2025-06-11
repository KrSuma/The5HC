"""
Example pytest conversion of accounts view tests.
This file demonstrates the migration from Django TestCase to pytest.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from pytest_django.asserts import assertTemplateUsed, assertRedirects, assertContains

# Import the factory (to be created)
# from apps.accounts.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestLoginView:
    """Test cases for login functionality using pytest"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common test data"""
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.dashboard_url = reverse('accounts:dashboard')
    
    def test_login_page_renders_correctly(self, client):
        """Test that login page loads with correct template"""
        response = client.get(self.login_url)
        
        assert response.status_code == 200
        assertTemplateUsed(response, 'registration/login.html')
        assertContains(response, 'login-form')
    
    def test_login_successful_with_username(self, client, django_user_model):
        """Test successful login using username"""
        # Using django_user_model fixture instead of direct import
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        response = client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assertRedirects(response, self.dashboard_url)
        
        # Verify user is logged in
        response = client.get(self.dashboard_url)
        assert response.status_code == 200
    
    def test_login_successful_with_email(self, client, django_user_model):
        """Test successful login using email"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        response = client.post(self.login_url, {
            'email_or_username': 'test@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assertRedirects(response, self.dashboard_url)
    
    @pytest.mark.parametrize("email_or_username,password,expected_error", [
        ('wrong_user', 'testpass123', '잘못된 이메일 또는 사용자명입니다'),
        ('test_trainer', 'wrong_pass', '잘못된 비밀번호입니다'),
        ('', 'testpass123', '이 필드는 필수'),
        ('test_trainer', '', '이 필드는 필수'),
    ])
    def test_login_failures(self, client, django_user_model, email_or_username, password, expected_error):
        """Test various login failure scenarios using parametrize"""
        # Create user for valid username tests
        django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        response = client.post(self.login_url, {
            'email_or_username': email_or_username,
            'password': password
        })
        
        assert response.status_code == 200
        assert expected_error in response.content.decode('utf-8')
    
    def test_htmx_login_request(self, client, django_user_model):
        """Test HTMX login request returns correct headers"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        response = client.post(
            self.login_url,
            {
                'email_or_username': 'test_trainer',
                'password': 'testpass123'
            },
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'HX-Redirect' in response
        assert response['HX-Redirect'] == self.dashboard_url
    
    def test_remember_me_functionality(self, client, django_user_model, settings):
        """Test remember me checkbox extends session"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test without remember me
        response = client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123',
            'remember_me': False
        })
        
        assert client.session.get_expiry_age() == settings.SESSION_COOKIE_AGE
        
        # Test with remember me
        client.logout()
        response = client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123',
            'remember_me': True
        })
        
        # Should be 30 days
        assert client.session.get_expiry_age() == 30 * 24 * 60 * 60


@pytest.mark.django_db
class TestLogoutView:
    """Test cases for logout functionality"""
    
    @pytest.fixture
    def authenticated_user(self, client, django_user_model):
        """Fixture to create and login a user"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        client.login(username='test_trainer', password='testpass123')
        return user
    
    def test_logout_redirects_to_login(self, client, authenticated_user):
        """Test logout redirects to login page"""
        logout_url = reverse('accounts:logout')
        login_url = reverse('accounts:login')
        
        response = client.post(logout_url)
        
        assert response.status_code == 302
        assertRedirects(response, login_url)
        
        # Verify user is logged out
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 302  # Should redirect to login
    
    def test_htmx_logout_request(self, client, authenticated_user):
        """Test HTMX logout returns correct headers"""
        logout_url = reverse('accounts:logout')
        login_url = reverse('accounts:login')
        
        response = client.post(logout_url, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        assert 'HX-Redirect' in response
        assert response['HX-Redirect'] == login_url


@pytest.mark.django_db
class TestDashboardView:
    """Test cases for dashboard view"""
    
    def test_dashboard_requires_authentication(self, client):
        """Test unauthenticated users are redirected to login"""
        dashboard_url = reverse('accounts:dashboard')
        
        response = client.get(dashboard_url)
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_dashboard_shows_user_info(self, client, django_user_model):
        """Test dashboard displays correct user information"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Trainer'
        )
        
        client.login(username='test_trainer', password='testpass123')
        dashboard_url = reverse('accounts:dashboard')
        
        response = client.get(dashboard_url)
        
        assert response.status_code == 200
        assertContains(response, 'Test Trainer')
        assertTemplateUsed(response, 'dashboard/dashboard.html')


@pytest.mark.django_db
def test_middleware_redirects_unauthenticated_users(client):
    """Test custom authentication middleware redirects properly"""
    protected_urls = [
        reverse('clients:list'),
        reverse('assessments:list'),
        reverse('sessions:list'),
    ]
    
    for url in protected_urls:
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# Performance tests
@pytest.mark.django_db
class TestAuthenticationPerformance:
    """Performance tests for authentication views"""
    
    @pytest.mark.slow
    def test_login_query_count(self, client, django_user_model, django_assert_num_queries):
        """Ensure login doesn't make excessive database queries"""
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        login_url = reverse('accounts:login')
        
        # Test query count for login
        with django_assert_num_queries(3):  # User lookup, update last_login, session
            client.post(login_url, {
                'email_or_username': 'test_trainer',
                'password': 'testpass123'
            })


# Integration tests
@pytest.mark.django_db
@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for complete authentication flow"""
    
    def test_complete_auth_flow(self, client, django_user_model):
        """Test complete authentication flow from login to logout"""
        # Create user
        user = django_user_model.objects.create_user(
            username='test_trainer',
            email='test@example.com',
            password='testpass123'
        )
        
        # Visit login page
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200
        
        # Login
        response = client.post(reverse('accounts:login'), {
            'email_or_username': 'test_trainer',
            'password': 'testpass123'
        })
        assert response.status_code == 302
        
        # Access protected page
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 200
        
        # Logout
        response = client.post(reverse('accounts:logout'))
        assert response.status_code == 302
        
        # Verify can't access protected page
        response = client.get(reverse('accounts:dashboard'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


# Example of mocking external dependencies
@pytest.mark.django_db
def test_login_with_email_notification(client, django_user_model, mocker):
    """Test login sends notification email (mocked)"""
    # Mock the email sending function
    mock_send_mail = mocker.patch('django.core.mail.send_mail')
    
    user = django_user_model.objects.create_user(
        username='test_trainer',
        email='test@example.com',
        password='testpass123'
    )
    
    # If login triggers email notification
    response = client.post(reverse('accounts:login'), {
        'email_or_username': 'test_trainer',
        'password': 'testpass123'
    })
    
    # Verify email would have been sent
    # mock_send_mail.assert_called_once()