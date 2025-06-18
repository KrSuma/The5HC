# Fitness Assessment Enhancement Implementation Plan

**Created**: 2025-01-18  
**Purpose**: Comprehensive plan to enhance the fitness assessment scoring system based on analysis of the fitness assessment scoring report

## Overview

This plan ensures all changes augment the existing Django assessment system without breaking current functionality. The enhancements are divided into 5 phases, each building upon the previous while maintaining backward compatibility.

## Phase 1: FMS Scoring Enhancement (Days 1-2)

### Objective
Add proper movement quality tracking for FMS tests while preserving existing scoring functionality.

### Step 1.1: Add Movement Quality Fields to Assessment Model
**File**: `apps/assessments/models.py`

```python
# Add after existing overhead_squat fields (line ~48)
overhead_squat_knee_valgus = models.BooleanField(
    default=False, blank=True,
    help_text="Knees cave inward during squat"
)
overhead_squat_forward_lean = models.BooleanField(
    default=False, blank=True,
    help_text="Excessive forward lean"
)
overhead_squat_heel_lift = models.BooleanField(
    default=False, blank=True,
    help_text="Heels lift off ground"
)

# Add after existing shoulder_mobility fields (line ~104)
shoulder_mobility_pain = models.BooleanField(
    default=False, blank=True,
    help_text="Pain during clearing test"
)
shoulder_mobility_asymmetry = models.FloatField(
    null=True, blank=True,
    help_text="Difference between sides in cm"
)
```

### Step 1.2: Create Migration
```bash
python manage.py makemigrations assessments -name add_movement_quality_fields
```

### Step 1.3: Update Scoring Functions
**File**: `apps/assessments/scoring.py`

```python
# Update calculate_overhead_squat_score function (line ~86)
def calculate_overhead_squat_score(form_quality=None, knee_valgus=False, 
                                   forward_lean=False, heel_lift=False, pain=False):
    """
    Calculate score for overhead squat test with movement quality
    """
    if pain:
        return 0
    
    # If form_quality provided (backward compatibility)
    if form_quality is not None:
        return max(0, min(3, form_quality))
    
    # Calculate based on compensations
    compensations = sum([knee_valgus, forward_lean, heel_lift])
    
    if compensations == 0:
        return 3  # Perfect form
    elif compensations == 1:
        return 2  # Minor compensations
    elif compensations >= 2:
        return 1  # Major compensations
    
    return 1
```

### Step 1.4: Update Assessment Model's calculate_scores Method
**File**: `apps/assessments/models.py`

```python
# Update line ~176 in calculate_scores method
if self.overhead_squat_score is None:
    self.overhead_squat_score = calculate_overhead_squat_score(
        knee_valgus=self.overhead_squat_knee_valgus,
        forward_lean=self.overhead_squat_forward_lean,
        heel_lift=self.overhead_squat_heel_lift,
        pain=False  # Could add pain field if needed
    )
```

### Step 1.5: Update Forms
**File**: `apps/assessments/forms.py`

Add the new fields to the assessment form fields list.

### Step 1.6: Update Templates
Update assessment form templates to include checkboxes for movement compensations.

## Phase 2: Risk Scoring System (Days 3-4)

### Objective
Implement injury risk calculations based on assessment data patterns.

### Step 2.1: Add Risk Score Fields to Model
**File**: `apps/assessments/models.py`

```python
# Add after existing score fields (line ~156)
injury_risk_score = models.FloatField(
    null=True, blank=True,
    help_text="Calculated injury risk score (0-100)"
)
risk_factors = models.JSONField(
    null=True, blank=True,
    help_text="Detailed risk factor analysis"
)
```

### Step 2.2: Create Risk Calculation Module
**New File**: `apps/assessments/risk_calculator.py`

