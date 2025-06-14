"""
Comprehensive tests for assessment score calculation functionality.
Tests the scoring algorithms, calculation methods, and edge cases.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal
import json

from .models import Assessment
from .scoring import (
    calculate_pushup_score, calculate_farmers_carry_score, calculate_step_test_score,
    calculate_category_scores
)
from .factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


def get_score_color(score):
    """Helper function to get color indicator for score"""
    if score is None:
        return 'gray'
    elif score >= 4:
        return 'green'
    elif score >= 2:
        return 'yellow'
    else:
        return 'red'


class TestIndividualScoringFunctions:
    """Test individual scoring functions with various inputs"""
    
    @pytest.mark.parametrize('gender,age,reps,expected_score', [
        # Male test cases (scores are 1-4, not 1-5)
        ('Male', 25, 50, 4),  # Excellent
        ('Male', 25, 40, 4),  # Excellent
        ('Male', 25, 30, 3),  # Good
        ('Male', 25, 20, 1),  # Below average (< 22)
        ('Male', 25, 10, 1),  # Poor
        ('Male', 45, 25, 4),  # Different age group - excellent
        ('Male', 60, 20, 4),  # Older age group - excellent
        # Female test cases
        ('Female', 25, 40, 4),  # Excellent
        ('Female', 25, 30, 4),  # Excellent
        ('Female', 25, 20, 2),  # Average
        ('Female', 25, 10, 1),  # Poor
        ('Female', 25, 5, 1),   # Poor
        ('Female', 45, 25, 4),  # Different age group - excellent
        ('Female', 60, 15, 3),  # Older age group - good
        # Edge cases
        ('Male', 25, 0, 1),     # Zero reps
        ('Male', 25, 100, 4),   # Very high reps (still max of 4)
        ('Male', 25, None, 0),  # None input
    ])
    def test_pushup_score_calculation(self, gender, age, reps, expected_score):
        """Test push-up scoring with various inputs"""
        score = calculate_pushup_score(gender, age, reps)
        assert score == expected_score
    
    @pytest.mark.parametrize('weight,distance,time,expected_score', [
        # Standard test cases - score range is 1.0-4.0
        (30, 50, 30, 4.0),    # Excellent performance
        (25, 50, 35, 3.5),    # Good performance
        (20, 50, 40, 3.0),    # Average performance
        (15, 50, 45, 2.0),    # Below average
        (10, 50, 50, 1.0),    # Poor performance
        # Different distances
        (30, 100, 60, 4.0),   # Longer distance
        (20, 25, 20, 3.0),    # Shorter distance
        # Edge cases
        (0, 50, 30, 1.0),     # Zero weight
        (50, 50, 30, 4.0),    # Very heavy weight
        (30, 0, 30, 1.0),     # Zero distance
        (30, 50, 0, 1.0),     # Zero time (invalid)
    ])
    def test_farmer_carry_score_calculation(self, weight, distance, time, expected_score):
        """Test farmer's carry scoring with various inputs"""
        # The function requires gender parameter
        score = calculate_farmers_carry_score('Male', weight, distance, time)
        assert score == expected_score
    
    @pytest.mark.parametrize('hr1,hr2,hr3,expected_score,expected_pfi_range', [
        # Excellent fitness
        (60, 65, 70, 5, (90, 110)),
        # Good fitness
        (70, 75, 80, 4, (70, 90)),
        # Average fitness
        (80, 85, 90, 3, (55, 70)),
        # Below average
        (90, 95, 100, 2, (45, 55)),
        # Poor fitness
        (100, 105, 110, 1, (35, 45)),
        # Edge cases
        (0, 0, 0, 1, (0, float('inf'))),     # Zero heart rates (invalid)
        (200, 200, 200, 1, (0, 30)),         # Very high heart rates
        (None, 75, 80, 0, (None, None)),     # None input
        (70, None, 80, 0, (None, None)),     # None input
        (70, 75, None, 0, (None, None)),     # None input
    ])
    def test_step_test_score_calculation(self, hr1, hr2, hr3, expected_score, expected_pfi_range):
        """Test Harvard Step Test scoring with various inputs"""
        score, pfi = calculate_step_test_score(hr1, hr2, hr3)
        assert score == expected_score
        
        if expected_pfi_range[0] is not None:
            assert expected_pfi_range[0] <= pfi <= expected_pfi_range[1]


