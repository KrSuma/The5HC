"""
Tests for Client API endpoints
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.sessions.factories import SessionPackageFactory

User = get_user_model()


@pytest.mark.django_db
class TestClientAPI:
    """Test Client API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create test data
        self.client1 = ClientFactory(trainer=self.user)
        self.client2 = ClientFactory(trainer=self.user)
        self.other_client = ClientFactory(trainer=self.other_user)
    
    def test_list_clients_success(self):
        """Test listing clients for authenticated user"""
        response = self.client.get('/api/v1/clients/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        client_ids = [c['id'] for c in response.data['results']]
        assert self.client1.id in client_ids
        assert self.client2.id in client_ids
        assert self.other_client.id not in client_ids
    
    def test_retrieve_client_success(self):
        """Test retrieving a single client"""
        response = self.client.get(f'/api/v1/clients/{self.client1.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.client1.id
        assert response.data['name'] == self.client1.name
        assert 'email' in response.data
        assert 'phone_number' in response.data
    
    def test_retrieve_other_trainers_client_forbidden(self):
        """Test retrieving another trainer's client is forbidden"""
        response = self.client.get(f'/api/v1/clients/{self.other_client.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_client_success(self):
        """Test creating a new client"""
        data = {
            'name': '새로운 회원',
            'email': 'new@example.com',
            'phone_number': '010-1234-5678',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'height': 175.5,
            'weight': 70.0,
            'goal': '체중 감량',
            'medical_history': '없음'
        }
        
        response = self.client.post('/api/v1/clients/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '새로운 회원'
        assert response.data['trainer'] == self.user.id
    
    def test_create_client_invalid_data(self):
        """Test creating client with invalid data"""
        data = {
            'name': '',  # Required field
            'email': 'invalid-email',  # Invalid format
        }
        
        response = self.client.post('/api/v1/clients/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert 'email' in response.data
    
    def test_update_client_success(self):
        """Test updating a client"""
        data = {
            'name': '수정된 이름',
            'email': self.client1.email,
            'phone_number': self.client1.phone_number,
            'birth_date': self.client1.birth_date,
            'gender': self.client1.gender,
            'height': 180.0,  # Updated
            'weight': 75.0,   # Updated
        }
        
        response = self.client.put(f'/api/v1/clients/{self.client1.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == '수정된 이름'
        assert response.data['height'] == 180.0
        assert response.data['weight'] == 75.0
    
    def test_partial_update_client_success(self):
        """Test partial update of a client"""
        data = {
            'weight': 72.5
        }
        
        response = self.client.patch(f'/api/v1/clients/{self.client1.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weight'] == 72.5
        assert response.data['name'] == self.client1.name  # Unchanged
    
    def test_delete_client_success(self):
        """Test deleting a client"""
        response = self.client.delete(f'/api/v1/clients/{self.client1.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = self.client.get(f'/api/v1/clients/{self.client1.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_search_clients(self):
        """Test searching clients"""
        # Create client with specific name
        search_client = ClientFactory(trainer=self.user, name='김철수')
        
        response = self.client.get('/api/v1/clients/', {'search': '김철수'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == '김철수'
    
    def test_order_clients(self):
        """Test ordering clients"""
        response = self.client.get('/api/v1/clients/', {'ordering': 'name'})
        
        assert response.status_code == status.HTTP_200_OK
        names = [c['name'] for c in response.data['results']]
        assert names == sorted(names)
        
        # Test reverse ordering
        response = self.client.get('/api/v1/clients/', {'ordering': '-name'})
        names = [c['name'] for c in response.data['results']]
        assert names == sorted(names, reverse=True)
    
    def test_client_assessments_endpoint(self):
        """Test getting assessments for a client"""
        # Create assessments
        assessment1 = AssessmentFactory(client=self.client1)
        assessment2 = AssessmentFactory(client=self.client1)
        other_assessment = AssessmentFactory(client=self.client2)
        
        response = self.client.get(f'/api/v1/clients/{self.client1.id}/assessments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assessment_ids = [a['id'] for a in response.data]
        assert assessment1.id in assessment_ids
        assert assessment2.id in assessment_ids
        assert other_assessment.id not in assessment_ids
    
    def test_client_packages_endpoint(self):
        """Test getting packages for a client"""
        # Create packages
        package1 = SessionPackageFactory(client=self.client1, trainer=self.user)
        package2 = SessionPackageFactory(client=self.client1, trainer=self.user)
        other_package = SessionPackageFactory(client=self.client2, trainer=self.user)
        
        response = self.client.get(f'/api/v1/clients/{self.client1.id}/packages/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        package_ids = [p['id'] for p in response.data]
        assert package1.id in package_ids
        assert package2.id in package_ids
        assert other_package.id not in package_ids
    
    def test_client_statistics_endpoint(self):
        """Test getting statistics for a client"""
        # Create test data
        AssessmentFactory(client=self.client1, total_score=80)
        AssessmentFactory(client=self.client1, total_score=85)
        SessionPackageFactory(client=self.client1, trainer=self.user, is_active=True)
        SessionPackageFactory(client=self.client1, trainer=self.user, is_active=False)
        
        response = self.client.get(f'/api/v1/clients/{self.client1.id}/statistics/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_assessments'] == 2
        assert response.data['total_packages'] == 2
        assert response.data['active_packages'] == 1
        assert response.data['average_score'] == 82.5