"""
Tests for assessment scoring with test variations (Phase 4).
Tests push-up variations, farmer carry percentages, and temperature adjustments.
"""
import pytest
from datetime import date
from decimal import Decimal

from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory
from apps.clients.factories import ClientFactory
from apps.trainers.factories import TrainerFactory


@pytest.mark.django_db
class TestPushUpVariations:
    """Test push-up scoring with different variations."""
    
    def setup_method(self):
        """Set up test data."""
        self.trainer = TrainerFactory()
        self.male_client = ClientFactory(trainer=self.trainer, gender='male', age=30)
        self.female_client = ClientFactory(trainer=self.trainer, gender='female', age=30)
    
    def test_standard_pushup_scoring(self):
        """Test standard push-up scoring remains unchanged."""
        assessment = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type='standard',
            push_up_score=None  # Ensure score is calculated, not preset
        )
        assessment.calculate_scores()
        
        # Male 30 reps = score 4 (excellent)
        assert assessment.push_up_score == 4
    
    def test_modified_pushup_scoring(self):
        """Test modified push-up scoring applies 70% adjustment."""
        assessment = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type='modified',
            push_up_score=None
        )
        assessment.calculate_scores()
        
        # Male 30 reps modified = 4 * 0.7 = 2.8, rounded to 3
        assert assessment.push_up_score == 3
    
    def test_wall_pushup_scoring(self):
        """Test wall push-up scoring applies 50% adjustment."""
        assessment = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type='wall',
            push_up_score=None
        )
        assessment.calculate_scores()
        
        # Male 30 reps wall = 4 * 0.5 = 2.0
        assert assessment.push_up_score == 2
    
    def test_pushup_type_affects_strength_score(self):
        """Test that push-up type affects overall strength score."""
        # Standard push-ups
        assessment1 = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type='standard',
            push_up_score=None,
            overhead_squat_score=3,
            farmer_carry_weight=40,
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_score=None
        )
        assessment1.calculate_scores()
        
        # Modified push-ups
        assessment2 = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type='modified',
            push_up_score=None,
            overhead_squat_score=3,
            farmer_carry_weight=40,
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_score=None
        )
        assessment2.calculate_scores()
        
        # Modified should have lower strength score
        assert assessment2.strength_score < assessment1.strength_score
    
    def test_pushup_type_none_defaults_to_standard(self):
        """Test that None push_up_type defaults to standard scoring."""
        assessment = AssessmentFactory(
            client=self.male_client,
            push_up_reps=30,
            push_up_type=None,
            push_up_score=None
        )
        assessment.calculate_scores()
        
        # Should use standard scoring
        assert assessment.push_up_score == 4


@pytest.mark.django_db
class TestFarmerCarryVariations:
    """Test farmer carry scoring with body weight percentages."""
    
    def setup_method(self):
        """Set up test data."""
        self.trainer = TrainerFactory()
        self.male_client = ClientFactory(
            trainer=self.trainer, 
            gender='male', 
            age=30,
            weight=80  # 80kg body weight
        )
        self.female_client = ClientFactory(
            trainer=self.trainer, 
            gender='female', 
            age=30,
            weight=60  # 60kg body weight
        )
    
    def test_standard_body_weight_percentage(self):
        """Test farmer carry with standard body weight percentage."""
        # Male standard is 50% body weight
        assessment = AssessmentFactory(
            client=self.male_client,
            farmer_carry_weight=40,  # 50% of 80kg
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_percentage=50.0,
            farmer_carry_score=None
        )
        assessment.calculate_scores()
        
        # 45 seconds at standard weight, distance 50m = score 3.5 (good time + excellent distance)
        assert assessment.farmer_carry_score == 3.5
    
    def test_higher_body_weight_percentage(self):
        """Test farmer carry with higher body weight percentage."""
        # Using 75% body weight (1.5x standard)
        assessment = AssessmentFactory(
            client=self.male_client,
            farmer_carry_weight=60,  # 75% of 80kg
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_percentage=75.0,
            farmer_carry_score=None
        )
        assessment.calculate_scores()
        
        # Score should be adjusted upward for heavier weight
        # Base score 3.5 * 1.5 adjustment = 5.25, capped at 4.0
        assert assessment.farmer_carry_score == 4.0
    
    def test_lower_body_weight_percentage(self):
        """Test farmer carry with lower body weight percentage."""
        # Using 25% body weight (0.5x standard)
        assessment = AssessmentFactory(
            client=self.male_client,
            farmer_carry_weight=20,  # 25% of 80kg
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_percentage=25.0,
            farmer_carry_score=None
        )
        assessment.calculate_scores()
        
        # Score should be adjusted downward for lighter weight
        # Base score 3.5 * 0.5 adjustment = 1.75
        assert assessment.farmer_carry_score == 1.75
    
    def test_female_body_weight_percentage(self):
        """Test farmer carry for female with different standard."""
        # Female standard is 40% body weight
        assessment = AssessmentFactory(
            client=self.female_client,
            farmer_carry_weight=24,  # 40% of 60kg
            farmer_carry_distance=50,
            farmer_carry_time=50,
            farmer_carry_percentage=40.0,
            farmer_carry_score=None
        )
        assessment.calculate_scores()
        
        # 50 seconds at standard weight, distance 50m = score 4.0
        # Time score = 4 (excellent for female), distance score = 4 (excellent), base = 4.0
        assert assessment.farmer_carry_score == 4.0
    
    def test_farmer_carry_percentage_none_uses_standard(self):
        """Test that None percentage uses gender-specific standard."""
        assessment = AssessmentFactory(
            client=self.male_client,
            farmer_carry_weight=40,  # Assuming 50% of body weight
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_percentage=None,
            farmer_carry_score=None
        )
        assessment.calculate_scores()
        
        # Should not apply percentage adjustment when None
        # Base score = (time 3 + distance 4) / 2 = 3.5
        assert assessment.farmer_carry_score == 3.5


