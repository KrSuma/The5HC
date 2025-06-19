import pytest
from django.urls import reverse
from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory, ClientFactory
from apps.accounts.factories import UserFactory

@pytest.mark.django_db
class TestMovementQualityEnhancements:
    """Test the new movement quality assessment fields"""
    
    def test_new_fields_exist_in_model(self):
        """Test that new fields are available in the Assessment model"""
        assessment = AssessmentFactory()
        
        # Test overhead squat fields
        assert hasattr(assessment, 'overhead_squat_arm_drop')
        assert hasattr(assessment, 'overhead_squat_quality')
        
        # Test toe touch field
        assert hasattr(assessment, 'toe_touch_flexibility')
        
        # Test shoulder mobility field
        assert hasattr(assessment, 'shoulder_mobility_category')
    
    def test_overhead_squat_quality_choices(self):
        """Test overhead squat quality field choices"""
        assessment = AssessmentFactory(
            overhead_squat_quality='pain'
        )
        assert assessment.get_overhead_squat_quality_display() == '동작 중 통증 발생'
        
        assessment.overhead_squat_quality = 'perfect'
        assessment.save()
        assert assessment.get_overhead_squat_quality_display() == '완벽한 동작'
    
    def test_toe_touch_flexibility_choices(self):
        """Test toe touch flexibility field choices"""
        assessment = AssessmentFactory(
            toe_touch_flexibility='palm_full'
        )
        assert assessment.get_toe_touch_flexibility_display() == '손바닥이 발에 완전히 닿음'
        
        assessment.toe_touch_flexibility = 'no_reach'
        assessment.save()
        assert assessment.get_toe_touch_flexibility_display() == '손끝이 발에 닿지 않음'
    
    def test_shoulder_mobility_category_choices(self):
        """Test shoulder mobility category field choices"""
        assessment = AssessmentFactory(
            shoulder_mobility_category='under_1x'
        )
        assert assessment.get_shoulder_mobility_category_display() == '손 간 거리가 신장 1배 미만'
        
    def test_form_includes_new_fields(self):
        """Test that the assessment form includes new fields"""
        from apps.assessments.forms import AssessmentForm
        form = AssessmentForm()
        
        # Check fields are in the form
        assert 'overhead_squat_arm_drop' in form.fields
        assert 'overhead_squat_quality' in form.fields
        assert 'toe_touch_flexibility' in form.fields
        assert 'shoulder_mobility_category' in form.fields
    
    def test_assessment_with_all_new_fields(self):
        """Test creating an assessment with all new fields populated"""
        client = ClientFactory()
        assessment = Assessment.objects.create(
            client=client,
            date='2025-06-19',
            # New fields
            overhead_squat_arm_drop=True,
            overhead_squat_quality='compensations',
            toe_touch_flexibility='fingertips',
            shoulder_mobility_category='1_to_1_5x'
        )
        
        assert assessment.overhead_squat_arm_drop is True
        assert assessment.overhead_squat_quality == 'compensations'
        assert assessment.toe_touch_flexibility == 'fingertips'
        assert assessment.shoulder_mobility_category == '1_to_1_5x'