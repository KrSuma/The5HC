from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import date


class Client(models.Model):
    """
    Client model representing fitness assessment clients.
    """
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
    ]
    
    # Relationships
    trainer = models.ForeignKey(
        'trainers.Trainer',
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name=_('Trainer'),
        help_text=_('The trainer managing this client')
    )
    
    # Personal information
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    age = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(150)],
        verbose_name=_('Age')
    )
    gender = models.CharField(
        max_length=20, 
        choices=GENDER_CHOICES,
        verbose_name=_('Gender')
    )
    height = models.FloatField(
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text=_("Height in cm"),
        verbose_name=_('Height')
    )
    weight = models.FloatField(
        validators=[MinValueValidator(20), MaxValueValidator(500)],
        help_text=_("Weight in kg"),
        verbose_name=_('Weight')
    )
    
    # Contact information
    email = models.EmailField(blank=True, null=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Phone'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.age}세, {self.gender})"
    
    @property
    def bmi(self):
        """Calculate BMI from height and weight."""
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None
    
    @property
    def bmi_category(self):
        """Return BMI category based on Korean standards."""
        if not self.bmi:
            return None
            
        if self.bmi < 18.5:
            return "저체중"
        elif self.bmi < 23:
            return "정상"
        elif self.bmi < 25:
            return "과체중"
        elif self.bmi < 30:
            return "비만"
        else:
            return "고도비만"
