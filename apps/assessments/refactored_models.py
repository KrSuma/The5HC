"""
Refactored Assessment models - Breaking down the monolithic Assessment model.

This file demonstrates how to split the 1,495-line Assessment model into
focused, cohesive models following Django best practices.

IMPORTANT: This is a design demonstration - NOT for production use yet.
Production migration will require careful data migration and testing.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from datetime import date


# =============================================================================
# CORE ASSESSMENT MODEL (Reduced from 1,495 lines to ~150 lines)
# =============================================================================

class Assessment(models.Model):
    """
    Core assessment model - metadata and relationships only.
    Individual test data moved to separate models for better organization.
    """
    # Core relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    trainer = models.ForeignKey(
        'trainers.Trainer',
        on_delete=models.CASCADE,
        related_name='assessments_conducted',
        verbose_name='Trainer'
    )
    
    # Assessment metadata
    date = models.DateTimeField()
    test_environment = models.CharField(
        max_length=10,
        choices=[('indoor', '실내'), ('outdoor', '실외')],
        default='indoor'
    )
    temperature = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-10), MaxValueValidator(50)],
        help_text="Ambient temperature in Celsius"
    )
    
    # Calculated aggregate scores
    overall_score = models.FloatField(null=True, blank=True)
    strength_score = models.FloatField(null=True, blank=True)
    mobility_score = models.FloatField(null=True, blank=True)
    balance_score = models.FloatField(null=True, blank=True)
    cardio_score = models.FloatField(null=True, blank=True)
    
    # Risk assessment
    injury_risk_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    risk_factors = models.JSONField(null=True, blank=True)
    
    # MCQ integration
    knowledge_score = models.FloatField(null=True, blank=True)
    lifestyle_score = models.FloatField(null=True, blank=True)
    readiness_score = models.FloatField(null=True, blank=True)
    comprehensive_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-date', '-created_at']
        
    def __str__(self):
        return f"Assessment for {self.client.name} on {self.date.strftime('%Y-%m-%d')}"
    
    def calculate_scores(self):
        """Calculate aggregate scores from individual test results."""
        # Implementation moved to AssessmentService
        from apps.core.services import AssessmentService
        service = AssessmentService()
        service.calculate_assessment_scores(self)
    
    def save(self, *args, **kwargs):
        """Override save to calculate scores."""
        super().save(*args, **kwargs)
        # Calculate scores after save to ensure all related data exists
        self.calculate_scores()


# =============================================================================
# INDIVIDUAL TEST MODELS
# =============================================================================

class OverheadSquatTest(models.Model):
    """Overhead Squat Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='overhead_squat'
    )
    
    # Test results
    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    notes = models.TextField(blank=True, null=True)
    
    # Movement quality compensations
    knee_valgus = models.BooleanField(default=False)
    forward_lean = models.BooleanField(default=False)
    heel_lift = models.BooleanField(default=False)
    arm_drop = models.BooleanField(default=False)
    
    # Quality assessment
    quality = models.CharField(
        max_length=30,
        choices=[
            ('pain', '동작 중 통증 발생'),
            ('cannot_squat', '깊은 스쿼트 수행 불가능'),
            ('compensations', '보상 동작 관찰됨'),
            ('perfect', '완벽한 동작'),
        ],
        null=True, blank=True
    )
    
    # Manual override tracking
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'overhead_squat_tests'
    
    def calculate_score(self):
        """Calculate score based on movement quality."""
        if self.score_manual_override:
            return self.score
        
        from apps.assessments.scoring import calculate_overhead_squat_score
        return calculate_overhead_squat_score(
            knee_valgus=self.knee_valgus,
            forward_lean=self.forward_lean,
            heel_lift=self.heel_lift,
            pain=(self.quality == 'pain')
        )