```python
from typing import Dict, List, Tuple

def calculate_injury_risk(assessment) -> Tuple[float, Dict]:
    """
    Calculate injury risk score based on assessment data
    
    Returns:
        Tuple of (risk_score, risk_factors)
    """
    risk_factors = {}
    risk_score = 0
    
    # Category imbalance check
    scores = [
        assessment.strength_score or 0,
        assessment.mobility_score or 0,
        assessment.balance_score or 0,
        assessment.cardio_score or 0
    ]
    
    if scores:
        max_score = max(scores)
        min_score = min(scores)
        imbalance = max_score - min_score
        
        if imbalance > 30:
            risk_score += 20
            risk_factors['category_imbalance'] = {
                'severity': 'high',
                'difference': imbalance,
                'message': f'Large imbalance between categories ({imbalance:.1f} points)'
            }
    
    # Bilateral asymmetry check
    if assessment.single_leg_balance_right_eyes_open and assessment.single_leg_balance_left_eyes_open:
        asymmetry = abs(assessment.single_leg_balance_right_eyes_open - 
                       assessment.single_leg_balance_left_eyes_open)
        if asymmetry > 10:
            risk_score += 15
            risk_factors['balance_asymmetry'] = {
                'severity': 'moderate',
                'difference': asymmetry,
                'message': f'Significant balance asymmetry ({asymmetry}s difference)'
            }
    
    # Poor balance indicator
    if assessment.balance_score and assessment.balance_score < 50:
        risk_score += 25
        risk_factors['poor_balance'] = {
            'severity': 'high',
            'score': assessment.balance_score,
            'message': 'Poor balance increases fall risk'
        }
    
    # Poor mobility indicator
    if assessment.mobility_score and assessment.mobility_score < 50:
        risk_score += 20
        risk_factors['poor_mobility'] = {
            'severity': 'high',
            'score': assessment.mobility_score,
            'message': 'Limited mobility increases injury risk'
        }
    
    # Movement compensations
    compensations = sum([
        getattr(assessment, 'overhead_squat_knee_valgus', False),
        getattr(assessment, 'overhead_squat_forward_lean', False),
        getattr(assessment, 'overhead_squat_heel_lift', False)
    ])
    if compensations >= 2:
        risk_score += 15
        risk_factors['movement_quality'] = {
            'severity': 'moderate',
            'count': compensations,
            'message': f'{compensations} movement compensations detected'
        }
    
    return min(risk_score, 100), risk_factors
```

### Step 2.3: Integrate Risk Calculation
**File**: `apps/assessments/models.py`

```python
# Add import at top
from .risk_calculator import calculate_injury_risk

# Update calculate_scores method (add at end, ~line 305)
# Calculate injury risk
self.injury_risk_score, self.risk_factors = calculate_injury_risk(self)
```

### Step 2.4: Add Risk Display to Templates
Create UI components to display risk score and factors in assessment detail view.

## Phase 3: Analytics Enhancement (Days 5-6)

### Objective
Add peer comparison analytics and normative data tracking.

### Step 3.1: Create Normative Data Model
**File**: `apps/assessments/models.py` (add to existing file)

```python
class NormativeData(models.Model):
    """Population normative data for assessments"""
    test_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    age_min = models.IntegerField()
    age_max = models.IntegerField()
    percentile_10 = models.FloatField()
    percentile_25 = models.FloatField()
    percentile_50 = models.FloatField()
    percentile_75 = models.FloatField()
    percentile_90 = models.FloatField()
    sample_size = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['test_name', 'gender', 'age_min', 'age_max']
        verbose_name = "Normative Data"
        verbose_name_plural = "Normative Data"
```

### Step 3.2: Add Percentile Calculation Methods
**File**: `apps/assessments/models.py`

