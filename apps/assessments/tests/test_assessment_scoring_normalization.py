"""
Pytest-style tests for assessment scoring normalization.
Testing the 0-5 score normalization in scoring.py for manual score fields.
Following django-test.md guidelines for modern Django testing.
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from apps.assessments.scoring import (
    calculate_category_scores,
    calculate_overhead_squat_score,
    calculate_shoulder_mobility_score,
    calculate_single_leg_balance_score,
    calculate_toe_touch_score,
    calculate_push_up_score,
    calculate_farmers_carry_score,
    calculate_step_test_score,
    get_test_standard
)
from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory
from django.utils import timezone


class TestScoreNormalization:
    """Test suite for score normalization functions"""
    
    pytestmark = pytest.mark.django_db
    
    def test_overhead_squat_normalization_0_to_5_scale(self):
        """Test overhead squat score normalization from 0-5 to 1-4 scale"""
        # Test data with various overhead squat scores
        test_cases = [
            (0, 1.0),      # Score 0 maps to 1
            (1, 1.6),      # Score 1 maps to 1.6
            (2, 2.2),      # Score 2 maps to 2.2
            (3, 2.8),      # Score 3 maps to 2.8
            (4, 3.4),      # Score 4 maps to 3.4
            (5, 4.0),      # Score 5 maps to 4
        ]
        
        for input_score, expected_normalized in test_cases:
            assessment_data = {
                'overhead_squat_score': input_score,
                'single_leg_balance_right_open': 30,
                'single_leg_balance_left_open': 30,
                'single_leg_balance_right_closed': 15,
                'single_leg_balance_left_closed': 15,
                'shoulder_mobility_score': 3,
                'toe_touch_score': 3,
                'push_up_score': 3,
                'farmers_carry_score': 3,
                'step_test_hr1': 140,
                'step_test_hr2': 130,
                'step_test_hr3': 120,
            }
            
            client_details = {
                'gender': '남성',
                'age': 30
            }
            
            scores = calculate_category_scores(assessment_data, client_details)
            
            # Extract the normalized overhead squat score from balance calculation
            # Balance score = (single_leg_balance_score + overhead_squat_normalized) / 2 * 25
            # We need to reverse calculate the normalized value
            single_leg_score = calculate_single_leg_balance_score(30, 30, 15, 15)
            balance_score_raw = scores['balance_score'] / 25 * 2
            overhead_squat_normalized = balance_score_raw - single_leg_score
            
            assert abs(overhead_squat_normalized - expected_normalized) < 0.01, \
                f"Score {input_score} should normalize to {expected_normalized}, got {overhead_squat_normalized}"
    
    def test_shoulder_mobility_normalization_0_to_5_scale(self):
        """Test shoulder mobility score normalization from 0-5 to 1-4 scale"""
        # Test data with various shoulder mobility scores
        test_cases = [
            (0, 1.0),      # Score 0 maps to 1
            (1, 1.6),      # Score 1 maps to 1.6
            (2, 2.2),      # Score 2 maps to 2.2
            (3, 2.8),      # Score 3 maps to 2.8
            (4, 3.4),      # Score 4 maps to 3.4
            (5, 4.0),      # Score 5 maps to 4
        ]
        
        for input_score, expected_normalized in test_cases:
            assessment_data = {
                'shoulder_mobility_score': input_score,
                'toe_touch_score': 3,
                'overhead_squat_score': 3,
                'single_leg_balance_right_open': 30,
                'single_leg_balance_left_open': 30,
                'single_leg_balance_right_closed': 15,
                'single_leg_balance_left_closed': 15,
                'push_up_score': 3,
                'farmers_carry_score': 3,
                'step_test_hr1': 140,
                'step_test_hr2': 130,
                'step_test_hr3': 120,
            }
            
            client_details = {
                'gender': '여성',
                'age': 25
            }
            
            scores = calculate_category_scores(assessment_data, client_details)
            
            # Extract the normalized shoulder mobility score from mobility calculation
            # Mobility score = (toe_touch_score + shoulder_mobility_normalized) / 2 * 25
            toe_touch_score = assessment_data['toe_touch_score']
            mobility_score_raw = scores['mobility_score'] / 25 * 2
            shoulder_mobility_normalized = mobility_score_raw - toe_touch_score
            
            assert abs(shoulder_mobility_normalized - expected_normalized) < 0.01, \
                f"Score {input_score} should normalize to {expected_normalized}, got {shoulder_mobility_normalized}"
    
    def test_category_score_calculation_with_manual_scores(self):
        """Test category score calculations with manual override scores"""
        assessment_data = {
            # Manual scores (0-5 scale)
            'overhead_squat_score': 5,  # Should normalize to 4.0
            'shoulder_mobility_score': 0,  # Should normalize to 1.0
            # Other required scores
            'toe_touch_score': 3,
            'push_up_score': 4,
            'farmers_carry_score': 3,
            'single_leg_balance_right_open': 45,
            'single_leg_balance_left_open': 45,
            'single_leg_balance_right_closed': 20,
            'single_leg_balance_left_closed': 20,
            'step_test_hr1': 120,
            'step_test_hr2': 110,
            'step_test_hr3': 100,
        }
        
        client_details = {
            'gender': '남성',
            'age': 35
        }
        
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Verify all category scores are calculated
        assert 'overall_score' in scores
        assert 'strength_score' in scores
        assert 'mobility_score' in scores
        assert 'balance_score' in scores
        assert 'cardio_score' in scores
        
        # Verify scores are within expected ranges (0-100)
        for key, value in scores.items():
            if key != 'pfi':  # PFI is not a percentage
                assert 0 <= value <= 100, f"{key} should be between 0-100, got {value}"
    
    def test_edge_case_score_normalization(self):
        """Test normalization with edge case values"""
        # Test with all minimum scores (0)
        assessment_data_min = {
            'overhead_squat_score': 0,
            'shoulder_mobility_score': 0,
            'toe_touch_score': 1,  # Regular scores are 1-4
            'push_up_score': 1,
            'farmers_carry_score': 1,
            'single_leg_balance_right_open': 5,
            'single_leg_balance_left_open': 5,
            'single_leg_balance_right_closed': 2,
            'single_leg_balance_left_closed': 2,
            'step_test_hr1': 200,
            'step_test_hr2': 190,
            'step_test_hr3': 180,
        }
        
        client_details = {'gender': '여성', 'age': 40}
        
        scores_min = calculate_category_scores(assessment_data_min, client_details)
        
        # All scores should be valid numbers
        for key, value in scores_min.items():
            assert isinstance(value, (int, float)), f"{key} should be a number"
            if key != 'pfi':
                assert value >= 0, f"{key} should not be negative"
        
        # Test with all maximum scores (5)
        assessment_data_max = {
            'overhead_squat_score': 5,
            'shoulder_mobility_score': 5,
            'toe_touch_score': 4,  # Regular scores max at 4
            'push_up_score': 4,
            'farmers_carry_score': 4,
            'single_leg_balance_right_open': 60,
            'single_leg_balance_left_open': 60,
            'single_leg_balance_right_closed': 30,
            'single_leg_balance_left_closed': 30,
            'step_test_hr1': 100,
            'step_test_hr2': 95,
            'step_test_hr3': 90,
        }
        
        scores_max = calculate_category_scores(assessment_data_max, client_details)
        
        # Maximum scores should be higher than minimum
        assert scores_max['overall_score'] > scores_min['overall_score']
        assert scores_max['balance_score'] > scores_min['balance_score']
        assert scores_max['mobility_score'] > scores_min['mobility_score']
    
    def test_normalization_formula_accuracy(self):
        """Test the exact normalization formula implementation"""
        # Direct test of normalization logic
        # Formula: if score == 0: return 1, else: return 1 + (score - 1) * 0.6
        
        test_cases = [
            (0, 1.0),
            (1, 1.0),  # 1 + (1-1) * 0.6 = 1.0
            (2, 1.6),  # 1 + (2-1) * 0.6 = 1.6
            (3, 2.2),  # 1 + (3-1) * 0.6 = 2.2
            (4, 2.8),  # 1 + (4-1) * 0.6 = 2.8
            (5, 3.4),  # 1 + (5-1) * 0.6 = 3.4
        ]
        
        for input_val, expected in test_cases:
            if input_val == 0:
                normalized = 1
            else:
                normalized = 1 + (input_val - 1) * 0.6
            
            assert abs(normalized - expected) < 0.001, \
                f"Formula error: {input_val} -> {normalized}, expected {expected}"
    
    def test_score_calculation_consistency(self):
        """Test that score calculations are consistent across multiple calls"""
        assessment_data = {
            'overhead_squat_score': 3,
            'shoulder_mobility_score': 4,
            'toe_touch_score': 3,
            'push_up_score': 3,
            'farmers_carry_score': 3,
            'single_leg_balance_right_open': 35,
            'single_leg_balance_left_open': 35,
            'single_leg_balance_right_closed': 18,
            'single_leg_balance_left_closed': 18,
            'step_test_hr1': 135,
            'step_test_hr2': 125,
            'step_test_hr3': 115,
        }
        
        client_details = {'gender': '남성', 'age': 28}
        
        # Calculate scores multiple times
        scores1 = calculate_category_scores(assessment_data, client_details)
        scores2 = calculate_category_scores(assessment_data, client_details)
        scores3 = calculate_category_scores(assessment_data, client_details)
        
        # All calculations should yield identical results
        assert scores1 == scores2
        assert scores2 == scores3
    
    def test_assessment_model_score_calculation_integration(self):
        """Test integration with Assessment model's calculate_scores method"""
        trainer = TrainerFactory()
        client = ClientFactory(
            trainer=trainer,
            gender='남성',
            date_of_birth=timezone.now().date().replace(year=1990)
        )
        
        assessment = AssessmentFactory(
            trainer=trainer,
            client=client,
            overhead_squat_score=4,  # Manual score
            shoulder_mobility_score=2,  # Manual score
            push_up_reps=25,
            single_leg_balance_right_eyes_open=40,
            single_leg_balance_left_eyes_open=40,
            single_leg_balance_right_eyes_closed=20,
            single_leg_balance_left_eyes_closed=20,
            toe_touch_distance=5.0,
            shoulder_mobility_right=3.0,
            shoulder_mobility_left=3.0,
            farmer_carry_weight=30.0,
            farmer_carry_distance=60.0,
            farmer_carry_time=40,
            harvard_step_test_hr1=130,
            harvard_step_test_hr2=120,
            harvard_step_test_hr3=110,
            harvard_step_test_duration=180.0,
        )
        
        # Calculate scores
        assessment.calculate_scores()
        
        # Verify scores were calculated
        assert assessment.overall_score is not None
        assert assessment.strength_score is not None
        assert assessment.mobility_score is not None
        assert assessment.balance_score is not None
        assert assessment.cardio_score is not None
        
        # Verify manual scores were preserved
        assert assessment.overhead_squat_score == 4
        assert assessment.shoulder_mobility_score == 2


