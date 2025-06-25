import pytest
from apps.assessments.models import Assessment
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory, OrganizationFactory


@pytest.mark.django_db
class TestManualScoreOverride:
    """Test manual score override functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client = ClientFactory(trainer=self.trainer, gender='male', age=30)
        
    def test_manual_override_fields_exist(self):
        """Test that all manual override fields are present in the model"""
        assessment = Assessment(
            client=self.client,
            trainer=self.trainer,
            date='2025-06-25'
        )
        
        # Check individual test score override fields
        assert hasattr(assessment, 'overhead_squat_score_manual_override')
        assert hasattr(assessment, 'push_up_score_manual_override')
        assert hasattr(assessment, 'toe_touch_score_manual_override')
        assert hasattr(assessment, 'shoulder_mobility_score_manual_override')
        assert hasattr(assessment, 'farmer_carry_score_manual_override')
        assert hasattr(assessment, 'single_leg_balance_score_manual_override')
        assert hasattr(assessment, 'harvard_step_test_score_manual_override')
        
        # Check manual score fields for tests without dedicated score fields
        assert hasattr(assessment, 'single_leg_balance_score_manual')
        assert hasattr(assessment, 'harvard_step_test_score_manual')
        
        # Check category score override fields
        assert hasattr(assessment, 'overall_score_manual_override')
        assert hasattr(assessment, 'strength_score_manual_override')
        assert hasattr(assessment, 'mobility_score_manual_override')
        assert hasattr(assessment, 'balance_score_manual_override')
        assert hasattr(assessment, 'cardio_score_manual_override')
        
    def test_automatic_calculation_respects_manual_override(self):
        """Test that automatic calculation skips manually overridden scores"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer,
            date='2025-06-25',
            # Set test data
            push_up_reps=20,
            push_up_score=5,  # Manually set high score
            push_up_score_manual_override=True,  # Mark as manually overridden
            # Other test data
            toe_touch_distance=-10,  # Would normally calculate to a lower score
            toe_touch_score=5,  # Manually set high score
            toe_touch_score_manual_override=True
        )
        
        # Run calculate_scores
        assessment.calculate_scores()
        assessment.save()
        
        # Check that manual scores were preserved
        assert assessment.push_up_score == 5  # Should not be recalculated
        assert assessment.toe_touch_score == 5  # Should not be recalculated
        
    def test_manual_override_false_allows_calculation(self):
        """Test that scores are calculated when manual override is false"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer,
            date='2025-06-25',
            # Set test data
            push_up_reps=20,
            push_up_score_manual_override=False,  # Not manually overridden
            toe_touch_distance=5,  # Positive distance
            toe_touch_score_manual_override=False
        )
        
        # Run calculate_scores
        assessment.calculate_scores()
        assessment.save()
        
        # Check that scores were calculated
        assert assessment.push_up_score is not None
        assert assessment.toe_touch_score is not None
        
    def test_balance_and_harvard_manual_scores(self):
        """Test manual score fields for balance and Harvard tests"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer,
            date='2025-06-25',
            # Set manual scores
            single_leg_balance_score_manual=4,
            single_leg_balance_score_manual_override=True,
            harvard_step_test_score_manual=5,
            harvard_step_test_score_manual_override=True,
            # Set test data that would normally calculate differently
            single_leg_balance_right_eyes_open=10,
            single_leg_balance_left_eyes_open=10,
            single_leg_balance_right_eyes_closed=5,
            single_leg_balance_left_eyes_closed=5,
            harvard_step_test_hr1=100,
            harvard_step_test_hr2=95,
            harvard_step_test_hr3=90
        )
        
        # Run calculate_scores
        assessment.calculate_scores()
        assessment.save()
        
        # Check that manual scores were preserved
        assert assessment.single_leg_balance_score_manual == 4
        assert assessment.harvard_step_test_score_manual == 5
        
    def test_category_score_manual_override(self):
        """Test that category scores can be manually overridden"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer,
            date='2025-06-25',
            # Set category scores manually
            overall_score=95.0,
            overall_score_manual_override=True,
            strength_score=90.0,
            strength_score_manual_override=True,
            # Provide minimal test data
            push_up_reps=10,
            push_up_score=2
        )
        
        # Run calculate_scores
        assessment.calculate_scores()
        assessment.save()
        
        # Check that manual category scores were preserved
        assert assessment.overall_score == 95.0
        assert assessment.strength_score == 90.0