```python
def get_percentile_rankings(self):
    """Get percentile rankings compared to normative data"""
    rankings = {}
    
    # Get client age and gender
    age = self._calculate_client_age()
    gender = self.client.gender
    
    if not age or not gender:
        return rankings
    
    # Lookup normative data for each test
    tests = {
        'push_up': self.push_up_reps,
        'balance_open': (self.single_leg_balance_right_eyes_open + 
                        self.single_leg_balance_left_eyes_open) / 2 if 
                        self.single_leg_balance_right_eyes_open else None,
        'toe_touch': self.toe_touch_distance,
        'farmers_carry_distance': self.farmer_carry_distance,
        'harvard_pfi': self.harvard_step_test_pfi
    }
    
    for test_name, value in tests.items():
        if value is None:
            continue
            
        try:
            norm_data = NormativeData.objects.get(
                test_name=test_name,
                gender=gender,
                age_min__lte=age,
                age_max__gte=age
            )
            
            # Calculate percentile
            if value <= norm_data.percentile_10:
                percentile = 10
            elif value <= norm_data.percentile_25:
                percentile = 25
            elif value <= norm_data.percentile_50:
                percentile = 50
            elif value <= norm_data.percentile_75:
                percentile = 75
            elif value <= norm_data.percentile_90:
                percentile = 90
            else:
                percentile = 95
                
            rankings[test_name] = {
                'value': value,
                'percentile': percentile,
                'interpretation': self._get_percentile_interpretation(percentile)
            }
        except NormativeData.DoesNotExist:
            continue
    
    return rankings

def _get_percentile_interpretation(self, percentile):
    """Get interpretation for percentile ranking"""
    if percentile >= 90:
        return "상위 10% (우수)"
    elif percentile >= 75:
        return "상위 25% (양호)"
    elif percentile >= 50:
        return "평균"
    elif percentile >= 25:
        return "하위 25% (개선 필요)"
    else:
        return "하위 10% (집중 개선 필요)"
```

### Step 3.3: Create Management Command for Sample Data
**New File**: `apps/assessments/management/commands/load_normative_data.py`

```python
from django.core.management.base import BaseCommand
from apps.assessments.models import NormativeData

class Command(BaseCommand):
    help = 'Load sample normative data for testing'
    
    def handle(self, *args, **options):
        # Example data - replace with actual normative data
        sample_data = [
            {
                'test_name': 'push_up',
                'gender': 'male',
                'age_min': 20,
                'age_max': 29,
                'percentile_10': 15,
                'percentile_25': 22,
                'percentile_50': 29,
                'percentile_75': 36,
                'percentile_90': 45,
                'sample_size': 1000
            },
            # Add more data...
        ]
        
        for data in sample_data:
            NormativeData.objects.update_or_create(
                test_name=data['test_name'],
                gender=data['gender'],
                age_min=data['age_min'],
                age_max=data['age_max'],
                defaults=data
            )
```

### Step 3.4: Add Performance Age Calculation
**File**: `apps/assessments/models.py`

```python
def calculate_performance_age(self):
    """Calculate fitness age based on test results"""
    actual_age = self._calculate_client_age()
    if not actual_age:
        return None
    
    # Simple algorithm - can be enhanced
    score_modifier = (self.overall_score - 70) / 10  # Each 10 points = 1 year
    performance_age = actual_age - score_modifier
    
    return max(18, min(80, performance_age))  # Clamp between 18-80
```

## Phase 4: Test Variations Support (Days 7-8)

### Objective
Support multiple test conditions and variations.

### Step 4.1: Add Test Variation Fields
**File**: `apps/assessments/models.py`

```python
# Add after push_up fields
push_up_type = models.CharField(
    max_length=20,
    choices=[
        ('standard', '표준 푸시업'),
        ('modified', '변형 푸시업'),
        ('wall', '벽 푸시업')
    ],
    default='standard',
    blank=True
)

# Add after farmer_carry fields
farmer_carry_body_weight_percentage = models.FloatField(
    null=True, blank=True,
    help_text="Weight as percentage of body weight"
)

# Add general test conditions
test_environment = models.CharField(
    max_length=20,
    choices=[
        ('indoor', '실내'),
        ('outdoor', '실외')
    ],
    default='indoor',
    blank=True
)
test_temperature = models.FloatField(
    null=True, blank=True,
    help_text="Temperature in Celsius"
)
```

### Step 4.2: Update Scoring for Variations
**File**: `apps/assessments/scoring.py`