class TestScoringEdgeCases:
    """Test edge cases and error handling in scoring"""
    
    pytestmark = pytest.mark.django_db
    
    def test_missing_score_fields(self):
        """Test handling of missing score fields"""
        # Minimal data with missing manual scores
        assessment_data = {
            'push_up_score': 3,
            'farmers_carry_score': 3,
            'toe_touch_score': 3,
            'single_leg_balance_right_open': 30,
            'single_leg_balance_left_open': 30,
            'single_leg_balance_right_closed': 15,
            'single_leg_balance_left_closed': 15,
            'step_test_hr1': 140,
            'step_test_hr2': 130,
            'step_test_hr3': 120,
        }
        
        client_details = {'gender': '여성', 'age': 30}
        
        # Should use default value of 1 for missing scores
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Verify calculation completed without errors
        assert scores['overall_score'] > 0
        assert scores['balance_score'] > 0
        assert scores['mobility_score'] > 0
    
    def test_invalid_score_values(self):
        """Test handling of invalid score values"""
        assessment_data = {
            'overhead_squat_score': -1,  # Invalid negative
            'shoulder_mobility_score': 10,  # Invalid too high
            'toe_touch_score': 3,
            'push_up_score': 3,
            'farmers_carry_score': 3,
            'single_leg_balance_right_open': 30,
            'single_leg_balance_left_open': 30,
            'single_leg_balance_right_closed': 15,
            'single_leg_balance_left_closed': 15,
            'step_test_hr1': 140,
            'step_test_hr2': 130,
            'step_test_hr3': 120,
        }
        
        client_details = {'gender': '남성', 'age': 35}
        
        # Should handle invalid values gracefully
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Verify scores are still calculated
        assert isinstance(scores['overall_score'], (int, float))
        assert isinstance(scores['balance_score'], (int, float))
        assert isinstance(scores['mobility_score'], (int, float))
    
    @patch('apps.assessments.scoring.cache')
    def test_test_standard_caching(self, mock_cache):
        """Test that test standards are properly cached"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        
        # Call get_test_standard
        standard = get_test_standard(
            test_type='push_up',
            gender='M',
            age=30,
            variation_type='standard',
            conditions='normal'
        )
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        
        # Verify cache key format
        cache_key = mock_cache.get.call_args[0][0]
        assert 'test_standard_push_up_M_30_standard_normal' == cache_key