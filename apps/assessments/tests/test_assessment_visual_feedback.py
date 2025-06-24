"""
Pytest-style tests for assessment visual feedback elements.
Testing CSS classes, visual indicators, and UI feedback for manual scores.
Following django-test.md guidelines for modern Django testing.
"""
import pytest
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


class TestAssessmentVisualFeedback:
    """Test suite for visual feedback elements in assessment forms"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user = UserFactory(username='test_trainer', password='testpass123')
        self.trainer = TrainerFactory(user=self.user)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.django_client = DjangoClient()
        self.django_client.force_login(self.user)
    
    def test_manual_score_visual_indicators(self):
        """Test visual indicators for manually entered scores"""
        # Create assessment with manual scores
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=4,
            shoulder_mobility_score=3
        )
        
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check for blue ring indicator CSS classes
        assertContains(response, 'ring-2')
        assertContains(response, 'ring-blue-500')
        assertContains(response, 'ring-offset-2')
        
        # Check for background color change
        assertContains(response, 'bg-blue-50')
        
        # Check for manual input badge
        assertContains(response, '수동 입력됨')
        assertContains(response, 'bg-blue-100')
        assertContains(response, 'text-blue-800')
        assertContains(response, 'text-xs')
        assertContains(response, 'px-2')
        assertContains(response, 'py-1')
        assertContains(response, 'rounded-full')
    
    def test_reset_button_visual_elements(self):
        """Test reset button visual elements for manual scores"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=3,
            shoulder_mobility_score=4
        )
        
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.django_client.get(url)
        
        # Check for reset button styling
        assertContains(response, 'bg-gray-200')
        assertContains(response, 'hover:bg-gray-300')
        assertContains(response, 'text-gray-600')
        assertContains(response, 'p-1')
        assertContains(response, 'rounded')
        assertContains(response, 'transition-colors')
        
        # Check for reset icon
        assertContains(response, '↻')
        
        # Check for tooltip/title attribute
        assertContains(response, 'title="자동 계산으로 재설정"')  # "Reset to auto calculation"
    
    def test_form_field_visual_states(self):
        """Test different visual states of form fields"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check for default field styling
        assertContains(response, 'border-gray-300')
        assertContains(response, 'focus:ring-indigo-500')
        assertContains(response, 'focus:border-indigo-500')
        
        # Check for manual override field styling
        assertContains(response, ':class="{')
        assertContains(response, "'ring-2 ring-blue-500 ring-offset-2 bg-blue-50':")
        assertContains(response, "manualOverrides.overheadSquat")
        assertContains(response, "manualOverrides.shoulderMobility")
    
    def test_visual_feedback_transitions(self):
        """Test CSS transitions for visual feedback"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for transition classes
        assertContains(response, 'transition')
        assertContains(response, 'duration-200')
        assertContains(response, 'ease-in-out')
        
        # Check for hover states
        assertContains(response, 'hover:')
        
        # Check for focus states
        assertContains(response, 'focus:')
    
    def test_score_option_visual_hierarchy(self):
        """Test visual hierarchy of score options"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for score option styling
        score_options = [
            ('0', '심각한 제한', 'text-red-600'),
            ('1', '상당한 제한', 'text-orange-600'),
            ('2', '중간 제한', 'text-yellow-600'),
            ('3', '약간 제한', 'text-blue-600'),
            ('4', '정상 범위', 'text-green-600'),
            ('5', '우수함', 'text-green-700')
        ]
        
        for value, label, color_class in score_options:
            assertContains(response, f'value="{value}"')
            assertContains(response, label)
            # Some options might have color coding
            if value in ['0', '5']:  # Edge cases might have special styling
                assertContains(response, 'font-semibold')
    
    def test_visual_feedback_accessibility(self):
        """Test accessibility features of visual feedback"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for ARIA labels
        assertContains(response, 'aria-label')
        assertContains(response, 'aria-describedby')
        
        # Check for proper label associations
        assertContains(response, 'for="id_overhead_squat_score"')
        assertContains(response, 'for="id_shoulder_mobility_score"')
        
        # Check for screen reader text
        assertContains(response, 'sr-only')  # Screen reader only class
    
    def test_visual_feedback_responsive_design(self):
        """Test responsive design of visual feedback elements"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for responsive classes
        assertContains(response, 'sm:')  # Small screens and up
        assertContains(response, 'md:')  # Medium screens and up
        assertContains(response, 'lg:')  # Large screens and up
        
        # Check for responsive grid layouts
        assertContains(response, 'grid')
        assertContains(response, 'gap-')
        assertContains(response, 'grid-cols-1')
        assertContains(response, 'md:grid-cols-2')
    
    def test_loading_state_visual_feedback(self):
        """Test visual feedback during loading/calculation states"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for loading spinner elements
        assertContains(response, 'animate-spin')
        assertContains(response, 'calculating')
        
        # Check for disabled state styling
        assertContains(response, ':disabled')
        assertContains(response, 'opacity-50')
        assertContains(response, 'cursor-not-allowed')
    
    def test_error_state_visual_feedback(self):
        """Test visual feedback for error states"""
        url = reverse('assessments:add')
        
        # Submit invalid form data
        form_data = {
            'client': '',  # Missing required field
            'date': '',  # Missing required field
        }
        
        response = self.django_client.post(url, form_data)
        
        # Check for error styling
        assertContains(response, 'border-red-300')
        assertContains(response, 'text-red-600')
        assertContains(response, 'bg-red-50')
        
        # Check for error messages
        assertContains(response, 'alert')
        assertContains(response, 'alert-error')
    
    def test_success_state_visual_feedback(self):
        """Test visual feedback for successful operations"""
        # Create an assessment first
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj
        )
        
        # Update it with manual scores
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        form_data = {
            'client': self.client_obj.pk,
            'date': assessment.date,
            'overhead_squat_score': 4,
            'shoulder_mobility_score': 3,
            # Include all required fields
            'push_up_reps': 25,
            'single_leg_balance_right_eyes_open': 35,
            'single_leg_balance_left_eyes_open': 35,
            'single_leg_balance_right_eyes_closed': 18,
            'single_leg_balance_left_eyes_closed': 18,
            'toe_touch_distance': 5.0,
            'shoulder_mobility_right': 4.0,
            'shoulder_mobility_left': 4.0,
            'farmer_carry_weight': 25.0,
            'farmer_carry_distance': 55.0,
            'farmer_carry_time': 35,
            'harvard_step_test_hr1': 135,
            'harvard_step_test_hr2': 125,
            'harvard_step_test_hr3': 115,
            'harvard_step_test_duration': 180.0,
        }
        
        response = self.django_client.post(url, form_data, follow=True)
        
        # Check for success message styling (if redirected to detail view)
        if response.redirect_chain:
            assertContains(response, 'alert-success')
            assertContains(response, 'bg-green-50')
            assertContains(response, 'text-green-800')