```python
def calculate_pushup_score(gender, age, reps, test_type='standard'):
    """
    Updated to handle different push-up types
    """
    # Adjust reps based on test type
    if test_type == 'modified':
        # Modified push-ups are easier, adjust equivalence
        reps = int(reps * 0.7)
    elif test_type == 'wall':
        # Wall push-ups are much easier
        reps = int(reps * 0.4)
    
    # Rest of existing scoring logic...
    age = max(0, min(120, age))
    reps = max(0, reps)

    # Find the appropriate age range
    age_range = None
    for age_range_tuple in PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male']):
        if age_range_tuple[0] <= age <= age_range_tuple[1]:
            age_range = age_range_tuple
            break
    
    if age_range is None:
        age_range = max(PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male']).keys())

    thresholds = PUSHUP_THRESHOLDS.get(gender, PUSHUP_THRESHOLDS['Male'])[age_range]
    
    if reps >= thresholds['excellent']:
        return 4
    elif reps >= thresholds['good']:
        return 3
    elif reps >= thresholds['average']:
        return 2
    else:
        return 1
```

### Step 4.3: Update Model calculate_scores
**File**: `apps/assessments/models.py`

```python
# Update push-up scoring call to include type
if self.push_up_score is None and self.push_up_reps is not None:
    client_gender = self.client.gender
    client_age = self._calculate_client_age()
    
    if client_gender and client_age is not None:
        gender_for_scoring = client_gender.title() if client_gender else 'Male'
        self.push_up_score = calculate_pushup_score(
            gender=gender_for_scoring,
            age=client_age,
            reps=self.push_up_reps,
            test_type=self.push_up_type or 'standard'
        )
```

## Phase 5: Standards Configuration (Days 9-10)

### Objective
Move hardcoded scoring thresholds to database for easy configuration.

### Step 5.1: Create Test Standards Model
**File**: `apps/assessments/models.py`

```python
class TestStandard(models.Model):
    """Configurable test standards"""
    test_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, blank=True, null=True)
    age_min = models.IntegerField(null=True, blank=True)
    age_max = models.IntegerField(null=True, blank=True)
    score_level = models.IntegerField()  # 1-4
    score_label = models.CharField(max_length=20)  # Excellent, Good, etc
    min_value = models.FloatField()
    max_value = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['test_name', 'gender', 'age_min', 'score_level']
        verbose_name = "Test Standard"
        verbose_name_plural = "Test Standards"
    
    def __str__(self):
        return f"{self.test_name} - {self.gender or 'All'} - Score {self.score_level}"
```

### Step 5.2: Create Management Command to Load Standards
**New File**: `apps/assessments/management/commands/load_test_standards.py`

```python
from django.core.management.base import BaseCommand
from apps.assessments.models import TestStandard
from apps.assessments.scoring import PUSHUP_THRESHOLDS, BALANCE_THRESHOLDS, FARMERS_CARRY_THRESHOLDS

class Command(BaseCommand):
    help = 'Load test standards from current hardcoded values'
    
    def handle(self, *args, **options):
        # Clear existing standards
        TestStandard.objects.all().delete()
        
        # Load push-up standards
        for gender, age_groups in PUSHUP_THRESHOLDS.items():
            if gender in ['남성', '여성']:
                continue  # Skip Korean duplicates
                
            for age_range, thresholds in age_groups.items():
                # Score 4 - Excellent
                TestStandard.objects.create(
                    test_name='push_up',
                    gender=gender,
                    age_min=age_range[0],
                    age_max=age_range[1],
                    score_level=4,
                    score_label='Excellent',
                    min_value=thresholds['excellent']
                )
                
                # Score 3 - Good
                TestStandard.objects.create(
                    test_name='push_up',
                    gender=gender,
                    age_min=age_range[0],
                    age_max=age_range[1],
                    score_level=3,
                    score_label='Good',
                    min_value=thresholds['good'],
                    max_value=thresholds['excellent'] - 1
                )
                
                # Score 2 - Average
                TestStandard.objects.create(
                    test_name='push_up',
                    gender=gender,
                    age_min=age_range[0],
                    age_max=age_range[1],
                    score_level=2,
                    score_label='Average',
                    min_value=thresholds['average'],
                    max_value=thresholds['good'] - 1
                )
                
                # Score 1 - Below Average
                TestStandard.objects.create(
                    test_name='push_up',
                    gender=gender,
                    age_min=age_range[0],
                    age_max=age_range[1],
                    score_level=1,
                    score_label='Below Average',
                    min_value=0,
                    max_value=thresholds['average'] - 1
                )
        
        # Load balance standards
        for condition, thresholds in BALANCE_THRESHOLDS.items():
            test_name = f'balance_{condition}'
            
            TestStandard.objects.create(
                test_name=test_name,
                score_level=4,
                score_label='Excellent',
                min_value=thresholds['excellent']
            )
            
            TestStandard.objects.create(
                test_name=test_name,
                score_level=3,
                score_label='Good',
                min_value=thresholds['good'],
                max_value=thresholds['excellent'] - 1
            )
            
            TestStandard.objects.create(
                test_name=test_name,
                score_level=2,
                score_label='Average',
                min_value=thresholds['average'],
                max_value=thresholds['good'] - 1
            )
            
            TestStandard.objects.create(
                test_name=test_name,
                score_level=1,
                score_label='Below Average',
                min_value=0,
                max_value=thresholds['average'] - 1
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded test standards'))
```

