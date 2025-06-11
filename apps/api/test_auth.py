"""
Tests for API authentication endpoints
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.login_url = '/api/v1/auth/login/'
        self.refresh_url = '/api/v1/auth/refresh/'
    
    def test_login_with_username_success(self):
        """Test successful login with username"""
        # Create test user
        user = UserFactory(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        user.save()
        
        # Attempt login
        response = self.client.post(self.login_url, {
            'email_or_username': 'testuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'testuser'
    
    def test_login_with_email_success(self):
        """Test successful login with email"""
        # Create test user
        user = UserFactory(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        user.save()
        
        # Attempt login with email
        response = self.client.post(self.login_url, {
            'email_or_username': 'test@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['email'] == 'test@example.com'
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create test user
        user = UserFactory(username='testuser')
        user.set_password('testpass123')
        user.save()
        
        # Attempt login with wrong password
        response = self.client.post(self.login_url, {
            'email_or_username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
    
    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post(self.login_url, {
            'email_or_username': 'nonexistent',
            'password': 'password'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        # Missing password
        response = self.client.post(self.login_url, {
            'email_or_username': 'testuser'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Missing username/email
        response = self.client.post(self.login_url, {
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_token_refresh_success(self):
        """Test successful token refresh"""
        # Create user and get refresh token
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        
        # Refresh token
        response = self.client.post(self.refresh_url, {
            'refresh': str(refresh)
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_token_refresh_with_invalid_token(self):
        """Test token refresh with invalid token"""
        response = self.client.post(self.refresh_url, {
            'refresh': 'invalid-token'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        # Create user and get token
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Access protected endpoint
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_access_protected_endpoint_with_expired_token(self):
        """Test accessing protected endpoint with expired token"""
        # This would require mocking time or using a very short token lifetime
        # For now, test with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED