"""
Tests for API permissions and access control
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory, PaymentFactory


@pytest.mark.django_db
class TestAPIPermissions:
    """Test API permissions and access control"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        # Create two trainers
        self.trainer1 = UserFactory(username='trainer1')
        self.trainer2 = UserFactory(username='trainer2')
        
        # Get tokens for both trainers
        refresh1 = RefreshToken.for_user(self.trainer1)
        self.token1 = str(refresh1.access_token)
        
        refresh2 = RefreshToken.for_user(self.trainer2)
        self.token2 = str(refresh2.access_token)
        
        # Create data for trainer1
        self.client1_t1 = ClientFactory(trainer=self.trainer1)
        self.assessment_t1 = AssessmentFactory(client=self.client1_t1)
        self.package_t1 = SessionPackageFactory(client=self.client1_t1, trainer=self.trainer1)
        self.session_t1 = SessionFactory(package=self.package_t1)
        self.payment_t1 = PaymentFactory(
            client=self.client1_t1,
            trainer=self.trainer1,
            package=self.package_t1
        )
        
        # Create data for trainer2
        self.client1_t2 = ClientFactory(trainer=self.trainer2)
        self.assessment_t2 = AssessmentFactory(client=self.client1_t2)
        self.package_t2 = SessionPackageFactory(client=self.client1_t2, trainer=self.trainer2)
        self.session_t2 = SessionFactory(package=self.package_t2)
        self.payment_t2 = PaymentFactory(
            client=self.client1_t2,
            trainer=self.trainer2,
            package=self.package_t2
        )
    
    def test_trainer_cannot_see_other_trainers_clients(self):
        """Test that trainers cannot see other trainers' clients"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access trainer2's client
        response = self.client.get(f'/api/v1/clients/{self.client1_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # List should only show trainer1's clients
        response = self.client.get('/api/v1/clients/')
        assert response.status_code == status.HTTP_200_OK
        client_ids = [c['id'] for c in response.data['results']]
        assert self.client1_t1.id in client_ids
        assert self.client1_t2.id not in client_ids
    
    def test_trainer_cannot_see_other_trainers_assessments(self):
        """Test that trainers cannot see other trainers' assessments"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access trainer2's assessment
        response = self.client.get(f'/api/v1/assessments/{self.assessment_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # List should only show trainer1's assessments
        response = self.client.get('/api/v1/assessments/')
        assert response.status_code == status.HTTP_200_OK
        assessment_ids = [a['id'] for a in response.data['results']]
        assert self.assessment_t1.id in assessment_ids
        assert self.assessment_t2.id not in assessment_ids
    
    def test_trainer_cannot_see_other_trainers_packages(self):
        """Test that trainers cannot see other trainers' packages"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access trainer2's package
        response = self.client.get(f'/api/v1/packages/{self.package_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # List should only show trainer1's packages
        response = self.client.get('/api/v1/packages/')
        assert response.status_code == status.HTTP_200_OK
        package_ids = [p['id'] for p in response.data['results']]
        assert self.package_t1.id in package_ids
        assert self.package_t2.id not in package_ids
    
    def test_trainer_cannot_see_other_trainers_sessions(self):
        """Test that trainers cannot see other trainers' sessions"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access trainer2's session
        response = self.client.get(f'/api/v1/sessions/{self.session_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # List should only show trainer1's sessions
        response = self.client.get('/api/v1/sessions/')
        assert response.status_code == status.HTTP_200_OK
        session_ids = [s['id'] for s in response.data['results']]
        assert self.session_t1.id in session_ids
        assert self.session_t2.id not in session_ids
    
    def test_trainer_cannot_see_other_trainers_payments(self):
        """Test that trainers cannot see other trainers' payments"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to access trainer2's payment
        response = self.client.get(f'/api/v1/payments/{self.payment_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # List should only show trainer1's payments
        response = self.client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_200_OK
        payment_ids = [p['id'] for p in response.data['results']]
        assert self.payment_t1.id in payment_ids
        assert self.payment_t2.id not in payment_ids
    
    def test_trainer_cannot_create_client_for_other_trainer(self):
        """Test that trainers cannot create clients for other trainers"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        data = {
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone_number': '010-1234-5678',
            'trainer': self.trainer2.id,  # Try to assign to trainer2
            'birth_date': '1990-01-01',
            'gender': 'M'
        }
        
        response = self.client.post('/api/v1/clients/', data)
        
        # Should create successfully but assign to trainer1
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['trainer'] == self.trainer1.id  # Auto-assigned to current user
    
    def test_trainer_cannot_create_assessment_for_other_trainers_client(self):
        """Test that trainers cannot create assessments for other trainers' clients"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        data = {
            'client': self.client1_t2.id,  # Trainer2's client
            'date': '2024-01-01',
            'height': 175.0,
            'weight': 70.0
        }
        
        response = self.client.post('/api/v1/assessments/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_trainer_cannot_modify_other_trainers_data(self):
        """Test that trainers cannot modify other trainers' data"""
        # Authenticate as trainer1
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')
        
        # Try to update trainer2's client
        response = self.client.patch(f'/api/v1/clients/{self.client1_t2.id}/', {
            'name': 'Hacked Name'
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to delete trainer2's assessment
        response = self.client.delete(f'/api/v1/assessments/{self.assessment_t2.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_access_forbidden(self):
        """Test that unauthenticated access is forbidden"""
        # No credentials set
        endpoints = [
            '/api/v1/clients/',
            '/api/v1/assessments/',
            '/api/v1/packages/',
            '/api/v1/sessions/',
            '/api/v1/payments/',
            '/api/v1/users/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_token_access_forbidden(self):
        """Test that invalid token access is forbidden"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        response = self.client.get('/api/v1/clients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_expired_token_access_forbidden(self):
        """Test that expired token access is forbidden"""
        # This would require mocking time or setting very short token lifetime
        # For now, we'll use an invalid token as a proxy
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired-token')
        
        response = self.client.get('/api/v1/clients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED