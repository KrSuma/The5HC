"""
Tests for API documentation and error handling
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory


@pytest.mark.django_db
class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
    
    def test_schema_endpoint_accessible(self):
        """Test that schema endpoint is accessible"""
        response = self.client.get('/api/v1/schema/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response['content-type'] == 'application/vnd.oai.openapi+json; charset=utf-8'
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible"""
        response = self.client.get('/api/v1/docs/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'text/html' in response['content-type']
        assert 'swagger' in response.content.decode().lower()
    
    def test_redoc_accessible(self):
        """Test that ReDoc is accessible"""
        response = self.client.get('/api/v1/redoc/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'text/html' in response['content-type']
        assert 'redoc' in response.content.decode().lower()


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Test API error handling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_404_error_response(self):
        """Test 404 error response format"""
        response = self.client.get('/api/v1/clients/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
    
    def test_400_error_response(self):
        """Test 400 error response format"""
        # Try to create client with invalid data
        response = self.client.post('/api/v1/clients/', {
            'name': '',  # Required field
            'email': 'invalid-email'  # Invalid format
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert isinstance(response.data, dict)
        assert 'name' in response.data
        assert 'email' in response.data
    
    def test_401_error_response(self):
        """Test 401 error response format"""
        # Remove authentication
        self.client.credentials()
        
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
    
    def test_405_method_not_allowed(self):
        """Test 405 method not allowed response"""
        # Try an unsupported method
        response = self.client.put('/api/v1/auth/login/', {})
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert 'detail' in response.data
    
    def test_pagination_response_format(self):
        """Test pagination response format"""
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request"""
        # Send invalid JSON
        response = self.client.post(
            '/api/v1/clients/',
            data='{"invalid": json,}',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_content_type_validation(self):
        """Test content type validation"""
        # Send data without proper content type
        response = self.client.post(
            '/api/v1/auth/login/',
            data='email_or_username=test&password=test',
            content_type='text/plain'
        )
        
        # API should still handle it gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        ]