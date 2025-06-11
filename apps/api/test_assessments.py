"""
Tests for Assessment API endpoints
"""
import pytest
from datetime import date, timedelta
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory


@pytest.mark.django_db
class TestAssessmentAPI:
    """Test Assessment API endpoints"""
    
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
        
        # Create test clients
        self.client1 = ClientFactory(trainer=self.user)
        self.client2 = ClientFactory(trainer=self.user)
        self.other_trainer_client = ClientFactory(trainer=self.other_user)
        
        # Create test assessments
        self.assessment1 = AssessmentFactory(client=self.client1)
        self.assessment2 = AssessmentFactory(client=self.client2)
        self.other_assessment = AssessmentFactory(client=self.other_trainer_client)
    
    def test_list_assessments_success(self):
        """Test listing assessments for authenticated user's clients"""
        response = self.client.get('/api/v1/assessments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assessment_ids = [a['id'] for a in response.data['results']]
        assert self.assessment1.id in assessment_ids
        assert self.assessment2.id in assessment_ids
        assert self.other_assessment.id not in assessment_ids
    
    def test_retrieve_assessment_success(self):
        """Test retrieving a single assessment"""
        response = self.client.get(f'/api/v1/assessments/{self.assessment1.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.assessment1.id
        assert 'client' in response.data
        assert 'date' in response.data
        assert 'overall_score' in response.data
        assert 'strength_score' in response.data
        assert 'mobility_score' in response.data
    
    def test_retrieve_other_trainers_assessment_forbidden(self):
        """Test retrieving another trainer's client's assessment is forbidden"""
        response = self.client.get(f'/api/v1/assessments/{self.other_assessment.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_assessment_success(self):
        """Test creating a new assessment"""
        data = {
            'client': self.client1.id,
            'date': date.today().isoformat(),
            'height': 175.0,
            'weight': 70.0,
            'body_fat_percentage': 15.0,
            'muscle_mass': 30.0,
            'push_ups': 25,
            'squats': 30,
            'plank_duration': 60,
            'wall_sit_duration': 45,
            'sit_and_reach': 10.5,
            'shoulder_flexibility_left': 8.0,
            'shoulder_flexibility_right': 8.5,
            'single_leg_stand_left': 30,
            'single_leg_stand_right': 28,
            'timed_up_and_go': 8.5,
            'grip_strength_left': 35.0,
            'grip_strength_right': 37.0,
            'vo2_max': 45.0,
            'resting_heart_rate': 65,
            'blood_pressure_systolic': 120,
            'blood_pressure_diastolic': 80,
            'notes': '전반적으로 좋은 상태'
        }
        
        response = self.client.post('/api/v1/assessments/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['client'] == self.client1.id
        assert 'overall_score' in response.data
        assert 'strength_score' in response.data
        assert 'mobility_score' in response.data
    
    def test_create_assessment_for_other_trainers_client_fails(self):
        """Test creating assessment for another trainer's client fails"""
        data = {
            'client': self.other_trainer_client.id,
            'date': date.today().isoformat(),
            'height': 175.0,
            'weight': 70.0,
            # ... minimal required fields
        }
        
        response = self.client.post('/api/v1/assessments/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_assessment_success(self):
        """Test updating an assessment"""
        data = {
            'client': self.assessment1.client.id,
            'date': self.assessment1.date.isoformat(),
            'height': self.assessment1.height,
            'weight': 75.0,  # Updated weight
            'push_ups': 30,  # Updated
            'notes': '체중 증가, 근력 향상'
        }
        
        response = self.client.patch(f'/api/v1/assessments/{self.assessment1.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weight'] == 75.0
        assert response.data['push_ups'] == 30
        assert response.data['notes'] == '체중 증가, 근력 향상'
    
    def test_delete_assessment_success(self):
        """Test deleting an assessment"""
        response = self.client.delete(f'/api/v1/assessments/{self.assessment1.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = self.client.get(f'/api/v1/assessments/{self.assessment1.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_search_assessments(self):
        """Test searching assessments by client name"""
        # Update client name for search test
        self.client1.name = '김영희'
        self.client1.save()
        
        response = self.client.get('/api/v1/assessments/', {'search': '김영희'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == self.assessment1.id
    
    def test_order_assessments(self):
        """Test ordering assessments by date"""
        # Create assessments with different dates
        old_assessment = AssessmentFactory(
            client=self.client1,
            date=date.today() - timedelta(days=30)
        )
        new_assessment = AssessmentFactory(
            client=self.client1,
            date=date.today()
        )
        
        response = self.client.get('/api/v1/assessments/', {'ordering': 'date'})
        
        assert response.status_code == status.HTTP_200_OK
        dates = [a['date'] for a in response.data['results']]
        assert dates == sorted(dates)
        
        # Test reverse ordering (default)
        response = self.client.get('/api/v1/assessments/', {'ordering': '-date'})
        dates = [a['date'] for a in response.data['results']]
        assert dates == sorted(dates, reverse=True)
    
    def test_assessment_comparison_endpoint(self):
        """Test comparing assessments"""
        # Create previous assessment
        previous_assessment = AssessmentFactory(
            client=self.client1,
            date=date.today() - timedelta(days=30),
            overall_score=75.0,
            strength_score=70.0,
            mobility_score=80.0
        )
        
        # Create current assessment
        current_assessment = AssessmentFactory(
            client=self.client1,
            date=date.today(),
            overall_score=85.0,
            strength_score=82.0,
            mobility_score=88.0
        )
        
        response = self.client.get(f'/api/v1/assessments/{current_assessment.id}/comparison/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'current' in response.data
        assert 'previous' in response.data
        assert 'improvements' in response.data
        assert response.data['improvements']['overall_score'] == 10.0
        assert response.data['improvements']['strength_score'] == 12.0
        assert response.data['improvements']['mobility_score'] == 8.0
    
    def test_assessment_comparison_no_previous(self):
        """Test comparison when no previous assessment exists"""
        # Create only one assessment
        single_assessment = AssessmentFactory(
            client=ClientFactory(trainer=self.user),
            date=date.today()
        )
        
        response = self.client.get(f'/api/v1/assessments/{single_assessment.id}/comparison/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'message' in response.data
        assert '이전 평가 기록이 없습니다' in response.data['message']
    
    def test_assessment_list_pagination(self):
        """Test assessment list pagination"""
        # Create many assessments
        for i in range(25):
            AssessmentFactory(client=self.client1)
        
        response = self.client.get('/api/v1/assessments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert len(response.data['results']) <= 20  # Default page size