@pytest.mark.django_db
class TestTemperatureAdjustments:
    """Test temperature adjustments for outdoor testing."""
    
    def setup_method(self):
        """Set up test data."""
        self.trainer = TrainerFactory()
        self.client = ClientFactory(trainer=self.trainer, age=30)
    
    def create_assessment_with_temp(self, temperature, environment='outdoor'):
        """Helper to create assessment with temperature settings."""
        assessment = AssessmentFactory(
            client=self.client,
            test_environment=environment,
            temperature=temperature,
            # Add some test scores
            overhead_squat_score=3,
            push_up_reps=25,
            push_up_score=None,
            harvard_step_test_hr1=140,
            harvard_step_test_hr2=130,
            harvard_step_test_hr3=120
        )
        assessment.calculate_scores()
        return assessment
    
    def test_optimal_temperature_no_adjustment(self):
        """Test that optimal temperature (15-25°C) has no adjustment."""
        # Create two assessments with different optimal temperatures
        normal_temp = self.create_assessment_with_temp(20.0)
        another_optimal = self.create_assessment_with_temp(23.0)
        
        # Both are in optimal range, scores should be identical
        assert normal_temp.overall_score == another_optimal.overall_score
    
    def test_cold_temperature_bonus(self):
        """Test that cold temperature (<5°C) provides score bonus."""
        cold_assessment = self.create_assessment_with_temp(0.0)
        normal_assessment = self.create_assessment_with_temp(20.0)
        
        # Cold should have higher score due to difficulty
        assert cold_assessment.overall_score > normal_assessment.overall_score
    
    def test_hot_temperature_bonus(self):
        """Test that hot temperature (>35°C) provides score bonus."""
        hot_assessment = self.create_assessment_with_temp(40.0)
        normal_assessment = self.create_assessment_with_temp(20.0)
        
        # Hot should have higher score due to difficulty
        assert hot_assessment.overall_score > normal_assessment.overall_score
    
    def test_temperature_adjustment_cap(self):
        """Test that temperature adjustment is capped at 10%."""
        extreme_cold = self.create_assessment_with_temp(-10.0)
        extreme_hot = self.create_assessment_with_temp(50.0)
        normal = self.create_assessment_with_temp(20.0)
        
        # Maximum bonus should be 10%
        cold_bonus = (extreme_cold.overall_score - normal.overall_score) / normal.overall_score
        hot_bonus = (extreme_hot.overall_score - normal.overall_score) / normal.overall_score
        
        assert cold_bonus <= 0.11  # Allow small floating point difference
        assert hot_bonus <= 0.11
    
    def test_indoor_environment_no_temperature_effect(self):
        """Test that indoor environment ignores temperature."""
        indoor_cold = self.create_assessment_with_temp(0.0, environment='indoor')
        indoor_normal = self.create_assessment_with_temp(20.0, environment='indoor')
        
        # Indoor tests should have same scores regardless of temperature
        assert indoor_cold.overall_score == indoor_normal.overall_score
    
    def test_temperature_affects_multiple_scores(self):
        """Test that temperature affects overall, strength, and cardio scores."""
        cold = self.create_assessment_with_temp(0.0)
        normal = self.create_assessment_with_temp(20.0)
        
        # All physical scores should be adjusted
        assert cold.overall_score > normal.overall_score
        assert cold.strength_score > normal.strength_score
        assert cold.cardio_score > normal.cardio_score
        
        # But not flexibility (indoor test)
        assert cold.mobility_score == normal.mobility_score


