"""
Tests for movement quality scoring functionality.
Tests the FMS movement quality tracking and scoring algorithms.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date

from .models import Assessment
from .scoring import calculate_overhead_squat_score
from .factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


class TestMovementQualityScoringFunctions(TestCase):
    """Test movement quality scoring functions"""
    
    def test_overhead_squat_perfect_form(self):
        """Test overhead squat with no compensations"""
        score = calculate_overhead_squat_score(
            knee_valgus=False,
            forward_lean=False,
            heel_lift=False,
            pain=False
        )
        self.assertEqual(score, 3)  # Perfect form
    
    def test_overhead_squat_one_compensation(self):
        """Test overhead squat with one compensation"""
        # Test knee valgus only
        score = calculate_overhead_squat_score(
            knee_valgus=True,
            forward_lean=False,
            heel_lift=False,
            pain=False
        )
        self.assertEqual(score, 2)  # Minor compensations
        
        # Test forward lean only
        score = calculate_overhead_squat_score(
            knee_valgus=False,
            forward_lean=True,
            heel_lift=False,
            pain=False
        )
        self.assertEqual(score, 2)  # Minor compensations
        
        # Test heel lift only
        score = calculate_overhead_squat_score(
            knee_valgus=False,
            forward_lean=False,
            heel_lift=True,
            pain=False
        )
        self.assertEqual(score, 2)  # Minor compensations
    
    def test_overhead_squat_two_compensations(self):
        """Test overhead squat with two compensations"""
        score = calculate_overhead_squat_score(
            knee_valgus=True,
            forward_lean=True,
            heel_lift=False,
            pain=False
        )
        self.assertEqual(score, 1)  # Major compensations
        
        score = calculate_overhead_squat_score(
            knee_valgus=True,
            forward_lean=False,
            heel_lift=True,
            pain=False
        )
        self.assertEqual(score, 1)  # Major compensations
    
    def test_overhead_squat_all_compensations(self):
        """Test overhead squat with all compensations"""
        score = calculate_overhead_squat_score(
            knee_valgus=True,
            forward_lean=True,
            heel_lift=True,
            pain=False
        )
        self.assertEqual(score, 1)  # Major compensations
    
    def test_overhead_squat_with_pain(self):
        """Test overhead squat with pain"""
        # Pain always results in score 0
        score = calculate_overhead_squat_score(
            knee_valgus=False,
            forward_lean=False,
            heel_lift=False,
            pain=True
        )
        self.assertEqual(score, 0)
        
        # Even with no other compensations
        score = calculate_overhead_squat_score(
            knee_valgus=True,
            forward_lean=True,
            heel_lift=True,
            pain=True
        )
        self.assertEqual(score, 0)
    
    def test_overhead_squat_backward_compatibility(self):
        """Test backward compatibility with form_quality parameter"""
        # Test with form_quality parameter (old method)
        score = calculate_overhead_squat_score(form_quality=3)
        self.assertEqual(score, 3)
        
        score = calculate_overhead_squat_score(form_quality=2)
        self.assertEqual(score, 2)
        
        score = calculate_overhead_squat_score(form_quality=1)
        self.assertEqual(score, 1)
        
        score = calculate_overhead_squat_score(form_quality=0)
        self.assertEqual(score, 0)
        
        # Test boundary values
        score = calculate_overhead_squat_score(form_quality=5)  # Above max
        self.assertEqual(score, 3)  # Clamped to max
        
        score = calculate_overhead_squat_score(form_quality=-1)  # Below min
        self.assertEqual(score, 0)  # Clamped to min


@pytest.mark.django_db
class TestAssessmentMovementQualityIntegration:
    """Test Assessment model integration with movement quality fields"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(username='test_trainer')
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male'
        )
    
    def test_assessment_calculate_scores_with_movement_quality(self):
        """Test calculate_scores uses movement quality data"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Movement quality data
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=False,
            overhead_squat_heel_lift=False,
            overhead_squat_score=None  # Should be calculated
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Verify overhead squat score calculated from movement quality
        assert assessment.overhead_squat_score == 2  # One compensation
    
    def test_assessment_preserves_manual_scores(self):
        """Test that manually set scores are preserved"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Movement quality data that would give score 2
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=False,
            overhead_squat_heel_lift=False,
            overhead_squat_score=3  # Manually set to 3
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Manual score should be preserved
        assert assessment.overhead_squat_score == 3  # Not recalculated
    
    def test_assessment_multiple_compensations(self):
        """Test assessment with multiple movement compensations"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Multiple compensations
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=True,
            overhead_squat_heel_lift=True,
            overhead_squat_score=None
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Should get low score due to multiple compensations
        assert assessment.overhead_squat_score == 1  # Major compensations
    
    def test_assessment_perfect_movement_quality(self):
        """Test assessment with perfect movement quality"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # No compensations
            overhead_squat_knee_valgus=False,
            overhead_squat_forward_lean=False,
            overhead_squat_heel_lift=False,
            overhead_squat_score=None
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Should get perfect score
        assert assessment.overhead_squat_score == 3  # Perfect form
    
    def test_movement_quality_field_defaults(self):
        """Test movement quality fields have correct defaults"""
        assessment = Assessment()
        
        # Boolean fields should default to False
        assert assessment.overhead_squat_knee_valgus is False
        assert assessment.overhead_squat_forward_lean is False
        assert assessment.overhead_squat_heel_lift is False
        assert assessment.shoulder_mobility_pain is False
        
        # Float field should be None
        assert assessment.shoulder_mobility_asymmetry is None