class PushUpTest(models.Model):
    """Push-up Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='push_up'
    )
    
    # Test results
    reps = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    notes = models.TextField(blank=True, null=True)
    
    # Test variations
    push_up_type = models.CharField(
        max_length=10,
        choices=[
            ('standard', '표준'),
            ('modified', '보정됨'),
            ('wall', '벽'),
        ],
        default='standard'
    )
    
    # Manual override tracking
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'push_up_tests'
    
    def calculate_score(self):
        """Calculate score based on reps, age, and gender."""
        if self.score_manual_override or not self.reps:
            return self.score
        
        from apps.assessments.scoring import calculate_pushup_score
        client = self.assessment.client
        return calculate_pushup_score(
            gender=client.gender.title() if client.gender else 'Male',
            age=client.age or 30,
            reps=self.reps,
            push_up_type=self.push_up_type
        )


class SingleLegBalanceTest(models.Model):
    """Single Leg Balance Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='single_leg_balance'
    )
    
    # Test results (seconds)
    right_eyes_open = models.IntegerField(null=True, blank=True)
    left_eyes_open = models.IntegerField(null=True, blank=True)
    right_eyes_closed = models.IntegerField(null=True, blank=True)
    left_eyes_closed = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Calculated score
    score_manual = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'single_leg_balance_tests'
    
    def calculate_score(self):
        """Calculate score based on balance times."""
        if self.score_manual_override:
            return self.score_manual
        
        if not all([self.right_eyes_open, self.left_eyes_open, 
                   self.right_eyes_closed, self.left_eyes_closed]):
            return self.score_manual
        
        from apps.assessments.scoring import calculate_single_leg_balance_score
        return calculate_single_leg_balance_score(
            right_open=self.right_eyes_open,
            left_open=self.left_eyes_open,
            right_closed=self.right_eyes_closed,
            left_closed=self.left_eyes_closed
        )


class ToeTouchTest(models.Model):
    """Toe Touch Flexibility Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='toe_touch'
    )
    
    # Test results
    distance = models.FloatField(
        null=True, blank=True,
        help_text="Distance in cm (negative for below toes)"
    )
    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    notes = models.TextField(blank=True, null=True)
    
    # Flexibility assessment
    flexibility = models.CharField(
        max_length=30,
        choices=[
            ('no_reach', '손끝이 발에 닿지 않음'),
            ('fingertips', '손끝이 발에 닿음'),
            ('palm_cover', '손바닥이 발등을 덮음'),
            ('palm_full', '손바닥이 발에 완전히 닿음'),
        ],
        null=True, blank=True
    )
    
    # Manual override tracking
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'toe_touch_tests'
    
    def calculate_score(self):
        """Calculate score based on distance."""
        if self.score_manual_override or self.distance is None:
            return self.score
        
        from apps.assessments.scoring import calculate_toe_touch_score
        return calculate_toe_touch_score(distance=self.distance)


class ShoulderMobilityTest(models.Model):
    """Shoulder Mobility Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='shoulder_mobility'
    )
    
    # Test results
    right = models.FloatField(null=True, blank=True, help_text="Distance in cm")
    left = models.FloatField(null=True, blank=True, help_text="Distance in cm")
    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    notes = models.TextField(blank=True, null=True)
    
    # Movement quality
    pain = models.BooleanField(default=False)
    asymmetry = models.FloatField(null=True, blank=True)
    
    # Category assessment
    category = models.CharField(
        max_length=30,
        choices=[
            ('pain', '동작 중 통증'),
            ('over_1_5x', '손 간 거리가 신장 1.5배 이상'),
            ('1_to_1_5x', '손 간 거리가 신장 1~1.5배'),
            ('under_1x', '손 간 거리가 신장 1배 미만'),
        ],
        null=True, blank=True
    )
    
    # Manual override tracking
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'shoulder_mobility_tests'


