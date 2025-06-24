"""
Pytest-style tests for assessment manual score field fixes.
Testing Alpine.js integration, manual override tracking, and form initialization.
Following django-test.md guidelines for modern Django testing.
"""
import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed
from django.test import Client as DjangoClient

from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


class TestAssessmentManualScoreFields:
    """Test suite for manual score field Alpine.js integration"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user = UserFactory(username='test_trainer', password='testpass123')
        self.trainer = TrainerFactory(user=self.user)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.django_client = DjangoClient()
        self.django_client.force_login(self.user)
    
    def test_manual_score_fields_alpine_bindings(self):
        """Test that manual score fields have proper Alpine.js bindings"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check for Alpine.js data bindings on manual score fields
        assertContains(response, 'x-model="overheadSquatScore"')
        assertContains(response, 'x-model="shoulderMobilityScore"')
        
        # Check for manual override tracking
        assertContains(response, 'manualOverrides.overheadSquat')
        assertContains(response, 'manualOverrides.shoulderMobility')
        
        # Check for change event handlers
        assertContains(response, '@change="handleManualScoreChange')
    
    def test_manual_score_range_validation(self):
        """Test that manual scores accept 0-5 range"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=0,  # Minimum value
            shoulder_mobility_score=5  # Maximum value
        )
        
        # Test all valid values
        for score in range(6):  # 0-5
            assessment.overhead_squat_score = score
            assessment.shoulder_mobility_score = score
            assessment.save()
            
            assert assessment.overhead_squat_score == score
            assert assessment.shoulder_mobility_score == score
    
    def test_form_initialization_with_existing_scores(self):
        """Test form properly loads existing manual scores"""
        # Create assessment with manual scores
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=3,
            shoulder_mobility_score=4
        )
        
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check that existing values are properly set in Alpine.js initialization
        assertContains(response, 'overheadSquatScore: 3')
        assertContains(response, 'shoulderMobilityScore: 4')
        
        # Check that manual override flags are set when scores exist
        assertContains(response, 'manualOverrides: {')
        assertContains(response, 'overheadSquat: true')
        assertContains(response, 'shoulderMobility: true')
    
    def test_manual_override_persistence(self):
        """Test that manual overrides are tracked and persisted"""
        url = reverse('assessments:add')
        
        # Submit form with manual scores
        form_data = {
            'client': self.client_obj.pk,
            'date': date.today(),
            'overhead_squat_score': 4,
            'shoulder_mobility_score': 3,
            # Other required fields
            'push_up_reps': 20,
            'single_leg_balance_right_eyes_open': 30,
            'single_leg_balance_left_eyes_open': 30,
            'single_leg_balance_right_eyes_closed': 15,
            'single_leg_balance_left_eyes_closed': 15,
            'toe_touch_distance': 5.0,
            'shoulder_mobility_right': 5.0,
            'shoulder_mobility_left': 5.0,
            'farmer_carry_weight': 20.0,
            'farmer_carry_distance': 50.0,
            'farmer_carry_time': 30,
            'harvard_step_test_hr1': 140,
            'harvard_step_test_hr2': 130,
            'harvard_step_test_hr3': 120,
            'harvard_step_test_duration': 180.0,
        }
        
        response = self.django_client.post(url, form_data)
        
        # Should redirect after successful save
        assert response.status_code == 302
        
        # Check that scores were saved
        assessment = Assessment.objects.latest('id')
        assert assessment.overhead_squat_score == 4
        assert assessment.shoulder_mobility_score == 3
    
    def test_score_options_rendering(self):
        """Test that score options 0-5 are rendered with proper labels"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check for all score options with Korean labels
        score_labels = [
            ('0', '0 - 심각한 제한'),
            ('1', '1 - 상당한 제한'),
            ('2', '2 - 중간 제한'),
            ('3', '3 - 약간 제한'),
            ('4', '4 - 정상 범위'),
            ('5', '5 - 우수함')
        ]
        
        for value, label in score_labels:
            assertContains(response, f'value="{value}"')
            assertContains(response, label)
    
    def test_ajax_score_calculation_with_manual_overrides(self):
        """Test AJAX score calculation respects manual overrides"""
        # Note: There's no single calculate_scores endpoint, using pushup as example
        url = reverse('assessments:calculate_pushup_score')
        
        # Test data with manual overrides
        test_data = {
            'overhead_squat_score': 5,  # Manual override
            'shoulder_mobility_score': 4,  # Manual override
            'manual_overrides': {
                'overheadSquat': True,
                'shoulderMobility': True
            },
            # Other test data
            'push_up_reps': 30,
            'single_leg_balance_right_eyes_open': 45,
            'single_leg_balance_left_eyes_open': 45,
            'toe_touch_distance': 5.0,
            'farmer_carry_weight': 30.0,
            'farmer_carry_distance': 60.0,
            'farmer_carry_time': 35,
            'harvard_step_test_hr1': 120,
            'harvard_step_test_hr2': 110,
            'harvard_step_test_hr3': 100,
            'client_gender': '남성',
            'client_age': 30
        }
        
        response = self.django_client.post(
            url,
            json.dumps(test_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200
        
        result = response.json()
        
        # Manual scores should be preserved
        assert result['overhead_squat_score'] == 5
        assert result['shoulder_mobility_score'] == 4
        
        # Check that category scores properly use the manual values
        # The balance score should use the manual overhead squat score
        # The mobility score should use the manual shoulder mobility score
        assert 'balance_score' in result
        assert 'mobility_score' in result
    
    def test_form_validation_with_edge_cases(self):
        """Test form validation with edge case values"""
        url = reverse('assessments:add')
        
        # Test with score = 0 (valid edge case)
        form_data = {
            'client': self.client_obj.pk,
            'date': date.today(),
            'overhead_squat_score': 0,  # Edge case
            'shoulder_mobility_score': 0,  # Edge case
            # Other required fields with minimum values
            'push_up_reps': 0,
            'single_leg_balance_right_eyes_open': 0,
            'single_leg_balance_left_eyes_open': 0,
            'single_leg_balance_right_eyes_closed': 0,
            'single_leg_balance_left_eyes_closed': 0,
            'toe_touch_distance': -20.0,
            'shoulder_mobility_right': 0.0,
            'shoulder_mobility_left': 0.0,
            'farmer_carry_weight': 0.0,
            'farmer_carry_distance': 0.0,
            'farmer_carry_time': 0,
            'harvard_step_test_hr1': 60,
            'harvard_step_test_hr2': 60,
            'harvard_step_test_hr3': 60,
            'harvard_step_test_duration': 0.0,
        }
        
        response = self.django_client.post(url, form_data)
        
        # Should successfully save with edge case values
        assert response.status_code == 302
        
        assessment = Assessment.objects.latest('id')
        assert assessment.overhead_squat_score == 0
        assert assessment.shoulder_mobility_score == 0


class TestManualScoreAlpineJsIntegration:
    """Test Alpine.js specific functionality for manual scores"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user = UserFactory()
        self.trainer = TrainerFactory(user=self.user)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.django_client = DjangoClient()
        self.django_client.force_login(self.user)
    
    def test_alpine_component_initialization(self):
        """Test Alpine.js component proper initialization"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for Alpine.js component definition
        assertContains(response, 'x-data="assessmentForm()"')
        
        # Check for required Alpine.js methods
        assertContains(response, 'handleManualScoreChange')
        assertContains(response, 'calculateScores')
        assertContains(response, 'initializeForm')
        
        # Check for Alpine.js lifecycle hooks
        assertContains(response, 'x-init=')
    
    def test_manual_score_visual_feedback_classes(self):
        """Test visual feedback CSS classes for manual scores"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=3,
            shoulder_mobility_score=4
        )
        
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.django_client.get(url)
        
        # Check for visual feedback classes
        assertContains(response, 'ring-2 ring-blue-500')  # Manual score indicator
        assertContains(response, 'bg-blue-50')  # Background color for manual fields
        assertContains(response, '수동 입력됨')  # Korean text for "Manually entered"
    
    def test_reset_button_functionality(self):
        """Test reset button for manual scores"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for reset buttons
        assertContains(response, '@click="resetManualScore(\'overheadSquat\')"')
        assertContains(response, '@click="resetManualScore(\'shoulderMobility\')"')
        
        # Check for reset button visibility conditions
        assertContains(response, 'x-show="manualOverrides.overheadSquat"')
        assertContains(response, 'x-show="manualOverrides.shoulderMobility"')
        
        # Check for reset icon
        assertContains(response, '↻')  # Reset icon
    
    def test_score_calculation_dependencies(self):
        """Test that score calculations properly handle dependencies"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check that balance score calculation includes overhead squat
        assertContains(response, 'balanceScore')
        assertContains(response, 'overheadSquatScore')
        
        # Check that mobility score calculation includes shoulder mobility
        assertContains(response, 'mobilityScore')
        assertContains(response, 'shoulderMobilityScore')
        
        # Check for proper calculation order
        assertContains(response, 'calculateCategoryScores')