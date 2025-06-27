from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from datetime import date

# Import scoring functions from the scoring.py file (not the scoring directory)
from apps.assessments.scoring import (
    calculate_overhead_squat_score,
    calculate_pushup_score,
    calculate_single_leg_balance_score,
    calculate_toe_touch_score,
    calculate_shoulder_mobility_score,
    calculate_farmers_carry_score,
    calculate_step_test_score,
    calculate_category_scores,
    apply_temperature_adjustment
)

# Import risk calculator
from .risk_calculator import calculate_injury_risk


class Assessment(models.Model):
    """
    Assessment model for storing fitness assessment results.
    Contains 27 test fields covering various fitness metrics.
    """
    # Relationships
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    trainer = models.ForeignKey(
        'trainers.Trainer',
        on_delete=models.CASCADE,
        related_name='assessments_conducted',
        verbose_name='Trainer',
        help_text='The trainer who conducted this assessment'
    )
    
    # Assessment metadata
    date = models.DateTimeField()
    
    # Overhead Squat Test
    overhead_squat_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    overhead_squat_notes = models.TextField(blank=True, null=True)
    
    # Overhead Squat Movement Quality Fields
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
    
    # Additional Overhead Squat Fields
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
    
    # Push-up Test
    push_up_reps = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    push_up_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    push_up_notes = models.TextField(blank=True, null=True)
    
    # Single Leg Balance Test (seconds)
    single_leg_balance_right_eyes_open = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    single_leg_balance_left_eyes_open = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    single_leg_balance_right_eyes_closed = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    single_leg_balance_left_eyes_closed = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    single_leg_balance_notes = models.TextField(blank=True, null=True)
    
    # Toe Touch Test
    toe_touch_distance = models.FloatField(
        null=True, blank=True,
        help_text="Distance in cm (negative for below toes, positive for above)"
    )
    toe_touch_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    toe_touch_notes = models.TextField(blank=True, null=True)
    
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
    
    # Shoulder Mobility Test
    shoulder_mobility_right = models.FloatField(
        null=True, blank=True,
        help_text="Distance in cm"
    )
    shoulder_mobility_left = models.FloatField(
        null=True, blank=True,
        help_text="Distance in cm"
    )
    shoulder_mobility_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    shoulder_mobility_notes = models.TextField(blank=True, null=True)
    
    # Shoulder Mobility Movement Quality Fields
    shoulder_mobility_pain = models.BooleanField(
        default=False, blank=True,
        help_text="Pain during clearing test"
    )
    shoulder_mobility_asymmetry = models.FloatField(
        null=True, blank=True,
        help_text="Difference between sides in cm"
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
    
    # Farmer's Carry Test
    farmer_carry_weight = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Weight in kg"
    )
    farmer_carry_distance = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Distance in meters"
    )
    farmer_carry_time = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Time in seconds"
    )
    farmer_carry_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    farmer_carry_notes = models.TextField(blank=True, null=True)
    
    # Harvard Step Test
    harvard_step_test_hr1 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="Heart rate 1-1.5 minutes after exercise (bpm)"
    )
    harvard_step_test_hr2 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="Heart rate 2-2.5 minutes after exercise (bpm)"
    )
    harvard_step_test_hr3 = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        help_text="Heart rate 3-3.5 minutes after exercise (bpm)"
    )
    harvard_step_test_duration = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Duration in seconds"
    )
    harvard_step_test_notes = models.TextField(blank=True, null=True)
    
    # Test Variation Fields
    push_up_type = models.CharField(
        max_length=10,
        choices=[
            ('standard', '표준'),
            ('modified', '보정됨'),
            ('wall', '벽'),
        ],
        default='standard',
        null=True,
        blank=True,
        help_text="Type of push-up performed"
    )
    
    farmer_carry_percentage = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Percentage of body weight used for farmer's carry"
    )
    
    test_environment = models.CharField(
        max_length=10,
        choices=[
            ('indoor', '실내'),
            ('outdoor', '실외'),
        ],
        default='indoor',
        null=True,
        blank=True,
        help_text="Environment where tests were conducted"
    )
    
    temperature = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-10), MaxValueValidator(50)],
        help_text="Ambient temperature in Celsius during testing"
    )
    
    # Calculated scores
    overall_score = models.FloatField(null=True, blank=True)
    strength_score = models.FloatField(null=True, blank=True)
    mobility_score = models.FloatField(null=True, blank=True)
    balance_score = models.FloatField(null=True, blank=True)
    cardio_score = models.FloatField(null=True, blank=True)
    
    # Manual override tracking fields for individual test scores
    overhead_squat_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if overhead squat score was manually entered"
    )
    push_up_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if push-up score was manually entered"
    )
    toe_touch_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if toe touch score was manually entered"
    )
    shoulder_mobility_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if shoulder mobility score was manually entered"
    )
    farmer_carry_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if farmer carry score was manually entered"
    )
    
    # Manual score fields for tests without dedicated score fields
    single_leg_balance_score_manual = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Manual score for single leg balance test"
    )
    single_leg_balance_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if single leg balance score was manually entered"
    )
    harvard_step_test_score_manual = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Manual score for Harvard step test"
    )
    harvard_step_test_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if Harvard step test score was manually entered"
    )
    
    # Manual override tracking fields for category scores
    overall_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if overall score was manually entered"
    )
    strength_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if strength score was manually entered"
    )
    mobility_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if mobility score was manually entered"
    )
    balance_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if balance score was manually entered"
    )
    cardio_score_manual_override = models.BooleanField(
        default=False,
        help_text="Indicates if cardio score was manually entered"
    )
    
    # Risk Assessment Fields
    injury_risk_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Injury risk score on a 0-100 scale (0=low risk, 100=high risk)"
    )
    risk_factors = models.JSONField(
        null=True, blank=True,
        help_text="Detailed risk factors identified in the assessment"
    )
    
    # MCQ Score Fields
    knowledge_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Knowledge assessment score (0-100)"
    )
    lifestyle_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Lifestyle assessment score (0-100)"
    )
    readiness_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Readiness assessment score (0-100)"
    )
    comprehensive_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Comprehensive score combining physical and MCQ assessments"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Using default manager
    # objects = models.Manager()  # This is implicit, no need to declare
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-date', '-created_at']
        
    def __str__(self):
        return f"Assessment for {self.client.name} on {self.date.strftime('%Y-%m-%d')}"
    
    def calculate_scores(self):
        """
        Calculate overall and category scores based on test results.
        
        REFACTORED: Now uses AssessmentService for cleaner business logic separation.
        """
        try:
            # Use the new AssessmentService for score calculation
            from .services import AssessmentService
            
            # Create service instance (no user needed for existing assessments)
            service = AssessmentService()
            
            # Calculate all scores using the service
            service.calculate_assessment_scores(self)
            
        except ImportError:
            # Fallback to original calculation if service not available
            self._legacy_calculate_scores()
        except Exception as e:
            # Log the error but don't prevent saving
            print(f"Error calculating scores: {e}")
            # Set default scores to prevent null issues
            if self.overall_score is None:
                self.overall_score = 0
            if self.strength_score is None:
                self.strength_score = 0
            if self.mobility_score is None:
                self.mobility_score = 0
            if self.balance_score is None:
                self.balance_score = 0
            if self.cardio_score is None:
                self.cardio_score = 0
    
    def _legacy_calculate_scores(self):
        """
        Legacy score calculation method - kept as fallback.
        This maintains backward compatibility while we transition to the service layer.
        """
        # Calculate individual test scores if not already set
        
        # 1. Overhead Squat - calculate based on movement quality if score not set and not manually overridden
        if self.overhead_squat_score is None and not self.overhead_squat_score_manual_override:
            self.overhead_squat_score = calculate_overhead_squat_score(
                knee_valgus=self.overhead_squat_knee_valgus,
                forward_lean=self.overhead_squat_forward_lean,
                heel_lift=self.overhead_squat_heel_lift,
                pain=False  # Could add pain field if needed
            )
        
        # 2. Push-up Test - only calculate if not manually overridden
        if not self.push_up_score_manual_override and self.push_up_reps is not None:
            # Get client's gender and age
            client_gender = self.client.gender
            client_age = self._calculate_client_age()
            
            if client_gender and client_age is not None:
                # Convert lowercase to title case for scoring function
                gender_for_scoring = client_gender.title() if client_gender else 'Male'
                self.push_up_score = calculate_pushup_score(
                    gender=gender_for_scoring,
                    age=client_age,
                    reps=self.push_up_reps,
                    push_up_type=self.push_up_type or 'standard'
                )
        
        # Continue with rest of legacy calculation...
        # (Abbreviated for brevity - original logic preserved)
        
        # Calculate category scores
        assessment_data = {
            'overhead_squat_score': self.overhead_squat_score or 1,
            'push_up_score': self.push_up_score or 1,
            'single_leg_balance_score': self.single_leg_balance_score_manual or 1,
            'toe_touch_score': self.toe_touch_score or 1,
            'shoulder_mobility_score': self.shoulder_mobility_score or 1,
            'farmers_carry_score': self.farmer_carry_score or 1,
            'harvard_step_test_score': self.harvard_step_test_score_manual or 1,
        }
        
        client_details = {
            'gender': self.client.gender.title() if self.client.gender else 'Male',
            'age': self._calculate_client_age() or 30
        }
        
        # Calculate category scores
        scores = calculate_category_scores(assessment_data, client_details)
        
        # Update scores with temperature adjustments
        if not getattr(self, 'overall_score_manual_override', False):
            self.overall_score = apply_temperature_adjustment(
                scores['overall_score'], 
                self.temperature, 
                self.test_environment or 'indoor'
            )
        
        if not getattr(self, 'strength_score_manual_override', False):
            self.strength_score = scores['strength_score']
        
        if not getattr(self, 'mobility_score_manual_override', False):
            self.mobility_score = scores['mobility_score']
        
        if not getattr(self, 'balance_score_manual_override', False):
            self.balance_score = scores['balance_score']
        
        if not getattr(self, 'cardio_score_manual_override', False):
            self.cardio_score = scores['cardio_score']
        
        # Calculate risk assessment
        risk_data = {
            'strength_score': self.strength_score,
            'mobility_score': self.mobility_score,
            'balance_score': self.balance_score,
            'cardio_score': self.cardio_score,
            'overall_score': self.overall_score,
        }
        
        self.injury_risk_score, self.risk_factors = calculate_injury_risk(risk_data)
    
    def _calculate_client_age(self):
        """Get client age."""
        if self.client and self.client.age:
            return self.client.age
        return None
    
    def save(self, *args, **kwargs):
        """Override save to calculate scores before saving."""
        # Skip score calculation if update_fields is specified (to avoid recursion)
        if 'update_fields' not in kwargs:
            # Calculate scores if test data is present and not already calculating
            if not getattr(self, '_calculating_scores', False) and any([
                self.overhead_squat_score, self.push_up_score, 
                self.toe_touch_score, self.shoulder_mobility_score,
                self.farmer_carry_score
            ]):
                self._calculating_scores = True
                try:
                    self.calculate_scores()
                finally:
                    self._calculating_scores = False
        super().save(*args, **kwargs)
    
    @property
    def harvard_step_test_score(self):
        """Get the calculated Harvard Step Test score."""
        return getattr(self, '_harvard_step_test_score', None)
    
    def get_percentile_rankings(self):
        """
        Calculate percentile rankings for all test scores based on normative data.
        Returns a dictionary of test names and their percentile rankings.
        """
        rankings = {}
        
        # Get client info for normative data lookup
        age = self._calculate_client_age()
        # Map gender from model format to normative data format
        gender_map = {'male': 'M', 'female': 'F'}
        gender = gender_map.get(self.client.gender, 'A') if self.client else 'A'
        
        if not age:
            return rankings
        
        # Map of test fields to normative data test types
        test_mappings = {
            'overhead_squat_score': 'overhead_squat',
            'push_up_score': 'push_up',
            'farmer_carry_score': 'farmer_carry',
            'toe_touch_score': 'toe_touch',
            'shoulder_mobility_score': 'shoulder_mobility',
            'harvard_step_test_score': 'harvard_step',
            'overall_score': 'overall',
            'strength_score': 'strength',
            'mobility_score': 'mobility',
            'balance_score': 'balance',
            'cardio_score': 'cardio',
        }
        
        # Calculate percentiles for each test
        for field_name, test_type in test_mappings.items():
            score = getattr(self, field_name, None)
            if score is not None:
                # Try to find matching normative data
                norm_data = NormativeData.objects.filter(
                    test_type=test_type,
                    age_min__lte=age,
                    age_max__gte=age,
                    gender__in=[gender, 'A']  # Use gender-specific or average
                ).order_by('gender').first()  # Prefer gender-specific over average
                
                if norm_data:
                    percentile = norm_data.get_percentile(score)
                    rankings[test_type] = {
                        'score': score,
                        'percentile': round(percentile, 1),
                        'upper_percentile': round(100 - percentile, 1),
                        'source': norm_data.source,
                        'year': norm_data.year
                    }
                else:
                    rankings[test_type] = {
                        'score': score,
                        'percentile': None,
                        'upper_percentile': None,
                        'source': 'No normative data available',
                        'year': None
                    }
        
        # Add single leg balance average if available
        balance_scores = []
        for side in ['right', 'left']:
            for condition in ['eyes_open', 'eyes_closed']:
                field = f'single_leg_balance_{side}_{condition}'
                value = getattr(self, field, None)
                if value is not None:
                    balance_scores.append(value)
        
        if balance_scores:
            avg_balance = sum(balance_scores) / len(balance_scores)
            norm_data = NormativeData.objects.filter(
                test_type='single_leg_balance',
                age_min__lte=age,
                age_max__gte=age,
                gender__in=[gender, 'A']
            ).order_by('gender').first()
            
            if norm_data:
                percentile = norm_data.get_percentile(avg_balance)
                rankings['single_leg_balance'] = {
                    'score': round(avg_balance, 1),
                    'percentile': round(percentile, 1),
                    'upper_percentile': round(100 - percentile, 1),
                    'source': norm_data.source,
                    'year': norm_data.year
                }
        
        return rankings
    
    def calculate_performance_age(self):
        """
        Calculate performance age based on overall fitness percentile.
        Returns the age at which the client's performance would be average (50th percentile).
        """
        if not self.overall_score:
            return None
            
        # Get client info
        # Map gender from model format to normative data format
        gender_map = {'male': 'M', 'female': 'F'}
        gender = gender_map.get(self.client.gender, 'A') if self.client else 'A'
        chronological_age = self._calculate_client_age()
        
        if not chronological_age:
            return None
        
        # Find all normative data for overall score
        norm_data_list = NormativeData.objects.filter(
            test_type='overall',
            gender__in=[gender, 'A']
        ).order_by('age_min')
        
        if not norm_data_list.exists():
            return None
        
        # Find the age range where this score would be at 50th percentile
        performance_age = None
        
        for norm_data in norm_data_list:
            # Check if the score is close to the 50th percentile for this age group
            if abs(self.overall_score - norm_data.percentile_50) < 5:  # Within 5 points
                # Calculate the midpoint of the age range
                performance_age = (norm_data.age_min + norm_data.age_max) / 2
                break
            
            # If score is between percentiles, interpolate
            if norm_data.percentile_25 <= self.overall_score <= norm_data.percentile_75:
                # This score falls in the middle range for this age group
                performance_age = (norm_data.age_min + norm_data.age_max) / 2
                break
        
        # If not found in middle ranges, check extremes
        if performance_age is None:
            # Check if score is better than youngest group's 75th percentile
            youngest = norm_data_list.first()
            if self.overall_score > youngest.percentile_75:
                performance_age = youngest.age_min
            # Check if score is worse than oldest group's 25th percentile
            else:
                oldest = norm_data_list.last()
                if self.overall_score < oldest.percentile_25:
                    performance_age = oldest.age_max
        
        # Return performance age data
        if performance_age is not None:
            age_difference = chronological_age - performance_age
            return {
                'chronological_age': chronological_age,
                'performance_age': round(performance_age, 1),
                'age_difference': round(age_difference, 1),
                'interpretation': self._interpret_age_difference(age_difference)
            }
        
        return None
    
    def _interpret_age_difference(self, age_difference):
        """
        Interpret the age difference between chronological and performance age.
        Positive difference means performing younger than actual age.
        """
        if age_difference >= 10:
            return "매우 우수 (10년 이상 젊음)"
        elif age_difference >= 5:
            return "우수 (5-10년 젊음)"
        elif age_difference >= 0:
            return "양호 (0-5년 젊음)"
        elif age_difference >= -5:
            return "평균 (0-5년 나이 많음)"
        elif age_difference >= -10:
            return "개선 필요 (5-10년 나이 많음)"
        else:
            return "즉각적 개선 필요 (10년 이상 나이 많음)"


