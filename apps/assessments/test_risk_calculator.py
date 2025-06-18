"""
Tests for injury risk calculation functionality.
Tests the risk scoring algorithms and risk factor identification.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
import json

from .models import Assessment
from .risk_calculator import calculate_injury_risk, interpret_risk_score, _get_primary_concerns
from .factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


class TestRiskCalculationFunctions(TestCase):
    """Test risk calculation functions"""
    
    def test_calculate_injury_risk_low_risk(self):
        """Test risk calculation for a healthy individual with good scores"""
        assessment_data = {
            'strength_score': 85,
            'mobility_score': 80,
            'balance_score': 82,
            'cardio_score': 78,
            'overall_score': 81,
            'overhead_squat_score': 3,
            'push_up_score': 3,
            'toe_touch_score': 3,
            'shoulder_mobility_score': 3,
            'overhead_squat_knee_valgus': False,
            'overhead_squat_forward_lean': False,
            'overhead_squat_heel_lift': False,
            'shoulder_mobility_pain': False,
            'shoulder_mobility_asymmetry': 0.5,
            'single_leg_balance_right_eyes_open': 30,
            'single_leg_balance_left_eyes_open': 28,
            'single_leg_balance_right_eyes_closed': 15,
            'single_leg_balance_left_eyes_closed': 14,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should have low risk
        self.assertLess(risk_score, 20)
        self.assertEqual(risk_factors['overall_risk_level'], 'low')
        self.assertEqual(len(risk_factors['summary']['primary_concerns']), 0)
    
    def test_calculate_injury_risk_moderate_risk(self):
        """Test risk calculation for someone with moderate imbalances"""
        assessment_data = {
            'strength_score': 70,
            'mobility_score': 45,  # Significant imbalance
            'balance_score': 68,
            'cardio_score': 72,
            'overall_score': 64,
            'overhead_squat_score': 2,
            'push_up_score': 2,
            'toe_touch_score': 1,  # Poor mobility
            'shoulder_mobility_score': 2,
            'overhead_squat_knee_valgus': True,  # One compensation
            'overhead_squat_forward_lean': False,
            'overhead_squat_heel_lift': False,
            'shoulder_mobility_pain': False,
            'shoulder_mobility_asymmetry': 3,  # Moderate asymmetry
            'single_leg_balance_right_eyes_open': 20,
            'single_leg_balance_left_eyes_open': 12,  # Asymmetry
            'single_leg_balance_right_eyes_closed': 8,
            'single_leg_balance_left_eyes_closed': 5,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should have moderate risk
        self.assertGreaterEqual(risk_score, 20)
        self.assertLess(risk_score, 70)
        self.assertIn(risk_factors['overall_risk_level'], ['low-moderate', 'moderate'])
        self.assertGreater(len(risk_factors['summary']['primary_concerns']), 0)
        
        # Check specific risk factors identified
        self.assertIn('mobility', risk_factors['category_imbalance'])
        self.assertGreater(len(risk_factors['poor_mobility']), 0)
    
    def test_calculate_injury_risk_high_risk(self):
        """Test risk calculation for high-risk individual"""
        assessment_data = {
            'strength_score': 25,  # Very poor
            'mobility_score': 20,  # Very poor
            'balance_score': 15,  # Very poor
            'cardio_score': 60,   # Major imbalance
            'overall_score': 30,
            'overhead_squat_score': 0,  # Severe limitation
            'push_up_score': 1,
            'toe_touch_score': 0,  # Severe limitation
            'shoulder_mobility_score': 1,
            'overhead_squat_knee_valgus': True,   # Multiple compensations
            'overhead_squat_forward_lean': True,
            'overhead_squat_heel_lift': True,
            'shoulder_mobility_pain': True,  # Pain present
            'shoulder_mobility_asymmetry': 8,  # Large asymmetry
            'single_leg_balance_right_eyes_open': 5,   # Very poor
            'single_leg_balance_left_eyes_open': 15,   # Large asymmetry
            'single_leg_balance_right_eyes_closed': 2,
            'single_leg_balance_left_eyes_closed': 1,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should have high risk
        self.assertGreaterEqual(risk_score, 70)
        self.assertEqual(risk_factors['overall_risk_level'], 'high')
        self.assertEqual(len(risk_factors['summary']['primary_concerns']), 3)  # Max 3 concerns
        
        # Multiple risk factors should be present
        self.assertGreater(len(risk_factors['category_imbalance']), 0)
        self.assertGreater(len(risk_factors['bilateral_asymmetry']), 0)
        self.assertGreater(len(risk_factors['poor_mobility']), 0)
        self.assertGreater(len(risk_factors['poor_balance']), 0)
        self.assertIn('overhead_squat', risk_factors['movement_compensations'])
    
    def test_category_imbalance_detection(self):
        """Test detection of category imbalances"""
        assessment_data = {
            'strength_score': 90,  # Very high
            'mobility_score': 40,  # Low - major imbalance
            'balance_score': 85,
            'cardio_score': 82,
            'overall_score': 74,
            # Other fields with defaults
            'overhead_squat_score': 3,
            'push_up_score': 3,
            'toe_touch_score': 2,
            'shoulder_mobility_score': 2,
            'single_leg_balance_right_eyes_open': 30,
            'single_leg_balance_left_eyes_open': 30,
            'single_leg_balance_right_eyes_closed': 15,
            'single_leg_balance_left_eyes_closed': 15,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should detect mobility imbalance
        self.assertIn('mobility', risk_factors['category_imbalance'])
        mobility_imbalance = risk_factors['category_imbalance']['mobility']
        self.assertEqual(mobility_imbalance['score'], 40)
        self.assertGreater(mobility_imbalance['deviation'], 20)
    
    def test_bilateral_asymmetry_detection(self):
        """Test detection of bilateral asymmetries"""
        assessment_data = {
            'strength_score': 70,
            'mobility_score': 70,
            'balance_score': 70,
            'cardio_score': 70,
            'overall_score': 70,
            'overhead_squat_score': 2,
            'push_up_score': 2,
            'toe_touch_score': 2,
            'shoulder_mobility_score': 2,
            'shoulder_mobility_asymmetry': 6,  # Significant asymmetry
            'single_leg_balance_right_eyes_open': 30,
            'single_leg_balance_left_eyes_open': 10,  # 66% difference
            'single_leg_balance_right_eyes_closed': 15,
            'single_leg_balance_left_eyes_closed': 5,   # 66% difference
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should detect multiple asymmetries
        self.assertIn('shoulder_mobility', risk_factors['bilateral_asymmetry'])
        self.assertIn('balance_eyes_open', risk_factors['bilateral_asymmetry'])
        self.assertIn('balance_eyes_closed', risk_factors['bilateral_asymmetry'])
        
        # Check asymmetry percentages
        balance_open = risk_factors['bilateral_asymmetry']['balance_eyes_open']
        self.assertGreater(balance_open['asymmetry_percentage'], 50)
    
    def test_movement_compensation_risk(self):
        """Test risk calculation for movement compensations"""
        # No compensations
        assessment_data_good = {
            'strength_score': 70,
            'mobility_score': 70,
            'balance_score': 70,
            'cardio_score': 70,
            'overall_score': 70,
            'overhead_squat_score': 3,
            'overhead_squat_knee_valgus': False,
            'overhead_squat_forward_lean': False,
            'overhead_squat_heel_lift': False,
            'shoulder_mobility_pain': False,
            'single_leg_balance_right_eyes_open': 20,
            'single_leg_balance_left_eyes_open': 20,
        }
        
        risk_score_good, risk_factors_good = calculate_injury_risk(assessment_data_good)
        
        # Multiple compensations
        assessment_data_bad = assessment_data_good.copy()
        assessment_data_bad.update({
            'overhead_squat_knee_valgus': True,
            'overhead_squat_forward_lean': True,
            'overhead_squat_heel_lift': True,
            'shoulder_mobility_pain': True,
        })
        
        risk_score_bad, risk_factors_bad = calculate_injury_risk(assessment_data_bad)
        
        # Risk should be higher with compensations
        self.assertGreater(risk_score_bad, risk_score_good)
        self.assertIn('overhead_squat', risk_factors_bad['movement_compensations'])
        self.assertEqual(len(risk_factors_bad['movement_compensations']['overhead_squat']), 3)
    
    def test_interpret_risk_score(self):
        """Test risk score interpretation function"""
        # Test all risk levels
        low_risk = interpret_risk_score(10)
        self.assertEqual(low_risk['level'], 'Low Risk')
        self.assertEqual(low_risk['color'], 'green')
        self.assertIn('Minimal injury risk', low_risk['interpretation'])
        
        low_mod_risk = interpret_risk_score(25)
        self.assertEqual(low_mod_risk['level'], 'Low-Moderate Risk')
        self.assertEqual(low_mod_risk['color'], 'yellow')
        
        mod_risk = interpret_risk_score(50)
        self.assertEqual(mod_risk['level'], 'Moderate Risk')
        self.assertEqual(mod_risk['color'], 'orange')
        
        high_risk = interpret_risk_score(80)
        self.assertEqual(high_risk['level'], 'High Risk')
        self.assertEqual(high_risk['color'], 'red')
        self.assertIn('Significant injury risk', high_risk['interpretation'])
    
    def test_get_primary_concerns(self):
        """Test extraction of primary concerns from risk factors"""
        risk_factors = {
            'category_imbalance': {
                'strength': {'deviation': 25, 'percentage': 50}
            },
            'bilateral_asymmetry': {
                'shoulder_mobility': {'difference_cm': 5},
                'balance_eyes_open': {'asymmetry_percentage': 45}
            },
            'movement_compensations': {
                'overhead_squat': ['knee valgus', 'forward lean'],
                'count': 2
            },
            'poor_mobility': [
                {'test': 'toe_touch', 'score': 0}
            ]
        }
        
        concerns = _get_primary_concerns(risk_factors)
        
        # Should return top 3 concerns
        self.assertLessEqual(len(concerns), 3)
        self.assertGreater(len(concerns), 0)
        
        # Should include formatted concern strings
        self.assertTrue(any('strength imbalance' in c for c in concerns))
        self.assertTrue(any('Shoulder mobility asymmetry' in c for c in concerns))


@pytest.mark.django_db
class TestAssessmentRiskIntegration:
    """Test Assessment model integration with risk calculations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(username='test_trainer')
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male'
        )
    
    def test_assessment_calculates_risk_score(self):
        """Test that risk score is calculated when assessment is saved"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Good overall scores
            overhead_squat_score=3,
            push_up_score=3,
            toe_touch_score=3,
            shoulder_mobility_score=3,
            farmer_carry_score=3,
            # Balance data
            single_leg_balance_right_eyes_open=30,
            single_leg_balance_left_eyes_open=28,
            single_leg_balance_right_eyes_closed=15,
            single_leg_balance_left_eyes_closed=14,
            # No movement compensations
            overhead_squat_knee_valgus=False,
            overhead_squat_forward_lean=False,
            overhead_squat_heel_lift=False,
            shoulder_mobility_pain=False,
            shoulder_mobility_asymmetry=1.0
        )
        
        # Force calculation
        assessment.calculate_scores()
        assessment.save()
        
        # Risk score should be calculated
        assert assessment.injury_risk_score is not None
        assert assessment.injury_risk_score < 20  # Low risk
        assert assessment.risk_factors is not None
        assert isinstance(assessment.risk_factors, dict)
        assert assessment.risk_factors['overall_risk_level'] == 'low'
    
    def test_assessment_high_risk_calculation(self):
        """Test risk calculation for high-risk assessment"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Poor scores
            overhead_squat_score=1,
            push_up_score=1,
            toe_touch_score=0,
            shoulder_mobility_score=1,
            farmer_carry_score=1,
            # Poor balance with asymmetry
            single_leg_balance_right_eyes_open=5,
            single_leg_balance_left_eyes_open=20,
            single_leg_balance_right_eyes_closed=2,
            single_leg_balance_left_eyes_closed=8,
            # Multiple compensations
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=True,
            overhead_squat_heel_lift=True,
            shoulder_mobility_pain=True,
            shoulder_mobility_asymmetry=7.0
        )
        
        # Force calculation
        assessment.calculate_scores()
        assessment.save()
        
        # Should have high risk
        assert assessment.injury_risk_score > 40
        assert assessment.risk_factors['overall_risk_level'] in ['moderate', 'high']
        assert len(assessment.risk_factors['summary']['primary_concerns']) > 0
    
    def test_risk_calculation_with_missing_data(self):
        """Test risk calculation handles missing data gracefully"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Minimal data
            overhead_squat_score=2,
            push_up_score=None,
            toe_touch_score=None,
            shoulder_mobility_score=2,
            farmer_carry_score=None,
            # No balance data
            single_leg_balance_right_eyes_open=None,
            single_leg_balance_left_eyes_open=None,
            single_leg_balance_right_eyes_closed=None,
            single_leg_balance_left_eyes_closed=None,
        )
        
        # Should still calculate without errors
        assessment.calculate_scores()
        assessment.save()
        
        # Risk score should be calculated
        assert assessment.injury_risk_score is not None
        assert assessment.risk_factors is not None
    
    def test_risk_factors_json_field(self):
        """Test that risk_factors are properly stored as JSON"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=True,
            shoulder_mobility_asymmetry=5.0,
            single_leg_balance_right_eyes_open=10,
            single_leg_balance_left_eyes_open=25,
        )
        
        assessment.calculate_scores()
        assessment.save()
        
        # Refresh from database
        assessment.refresh_from_db()
        
        # Risk factors should be accessible as dict
        assert isinstance(assessment.risk_factors, dict)
        assert 'summary' in assessment.risk_factors
        assert 'overall_risk_level' in assessment.risk_factors
        
        # Should be able to serialize back to JSON
        json_str = json.dumps(assessment.risk_factors)
        assert len(json_str) > 0
    
    def test_existing_assessments_without_risk_fields(self):
        """Test that existing assessments work without risk fields"""
        # Create assessment without calling calculate_scores
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            date=date.today(),
            overhead_squat_score=2,
            push_up_reps=30
        )
        
        # Should have null risk fields
        assert assessment.injury_risk_score is None
        assert assessment.risk_factors is None
        
        # Calculate scores should add risk data
        assessment.calculate_scores()
        assessment.save()
        
        assert assessment.injury_risk_score is not None
        assert assessment.risk_factors is not None


