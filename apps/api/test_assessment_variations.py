"""
Tests for Assessment API test variation support
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.trainers.factories import TrainerFactory, UserFactory


@pytest.mark.django_db
class TestAssessmentVariationAPI:
    """Test API support for assessment test variations"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.trainer = TrainerFactory()
        self.user = self.trainer.user
        self.test_client = ClientFactory(trainer=self.trainer)
        self.client.force_authenticate(user=self.user)
        
        # URLs
        self.list_url = reverse('api:assessment-list')
        self.detail_url = lambda pk: reverse('api:assessment-detail', kwargs={'pk': pk})
    
    def test_create_assessment_with_variations(self):
        """Test creating assessment with test variation data"""
        data = {
            'client': self.test_client.id,
            'date': '2025-01-20',
            'push_up_reps': 15,
            'push_up_type': 'modified',
            'farmer_carry_weight': 30,
            'farmer_carry_distance': 20,
            'farmer_carry_time': 45,
            'farmer_carry_percentage': 60,
            'test_environment': 'outdoor',
            'temperature': 25.5,
            'overhead_squat_score': 2,
            'toe_touch_distance': 5
        }
        
        response = self.client.post(self.list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify variation fields were saved
        assert response.data['push_up_type'] == 'modified'
        assert response.data['farmer_carry_percentage'] == 60
        assert response.data['test_environment'] == 'outdoor'
        assert response.data['temperature'] == 25.5
    
    def test_retrieve_assessment_with_variations(self):
        """Test retrieving assessment shows variation data"""
        assessment = AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer,
            push_up_type='wall',
            farmer_carry_percentage=75.5,
            test_environment='outdoor',
            temperature=32.0
        )
        
        response = self.client.get(self.detail_url(assessment.id))
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all variation fields are present
        assert response.data['push_up_type'] == 'wall'
        assert response.data['farmer_carry_percentage'] == 75.5
        assert response.data['test_environment'] == 'outdoor'
        assert response.data['temperature'] == 32.0
    
    def test_update_assessment_variations(self):
        """Test updating assessment variation fields"""
        assessment = AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer,
            push_up_type='standard'
        )
        
        data = {
            'push_up_type': 'modified',
            'test_environment': 'outdoor',
            'temperature': 28.0
        }
        
        response = self.client.patch(self.detail_url(assessment.id), data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Verify updates
        assert response.data['push_up_type'] == 'modified'
        assert response.data['test_environment'] == 'outdoor'
        assert response.data['temperature'] == 28.0
    
    def test_filter_by_push_up_type(self):
        """Test filtering assessments by push-up type"""
        # Create assessments with different push-up types
        AssessmentFactory(client=self.test_client, trainer=self.trainer, push_up_type='standard')
        AssessmentFactory(client=self.test_client, trainer=self.trainer, push_up_type='modified')
        AssessmentFactory(client=self.test_client, trainer=self.trainer, push_up_type='wall')
        
        # Filter for modified push-ups
        response = self.client.get(self.list_url, {'push_up_type': 'modified'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        results = response.data['results']
        assert len(results) == 1
    
    def test_filter_by_test_environment(self):
        """Test filtering assessments by test environment"""
        # Create assessments with different environments
        AssessmentFactory(client=self.test_client, trainer=self.trainer, test_environment='indoor')
        AssessmentFactory(client=self.test_client, trainer=self.trainer, test_environment='outdoor')
        
        # Filter for outdoor tests
        response = self.client.get(self.list_url, {'test_environment': 'outdoor'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        results = response.data['results']
        assert len(results) == 1
    
    def test_filter_has_variations(self):
        """Test filtering for assessments with any variations"""
        # Create standard assessment
        AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer,
            push_up_type='standard',
            test_environment='indoor'
        )
        
        # Create assessment with variations
        AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer,
            push_up_type='modified',
            farmer_carry_percentage=80
        )
        
        # Filter for assessments with variations
        response = self.client.get(self.list_url, {'has_variations': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
    
    def test_variation_field_validation(self):
        """Test validation of variation field values"""
        data = {
            'client': self.test_client.id,
            'date': '2025-01-20',
            'push_up_reps': 20,
            'push_up_type': 'invalid_type',  # Invalid choice
            'farmer_carry_percentage': 250,   # Exceeds max value
            'temperature': 60                 # Exceeds max value
        }
        
        response = self.client.post(self.list_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Check specific field errors
        assert 'push_up_type' in response.data
        assert 'farmer_carry_percentage' in response.data
        assert 'temperature' in response.data
    
    def test_backward_compatibility(self):
        """Test that existing assessments without variations still work"""
        # Create assessment without any variation data
        assessment = AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer
        )
        
        response = self.client.get(self.detail_url(assessment.id))
        assert response.status_code == status.HTTP_200_OK
        
        # Verify default values are returned
        assert response.data['push_up_type'] == 'standard'
        assert response.data['test_environment'] == 'indoor'
        assert response.data['farmer_carry_percentage'] is None
        assert response.data['temperature'] is None
    
    def test_list_serializer_excludes_variations(self):
        """Test that list serializer doesn't include variation fields"""
        AssessmentFactory(
            client=self.test_client,
            trainer=self.trainer,
            push_up_type='modified'
        )
        
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        
        # List serializer should not include variation fields
        results = response.data['results']
        assert len(results) > 0
        assert 'push_up_type' not in results[0]
        assert 'farmer_carry_percentage' not in results[0]
        assert 'test_environment' not in results[0]
        assert 'temperature' not in results[0]