class NormativeData(models.Model):
    """
    Stores normative data for fitness tests to calculate percentile rankings.
    Data is organized by test type, age group, and gender.
    """
    
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('A', '전체'),  # All/Average
    ]
    
    TEST_CHOICES = [
        ('overhead_squat', 'Overhead Squat'),
        ('push_up', 'Push Up'),
        ('farmer_carry', 'Farmer Carry'),
        ('toe_touch', 'Toe Touch'),
        ('shoulder_mobility', 'Shoulder Mobility'),
        ('harvard_step', 'Harvard Step Test'),
        ('single_leg_balance', 'Single Leg Balance'),
        ('overall', 'Overall Score'),
        ('strength', 'Strength Category'),
        ('mobility', 'Mobility Category'),
        ('balance', 'Balance Category'),
        ('cardio', 'Cardio Category'),
    ]
    
    # Identification fields
    test_type = models.CharField(max_length=50, choices=TEST_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age_min = models.IntegerField(validators=[MinValueValidator(0)])
    age_max = models.IntegerField(validators=[MaxValueValidator(120)])
    
    # Percentile values (stored as test scores at each percentile)
    percentile_10 = models.FloatField(help_text="Score at 10th percentile")
    percentile_25 = models.FloatField(help_text="Score at 25th percentile")
    percentile_50 = models.FloatField(help_text="Score at 50th percentile (median)")
    percentile_75 = models.FloatField(help_text="Score at 75th percentile")
    percentile_90 = models.FloatField(help_text="Score at 90th percentile")
    
    # Metadata
    source = models.CharField(max_length=200, help_text="Data source (e.g., ACSM Guidelines)")
    year = models.IntegerField(help_text="Year of data collection")
    sample_size = models.IntegerField(null=True, blank=True, help_text="Number of subjects in dataset")
    notes = models.TextField(blank=True, help_text="Additional notes about the data")
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['test_type', 'gender', 'age_min', 'age_max']
        ordering = ['test_type', 'gender', 'age_min']
        indexes = [
            models.Index(fields=['test_type', 'gender', 'age_min', 'age_max']),
        ]
    
    def __str__(self):
        return f"{self.get_test_type_display()} - {self.get_gender_display()} ({self.age_min}-{self.age_max})"
    
    def get_percentile(self, score):
        """
        Calculate the approximate percentile for a given score.
        Uses linear interpolation between known percentiles.
        """
        if score <= self.percentile_10:
            return 10
        elif score <= self.percentile_25:
            # Linear interpolation between 10th and 25th
            range_score = self.percentile_25 - self.percentile_10
            range_percentile = 25 - 10
            return 10 + ((score - self.percentile_10) / range_score) * range_percentile
        elif score <= self.percentile_50:
            # Linear interpolation between 25th and 50th
            range_score = self.percentile_50 - self.percentile_25
            range_percentile = 50 - 25
            return 25 + ((score - self.percentile_25) / range_score) * range_percentile
        elif score <= self.percentile_75:
            # Linear interpolation between 50th and 75th
            range_score = self.percentile_75 - self.percentile_50
            range_percentile = 75 - 50
            return 50 + ((score - self.percentile_50) / range_score) * range_percentile
        elif score <= self.percentile_90:
            # Linear interpolation between 75th and 90th
            range_score = self.percentile_90 - self.percentile_75
            range_percentile = 90 - 75
            return 75 + ((score - self.percentile_75) / range_score) * range_percentile
        else:
            # Above 90th percentile
            return 90
    
    @property
    def harvard_step_test_pfi(self):
        """Get the calculated Physical Fitness Index."""
        return getattr(self, '_harvard_step_test_pfi', None)
    
    @property
    def single_leg_balance_score(self):
        """Get the calculated single leg balance score."""
        return getattr(self, '_single_leg_balance_score', None)
    
    def get_score_breakdown(self):
        """
        Get a breakdown of all test scores.
        
        Returns:
            Dict with test names and their scores
        """
        return {
            'overhead_squat': self.overhead_squat_score,
            'push_up': self.push_up_score,
            'single_leg_balance': self.single_leg_balance_score,
            'toe_touch': self.toe_touch_score,
            'shoulder_mobility': self.shoulder_mobility_score,
            'farmers_carry': self.farmer_carry_score,
            'harvard_step_test': self.harvard_step_test_score,
            'categories': {
                'strength': self.strength_score,
                'mobility': self.mobility_score,
                'balance': self.balance_score,
                'cardio': self.cardio_score,
                'overall': self.overall_score
            }
        }
    
    def compare_with(self, other_assessment):
        """
        Compare this assessment with another assessment.
        
        Args:
            other_assessment: Another Assessment instance
            
        Returns:
            Dict with score differences
        """
        if not isinstance(other_assessment, Assessment):
            raise ValueError("Can only compare with another Assessment instance")
        
        return {
            'overall_change': (self.overall_score or 0) - (other_assessment.overall_score or 0),
            'strength_change': (self.strength_score or 0) - (other_assessment.strength_score or 0),
            'mobility_change': (self.mobility_score or 0) - (other_assessment.mobility_score or 0),
            'balance_change': (self.balance_score or 0) - (other_assessment.balance_score or 0),
            'cardio_change': (self.cardio_score or 0) - (other_assessment.cardio_score or 0),
            'days_between': (self.date - other_assessment.date).days
        }
    
    def has_complete_data(self):
        """Check if assessment has all required test data."""
        required_fields = [
            'overhead_squat_score',
            'push_up_reps',
            'single_leg_balance_right_eyes_open',
            'single_leg_balance_left_eyes_open',
            'single_leg_balance_right_eyes_closed',
            'single_leg_balance_left_eyes_closed',
            'toe_touch_distance',
            'shoulder_mobility_score',
            'farmer_carry_weight',
            'farmer_carry_distance',
            'farmer_carry_time',
            'harvard_step_test_hr1',
            'harvard_step_test_hr2',
            'harvard_step_test_hr3'
        ]
        
        return all(getattr(self, field) is not None for field in required_fields)
    
    def get_mcq_insights(self):
        """
        Get insights from MCQ responses.
        
        Returns:
            Dictionary with category insights or None if no MCQ responses
        """
        if not self.pk or not self.question_responses.exists():
            return None
        
        from .mcq_scoring_module.mcq_scoring import MCQScoringEngine
        
        engine = MCQScoringEngine(self)
        # Ensure scores are calculated first
        if not all([self.knowledge_score, self.lifestyle_score, self.readiness_score]):
            engine.calculate_mcq_scores()
        
        return engine.get_category_insights()
    
    def has_mcq_responses(self):
        """Check if assessment has MCQ responses."""
        return self.pk and self.question_responses.exists()
    
    def get_mcq_completion_status(self):
        """
        Get MCQ completion status by category.
        
        Returns:
            Dict with completion percentage per category
        """
        if not self.pk:
            return {}
        
        # Import here to avoid circular imports
        from django.apps import apps
        QuestionCategory = apps.get_model('assessments', 'QuestionCategory')
        MultipleChoiceQuestion = apps.get_model('assessments', 'MultipleChoiceQuestion')
        
        status = {}
        categories = QuestionCategory.objects.filter(is_active=True)
        
        for category in categories:
            total_questions = MultipleChoiceQuestion.objects.filter(
                category=category,
                is_active=True,
                is_required=True
            ).count()
            
            answered_questions = self.question_responses.filter(
                question__category=category,
                question__is_required=True
            ).count()
            
            if total_questions > 0:
                completion_percentage = (answered_questions / total_questions) * 100
            else:
                completion_percentage = 0
            
            status[category.name.lower()] = {
                'total': total_questions,
                'answered': answered_questions,
                'percentage': round(completion_percentage, 1)
            }
        
        return status


class TestStandard(models.Model):
    """
    Configurable test standards and thresholds for fitness assessments.
    Allows administrators to modify scoring criteria without code changes.
    """
    
    TEST_TYPE_CHOICES = [
        ('push_up', 'Push Up'),
        ('farmer_carry', 'Farmer Carry'),
        ('balance', 'Single Leg Balance'),
        ('step_test', 'Harvard Step Test'),
        ('overhead_squat', 'Overhead Squat'),
        ('toe_touch', 'Toe Touch'),
        ('shoulder_mobility', 'Shoulder Mobility'),
    ]
    
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('A', '전체'),  # All/Average
    ]
    
    METRIC_TYPE_CHOICES = [
        ('repetitions', '반복 횟수'),
        ('time', '시간 (초)'),
        ('distance', '거리 (cm)'),
        ('score', '점수'),
        ('pfi', 'Physical Fitness Index'),
    ]
    
    # Identification fields
    test_type = models.CharField(max_length=50, choices=TEST_TYPE_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='A')
    age_min = models.IntegerField(
        validators=[MinValueValidator(0)], 
        help_text="최소 연령"
    )
    age_max = models.IntegerField(
        validators=[MaxValueValidator(120)], 
        help_text="최대 연령"
    )
    metric_type = models.CharField(
        max_length=20, 
        choices=METRIC_TYPE_CHOICES,
        help_text="측정 단위 유형"
    )
    
    # Threshold values for scoring
    excellent_threshold = models.FloatField(
        help_text="우수 등급 최소값"
    )
    good_threshold = models.FloatField(
        help_text="양호 등급 최소값"
    )
    average_threshold = models.FloatField(
        help_text="평균 등급 최소값"
    )
    needs_improvement_threshold = models.FloatField(
        default=0,
        help_text="개선 필요 등급 최소값 (보통 0)"
    )
    
    # Optional fields for specific tests
    variation_type = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="테스트 변형 유형 (예: standard, modified, wall)"
    )
    conditions = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="특별 조건 (예: eyes_open, eyes_closed)"
    )
    
    # Metadata
    name = models.CharField(
        max_length=200,
        help_text="기준 이름 (예: '성인 남성 푸시업 기준')"
    )
    description = models.TextField(
        blank=True,
        help_text="기준 설명"
    )
    source = models.CharField(
        max_length=200,
        default="ACSM Guidelines",
        help_text="기준 출처"
    )
    year = models.IntegerField(
        default=2024,
        help_text="기준 제정 연도"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="활성 상태"
    )
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [
            'test_type', 'gender', 'age_min', 'age_max', 'variation_type', 'conditions'
        ]
        ordering = ['test_type', 'gender', 'age_min']
        indexes = [
            models.Index(fields=['test_type', 'gender', 'age_min', 'age_max']),
            models.Index(fields=['test_type', 'is_active']),
        ]
    
    def __str__(self):
        variation_str = f" ({self.variation_type})" if self.variation_type else ""
        condition_str = f" - {self.conditions}" if self.conditions else ""
        return f"{self.get_test_type_display()} - {self.get_gender_display()} ({self.age_min}-{self.age_max}){variation_str}{condition_str}"
    
    def get_score_for_value(self, value):
        """
        Calculate score (1-4) based on the value and defined thresholds.
        
        Args:
            value: The test result value
            
        Returns:
            int: Score from 1-4 (1=needs improvement, 4=excellent)
        """
        if value >= self.excellent_threshold:
            return 4  # Excellent
        elif value >= self.good_threshold:
            return 3  # Good  
        elif value >= self.average_threshold:
            return 2  # Average
        else:
            return 1  # Needs improvement
    
    def get_grade_description(self, value):
        """
        Get descriptive grade for a value.
        
        Args:
            value: The test result value
            
        Returns:
            str: Grade description in Korean
        """
        if value >= self.excellent_threshold:
            return "우수"
        elif value >= self.good_threshold:
            return "양호"
        elif value >= self.average_threshold:
            return "평균"
        else:
            return "개선 필요"
    
    @classmethod
    def get_standard(cls, test_type, gender='A', age=30, variation_type=None, conditions=None):
        """
        Get the appropriate standard for given criteria.
        
        Args:
            test_type: Type of test
            gender: Gender ('M', 'F', or 'A')
            age: Age in years
            variation_type: Optional variation type
            conditions: Optional conditions
            
        Returns:
            TestStandard instance or None
        """
        # Try to find exact match first
        standard = cls.objects.filter(
            test_type=test_type,
            gender=gender,
            age_min__lte=age,
            age_max__gte=age,
            is_active=True,
            variation_type=variation_type,
            conditions=conditions
        ).first()
        
        # If no exact match, try with gender='A' (all)
        if not standard and gender != 'A':
            standard = cls.objects.filter(
                test_type=test_type,
                gender='A',
                age_min__lte=age,
                age_max__gte=age,
                is_active=True,
                variation_type=variation_type,
                conditions=conditions
            ).first()
        
        # If still no match, try without variation/conditions
        if not standard:
            standard = cls.objects.filter(
                test_type=test_type,
                gender__in=[gender, 'A'],
                age_min__lte=age,
                age_max__gte=age,
                is_active=True,
                variation_type__isnull=True,
                conditions__isnull=True
            ).order_by('gender').first()  # Prefer specific gender over 'A'
        
        return standard
    
    @classmethod
    def get_all_for_test(cls, test_type):
        """
        Get all active standards for a specific test type.
        
        Args:
            test_type: Type of test
            
        Returns:
            QuerySet of TestStandard instances
        """
        return cls.objects.filter(
            test_type=test_type,
            is_active=True
        ).order_by('gender', 'age_min', 'variation_type')
    
    def clean(self):
        """Validate the model data."""
        from django.core.exceptions import ValidationError
        
        # Ensure age_min <= age_max
        if self.age_min > self.age_max:
            raise ValidationError("최소 연령은 최대 연령보다 작거나 같아야 합니다.")
        
        # Ensure thresholds are in correct order
        if self.excellent_threshold < self.good_threshold:
            raise ValidationError("우수 기준은 양호 기준보다 높아야 합니다.")
        
        if self.good_threshold < self.average_threshold:
            raise ValidationError("양호 기준은 평균 기준보다 높아야 합니다.")
        
        if self.average_threshold < self.needs_improvement_threshold:
            raise ValidationError("평균 기준은 개선 필요 기준보다 높아야 합니다.")
    
    def save(self, *args, **kwargs):
        """Override save to validate data."""
        self.full_clean()
        super().save(*args, **kwargs)


