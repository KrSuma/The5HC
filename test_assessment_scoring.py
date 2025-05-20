# test_assessment_scoring.py - Unit tests for assessment scoring functions

import unittest
from improved_assessment_scoring import (
    calculate_pushup_score, calculate_single_leg_balance_score,
    calculate_toe_touch_score, calculate_shoulder_mobility_score,
    calculate_farmers_carry_score, calculate_step_test_score,
    calculate_category_scores, get_score_description
)


class TestAssessmentScoring(unittest.TestCase):
    """Test cases for assessment scoring functions"""
    
    def test_pushup_score_male_under30(self):
        """Test push-up scoring for males under 30"""
        self.assertEqual(calculate_pushup_score('Male', 25, 40), 4)  # Excellent
        self.assertEqual(calculate_pushup_score('Male', 25, 30), 3)  # Good
        self.assertEqual(calculate_pushup_score('Male', 25, 25), 2)  # Average
        self.assertEqual(calculate_pushup_score('Male', 25, 15), 1)  # Needs improvement
    
    def test_pushup_score_female_under30(self):
        """Test push-up scoring for females under 30"""
        self.assertEqual(calculate_pushup_score('Female', 25, 35), 4)  # Excellent
        self.assertEqual(calculate_pushup_score('Female', 25, 25), 3)  # Good
        self.assertEqual(calculate_pushup_score('Female', 25, 18), 2)  # Average
        self.assertEqual(calculate_pushup_score('Female', 25, 10), 1)  # Needs improvement
    
    def test_pushup_score_male_over50(self):
        """Test push-up scoring for males over 50"""
        self.assertEqual(calculate_pushup_score('Male', 55, 25), 4)  # Excellent
        self.assertEqual(calculate_pushup_score('Male', 55, 18), 3)  # Good
        self.assertEqual(calculate_pushup_score('Male', 55, 12), 2)  # Average
        self.assertEqual(calculate_pushup_score('Male', 55, 5), 1)   # Needs improvement
    
    def test_pushup_score_female_over50(self):
        """Test push-up scoring for females over 50"""
        self.assertEqual(calculate_pushup_score('Female', 55, 25), 4)  # Excellent
        self.assertEqual(calculate_pushup_score('Female', 55, 15), 3)  # Good
        self.assertEqual(calculate_pushup_score('Female', 55, 10), 2)  # Average
        self.assertEqual(calculate_pushup_score('Female', 55, 5), 1)   # Needs improvement
    
    def test_pushup_score_korean_gender(self):
        """Test push-up scoring with Korean gender text"""
        self.assertEqual(calculate_pushup_score('남성', 25, 40), 4)  # Male, Excellent
        self.assertEqual(calculate_pushup_score('여성', 25, 35), 4)  # Female, Excellent
    
    def test_pushup_score_input_validation(self):
        """Test push-up scoring input validation"""
        self.assertEqual(calculate_pushup_score('Male', -5, 30), 3)  # Age bounded to 0
        self.assertEqual(calculate_pushup_score('Male', 200, 30), 3)  # Age bounded to 120
        self.assertEqual(calculate_pushup_score('Male', 25, -10), 1)  # Reps bounded to 0
    
    def test_single_leg_balance_score(self):
        """Test single leg balance scoring"""
        # Excellent scores (4.0)
        self.assertAlmostEqual(
            calculate_single_leg_balance_score(50, 50, 35, 35),
            4.0
        )
        
        # Good scores (3.0-3.6)
        self.assertGreaterEqual(
            calculate_single_leg_balance_score(35, 35, 25, 25),
            3.0
        )
        
        # Average scores (2.0-2.6)
        self.assertGreaterEqual(
            calculate_single_leg_balance_score(20, 20, 15, 15),
            2.0
        )
        
        # Poor scores (1.0-1.6)
        self.assertGreaterEqual(
            calculate_single_leg_balance_score(10, 10, 5, 5),
            1.0
        )
        
        # Test asymmetry handling - should get average of both sides
        balance_score = calculate_single_leg_balance_score(50, 10, 35, 5)
        self.assertGreaterEqual(balance_score, 1.0)
        self.assertLessEqual(balance_score, 4.0)
    
    def test_toe_touch_score(self):
        """Test toe touch scoring"""
        self.assertEqual(calculate_toe_touch_score(10), 4)   # +10cm (past floor)
        self.assertEqual(calculate_toe_touch_score(3), 3)    # +3cm (touching floor)
        self.assertEqual(calculate_toe_touch_score(-5), 2)   # -5cm (ankle level)
        self.assertEqual(calculate_toe_touch_score(-15), 1)  # -15cm (above ankle)
    
    def test_shoulder_mobility_score(self):
        """Test shoulder mobility scoring"""
        self.assertEqual(calculate_shoulder_mobility_score(3), 3)  # Excellent
        self.assertEqual(calculate_shoulder_mobility_score(2), 2)  # Good
        self.assertEqual(calculate_shoulder_mobility_score(1), 1)  # Average
        self.assertEqual(calculate_shoulder_mobility_score(0), 0)  # Pain
        
        # Test input validation
        self.assertEqual(calculate_shoulder_mobility_score(5), 3)  # Values > 3 should be bounded to 3
        self.assertEqual(calculate_shoulder_mobility_score(-1), 0)  # Values < 0 should be bounded to 0
    
    def test_farmers_carry_score(self):
        """Test farmers carry scoring"""
        # Test distance-based scoring
        self.assertEqual(calculate_farmers_carry_score('Male', 20, 35, 60), 4.0)  # Excellent distance, excellent time
        self.assertEqual(calculate_farmers_carry_score('Male', 20, 25, 50), 3.5)  # Good distance, excellent time
        self.assertEqual(calculate_farmers_carry_score('Male', 20, 15, 40), 2.5)  # Average distance, good time
        self.assertEqual(calculate_farmers_carry_score('Male', 20, 5, 20), 1.0)   # Poor distance, poor time
        
        # Test gender differences
        male_score = calculate_farmers_carry_score('Male', 20, 20, 40)
        female_score = calculate_farmers_carry_score('Female', 20, 20, 40)
        self.assertGreater(female_score, male_score)  # Females should score higher for same time
    
    def test_step_test_score(self):
        """Test Harvard Step Test scoring"""
        # Excellent PFI (>90)
        score, pfi = calculate_step_test_score(70, 65, 60)
        self.assertEqual(score, 4)
        self.assertGreater(pfi, 90)
        
        # Good PFI (80-90)
        score, pfi = calculate_step_test_score(80, 75, 70)
        self.assertEqual(score, 3)
        self.assertGreaterEqual(pfi, 80)
        self.assertLess(pfi, 90)
        
        # Average PFI (65-80)
        score, pfi = calculate_step_test_score(90, 85, 80)
        self.assertEqual(score, 2)
        self.assertGreaterEqual(pfi, 65)
        self.assertLess(pfi, 80)
        
        # Poor PFI (<65)
        score, pfi = calculate_step_test_score(110, 105, 100)
        self.assertEqual(score, 1)
        self.assertLess(pfi, 65)
    
    def test_category_scores(self):
        """Test category scores calculation"""
        # Create mock assessment data
        assessment_data = {
            'push_up_score': 3,
            'push_up_reps': 30,
            'farmers_carry_score': 3,
            'toe_touch_score': 3,
            'toe_touch_distance': 0,
            'shoulder_mobility_score': 2,
            'overhead_squat_score': 2,
            'single_leg_balance_right_open': 30,
            'single_leg_balance_left_open': 30,
            'single_leg_balance_right_closed': 20,
            'single_leg_balance_left_closed': 20,
            'step_test_hr1': 80,
            'step_test_hr2': 75,
            'step_test_hr3': 70,
            'step_test_score': 3,
        }
        
        # Create mock client details
        client_details = {
            'gender': 'Male',
            'age': 30
        }
        
        # Calculate category scores
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Check basic structure
        self.assertIn('overall_score', scores)
        self.assertIn('strength_score', scores)
        self.assertIn('mobility_score', scores)
        self.assertIn('balance_score', scores)
        self.assertIn('cardio_score', scores)
        
        # Check ranges
        self.assertGreaterEqual(scores['overall_score'], 0)
        self.assertLessEqual(scores['overall_score'], 100)
        
        self.assertGreaterEqual(scores['strength_score'], 0)
        self.assertLessEqual(scores['strength_score'], 25)
        
        self.assertGreaterEqual(scores['mobility_score'], 0)
        self.assertLessEqual(scores['mobility_score'], 25)
        
        self.assertGreaterEqual(scores['balance_score'], 0)
        self.assertLessEqual(scores['balance_score'], 25)
        
        self.assertGreaterEqual(scores['cardio_score'], 0)
        self.assertLessEqual(scores['cardio_score'], 25)
        
        # Check that overall score is weighted sum of category scores
        expected_overall = (
            scores['strength_score'] * 0.3 + 
            scores['mobility_score'] * 0.25 + 
            scores['balance_score'] * 0.25 + 
            scores['cardio_score'] * 0.2
        )
        self.assertAlmostEqual(scores['overall_score'], expected_overall, places=1)
    
    def test_get_score_description(self):
        """Test score description conversion"""
        self.assertEqual(get_score_description(95), "매우 우수")
        self.assertEqual(get_score_description(85), "우수")
        self.assertEqual(get_score_description(75), "보통")
        self.assertEqual(get_score_description(65), "주의 필요")
        self.assertEqual(get_score_description(55), "개선 필요")
        
        # Test with different max_score
        self.assertEqual(get_score_description(9, 10), "매우 우수")
        self.assertEqual(get_score_description(3, 4), "우수")
        
        # Test input validation
        self.assertEqual(get_score_description(-10), "개선 필요")
        self.assertEqual(get_score_description(110), "매우 우수")


if __name__ == '__main__':
    unittest.main()