@pytest.mark.django_db
class TestBackwardCompatibility:
    """Test backward compatibility with existing assessments"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(username='test_trainer')
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male'
        )
    
    def test_existing_assessment_without_movement_quality(self):
        """Test that existing assessments work without movement quality data"""
        # Create assessment as if it existed before migration
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            date=date.today(),
            overhead_squat_score=2,  # Existing manual score
            push_up_reps=30
        )
        
        # Calculate scores should work without errors
        assessment.calculate_scores()
        assessment.save()
        
        # Existing score should be preserved
        assert assessment.overhead_squat_score == 2
        
        # Movement quality fields should have defaults
        assert assessment.overhead_squat_knee_valgus is False
        assert assessment.overhead_squat_forward_lean is False
        assert assessment.overhead_squat_heel_lift is False
    
    def test_migration_preserves_existing_scores(self):
        """Test that migration doesn't affect existing scores"""
        # Create assessment with manual score
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            overhead_squat_score=2,
            shoulder_mobility_score=3
        )
        
        # After migration, scores should be unchanged
        assessment.refresh_from_db()
        assert assessment.overhead_squat_score == 2
        assert assessment.shoulder_mobility_score == 3
    
    def test_mixed_manual_and_calculated_scores(self):
        """Test mixing manual scores with calculated scores"""
        assessment = AssessmentFactory(
            trainer=self.trainer,
            client=self.client,
            # Manual score for shoulder mobility
            shoulder_mobility_score=3,
            # Movement quality data for overhead squat
            overhead_squat_knee_valgus=True,
            overhead_squat_forward_lean=True,
            overhead_squat_heel_lift=False,
            overhead_squat_score=None,  # Should be calculated
            # Other test data
            push_up_reps=30,
            push_up_score=None  # Should be calculated
        )
        
        # Calculate scores
        assessment.calculate_scores()
        assessment.save()
        
        # Manual score preserved
        assert assessment.shoulder_mobility_score == 3
        
        # Calculated scores
        assert assessment.overhead_squat_score == 1  # Two compensations
        assert assessment.push_up_score == 3  # Based on reps


class TestMovementQualityFormIntegration(TestCase):
    """Test movement quality fields in forms"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(username='test_trainer')
        self.client = ClientFactory(
            trainer=self.trainer,
            age=30,
            gender='male'
        )
    
    def test_form_includes_movement_quality_fields(self):
        """Test that AssessmentForm includes movement quality fields"""
        from .forms import AssessmentForm
        
        form = AssessmentForm()
        
        # Check overhead squat movement quality fields
        self.assertIn('overhead_squat_knee_valgus', form.fields)
        self.assertIn('overhead_squat_forward_lean', form.fields)
        self.assertIn('overhead_squat_heel_lift', form.fields)
        
        # Check shoulder mobility movement quality fields
        self.assertIn('shoulder_mobility_pain', form.fields)
        self.assertIn('shoulder_mobility_asymmetry', form.fields)
    
    def test_form_movement_quality_widgets(self):
        """Test that movement quality fields have correct widgets"""
        from .forms import AssessmentForm
        from django import forms
        
        form = AssessmentForm()
        
        # Boolean fields should have CheckboxInput widgets
        self.assertIsInstance(
            form.fields['overhead_squat_knee_valgus'].widget,
            forms.CheckboxInput
        )
        self.assertIsInstance(
            form.fields['overhead_squat_forward_lean'].widget,
            forms.CheckboxInput
        )
        self.assertIsInstance(
            form.fields['overhead_squat_heel_lift'].widget,
            forms.CheckboxInput
        )
        self.assertIsInstance(
            form.fields['shoulder_mobility_pain'].widget,
            forms.CheckboxInput
        )
        
        # Float field should have NumberInput widget
        self.assertIsInstance(
            form.fields['shoulder_mobility_asymmetry'].widget,
            forms.NumberInput
        )