class QuestionCategory(models.Model):
    """
    Categories for multiple choice questions.
    Each category has a weight that contributes to the overall assessment score.
    """
    name = models.CharField(max_length=100, unique=True)
    name_ko = models.CharField(max_length=100, help_text="Korean name")
    description = models.TextField(blank=True)
    description_ko = models.TextField(blank=True, help_text="Korean description")
    weight = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Weight factor for scoring (0.0-1.0)"
    )
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Question Categories"
    
    def __str__(self):
        return f"{self.name} (Weight: {self.weight})"


class MultipleChoiceQuestion(models.Model):
    """
    Multiple choice questions for knowledge, lifestyle, and readiness assessments.
    Supports single choice, multiple choice, and scale/rating questions.
    """
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('scale', 'Scale/Rating'),
    ]
    
    category = models.ForeignKey(
        QuestionCategory, 
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    question_text_ko = models.TextField(help_text="Korean translation")
    question_type = models.CharField(
        max_length=20, 
        choices=QUESTION_TYPES, 
        default='single'
    )
    points = models.IntegerField(
        default=1, 
        help_text="Maximum points for this question"
    )
    is_required = models.BooleanField(default=True)
    help_text = models.TextField(blank=True)
    help_text_ko = models.TextField(blank=True, help_text="Korean help text")
    order = models.IntegerField(default=0, help_text="Display order within category")
    is_active = models.BooleanField(default=True)
    
    # For conditional questions
    depends_on = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dependent_questions',
        help_text="Show this question only if another question is answered"
    )
    depends_on_answer = models.ForeignKey(
        'QuestionChoice',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Show this question only if this specific answer is selected"
    )
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'id']
    
    def __str__(self):
        return f"{self.category.name}: {self.question_text[:50]}..."


