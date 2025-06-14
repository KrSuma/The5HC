from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date

# Import scoring functions
from .scoring import (
    calculate_overhead_squat_score,
    calculate_pushup_score,
    calculate_single_leg_balance_score,
    calculate_toe_touch_score,
    calculate_shoulder_mobility_score,
    calculate_farmers_carry_score,
    calculate_step_test_score,
    calculate_category_scores
)


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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments_conducted'
    )
    
    # Assessment metadata
    date = models.DateTimeField()
    
    # Overhead Squat Test
    overhead_squat_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    overhead_squat_notes = models.TextField(blank=True, null=True)
    
    # Push-up Test
    push_up_reps = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    push_up_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
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
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    toe_touch_notes = models.TextField(blank=True, null=True)
    
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
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    shoulder_mobility_notes = models.TextField(blank=True, null=True)
    
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
        validators=[MinValueValidator(0), MaxValueValidator(5)]
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
    
    # Calculated scores
    overall_score = models.FloatField(null=True, blank=True)
    strength_score = models.FloatField(null=True, blank=True)
    mobility_score = models.FloatField(null=True, blank=True)
    balance_score = models.FloatField(null=True, blank=True)
    cardio_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessments'
        ordering = ['-date', '-created_at']
        
    def __str__(self):
        return f"Assessment for {self.client.name} on {self.date.strftime('%Y-%m-%d')}"
    
    def calculate_scores(self):
        """
        Calculate overall and category scores based on test results.
        This method should be called after saving test results.
        """
        try:
            # Calculate individual test scores if not already set
            
            # 1. Overhead Squat - already has score field
            if self.overhead_squat_score is None and hasattr(self, 'overhead_squat_form_quality'):
                # If we had a form quality field, we'd use it
                # For now, keep the manually entered score
                pass
            
            # 2. Push-up Test
            if self.push_up_score is None and self.push_up_reps is not None:
                # Get client's gender and age
                client_gender = self.client.gender
                client_age = self._calculate_client_age()
                
                if client_gender and client_age is not None:
                    # Convert lowercase to title case for scoring function
                    gender_for_scoring = client_gender.title() if client_gender else 'Male'
                    self.push_up_score = calculate_pushup_score(
                        gender=gender_for_scoring,
                        age=client_age,
                        reps=self.push_up_reps
                    )
            
            # 3. Single Leg Balance - calculate if we have the times
            if all([
                self.single_leg_balance_right_eyes_open is not None,
                self.single_leg_balance_left_eyes_open is not None,
                self.single_leg_balance_right_eyes_closed is not None,
                self.single_leg_balance_left_eyes_closed is not None
            ]):
                balance_score = calculate_single_leg_balance_score(
                    right_open=self.single_leg_balance_right_eyes_open,
                    left_open=self.single_leg_balance_left_eyes_open,
                    right_closed=self.single_leg_balance_right_eyes_closed,
                    left_closed=self.single_leg_balance_left_eyes_closed
                )
                # Store as a property or in notes since we don't have a dedicated field
                self._single_leg_balance_score = balance_score
            else:
                self._single_leg_balance_score = None
            
            # 4. Toe Touch Test
            if self.toe_touch_score is None and self.toe_touch_distance is not None:
                self.toe_touch_score = calculate_toe_touch_score(
                    distance=self.toe_touch_distance
                )
            
            # 5. Shoulder Mobility - already has score field
            # Keep the manually entered score
            
            # 6. Farmer's Carry
            if self.farmer_carry_score is None and all([
                self.farmer_carry_weight is not None,
                self.farmer_carry_distance is not None,
                self.farmer_carry_time is not None
            ]):
                client_gender = self.client.gender
                if client_gender:
                    # Convert lowercase to title case for scoring function
                    gender_for_scoring = client_gender.title() if client_gender else 'Male'
                    self.farmer_carry_score = calculate_farmers_carry_score(
                        gender=gender_for_scoring,
                        weight=self.farmer_carry_weight,
                        distance=self.farmer_carry_distance,
                        time=self.farmer_carry_time
                    )
            
            # 7. Harvard Step Test
            if all([
                self.harvard_step_test_hr1 is not None,
                self.harvard_step_test_hr2 is not None,
                self.harvard_step_test_hr3 is not None
            ]):
                step_score, pfi = calculate_step_test_score(
                    hr1=self.harvard_step_test_hr1,
                    hr2=self.harvard_step_test_hr2,
                    hr3=self.harvard_step_test_hr3
                )
                # Store as properties since we don't have dedicated fields
                self._harvard_step_test_score = step_score
                self._harvard_step_test_pfi = pfi
            else:
                self._harvard_step_test_score = None
                self._harvard_step_test_pfi = None
            
            # Prepare data for category score calculation
            assessment_data = {
                'overhead_squat_score': self.overhead_squat_score or 1,
                'push_up_score': self.push_up_score or 1,
                'single_leg_balance_right_open': self.single_leg_balance_right_eyes_open or 0,
                'single_leg_balance_left_open': self.single_leg_balance_left_eyes_open or 0,
                'single_leg_balance_right_closed': self.single_leg_balance_right_eyes_closed or 0,
                'single_leg_balance_left_closed': self.single_leg_balance_left_eyes_closed or 0,
                'toe_touch_score': self.toe_touch_score or 1,
                'shoulder_mobility_score': self.shoulder_mobility_score or 1,
                'farmers_carry_score': self.farmer_carry_score or 1,
                'step_test_hr1': self.harvard_step_test_hr1 or 90,
                'step_test_hr2': self.harvard_step_test_hr2 or 80,
                'step_test_hr3': self.harvard_step_test_hr3 or 70
            }
            
            client_details = {
                'gender': self.client.gender.title() if self.client.gender else 'Male',
                'age': self._calculate_client_age() or 30
            }
            
            # Calculate category scores
            scores = calculate_category_scores(assessment_data, client_details)
            
            # Update model fields
            self.overall_score = scores['overall_score']
            self.strength_score = scores['strength_score']
            self.mobility_score = scores['mobility_score']
            self.balance_score = scores['balance_score']
            self.cardio_score = scores['cardio_score']
            
            # Store PFI as a property
            self._pfi = scores.get('pfi')
            
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
    
    def _calculate_client_age(self):
        """Get client age."""
        if self.client and hasattr(self.client, 'age'):
            return self.client.age
        return None
    
    def save(self, *args, **kwargs):
        """Override save to calculate scores before saving."""
        # Calculate scores if test data is present
        if any([self.overhead_squat_score, self.push_up_score, 
                self.toe_touch_score, self.shoulder_mobility_score,
                self.farmer_carry_score]):
            self.calculate_scores()
        super().save(*args, **kwargs)
    
    @property
    def harvard_step_test_score(self):
        """Get the calculated Harvard Step Test score."""
        return getattr(self, '_harvard_step_test_score', None)
    
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