### Step 5.3: Update Scoring to Use Database Standards
**File**: `apps/assessments/scoring.py`

```python
def get_test_standard(test_name, gender=None, age=None, score_level=None):
    """Get test standard from database with fallback to hardcoded"""
    try:
        from apps.assessments.models import TestStandard
        
        query = TestStandard.objects.filter(test_name=test_name)
        if gender:
            query = query.filter(gender=gender)
        if age is not None:
            query = query.filter(age_min__lte=age, age_max__gte=age)
        if score_level:
            query = query.filter(score_level=score_level)
            
        return query.first()
    except:
        # Fallback to hardcoded values
        return None

def calculate_pushup_score_with_db(gender, age, reps, test_type='standard'):
    """Calculate push-up score using database standards"""
    # Adjust reps based on test type
    if test_type == 'modified':
        reps = int(reps * 0.7)
    elif test_type == 'wall':
        reps = int(reps * 0.4)
    
    # Try to get from database first
    for score_level in [4, 3, 2, 1]:
        standard = get_test_standard('push_up', gender, age, score_level)
        if standard and reps >= standard.min_value:
            return score_level
    
    # Fallback to hardcoded calculation
    return calculate_pushup_score(gender, age, reps, test_type)
```

### Step 5.4: Admin Configuration
**File**: `apps/assessments/admin.py`

```python
from django.contrib import admin
from .models import TestStandard, NormativeData

@admin.register(TestStandard)
class TestStandardAdmin(admin.ModelAdmin):
    list_display = ['test_name', 'gender', 'age_min', 'age_max', 'score_level', 'score_label', 'min_value']
    list_filter = ['test_name', 'gender', 'score_level']
    search_fields = ['test_name', 'score_label']
    ordering = ['test_name', 'gender', 'age_min', 'score_level']

@admin.register(NormativeData)
class NormativeDataAdmin(admin.ModelAdmin):
    list_display = ['test_name', 'gender', 'age_min', 'age_max', 'sample_size']
    list_filter = ['test_name', 'gender']
    search_fields = ['test_name']
```

## Implementation Timeline

| Phase | Duration | Priority | Dependencies | Key Deliverables |
|-------|----------|----------|--------------|------------------|
| Phase 1 | 2 days | High | None | Movement quality tracking, Enhanced FMS scoring |
| Phase 2 | 2 days | High | Phase 1 | Risk scoring system, Risk factor analysis |
| Phase 3 | 2 days | Medium | Phase 2 | Percentile rankings, Performance age |
| Phase 4 | 2 days | Medium | None | Test variations, Environmental tracking |
| Phase 5 | 2 days | Low | None | Database-driven standards, Admin configuration |

## Testing Strategy

### Unit Tests for Each Phase