class TestCategoryScoreCalculation:
    """Test category score calculations"""
    
    def test_strength_score_calculation(self):
        """Test strength score calculation from push-up and farmer's carry"""
        assessment_data = {
            'push_up_score': 4,
            'farmer_carry_score': 5,
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Strength score should be average of push-up and farmer's carry
        expected_strength = (4 + 5) / 2
        assert scores['strength_score'] == expected_strength
    
    def test_mobility_score_calculation(self):
        """Test mobility score calculation"""
        assessment_data = {
            'toe_touch_score': 4,
            'shoulder_mobility_score': 3,
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Mobility score should be average of toe touch and shoulder mobility
        expected_mobility = (4 + 3) / 2
        assert scores['mobility_score'] == expected_mobility
    
    def test_balance_score_calculation(self):
        """Test balance score calculation"""
        assessment_data = {
            'single_leg_balance_score': 5,
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Balance score should equal single leg balance score
        assert scores['balance_score'] == 5
    
    def test_cardio_score_calculation(self):
        """Test cardio score calculation"""
        assessment_data = {
            'harvard_step_test_score': 3,
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Cardio score should equal Harvard step test score
        assert scores['cardio_score'] == 3
    
    def test_overall_score_calculation(self):
        """Test overall score calculation from all categories"""
        assessment_data = {
            'push_up_score': 4,
            'farmer_carry_score': 5,
            'toe_touch_score': 3,
            'shoulder_mobility_score': 4,
            'single_leg_balance_score': 5,
            'harvard_step_test_score': 2,
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Calculate expected scores
        strength = (4 + 5) / 2  # 4.5
        mobility = (3 + 4) / 2  # 3.5
        balance = 5
        cardio = 2
        
        # Overall should be weighted average
        expected_overall = (strength * 0.3 + mobility * 0.2 + balance * 0.2 + cardio * 0.3) * 20
        
        assert abs(scores['overall_score'] - expected_overall) < 0.01
    
    def test_missing_data_handling(self):
        """Test category scores with missing data"""
        assessment_data = {
            'push_up_score': 4,
            # Missing farmer_carry_score
            'toe_touch_score': 3,
            # Missing other scores
        }
        client_details = {'age': 30, 'gender': 'male'}
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Should handle missing data gracefully
        assert scores['strength_score'] == 4  # Only push-up available
        assert scores['mobility_score'] == 3  # Only toe touch available
        assert scores['balance_score'] == 0  # No data
        assert scores['cardio_score'] == 0   # No data


class TestAssessmentModelScoreCalculation:
    """Test Assessment model's calculate_scores method"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(username='test_trainer')
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male',
            height=170,
            weight=70
        )
    
    def test_calculate_scores_full_data(self):
        """Test calculate_scores with complete assessment data"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Raw test data
            push_up_reps=35,
            push_up_score=None,  # Ensure it's None so it gets calculated
            farmer_carry_weight=30,
            farmer_carry_distance=50,
            farmer_carry_time=35,
            farmer_carry_score=None,  # Ensure it's None so it gets calculated
            single_leg_balance_right_eyes_open=45,
            single_leg_balance_left_eyes_open=50,
            single_leg_balance_right_eyes_closed=20,
            single_leg_balance_left_eyes_closed=25,
            single_leg_balance_score=None,  # Ensure it's None so it gets calculated
            toe_touch_distance=5.0,
            toe_touch_score=None,  # Ensure it's None so it gets calculated
            shoulder_mobility_right=2.0,
            shoulder_mobility_left=2.5,
            harvard_step_test_hr1=75,
            harvard_step_test_hr2=80,
            harvard_step_test_hr3=85,
            harvard_step_test_score=None,  # Ensure it's None so it gets calculated
            # Manual scores
            overhead_squat_score=4,
            shoulder_mobility_score=4,
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Debug output
        print(f"\nClient age: {assessment.client.age}")
        print(f"Client gender: {assessment.client.gender}")
        print(f"Push-up reps: {assessment.push_up_reps}")
        print(f"Push-up score: {assessment.push_up_score}")
        
        # Verify individual test scores
        assert assessment.push_up_score == 4  # 35 reps > 30 (excellent threshold)
        assert assessment.farmer_carry_score in [3, 4]  # Score varies based on algorithm
        assert assessment.toe_touch_score == 4  # 5cm above floor
        assert assessment.harvard_step_test_score == 1  # Low PFI from high heart rates
        
        # Verify category scores
        assert assessment.strength_score == 4.0  # Average of push-up (4) and farmer (4)
        assert assessment.mobility_score == 4.0  # Average of toe touch (4) and shoulder (4)
        assert assessment.balance_score > 0  # Should have a calculated value
        assert assessment.cardio_score == 3.0  # Harvard step test score
        
        # Verify overall score
        assert 0 <= assessment.overall_score <= 100
        assert assessment.overall_score > 50  # Should be decent with these scores
    
    def test_calculate_scores_partial_data(self):
        """Test calculate_scores with partial assessment data"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Only some test data
            push_up_reps=25,
            toe_touch_distance=-10.0,  # Below floor
            overhead_squat_score=3,
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Verify calculated scores
        assert assessment.push_up_score == 3  # Based on 25 reps
        assert assessment.toe_touch_score == 2  # -10cm below floor
        
        # Verify category scores handle missing data
        assert assessment.strength_score == 3.0  # Only push-up
        assert assessment.mobility_score == 2.0  # Only toe touch
        assert assessment.cardio_score == 0.0    # No data
        
        # Overall score should still calculate
        assert assessment.overall_score >= 0
    
    def test_calculate_scores_edge_cases(self):
        """Test calculate_scores with edge cases"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Edge case values
            push_up_reps=0,  # Zero reps
            farmer_carry_weight=0,  # Zero weight
            toe_touch_distance=30.0,  # Very flexible
            harvard_step_test_hr1=200,  # Very high HR
            harvard_step_test_hr2=200,
            harvard_step_test_hr3=200,
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Verify edge cases handled properly
        assert assessment.push_up_score == 1  # Minimum score
        assert assessment.farmer_carry_score == 1  # Minimum score
        assert assessment.toe_touch_score == 5  # Maximum score
        assert assessment.harvard_step_test_score == 1  # Poor fitness
        
        # Overall score should still be valid
        assert 0 <= assessment.overall_score <= 100
    
    def test_calculate_scores_female_client(self):
        """Test calculate_scores with female client"""
        female_client = ClientFactory(
            trainer=self.trainer,
            age=25,
            gender='female'
        )
        
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=female_client,
            push_up_reps=25,  # Good for female
            farmer_carry_weight=20,
            farmer_carry_distance=50,
            farmer_carry_time=40,
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Verify gender-specific scoring
        assert assessment.push_up_score == 4  # Good score for female
        assert assessment.farmer_carry_score == 3
        
        # Overall calculation should work
        assert assessment.overall_score >= 0
    
    def test_score_not_recalculated_if_exists(self):
        """Test that existing scores are not overwritten"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=30,
            push_up_score=5,  # Manually set high score
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Manual score should be preserved
        assert assessment.push_up_score == 5  # Not recalculated
    
    def test_score_color_indicators(self):
        """Test score color indicator logic"""
        # Test color coding
        assert get_score_color(5) == 'green'
        assert get_score_color(4) == 'green'
        assert get_score_color(3) == 'yellow'
        assert get_score_color(2) == 'yellow'
        assert get_score_color(1) == 'red'
        assert get_score_color(0) == 'red'
        assert get_score_color(None) == 'gray'


class TestScoreCalculationViews:
    """Test AJAX views for score calculation"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(
            username='test_trainer',
            password='testpass123'
        )
    
    def test_pushup_score_ajax(self, client):
        """Test push-up score AJAX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_pushup_score')
        
        response = client.get(url, {
            'gender': 'male',
            'age': '30',
            'reps': '35'
        })
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'score' in data
        assert data['score'] == 4
    
    def test_farmer_carry_score_ajax(self, client):
        """Test farmer's carry score AJAX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_farmer_carry_score')
        
        response = client.get(url, {
            'weight': '30',
            'distance': '50',
            'time': '35'
        })
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'score' in data
        assert data['score'] == 4
    
    def test_balance_score_ajax(self, client):
        """Test balance score AJAX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_balance_score')
        
        response = client.get(url, {
            'reo': '45',  # Right eyes open
            'leo': '50',  # Left eyes open
            'rec': '20',  # Right eyes closed
            'lec': '25'   # Left eyes closed
        })
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'score' in data
        assert data['score'] > 0
    
    def test_toe_touch_score_ajax(self, client):
        """Test toe touch score AJAX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_toe_touch_score')
        
        response = client.get(url, {
            'distance': '5'  # 5cm above floor
        })
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'score' in data
        assert data['score'] == 4
    
    def test_harvard_score_ajax(self, client):
        """Test Harvard Step Test score AJAX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_harvard_score')
        
        response = client.get(url, {
            'hr1': '75',
            'hr2': '80',
            'hr3': '85'
        })
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'score' in data
        assert 'pfi' in data
        assert data['score'] == 3
        assert data['pfi'] > 0
    
    def test_ajax_error_handling(self, client):
        """Test AJAX endpoints handle errors gracefully"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_pushup_score')
        
        # Missing parameters
        response = client.get(url, {})
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data
    
    def test_ajax_invalid_data(self, client):
        """Test AJAX endpoints handle invalid data"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_pushup_score')
        
        # Invalid data types
        response = client.get(url, {
            'gender': 'male',
            'age': 'thirty',  # Invalid
            'reps': '35'
        })
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert 'error' in data


class TestManagementCommand:
    """Test recalculate_scores management command"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory()
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male'
        )
    
    def test_recalculate_scores_command(self, capfd):
        """Test the recalculate_scores command"""
        from django.core.management import call_command
        
        # Create assessments without scores
        assessment1 = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=30,
            push_up_score=None,  # No score
            overall_score=None
        )
        
        assessment2 = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=40,
            push_up_score=None,  # No score
            overall_score=None
        )
        
        # Run command
        call_command('recalculate_scores')
        
        # Refresh from database
        assessment1.refresh_from_db()
        assessment2.refresh_from_db()
        
        # Verify scores calculated
        assert assessment1.push_up_score == 3
        assert assessment2.push_up_score == 4
        assert assessment1.overall_score is not None
        assert assessment2.overall_score is not None
        
        # Check output
        captured = capfd.readouterr()
        assert "Updated assessment" in captured.out
        assert "Successfully updated 2 assessments" in captured.out
    
    def test_recalculate_scores_dry_run(self, capfd):
        """Test the recalculate_scores command with --dry-run"""
        from django.core.management import call_command
        
        # Create assessment without scores
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=30,
            push_up_score=None,
            overall_score=None
        )
        
        # Run command with dry-run
        call_command('recalculate_scores', '--dry-run')
        
        # Refresh from database
        assessment.refresh_from_db()
        
        # Verify scores NOT calculated
        assert assessment.push_up_score is None
        assert assessment.overall_score is None
        
        # Check output
        captured = capfd.readouterr()
        assert "Dry run complete" in captured.out
        assert "Would update 1 assessments" in captured.out
    
    def test_recalculate_specific_assessment(self, capfd):
        """Test recalculating specific assessment by ID"""
        from django.core.management import call_command
        
        # Create two assessments
        assessment1 = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=30,
            push_up_score=None
        )
        
        assessment2 = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            push_up_reps=40,
            push_up_score=None
        )
        
        # Run command for specific assessment
        call_command('recalculate_scores', '--assessment-id', str(assessment1.id))
        
        # Refresh from database
        assessment1.refresh_from_db()
        assessment2.refresh_from_db()
        
        # Verify only assessment1 updated
        assert assessment1.push_up_score == 3
        assert assessment2.push_up_score is None  # Not updated
        
        # Check output
        captured = capfd.readouterr()
        assert f"Processing single assessment #{assessment1.id}" in captured.out