class TestRiskCalculatorEdgeCases(TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_zero_scores_handling(self):
        """Test handling of zero scores"""
        assessment_data = {
            'strength_score': 0,
            'mobility_score': 0,
            'balance_score': 0,
            'cardio_score': 0,
            'overall_score': 0,
            'overhead_squat_score': 0,
            'push_up_score': 0,
            'single_leg_balance_right_eyes_open': 0,
            'single_leg_balance_left_eyes_open': 0,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should handle zeros without errors
        self.assertIsInstance(risk_score, float)
        self.assertIsInstance(risk_factors, dict)
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)
    
    def test_perfect_scores_handling(self):
        """Test handling of perfect scores"""
        assessment_data = {
            'strength_score': 100,
            'mobility_score': 100,
            'balance_score': 100,
            'cardio_score': 100,
            'overall_score': 100,
            'overhead_squat_score': 3,
            'push_up_score': 3,
            'toe_touch_score': 3,
            'shoulder_mobility_score': 3,
            'overhead_squat_knee_valgus': False,
            'overhead_squat_forward_lean': False,
            'overhead_squat_heel_lift': False,
            'shoulder_mobility_pain': False,
            'shoulder_mobility_asymmetry': 0,
            'single_leg_balance_right_eyes_open': 60,
            'single_leg_balance_left_eyes_open': 60,
            'single_leg_balance_right_eyes_closed': 30,
            'single_leg_balance_left_eyes_closed': 30,
        }
        
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        # Should have very low risk
        self.assertEqual(risk_score, 0)
        self.assertEqual(risk_factors['overall_risk_level'], 'low')
        self.assertEqual(len(risk_factors['summary']['primary_concerns']), 0)
    
    def test_none_values_handling(self):
        """Test handling of None values in assessment data"""
        assessment_data = {
            'strength_score': None,
            'mobility_score': 70,
            'balance_score': None,
            'cardio_score': 75,
            'overall_score': 72,
            'overhead_squat_score': None,
            'push_up_score': 2,
            'toe_touch_score': None,
            'shoulder_mobility_score': 2,
            'overhead_squat_knee_valgus': None,
            'overhead_squat_forward_lean': False,
            'overhead_squat_heel_lift': None,
            'shoulder_mobility_pain': False,
            'shoulder_mobility_asymmetry': None,
            'single_leg_balance_right_eyes_open': None,
            'single_leg_balance_left_eyes_open': 20,
            'single_leg_balance_right_eyes_closed': None,
            'single_leg_balance_left_eyes_closed': None,
        }
        
        # Should handle None values without errors
        risk_score, risk_factors = calculate_injury_risk(assessment_data)
        
        self.assertIsInstance(risk_score, float)
        self.assertIsInstance(risk_factors, dict)
        self.assertIn('overall_risk_level', risk_factors)