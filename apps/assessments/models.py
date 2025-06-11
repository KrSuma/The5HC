from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


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
    farmer_carry_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    farmer_carry_notes = models.TextField(blank=True, null=True)
    
    # Harvard Step Test
    harvard_step_test_heart_rate = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(250)]
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
        # TODO: Implement score calculation logic from src/core/scoring.py
        pass
    
    def save(self, *args, **kwargs):
        """Override save to calculate scores before saving."""
        # Calculate scores if test data is present
        if any([self.overhead_squat_score, self.push_up_score, 
                self.toe_touch_score, self.shoulder_mobility_score,
                self.farmer_carry_score]):
            self.calculate_scores()
        super().save(*args, **kwargs)