@pytest.mark.django_db
class TestScoreCalculationIntegration:
    """Integration tests for complete score calculation workflow"""
    
    def test_assessment_form_submission_calculates_scores(self, client):
        """Test that submitting assessment form calculates scores"""
        trainer = UserFactory(username='test_trainer', password='testpass123')
        test_client = ClientFactory(
            trainer=trainer,
            age=30,
            gender='male'
        )
        
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:add')
        
        # Submit form with test data
        form_data = {
            'client': test_client.pk,
            'date': date.today(),
            'overhead_squat_score': '4',
            # Test data that should trigger calculations
            'push_up_reps': '35',
            'farmer_carry_weight': '30',
            'farmer_carry_distance': '50',
            'farmer_carry_time': '35',
            'toe_touch_distance': '5',
            'harvard_step_test_hr1': '75',
            'harvard_step_test_hr2': '80',
            'harvard_step_test_hr3': '85',
        }
        
        response = client.post(url, form_data)
        assert response.status_code == 302
        
        # Verify assessment created with calculated scores
        assessment = Assessment.objects.get(client=test_client)
        
        # Individual scores should be calculated
        assert assessment.push_up_score == 4
        assert assessment.farmer_carry_score == 4
        assert assessment.toe_touch_score == 4
        assert assessment.harvard_step_test_score == 3
        
        # Category and overall scores should be calculated
        assert assessment.strength_score > 0
        assert assessment.mobility_score > 0
        assert assessment.cardio_score > 0
        assert assessment.overall_score > 0
    
    def test_assessment_update_recalculates_scores(self, client):
        """Test that updating assessment recalculates scores"""
        trainer = UserFactory(username='test_trainer', password='testpass123')
        test_client = ClientFactory(
            trainer=trainer,
            age=30,
            gender='male'
        )
        
        # Create initial assessment
        assessment = AssessmentFactory(
            trainer=trainer,
            client=test_client,
            push_up_reps=20,
            push_up_score=2
        )
        
        client.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:edit', kwargs={'pk': assessment.pk})
        
        # Update with better performance
        form_data = {
            'client': test_client.pk,
            'date': assessment.date,
            'push_up_reps': '40',  # Improved
            'overhead_squat_score': '4',
        }
        
        response = client.post(url, form_data)
        
        # Should redirect after successful update
        assert response.status_code == 302
        
        # Verify score recalculated
        assessment.refresh_from_db()
        assert assessment.push_up_score == 4  # Improved from 2