#### Phase 1 Tests
```python
class TestMovementQuality(TestCase):
    def test_overhead_squat_with_compensations(self):
        assessment = AssessmentFactory()
        assessment.overhead_squat_knee_valgus = True
        assessment.overhead_squat_forward_lean = True
        assessment.calculate_scores()
        
        self.assertEqual(assessment.overhead_squat_score, 1)  # Major compensations
    
    def test_backward_compatibility(self):
        assessment = AssessmentFactory()
        assessment.overhead_squat_score = 3
        assessment.calculate_scores()
        
        self.assertEqual(assessment.overhead_squat_score, 3)  # Manual score preserved
```

#### Phase 2 Tests
```python
class TestRiskScoring(TestCase):
    def test_category_imbalance_risk(self):
        assessment = AssessmentFactory(
            strength_score=90,
            mobility_score=50,
            balance_score=85,
            cardio_score=80
        )
        assessment.calculate_scores()
        
        self.assertGreater(assessment.injury_risk_score, 0)
        self.assertIn('category_imbalance', assessment.risk_factors)
    
    def test_bilateral_asymmetry_risk(self):
        assessment = AssessmentFactory(
            single_leg_balance_right_eyes_open=30,
            single_leg_balance_left_eyes_open=15
        )
        assessment.calculate_scores()
        
        self.assertIn('balance_asymmetry', assessment.risk_factors)
```

#### Phase 3 Tests
```python
class TestAnalytics(TestCase):
    def test_percentile_ranking(self):
        # Create normative data
        NormativeData.objects.create(
            test_name='push_up',
            gender='male',
            age_min=20,
            age_max=29,
            percentile_50=29,
            sample_size=1000
        )
        
        client = ClientFactory(gender='male', age=25)
        assessment = AssessmentFactory(client=client, push_up_reps=35)
        
        rankings = assessment.get_percentile_rankings()
        
        self.assertGreater(rankings['push_up']['percentile'], 50)
```

### Migration Testing
1. Test with existing production data dump
2. Verify all new fields have proper defaults
3. Test score recalculation maintains existing scores
4. Ensure backward compatibility

### Integration Testing
1. Create assessment with all new fields
2. Verify risk calculations
3. Test percentile rankings
4. Confirm API endpoints still work
5. Test admin interface functionality

## Rollback Plan

Each phase can be rolled back independently:

### Phase-specific Rollback
1. **Migrations**: Keep separate migration files for each phase
2. **Feature Flags**: Use Django settings to enable/disable features
3. **Backward Compatibility**: All scoring functions maintain fallback logic
4. **Database Backups**: Create backup before each phase deployment

### Emergency Rollback Procedure
```bash
# Rollback specific migration
python manage.py migrate assessments 0XXX_previous_migration

# Disable feature in settings
ENABLE_RISK_SCORING = False
ENABLE_NORMATIVE_DATA = False

# Restore from backup if needed
pg_restore -d the5hc_db backup_pre_phase_X.dump
```

## Deployment Checklist

### Pre-deployment
- [ ] All tests passing
- [ ] Code review completed
- [ ] Database backup created
- [ ] Migration tested on staging
- [ ] Documentation updated

### Deployment
- [ ] Apply migrations
- [ ] Load initial data (standards, normative data)
- [ ] Verify admin interface
- [ ] Test key workflows
- [ ] Monitor error logs

### Post-deployment
- [ ] Verify scoring accuracy
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Plan next phase

## Success Metrics

### Phase 1
- Movement quality data captured for 90% of new assessments
- No regression in existing scoring

### Phase 2
- Risk scores calculated for all complete assessments
- Risk factors provide actionable insights

### Phase 3
- Percentile rankings available for 80% of tests
- Performance age correlates with overall fitness

### Phase 4
- Support for 3+ test variations
- Environmental data captured when relevant

### Phase 5
- Standards configurable without code changes
- Admin can update thresholds independently

## Notes and Considerations

1. **Data Privacy**: Ensure normative data is anonymized
2. **Performance**: Index new fields for query optimization
3. **Localization**: All new UI text should support Korean
4. **Mobile**: Ensure new features work on mobile devices
5. **Training**: Create documentation for trainers on new features

This comprehensive plan ensures smooth implementation while preserving existing functionality and data integrity.