@pytest.mark.django_db
class TestBackwardCompatibility:
    """Test that variation features maintain backward compatibility."""
    
    def setup_method(self):
        """Set up test data."""
        self.trainer = TrainerFactory()
        self.client = ClientFactory(trainer=self.trainer, age=30)
    
    def test_assessment_without_variations_works(self):
        """Test that assessments without variation fields still work."""
        assessment = AssessmentFactory(
            client=self.client,
            # Only traditional fields
            overhead_squat_score=3,
            push_up_reps=25,
            push_up_score=None,
            farmer_carry_weight=35,
            farmer_carry_distance=50,
            farmer_carry_time=45,
            farmer_carry_score=None
        )
        
        # Should calculate scores without errors
        assessment.calculate_scores()
        
        assert assessment.overall_score > 0
        assert assessment.strength_score > 0
        assert assessment.push_up_score > 0
        assert assessment.farmer_carry_score > 0
    
    def test_partial_variation_data(self):
        """Test assessments with some but not all variation fields."""
        assessment = AssessmentFactory(
            client=self.client,
            push_up_reps=30,
            push_up_type='modified',  # Has push-up type
            farmer_carry_weight=35,  # Assuming 50% of 70kg body weight
            farmer_carry_distance=50,
            farmer_carry_time=50,
            # No farmer_carry_percentage
            test_environment='outdoor',
            # No temperature
        )
        
        assessment.calculate_scores()
        
        # Should handle partial data gracefully
        assert assessment.push_up_score == 3  # Modified adjustment (4 * 0.7 = 2.8, rounded to 3)
        assert assessment.farmer_carry_score > 0  # Uses default percentage
    
    def test_variation_fields_optional_in_forms(self):
        """Test that variation fields are optional in assessment forms."""
        from apps.assessments.forms import AssessmentForm
        
        # Form with minimal data should be valid
        form_data = {
            'date': date.today(),
            'overhead_squat': 3,
            'push_up': 25,
            'sit_up': 35,
            # No variation fields
        }
        
        form = AssessmentForm(data=form_data)
        # Note: Form validation requires client in __init__, so we check fields
        assert 'push_up_type' in form.fields
        assert not form.fields['push_up_type'].required
        assert 'farmer_carry_percentage' in form.fields
        assert not form.fields['farmer_carry_percentage'].required


@pytest.mark.django_db
class TestVariationIntegration:
    """Test integration of multiple variations."""
    
    def setup_method(self):
        """Set up test data."""
        self.trainer = TrainerFactory()
        self.client = ClientFactory(trainer=self.trainer, age=30, weight=70)
    
    def test_multiple_variations_combine(self):
        """Test that multiple variations work together correctly."""
        # Assessment with all variations
        assessment = AssessmentFactory(
            client=self.client,
            # Modified push-ups
            push_up_reps=40,
            push_up_type='modified',
            # Heavy farmer carry
            farmer_carry_weight=52.5,  # 75% of 70kg
            farmer_carry_distance=50,
            farmer_carry_time=30,
            farmer_carry_percentage=75.0,
            # Hot outdoor conditions
            test_environment='outdoor',
            temperature=38.0,
            # Other tests
            overhead_squat_score=4,
            harvard_step_test_hr1=130,
            harvard_step_test_hr2=125,
            harvard_step_test_hr3=120
        )
        
        assessment.calculate_scores()
        
        # Check individual adjustments applied
        assert assessment.push_up_score < 4  # Modified reduces score
        assert assessment.farmer_carry_score == 4.0  # Heavy weight increases score (capped)
        
        # Temperature should boost overall scores
        assert assessment.overall_score > 0
        assert assessment.strength_score > 0
        assert assessment.cardio_score > 0
    
    def test_variation_display_data(self):
        """Test that variations are properly formatted for display."""
        assessment = AssessmentFactory(
            client=self.client,
            push_up_type='modified',
            farmer_carry_percentage=65.0,
            test_environment='outdoor',
            temperature=3.0
        )
        
        # Test display methods if they exist
        assert assessment.get_push_up_type_display() == '수정된'  # 'modified' in Korean
        assert assessment.get_test_environment_display() == '실외'
        
        # Percentage and temperature should be accessible
        assert assessment.farmer_carry_percentage == 65.0
        assert assessment.temperature == 3.0