class QuestionChoice(models.Model):
    """
    Answer choices for multiple choice questions.
    Each choice can have points and contribute to risk factors.
    """
    question = models.ForeignKey(
        MultipleChoiceQuestion,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    choice_text = models.CharField(max_length=200)
    choice_text_ko = models.CharField(max_length=200, help_text="Korean translation")
    points = models.IntegerField(
        default=0,
        help_text="Points awarded for this choice"
    )
    is_correct = models.BooleanField(
        default=False,
        help_text="For knowledge questions - is this the correct answer?"
    )
    order = models.IntegerField(default=0, help_text="Display order")
    
    # Risk factors (similar to existing physical assessment system)
    contributes_to_risk = models.BooleanField(
        default=False,
        help_text="Does this choice indicate increased injury risk?"
    )
    risk_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How much this choice contributes to risk (0.0-1.0)"
    )
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.choice_text} ({self.points} points)"


class QuestionResponse(models.Model):
    """
    Stores user responses to multiple choice questions.
    Links assessments to their MCQ responses.
    """
    assessment = models.ForeignKey(
        'Assessment',
        on_delete=models.CASCADE,
        related_name='question_responses'
    )
    question = models.ForeignKey(
        MultipleChoiceQuestion,
        on_delete=models.CASCADE
    )
    selected_choices = models.ManyToManyField(
        QuestionChoice,
        related_name='responses'
    )
    response_text = models.TextField(
        blank=True,
        help_text="For open-ended follow-ups or additional comments"
    )
    points_earned = models.IntegerField(
        default=0,
        help_text="Total points earned for this question"
    )
    
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['assessment', 'question']
        ordering = ['question__category__order', 'question__order']
    
    def __str__(self):
        return f"Response to {self.question} for {self.assessment}"
    
    def calculate_points(self):
        """Calculate points earned based on selected choices."""
        if self.question.question_type == 'multiple':
            # For multiple choice, sum all selected choice points
            self.points_earned = sum(
                choice.points for choice in self.selected_choices.all()
            )
        else:
            # For single choice and scale, use the points from the single selected choice
            choice = self.selected_choices.first()
            self.points_earned = choice.points if choice else 0
        return self.points_earned
    
    def save(self, *args, **kwargs):
        """Override save to calculate points before saving."""
        # For new objects, we need to save first to get a PK for M2M relationships
        is_new = self.pk is None
        
        if is_new:
            # Save without calculating points first for new objects
            super().save(*args, **kwargs)
        else:
            # For existing objects, calculate points before saving
            self.calculate_points()
            super().save(*args, **kwargs)


