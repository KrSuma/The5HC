"""
Tests for User API endpoints
"""
import pytest
from datetime import datetime
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory, PaymentFactory


@pytest.mark.django_db
class TestUserAPI:
    """Test User API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory(
            username='testtrainer',
            email='trainer@example.com',
            first_name='Test',
            last_name='Trainer'
        )
        self.user.set_password('oldpassword123')
        self.user.save()
        
        self.other_user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_list_users_only_shows_current_user(self):
        """Test that user list only shows the authenticated user"""
        response = self.client.get('/api/v1/users/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == self.user.id
        assert response.data['results'][0]['username'] == 'testtrainer'
    
    def test_retrieve_own_user_profile(self):
        """Test retrieving own user profile"""
        response = self.client.get(f'/api/v1/users/{self.user.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.user.id
        assert response.data['username'] == 'testtrainer'
        assert response.data['email'] == 'trainer@example.com'
        assert response.data['first_name'] == 'Test'
        assert response.data['last_name'] == 'Trainer'
    
    def test_cannot_retrieve_other_user_profile(self):
        """Test that users cannot retrieve other users' profiles"""
        response = self.client.get(f'/api/v1/users/{self.other_user.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_me_endpoint(self):
        """Test the /me endpoint returns current user"""
        response = self.client.get('/api/v1/users/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.user.id
        assert response.data['username'] == 'testtrainer'
        assert response.data['email'] == 'trainer@example.com'
    
    def test_change_password_success(self):
        """Test successful password change"""
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword456'
        }
        
        response = self.client.post('/api/v1/users/change_password/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert '성공적으로 변경되었습니다' in response.data['message']
        
        # Verify new password works
        self.user.refresh_from_db()
        assert self.user.check_password('newpassword456')
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password"""
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword456'
        }
        
        response = self.client.post('/api/v1/users/change_password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert '현재 비밀번호가 올바르지 않습니다' in response.data['error']
    
    def test_change_password_missing_fields(self):
        """Test password change with missing fields"""
        # Missing new password
        data = {
            'old_password': 'oldpassword123'
        }
        
        response = self.client.post('/api/v1/users/change_password/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard statistics endpoint"""
        # Create test data
        client1 = ClientFactory(trainer=self.user)
        client2 = ClientFactory(trainer=self.user)
        client3 = ClientFactory(trainer=self.other_user)  # Other trainer's client
        
        # Create assessments
        AssessmentFactory(client=client1)
        AssessmentFactory(client=client2)
        AssessmentFactory(client=client3)  # Should not be counted
        
        # Create active and inactive packages
        active_package = SessionPackageFactory(
            client=client1,
            trainer=self.user,
            is_active=True
        )
        inactive_package = SessionPackageFactory(
            client=client2,
            trainer=self.user,
            is_active=False
        )
        
        # Create sessions for this month
        SessionFactory(
            package=active_package,
            session_date=datetime.now().date()
        )
        SessionFactory(
            package=active_package,
            session_date=datetime.now().date()
        )
        
        # Create payments for this month
        PaymentFactory(
            client=client1,
            trainer=self.user,
            amount=100000,
            payment_date=datetime.now().date()
        )
        PaymentFactory(
            client=client2,
            trainer=self.user,
            amount=200000,
            payment_date=datetime.now().date()
        )
        
        response = self.client.get('/api/v1/users/dashboard_stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_clients'] == 2  # Only user's clients
        assert response.data['active_clients'] == 1  # Only client1 has active package
        assert response.data['total_assessments'] == 2  # Only user's assessments
        assert response.data['active_packages'] == 1
        assert response.data['sessions_this_month'] == 2
        assert response.data['revenue_this_month'] == 300000
    
    def test_dashboard_stats_no_data(self):
        """Test dashboard stats with no data"""
        response = self.client.get('/api/v1/users/dashboard_stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_clients'] == 0
        assert response.data['active_clients'] == 0
        assert response.data['total_assessments'] == 0
        assert response.data['active_packages'] == 0
        assert response.data['sessions_this_month'] == 0
        assert response.data['revenue_this_month'] == 0
    
    def test_users_endpoints_require_authentication(self):
        """Test that all user endpoints require authentication"""
        # Remove authentication
        self.client.credentials()
        
        # Test endpoints
        endpoints = [
            '/api/v1/users/',
            f'/api/v1/users/{self.user.id}/',
            '/api/v1/users/me/',
            '/api/v1/users/change_password/',
            '/api/v1/users/dashboard_stats/'
        ]
        
        for endpoint in endpoints:
            if 'change_password' in endpoint:
                response = self.client.post(endpoint, {})
            else:
                response = self.client.get(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cannot_update_user_profile_via_api(self):
        """Test that user profiles cannot be updated via API (read-only)"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        # Try PUT
        response = self.client.put(f'/api/v1/users/{self.user.id}/', data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Try PATCH
        response = self.client.patch(f'/api/v1/users/{self.user.id}/', data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Try DELETE
        response = self.client.delete(f'/api/v1/users/{self.user.id}/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED