# Movement Quality Assessment Enhancement - Implementation Plan

## Overview
Add detailed movement quality assessments to the main physical assessment form as trainer fact-checking tools (addendum notes) for better client evaluation.

## Requirements to Implement

### 1. Overhead Squat Enhancements
- **Current**: Score (0-5) + 3 compensation checkboxes
- **Add**: 
  - "팔 전방 하강" (Arms fall forward) checkbox
  - Performance quality radio selection:
    - "동작 중 통증 발생" (Pain during movement)
    - "깊은 스쿼트 수행 불가능" (Cannot perform deep squat)
    - "보상 동작 관찰됨" (Compensations observed)
    - "완벽한 동작" (Perfect execution)

### 2. Toe Touch Test Enhancements
- **Current**: Distance measurement + score
- **Add**: Flexibility level selection:
  - "손끝이 발에 닿지 않음" (Fingertips don't reach feet)
  - "손끝이 발에 닿음" (Fingertips touch feet)
  - "손바닥이 발등을 덮음" (Palms cover top of feet)
  - "손바닥이 발에 완전히 닿음" (Palms fully touch feet)

### 3. Shoulder Mobility Enhancements
- **Current**: Left/right measurements + score + pain checkbox
- **Add**: Distance category relative to height:
  - "동작 중 통증" (Pain during movement)
  - "손 간 거리가 신장 1.5배 이상" (Hand distance > 1.5x height)
  - "손 간 거리가 신장 1~1.5배" (Hand distance 1-1.5x height)
  - "손 간 거리가 신장 1배 미만" (Hand distance < 1x height)

## Implementation Steps

### Step 1: Database Model Updates
**File**: `apps/assessments/models.py`

Add new fields to the Assessment model:

```python
# Overhead Squat Additional Fields
overhead_squat_arm_drop = models.BooleanField(
    default=False, blank=True,
    verbose_name="팔 전방 하강",
    help_text="Arms fall forward during movement"
)

overhead_squat_quality = models.CharField(
    max_length=30,
    choices=[
        ('pain', '동작 중 통증 발생'),
        ('cannot_squat', '깊은 스쿼트 수행 불가능'),
        ('compensations', '보상 동작 관찰됨'),
        ('perfect', '완벽한 동작'),
    ],
    null=True, blank=True,
    verbose_name="수행 품질"
)

# Toe Touch Enhancement
toe_touch_flexibility = models.CharField(
    max_length=30,
    choices=[
        ('no_reach', '손끝이 발에 닿지 않음'),
        ('fingertips', '손끝이 발에 닿음'),
        ('palm_cover', '손바닥이 발등을 덮음'),
        ('palm_full', '손바닥이 발에 완전히 닿음'),
    ],
    null=True, blank=True,
    verbose_name="유연성 평가"
)

# Shoulder Mobility Enhancement
shoulder_mobility_category = models.CharField(
    max_length=30,
    choices=[
        ('pain', '동작 중 통증'),
        ('over_1_5x', '손 간 거리가 신장 1.5배 이상'),
        ('1_to_1_5x', '손 간 거리가 신장 1~1.5배'),
        ('under_1x', '손 간 거리가 신장 1배 미만'),
    ],
    null=True, blank=True,
    verbose_name="양손 간 거리 평가"
)
```

### Step 2: Create and Run Migration
```bash
python manage.py makemigrations assessments -n add_movement_quality_details
python manage.py migrate
```

### Step 3: Update Assessment Form
**File**: `apps/assessments/forms/assessment_forms.py`

Add form fields with proper widgets:

```python
class AssessmentForm(forms.ModelForm):
    # Add to existing fields
    overhead_squat_arm_drop = forms.BooleanField(
        required=False,
        label="팔 전방 하강",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
            'x-model': 'overheadSquatArmDrop',
            '@change': 'updateOverheadSquatScore()'
        })
    )
    
    overhead_squat_quality = forms.ChoiceField(
        required=False,
        choices=[('', '선택하세요')] + Assessment._meta.get_field('overhead_squat_quality').choices,
        label="수행 품질",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'x-model': 'overheadSquatQuality',
            '@change': 'updateOverheadSquatScore()'
        })
    )
    
    toe_touch_flexibility = forms.ChoiceField(
        required=False,
        choices=[('', '선택하세요')] + Assessment._meta.get_field('toe_touch_flexibility').choices,
        label="유연성 평가",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'x-model': 'toeTouchFlexibility',
            '@change': 'updateToeTouchScore()'
        })
    )
    
    shoulder_mobility_category = forms.ChoiceField(
        required=False,
        choices=[('', '선택하세요')] + Assessment._meta.get_field('shoulder_mobility_category').choices,
        label="양손 간 거리 평가",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'x-model': 'shoulderMobilityCategory'
        })
    )
    
    class Meta:
        model = Assessment
        fields = [...existing fields..., 
                 'overhead_squat_arm_drop', 'overhead_squat_quality',
                 'toe_touch_flexibility', 'shoulder_mobility_category']
```

### Step 4: Update Form Template
**File**: `templates/assessments/assessment_form_content.html`

Add new fields to the appropriate sections:

```html
<!-- In Overhead Squat Section (around line 120) -->
<div class="space-y-4">
    <!-- Existing checkboxes -->
    <label class="flex items-center">
        {{ form.overhead_squat_arm_drop }}
        <span class="ml-2 text-sm text-gray-700">팔 전방 하강</span>
    </label>
</div>

<!-- Performance Quality -->
<div class="mt-4">
    <label class="block text-sm font-medium text-gray-700">수행 품질</label>
    {{ form.overhead_squat_quality }}
</div>

<!-- In Toe Touch Section (around line 290) -->
<div class="mt-4">
    <label class="block text-sm font-medium text-gray-700">유연성 평가</label>
    {{ form.toe_touch_flexibility }}
</div>

<!-- In Shoulder Mobility Section (around line 340) -->
<div class="mt-4">
    <label class="block text-sm font-medium text-gray-700">양손 간 거리 평가</label>
    {{ form.shoulder_mobility_category }}
</div>
```

### Step 5: Update Alpine.js Data Model
**File**: `templates/assessments/assessment_form_content.html` (JavaScript section)

Add new properties to Alpine data:

```javascript
Alpine.data('assessmentForm', () => ({
    // Add to existing properties
    overheadSquatArmDrop: false,
    overheadSquatQuality: '',
    toeTouchFlexibility: '',
    shoulderMobilityCategory: '',
    
    // Update existing updateOverheadSquatScore method
    updateOverheadSquatScore() {
        let score = 3; // Base score
        let compensations = 0;
        
        if (this.overheadSquatKneeValgus) compensations++;
        if (this.overheadSquatForwardLean) compensations++;
        if (this.overheadSquatHeelLift) compensations++;
        if (this.overheadSquatArmDrop) compensations++; // New
        
        // Adjust score based on quality
        if (this.overheadSquatQuality === 'pain') {
            score = 0;
        } else if (this.overheadSquatQuality === 'cannot_squat') {
            score = 1;
        } else if (this.overheadSquatQuality === 'compensations' || compensations > 0) {
            score = Math.max(1, 3 - compensations);
        } else if (this.overheadSquatQuality === 'perfect') {
            score = 5;
        }
        
        this.overheadSquatScore = score;
    },
    
    // Add new method for toe touch
    updateToeTouchScore() {
        const flexibilityScores = {
            'no_reach': 1,
            'fingertips': 2,
            'palm_cover': 3,
            'palm_full': 5
        };
        
        if (this.toeTouchFlexibility && flexibilityScores[this.toeTouchFlexibility]) {
            this.toeTouchScore = flexibilityScores[this.toeTouchFlexibility];
        }
    }
}));
```

### Step 6: Update Risk Calculator (Optional)
**File**: `apps/assessments/risk_calculator.py`

If you want these new fields to influence risk scoring:

```python
def calculate_movement_quality_risk(assessment):
    """Enhanced movement quality risk calculation"""
    risk_points = 0
    
    # Existing compensations
    if assessment.overhead_squat_knee_valgus:
        risk_points += 5
    if assessment.overhead_squat_forward_lean:
        risk_points += 5
    if assessment.overhead_squat_heel_lift:
        risk_points += 5
    
    # New assessments
    if assessment.overhead_squat_arm_drop:
        risk_points += 5
    
    if assessment.overhead_squat_quality == 'pain':
        risk_points += 20
    elif assessment.overhead_squat_quality == 'cannot_squat':
        risk_points += 15
    elif assessment.overhead_squat_quality == 'compensations':
        risk_points += 10
    
    # Add similar logic for toe touch and shoulder mobility
    
    return min(risk_points, 30)  # Cap at 30 points
```

### Step 7: Update Admin Interface
**File**: `apps/assessments/admin.py`

Add new fields to admin display:

```python
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    fieldsets = (
        # Update Movement Quality section
        ('Movement Quality', {
            'fields': (
                'overhead_squat_knee_valgus',
                'overhead_squat_forward_lean', 
                'overhead_squat_heel_lift',
                'overhead_squat_arm_drop',  # New
                'overhead_squat_quality',    # New
                'toe_touch_flexibility',     # New
                'shoulder_mobility_category' # New
            ),
            'classes': ('collapse',)
        }),
    )
```

### Step 8: Update API Serializers
**File**: `apps/api/serializers.py`

Add fields to AssessmentSerializer:

```python
class AssessmentSerializer(serializers.ModelSerializer):
    # Add display values for choice fields
    overhead_squat_quality_display = serializers.CharField(
        source='get_overhead_squat_quality_display', 
        read_only=True
    )
    toe_touch_flexibility_display = serializers.CharField(
        source='get_toe_touch_flexibility_display', 
        read_only=True
    )
    shoulder_mobility_category_display = serializers.CharField(
        source='get_shoulder_mobility_category_display', 
        read_only=True
    )
    
    class Meta:
        model = Assessment
        fields = [...existing fields...,
                 'overhead_squat_arm_drop', 'overhead_squat_quality',
                 'overhead_squat_quality_display',
                 'toe_touch_flexibility', 'toe_touch_flexibility_display',
                 'shoulder_mobility_category', 'shoulder_mobility_category_display']
```

### Step 9: Update Report Template
**File**: `templates/reports/assessment_report_detailed.html`

Add new fields to PDF reports:

```html
<!-- In Movement Quality section -->
{% if assessment.overhead_squat_quality %}
<p><strong>수행 품질:</strong> {{ assessment.get_overhead_squat_quality_display }}</p>
{% endif %}

{% if assessment.toe_touch_flexibility %}
<p><strong>유연성 평가:</strong> {{ assessment.get_toe_touch_flexibility_display }}</p>
{% endif %}

{% if assessment.shoulder_mobility_category %}
<p><strong>양손 간 거리:</strong> {{ assessment.get_shoulder_mobility_category_display }}</p>
{% endif %}
```

### Step 10: Create Tests
**File**: `apps/assessments/test_movement_quality_enhancements.py`

```python
import pytest
from apps.assessments.models import Assessment
from apps.assessments.factories import AssessmentFactory

@pytest.mark.django_db
class TestMovementQualityEnhancements:
    def test_overhead_squat_quality_choices(self):
        """Test overhead squat quality field choices"""
        assessment = AssessmentFactory(
            overhead_squat_quality='pain'
        )
        assert assessment.get_overhead_squat_quality_display() == '동작 중 통증 발생'
    
    def test_toe_touch_flexibility_scoring(self):
        """Test toe touch flexibility affects scoring"""
        assessment = AssessmentFactory(
            toe_touch_flexibility='palm_full'
        )
        assessment.calculate_scores()
        assert assessment.toe_touch_score == 5
    
    def test_shoulder_mobility_category(self):
        """Test shoulder mobility categorization"""
        assessment = AssessmentFactory(
            shoulder_mobility_category='under_1x'
        )
        assert assessment.get_shoulder_mobility_category_display() == '손 간 거리가 신장 1배 미만'
```

## Testing Plan

1. **Unit Tests**: Test model fields, form validation, scoring logic
2. **Integration Tests**: Test full assessment workflow with new fields
3. **Manual Testing**: 
   - Create new assessment with all fields
   - Edit existing assessment
   - Verify PDF reports show new data
   - Test API endpoints return new fields

## Rollback Plan

If issues arise:
1. Keep migration file but don't deploy
2. Remove form fields from template
3. Fields remain in database but hidden from UI

## Timeline Estimate

- Step 1-2: 30 minutes (Model + Migration)
- Step 3-4: 45 minutes (Form + Template)
- Step 5: 30 minutes (JavaScript)
- Step 6-7: 30 minutes (Risk Calculator + Admin)
- Step 8-9: 30 minutes (API + Reports)
- Step 10: 45 minutes (Testing)
- **Total**: ~3.5 hours

## Notes

- All new fields are optional (null=True, blank=True)
- Won't break existing assessments
- Enhances trainer's ability to document movement quality
- Can be deployed incrementally (database first, UI later)