class FarmersCarryTest(models.Model):
    """Farmer's Carry Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='farmers_carry'
    )
    
    # Test results
    weight = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Weight in kg"
    )
    distance = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Distance in meters"
    )
    time = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Time in seconds"
    )
    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    notes = models.TextField(blank=True, null=True)
    
    # Test variation
    percentage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Percentage of body weight used"
    )
    
    # Manual override tracking
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'farmers_carry_tests'
    
    def calculate_score(self):
        """Calculate score based on performance."""
        if self.score_manual_override or not all([self.weight, self.distance, self.time]):
            return self.score
        
        from apps.assessments.scoring import calculate_farmers_carry_score
        client = self.assessment.client
        return calculate_farmers_carry_score(
            gender=client.gender.title() if client.gender else 'Male',
            weight=self.weight,
            distance=self.distance,
            time=self.time,
            body_weight_percentage=self.percentage
        )


class HarvardStepTest(models.Model):
    """Harvard Step Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='harvard_step'
    )
    
    # Test results (heart rate measurements)
    hr1 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="HR 1-1.5 minutes after exercise"
    )
    hr2 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="HR 2-2.5 minutes after exercise"
    )
    hr3 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="HR 3-3.5 minutes after exercise"
    )
    duration = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Duration in seconds"
    )
    notes = models.TextField(blank=True, null=True)
    
    # Calculated values
    score_manual = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    score_manual_override = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'harvard_step_tests'
    
    def calculate_score(self):
        """Calculate score and PFI."""
        if self.score_manual_override:
            return self.score_manual
        
        if not all([self.hr1, self.hr2, self.hr3]):
            return self.score_manual
        
        from apps.assessments.scoring import calculate_step_test_score
        score, pfi = calculate_step_test_score(
            hr1=self.hr1,
            hr2=self.hr2,
            hr3=self.hr3
        )
        self._pfi = pfi
        return score


# =============================================================================
# MANUAL OVERRIDE MANAGEMENT
# =============================================================================

class ManualScoreOverride(models.Model):
    """
    Centralized manual score overrides using JSON field.
    Replaces the 15+ individual boolean fields in original model.
    """
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='manual_overrides'
    )
    
    # JSON field storing all manual overrides
    overrides = models.JSONField(
        default=dict,
        help_text="Manual score overrides in JSON format"
    )
    
    # Audit information
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='score_overrides'
    )
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'manual_score_overrides'
    
    def set_override(self, test_type: str, field: str, value, user):
        """Set a manual override for a specific test field."""
        if 'overrides' not in self.overrides:
            self.overrides = {}
        
        if test_type not in self.overrides:
            self.overrides[test_type] = {}
        
        self.overrides[test_type][field] = {
            'value': value,
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None
        }
        
        self.modified_by = user
        self.save()
    
    def get_override(self, test_type: str, field: str):
        """Get manual override value for a specific field."""
        try:
            return self.overrides.get(test_type, {}).get(field, {}).get('value')
        except (KeyError, AttributeError):
            return None
    
    def has_override(self, test_type: str, field: str) -> bool:
        """Check if a field has a manual override."""
        return self.get_override(test_type, field) is not None
    
    def clear_override(self, test_type: str, field: str, user):
        """Clear a manual override."""
        if test_type in self.overrides and field in self.overrides[test_type]:
            del self.overrides[test_type][field]
            
            # Clean up empty test_type
            if not self.overrides[test_type]:
                del self.overrides[test_type]
            
            self.modified_by = user
            self.save()


# =============================================================================
# KEEP EXISTING MODELS (No changes needed)
# =============================================================================

# These models are already well-structured:
# - NormativeData
# - TestStandard  
# - QuestionCategory
# - MultipleChoiceQuestion
# - QuestionChoice
# - QuestionResponse

# They can remain in the same file or be moved to separate modules as needed.


# =============================================================================
# MIGRATION BENEFITS
# =============================================================================

"""
Benefits of this refactoring:

1. **Reduced Model Complexity**:
   - Main Assessment model: 1,495 lines → ~150 lines
   - Each test model: ~100 lines (focused, single responsibility)

2. **Better Organization**:
   - One model per test type
   - Clear separation of concerns
   - Easier to understand and maintain

3. **Easier Testing**:
   - Test individual models in isolation
   - Mock specific test results
   - Clearer test scenarios

4. **Improved Performance**:
   - Only load test data when needed
   - Better database query patterns
   - Selective updates

5. **Future Extensibility**:
   - Easy to add new test types
   - Modify individual tests without affecting others
   - Support for test variations

6. **Manual Override Simplification**:
   - 15+ boolean fields → 1 JSON field
   - Centralized override management
   - Better audit trail

7. **Service Layer Integration**:
   - Clean interfaces for business logic
   - Easier to unit test scoring algorithms
   - Better separation of concerns

Migration Strategy:
1. Create new models alongside existing Assessment
2. Migrate data gradually using Django data migrations
3. Update views/forms to use new models
4. Remove old fields after migration complete
5. Use AssessmentService for score calculations
"""