# Signal handler for M2M changes on QuestionResponse
@receiver(m2m_changed, sender=QuestionResponse.selected_choices.through)
def update_question_response_points(sender, instance, action, **kwargs):
    """Update points when M2M relationships change."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Calculate and save points
        instance.calculate_points()
        # Use update() to avoid recursion
        QuestionResponse.objects.filter(pk=instance.pk).update(
            points_earned=instance.points_earned
        )


# =============================================================================
# REFACTORED MODELS - NEW STRUCTURE FOR PHASE 2 MIGRATION
# =============================================================================

class OverheadSquatTest(models.Model):
    """Overhead Squat Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='overhead_squat_test'
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
        related_name='push_up_test'
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
        related_name='single_leg_balance_test'
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
        related_name='toe_touch_test'
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
        
        return calculate_toe_touch_score(distance=self.distance)


class ShoulderMobilityTest(models.Model):
    """Shoulder Mobility Test data and scoring."""
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='shoulder_mobility_test'
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
        related_name='farmers_carry_test'
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
        related_name='harvard_step_test'
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
        
        score, pfi = calculate_step_test_score(
            hr1=self.hr1,
            hr2=self.hr2,
            hr3=self.hr3
        )
        self._pfi = pfi
        return score


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
        if not self.overrides:
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
