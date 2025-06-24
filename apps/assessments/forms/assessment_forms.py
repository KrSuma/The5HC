from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import Assessment


class AssessmentForm(forms.ModelForm):
    """Main assessment form with all test fields"""
    
    class Meta:
        model = Assessment
        fields = [
            'client', 'date',
            # Test Variations
            'test_environment', 'temperature',
            # Overhead Squat
            'overhead_squat_score', 'overhead_squat_knee_valgus', 'overhead_squat_forward_lean', 
            'overhead_squat_heel_lift', 'overhead_squat_arm_drop', 'overhead_squat_quality', 
            'overhead_squat_notes',
            # Push-up
            'push_up_reps', 'push_up_type', 'push_up_score', 'push_up_notes',
            # Single Leg Balance
            'single_leg_balance_right_eyes_open', 'single_leg_balance_left_eyes_open',
            'single_leg_balance_right_eyes_closed', 'single_leg_balance_left_eyes_closed',
            'single_leg_balance_notes',
            # Toe Touch
            'toe_touch_distance', 'toe_touch_score', 'toe_touch_flexibility', 'toe_touch_notes',
            # Shoulder Mobility
            'shoulder_mobility_right', 'shoulder_mobility_left', 
            'shoulder_mobility_score', 'shoulder_mobility_pain', 'shoulder_mobility_asymmetry',
            'shoulder_mobility_category', 'shoulder_mobility_notes',
            # Farmer's Carry
            'farmer_carry_weight', 'farmer_carry_percentage', 'farmer_carry_distance', 'farmer_carry_time',
            'farmer_carry_score', 'farmer_carry_notes',
            # Harvard Step Test
            'harvard_step_test_hr1', 'harvard_step_test_hr2', 'harvard_step_test_hr3',
            'harvard_step_test_duration', 'harvard_step_test_notes'
        ]
        
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'value': timezone.now().strftime('%Y-%m-%d')
                }
            ),
            'client': forms.HiddenInput(),
            
            # Test Variations
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
            
            # Overhead Squat
            'overhead_squat_score': forms.Select(
                choices=[(None, '선택'), (0, '0 - 통증'), (1, '1 - 불가'), (2, '2 - 보정동작'), (3, '3 - 완벽')],
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'overhead_squat_knee_valgus': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                    'x-model': 'overheadSquatKneeValgus',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'overhead_squat_forward_lean': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                    'x-model': 'overheadSquatForwardLean',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'overhead_squat_heel_lift': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                    'x-model': 'overheadSquatHeelLift',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'overhead_squat_arm_drop': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                    'x-model': 'overheadSquatArmDrop',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'overhead_squat_quality': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'overheadSquatQuality',
                    '@change': 'calculateOverheadSquatScore()'
                }
            ),
            'overhead_squat_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Push-up
            'push_up_reps': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '완료한 개수',
                    'min': 0,
                    'x-model': 'pushUpReps',
                    '@input': 'calculatePushUpScore()'
                }
            ),
            'push_up_type': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'pushUpType',
                    '@change': 'calculatePushUpScore()'
                }
            ),
            'push_up_score': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100',
                    'x-model': 'pushUpScore',
                    'readonly': True
                }
            ),
            'push_up_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Single Leg Balance (all in seconds)
            'single_leg_balance_right_eyes_open': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceRightOpen',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'single_leg_balance_left_eyes_open': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceLeftOpen',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'single_leg_balance_right_eyes_closed': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceRightClosed',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'single_leg_balance_left_eyes_closed': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'min': 0,
                    'max': 120,
                    'x-model': 'balanceLeftClosed',
                    '@input': 'calculateBalanceScore()'
                }
            ),
            'single_leg_balance_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Toe Touch
            'toe_touch_distance': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': 'cm (바닥 위는 +, 아래는 -)',
                    'step': '0.1',
                    'x-model': 'toeTouchDistance',
                    '@input': 'calculateToeTouchScore()'
                }
            ),
            'toe_touch_score': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100',
                    'x-model': 'toeTouchScore',
                    'readonly': True
                }
            ),
            'toe_touch_flexibility': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'toeTouchFlexibility',
                    '@change': 'updateToeTouchScore()'
                }
            ),
            'toe_touch_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Shoulder Mobility
            'shoulder_mobility_right': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': 'cm',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'shoulder_mobility_left': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': 'cm',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'shoulder_mobility_score': forms.Select(
                choices=[(None, '선택'), (0, '0 - 통증'), (1, '1 - 2주먹 이상'), (2, '2 - 1.5주먹'), (3, '3 - 1주먹 이내')],
                attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'shoulder_mobility_pain': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                }
            ),
            'shoulder_mobility_asymmetry': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '좌우 차이 (cm)',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'shoulder_mobility_category': forms.Select(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'x-model': 'shoulderMobilityCategory'
                }
            ),
            'shoulder_mobility_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Farmer's Carry
            'farmer_carry_weight': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': 'kg',
                    'step': '0.5',
                    'min': 0,
                    'x-model': 'farmerWeight',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'farmer_carry_percentage': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '체중 대비 % (선택사항)',
                    'step': '1',
                    'min': 0,
                    'max': 200,
                    'x-model': 'farmerPercentage',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'farmer_carry_distance': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '미터',
                    'step': '0.1',
                    'min': 0,
                    'x-model': 'farmerDistance',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'farmer_carry_time': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'min': 0,
                    'x-model': 'farmerTime',
                    '@input': 'calculateFarmerScore()'
                }
            ),
            'farmer_carry_score': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100',
                    'x-model': 'farmerScore',
                    'readonly': True
                }
            ),
            'farmer_carry_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
            
            # Harvard Step Test
            'harvard_step_test_hr1': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '1-1.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR1',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'harvard_step_test_hr2': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '2-2.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR2',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'harvard_step_test_hr3': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '3-3.5분 후 심박수',
                    'min': 40,
                    'max': 250,
                    'x-model': 'harvardHR3',
                    '@input': 'calculateHarvardScore()'
                }
            ),
            'harvard_step_test_duration': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '초',
                    'step': '0.1',
                    'min': 0
                }
            ),
            'harvard_step_test_notes': forms.Textarea(
                attrs={
                    'rows': 2,
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'placeholder': '추가 메모 (선택사항)'
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to now
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now()
            
        # Set default values for all numeric fields
        defaults = {
            'overhead_squat_score': 2,
            'push_up_reps': 10,
            'push_up_score': 3,
            'single_leg_balance_right_eyes_open': 30,
            'single_leg_balance_left_eyes_open': 30,
            'single_leg_balance_right_eyes_closed': 10,
            'single_leg_balance_left_eyes_closed': 10,
            'toe_touch_distance': 0,
            'toe_touch_score': 3,
            'shoulder_mobility_right': 10,
            'shoulder_mobility_left': 10,
            'shoulder_mobility_score': 3,
            'farmer_carry_weight': 20,
            'farmer_carry_distance': 20,
            'farmer_carry_time': 30,
            'farmer_carry_score': 3,
            'harvard_step_test_hr1': 80,
            'harvard_step_test_hr2': 75,
            'harvard_step_test_hr3': 70,
            'harvard_step_test_duration': 180,
        }
        
        # Apply defaults to initial data only for new instances
        if not self.instance.pk:
            for field_name, default_value in defaults.items():
                if field_name in self.fields and not self.fields[field_name].initial:
                    self.fields[field_name].initial = default_value
            
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now():
            raise ValidationError("평가 날짜는 미래일 수 없습니다.")
        return date


class AssessmentSearchForm(forms.Form):
    """Form for searching and filtering assessments"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '회원 이름으로 검색...',
            'hx-get': '',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML',
            'hx-indicator': '#search-indicator'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    score_range = forms.ChoiceField(
        choices=[
            ('', '전체 점수'),
            ('90-100', '90-100 (매우 우수)'),
            ('80-89', '80-89 (우수)'),
            ('70-79', '70-79 (평균)'),
            ('60-69', '60-69 (주의 필요)'),
            ('0-59', '0-59 (개선 필요)')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    # New filters
    gender = forms.ChoiceField(
        choices=[
            ('', '전체 성별'),
            ('male', '남성'),
            ('female', '여성')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    age_min = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '최소 나이',
            'hx-get': '',
            'hx-trigger': 'change delay:500ms',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    age_max = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '최대 나이',
            'hx-get': '',
            'hx-trigger': 'change delay:500ms',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    bmi_range = forms.ChoiceField(
        choices=[
            ('', '전체 BMI'),
            ('underweight', '저체중 (< 18.5)'),
            ('normal', '정상 (18.5-24.9)'),
            ('overweight', '과체중 (25-29.9)'),
            ('obese', '비만 (≥ 30)')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    risk_range = forms.ChoiceField(
        choices=[
            ('', '전체 위험도'),
            ('0-20', '낮음 (0-20)'),
            ('21-40', '보통 (21-40)'),
            ('41-60', '주의 (41-60)'),
            ('61-80', '높음 (61-80)'),
            ('81-100', '매우 높음 (81-100)')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    # Category-specific score filters
    strength_range = forms.ChoiceField(
        choices=[
            ('', '전체 근력'),
            ('80-100', '우수 (80-100)'),
            ('60-79', '양호 (60-79)'),
            ('40-59', '보통 (40-59)'),
            ('0-39', '개선 필요 (0-39)')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )
    
    mobility_range = forms.ChoiceField(
        choices=[
            ('', '전체 유연성'),
            ('80-100', '우수 (80-100)'),
            ('60-79', '양호 (60-79)'),
            ('40-59', '보통 (40-59)'),
            ('0-39', '개선 필요 (0-39)')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'hx-get': '',
            'hx-trigger': 'change',
            'hx-target': '#assessment-list',
            'hx-swap': 'innerHTML'
        })
    )