"""
Refactored assessment forms that work with the new model structure.

These forms leverage the individual test models created in the Assessment refactoring
to provide better organization, validation, and user experience.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import formset_factory

from ..models import (
    Assessment, OverheadSquatTest, PushUpTest, SingleLegBalanceTest,
    ToeTouchTest, ShoulderMobilityTest, FarmersCarryTest, HarvardStepTest,
    ManualScoreOverride
)
from ..services import AssessmentService


class BaseTestForm(forms.ModelForm):
    """Base form for individual test forms with common functionality."""
    
    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop('assessment', None)
        super().__init__(*args, **kwargs)
        
        # Add common CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.Textarea)):
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                })


class OverheadSquatTestForm(BaseTestForm):
    """Form for Overhead Squat Test data."""
    
    class Meta:
        model = OverheadSquatTest
        fields = [
            'score', 'notes', 'knee_valgus', 'forward_lean', 
            'heel_lift', 'arm_drop', 'quality', 'score_manual_override'
        ]
        
        widgets = {
            'score': forms.Select(
                choices=[(None, '선택'), (0, '0 - 통증'), (1, '1 - 불가'), (2, '2 - 보상동작'), (3, '3 - 완벽')],
                attrs={
                    'x-model': 'overheadSquatScore',
                    '@change': 'onManualScoreChange("overheadSquat", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.overheadSquat}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.overheadSquat'}
            ),
            'knee_valgus': forms.CheckboxInput(
                attrs={
                    'x-model': 'overheadSquatKneeValgus',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'forward_lean': forms.CheckboxInput(
                attrs={
                    'x-model': 'overheadSquatForwardLean',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'heel_lift': forms.CheckboxInput(
                attrs={
                    'x-model': 'overheadSquatHeelLift',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'arm_drop': forms.CheckboxInput(
                attrs={
                    'x-model': 'overheadSquatArmDrop',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'quality': forms.Select(
                attrs={
                    'x-model': 'overheadSquatQuality',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class PushUpTestForm(BaseTestForm):
    """Form for Push-up Test data."""
    
    class Meta:
        model = PushUpTest
        fields = ['reps', 'score', 'notes', 'push_up_type', 'score_manual_override']
        
        widgets = {
            'reps': forms.NumberInput(
                attrs={
                    'placeholder': '완료한 개수',
                    'min': 0,
                    'x-model': 'pushUpReps',
                    '@input': 'calculatePushUpScore()'
                }
            ),
            'push_up_type': forms.Select(
                attrs={
                    'x-model': 'pushUpType',
                    '@change': 'calculatePushUpScore()'
                }
            ),
            'score': forms.Select(
                choices=[(None, '자동 계산'), (1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')],
                attrs={
                    'x-model': 'pushUpScore',
                    '@change': 'onManualScoreChange("pushUp", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.pushUp}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.pushUp'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class SingleLegBalanceTestForm(BaseTestForm):
    """Form for Single Leg Balance Test data."""
    
    class Meta:
        model = SingleLegBalanceTest
        fields = [
            'right_eyes_open', 'left_eyes_open', 'right_eyes_closed', 'left_eyes_closed',
            'notes', 'score_manual', 'score_manual_override'
        ]
        
        widgets = {
            'right_eyes_open': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceRightOpen',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'left_eyes_open': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceLeftOpen',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'right_eyes_closed': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceRightClosed',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'left_eyes_closed': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceLeftClosed',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'score_manual': forms.Select(
                choices=[(None, '자동 계산'), (1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')],
                attrs={
                    'x-model': 'balanceScore',
                    '@change': 'onManualScoreChange("balance", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.balance}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.balance'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class ToeTouchTestForm(BaseTestForm):
    """Form for Toe Touch Test data."""
    
    class Meta:
        model = ToeTouchTest
        fields = ['distance', 'score', 'flexibility', 'notes', 'score_manual_override']
        
        widgets = {
            'distance': forms.NumberInput(
                attrs={
                    'placeholder': 'cm (바닥 위는 +, 아래는 -)',
                    'step': '0.1',
                    'x-model': 'toeTouchDistance',
                    '@input': 'calculateToeTouchScore()'
                }
            ),
            'score': forms.Select(
                choices=[(None, '자동 계산'), (1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')],
                attrs={
                    'x-model': 'toeTouchScore',
                    '@change': 'onManualScoreChange("toeTouch", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.toeTouch}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.toeTouch'}
            ),
            'flexibility': forms.Select(
                attrs={
                    'x-model': 'toeTouchFlexibility',
                    '@change': 'updateToeTouchScore()'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class ShoulderMobilityTestForm(BaseTestForm):
    """Form for Shoulder Mobility Test data."""
    
    class Meta:
        model = ShoulderMobilityTest
        fields = [
            'right', 'left', 'score', 'notes', 'pain', 
            'asymmetry', 'category', 'score_manual_override'
        ]
        
        widgets = {
            'right': forms.NumberInput(
                attrs={
                    'placeholder': 'cm',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'left': forms.NumberInput(
                attrs={
                    'placeholder': 'cm',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'score': forms.Select(
                choices=[(None, '선택'), (0, '0 - 통증'), (1, '1 - 2주먹 이상'), (2, '2 - 1.5주먹'), (3, '3 - 1주먹 이내')],
                attrs={
                    'x-model': 'shoulderMobilityScore',
                    '@change': 'onManualScoreChange("shoulderMobility", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.shoulderMobility}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.shoulderMobility'}
            ),
            'asymmetry': forms.NumberInput(
                attrs={
                    'placeholder': '좌우 차이 (cm)',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'category': forms.Select(
                attrs={'x-model': 'shoulderMobilityCategory'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class FarmersCarryTestForm(BaseTestForm):
    """Form for Farmer's Carry Test data."""
    
    class Meta:
        model = FarmersCarryTest
        fields = [
            'weight', 'percentage', 'distance', 'time',
            'score', 'notes', 'score_manual_override'
        ]
        
        widgets = {
            'weight': forms.NumberInput(
                attrs={
                    'placeholder': 'kg',
                    'step': '0.5',
                    'min': 0,
                    'x-model': 'farmerWeight',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'percentage': forms.NumberInput(
                attrs={
                    'placeholder': '체중 대비 % (선택사항)',
                    'step': '1',
                    'min': 0,
                    'max': 200,
                    'x-model': 'farmerPercentage',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'distance': forms.NumberInput(
                attrs={
                    'placeholder': '미터',
                    'step': '0.1',
                    'min': 0,
                    'x-model': 'farmerDistance',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'time': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'min': 0,
                    'x-model': 'farmerTime',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'score': forms.Select(
                choices=[(None, '자동 계산'), (1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')],
                attrs={
                    'x-model': 'farmerScore',
                    '@change': 'onManualScoreChange("farmerCarry", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.farmerCarry}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.farmerCarry'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class HarvardStepTestForm(BaseTestForm):
    """Form for Harvard Step Test data."""
    
    class Meta:
        model = HarvardStepTest
        fields = [
            'hr1', 'hr2', 'hr3', 'duration', 'notes',
            'score_manual', 'score_manual_override'
        ]
        
        widgets = {
            'hr1': forms.NumberInput(
                attrs={
                    'placeholder': '1-1.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR1',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'hr2': forms.NumberInput(
                attrs={
                    'placeholder': '2-2.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR2',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'hr3': forms.NumberInput(
                attrs={
                    'placeholder': '3-3.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR3',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'duration': forms.NumberInput(
                attrs={
                    'placeholder': '초',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'score_manual': forms.Select(
                choices=[(None, '자동 계산'), (1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')],
                attrs={
                    'x-model': 'harvardScore',
                    '@change': 'onManualScoreChange("harvard", $event.target.value)',
                    ':class': "{'ring-2 ring-blue-500': manualOverrides.harvard}"
                }
            ),
            'score_manual_override': forms.HiddenInput(
                attrs={'x-model': 'manualOverrides.harvard'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }


class RefactoredAssessmentForm(forms.ModelForm):
    """
    Main assessment form that coordinates with individual test forms.
    Simplified to focus on core assessment data while test data is handled by individual forms.
    """
    
    class Meta:
        model = Assessment
        fields = ['client', 'date', 'test_environment', 'temperature']
        
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'value': timezone.now().strftime('%Y-%m-%d')
                }
            ),
            'client': forms.HiddenInput(),
            'test_environment': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'testEnvironment',
                    '@change': 'updateTemperatureVisibility()'
                }
            ),
            'temperature': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '온도 (°C)',
                    'step': '0.1',
                    'min': -10,
                    'max': 50,
                    'x-show': "testEnvironment === 'outdoor'",
                    'x-transition': True
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now()
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now():
            raise ValidationError("평가 날짜는 미래일 수 없습니다.")
        return date


class AssessmentWithTestsForm:
    """
    Composite form that manages the main assessment and all test forms together.
    This provides a clean interface for views to work with the complete assessment.
    """
    
    def __init__(self, data=None, files=None, instance=None, user=None):
        self.user = user
        self.instance = instance
        self.data = data
        self.files = files
        
        # Initialize main assessment form
        self.assessment_form = RefactoredAssessmentForm(
            data=data, files=files, instance=instance
        )
        
        # Initialize test forms
        self.test_forms = {
            'overhead_squat': OverheadSquatTestForm(
                data=data, files=files, 
                instance=getattr(instance, 'overhead_squat_test', None) if instance else None,
                assessment=instance, prefix='overhead_squat'
            ),
            'push_up': PushUpTestForm(
                data=data, files=files,
                instance=getattr(instance, 'push_up_test', None) if instance else None,
                assessment=instance, prefix='push_up'
            ),
            'balance': SingleLegBalanceTestForm(
                data=data, files=files,
                instance=getattr(instance, 'single_leg_balance_test', None) if instance else None,
                assessment=instance, prefix='balance'
            ),
            'toe_touch': ToeTouchTestForm(
                data=data, files=files,
                instance=getattr(instance, 'toe_touch_test', None) if instance else None,
                assessment=instance, prefix='toe_touch'
            ),
            'shoulder_mobility': ShoulderMobilityTestForm(
                data=data, files=files,
                instance=getattr(instance, 'shoulder_mobility_test', None) if instance else None,
                assessment=instance, prefix='shoulder_mobility'
            ),
            'farmers_carry': FarmersCarryTestForm(
                data=data, files=files,
                instance=getattr(instance, 'farmers_carry_test', None) if instance else None,
                assessment=instance, prefix='farmers_carry'
            ),
            'harvard_step': HarvardStepTestForm(
                data=data, files=files,
                instance=getattr(instance, 'harvard_step_test', None) if instance else None,
                assessment=instance, prefix='harvard_step'
            ),
        }
    
    def is_valid(self):
        """Check if all forms are valid."""
        valid = self.assessment_form.is_valid()
        for form in self.test_forms.values():
            if not form.is_valid():
                valid = False
        return valid
    
    def save(self, commit=True):
        """Save the assessment and all test data using AssessmentService."""
        if not self.is_valid():
            raise ValueError("Forms are not valid")
        
        if commit:
            # Use AssessmentService for creation/updates
            service = AssessmentService(user=self.user)
            
            # Prepare data for the service
            assessment_data = self.assessment_form.cleaned_data.copy()
            
            # Add test data from individual forms
            for test_type, form in self.test_forms.items():
                if form.cleaned_data:
                    # Prefix test data to avoid conflicts
                    for field, value in form.cleaned_data.items():
                        assessment_data[f"{test_type}_{field}"] = value
            
            if self.instance and self.instance.pk:
                # Update existing assessment
                for field, value in assessment_data.items():
                    if hasattr(self.instance, field):
                        setattr(self.instance, field, value)
                
                # Use service to recalculate scores
                service.calculate_assessment_scores(self.instance)
                return self.instance
            else:
                # Create new assessment
                assessment, success = service.create_assessment(assessment_data)
                if success:
                    return assessment
                else:
                    raise ValueError(f"Assessment creation failed: {service.errors}")
        
        return None
    
    @property
    def errors(self):
        """Collect all form errors."""
        errors = {}
        if self.assessment_form.errors:
            errors['assessment'] = self.assessment_form.errors
        
        for test_type, form in self.test_forms.items():
            if form.errors:
                errors[test_type] = form.errors
        
        return errors
    
    def get_test_form(self, test_type):
        """Get a specific test form."""
        return self.test_forms.get(test_type)
    
    def get_all_forms(self):
        """Get all forms as a dictionary."""
        return {
            'assessment': self.assessment_form,
            **self.test_forms
        }