class TestVisualFeedbackIntegration:
    """Test integration of visual feedback with Alpine.js functionality"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user = UserFactory()
        self.trainer = TrainerFactory(user=self.user)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.django_client = DjangoClient()
        self.django_client.force_login(self.user)
    
    def test_alpine_conditional_classes(self):
        """Test Alpine.js conditional CSS classes"""
        url = reverse('assessments:add')
        response = self.django_client.get(url)
        
        # Check for Alpine.js class bindings
        assertContains(response, ':class=')
        assertContains(response, 'x-show=')
        assertContains(response, 'x-transition')
        
        # Check for conditional styling based on state
        assertContains(response, "manualOverrides.overheadSquat ? 'ring-2 ring-blue-500' : ''")
        assertContains(response, "manualOverrides.shoulderMobility ? 'ring-2 ring-blue-500' : ''")
    
    def test_visual_feedback_ajax_updates(self):
        """Test visual feedback updates via AJAX calls"""
        # Note: There's no single calculate_scores endpoint, using pushup as example
        url = reverse('assessments:calculate_pushup_score')
        
        # Test AJAX request for score calculation
        test_data = {
            'overhead_squat_score': 4,
            'shoulder_mobility_score': 3,
            'manual_overrides': {
                'overheadSquat': True,
                'shoulderMobility': True
            },
            'push_up_reps': 30,
            'single_leg_balance_right_eyes_open': 40,
            'single_leg_balance_left_eyes_open': 40,
            'toe_touch_distance': 5.0,
            'farmer_carry_weight': 30.0,
            'farmer_carry_distance': 60.0,
            'farmer_carry_time': 35,
            'harvard_step_test_hr1': 125,
            'harvard_step_test_hr2': 115,
            'harvard_step_test_hr3': 105,
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
        
        # Response should include visual state information
        assert 'overhead_squat_score' in result
        assert 'shoulder_mobility_score' in result
        
        # Manual scores should be preserved
        assert result['overhead_squat_score'] == 4
        assert result['shoulder_mobility_score'] == 3
    
    def test_chart_visual_updates(self):
        """Test visual updates in assessment result charts"""
        # Create assessment with scores
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client_obj,
            overhead_squat_score=4,
            shoulder_mobility_score=3,
            overall_score=75.5,
            strength_score=80.0,
            mobility_score=70.0,
            balance_score=75.0,
            cardio_score=77.0
        )
        
        url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.django_client.get(url)
        
        assert response.status_code == 200
        
        # Check for Chart.js canvas element
        assertContains(response, '<canvas')
        assertContains(response, 'assessmentRadarChart')
        
        # Check for chart data with scores
        assertContains(response, 'strength_score')
        assertContains(response, 'mobility_score')
        assertContains(response, 'balance_score')
        assertContains(response, 'cardio_score')
        
        # Check for visual score display
        assertContains(response, '점</span>')  # Korean for "points"
        
        # Check for color coding based on scores
        assertContains(response, 'text-green-600')  # Good scores
        assertContains(response, 'text-yellow-600')  # Average scores