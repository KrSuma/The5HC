from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone

User = get_user_model()

# Import additional models
from .models_audit import AuditLog
from .models_notification import Notification


class Organization(models.Model):
    """
    Organization model for managing multi-trainer businesses.
    """
    name = models.CharField(
        _('Organization Name'),
        max_length=100,
        help_text=_('The name of the fitness organization or gym')
    )
    slug = models.SlugField(
        _('URL Slug'),
        max_length=100,
        unique=True,
        help_text=_('Unique identifier for URLs')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Brief description of the organization')
    )
    phone = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
            )
        ]
    )
    email = models.EmailField(
        _('Contact Email'),
        blank=True,
        help_text=_('Primary contact email for the organization')
    )
    address = models.TextField(
        _('Address'),
        blank=True,
        help_text=_('Physical address of the organization')
    )
    
    # Business settings
    business_hours = models.JSONField(
        _('Business Hours'),
        default=dict,
        blank=True,
        help_text=_('Operating hours for each day of the week')
    )
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='Asia/Seoul',
        help_text=_('Timezone for the organization')
    )
    
    # Subscription/plan info (for future use)
    max_trainers = models.IntegerField(
        _('Maximum Trainers'),
        default=5,
        help_text=_('Maximum number of trainers allowed in this organization')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_trainer_count(self):
        """Get the current number of trainers in the organization."""
        return self.trainers.filter(is_active=True).count()
    
    def can_add_trainer(self):
        """Check if the organization can add more trainers."""
        return self.get_trainer_count() < self.max_trainers


class Trainer(models.Model):
    """
    Trainer profile model extending the User model with fitness-specific information.
    """
    ROLE_CHOICES = [
        ('owner', _('Owner')),
        ('senior', _('Senior Trainer')),
        ('trainer', _('Trainer')),
        ('assistant', _('Assistant')),
    ]
    
    # Relationships
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='trainer_profile',
        verbose_name=_('User Account')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='trainers',
        verbose_name=_('Organization'),
        null=True,
        blank=True,
        help_text=_('The organization this trainer belongs to')
    )
    
    # Profile information
    bio = models.TextField(
        _('Biography'),
        blank=True,
        help_text=_('Brief introduction about the trainer')
    )
    profile_photo = models.ImageField(
        _('Profile Photo'),
        upload_to='trainers/photos/',
        blank=True,
        null=True,
        help_text=_('Professional photo of the trainer')
    )
    
    # Professional information
    certifications = models.JSONField(
        _('Certifications'),
        default=list,
        blank=True,
        help_text=_('List of professional certifications')
    )
    specialties = models.JSONField(
        _('Specialties'),
        default=list,
        blank=True,
        help_text=_('Areas of expertise (e.g., weight loss, strength training)')
    )
    years_of_experience = models.IntegerField(
        _('Years of Experience'),
        default=0,
        help_text=_('Years of professional experience')
    )
    
    # Role and permissions
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='trainer',
        help_text=_('Role within the organization')
    )
    
    # Business settings
    session_price = models.IntegerField(
        _('Default Session Price'),
        default=50000,
        help_text=_('Default price per session in Korean Won')
    )
    availability_schedule = models.JSONField(
        _('Availability Schedule'),
        default=dict,
        blank=True,
        help_text=_('Weekly availability schedule')
    )
    
    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this trainer is currently active')
    )
    deactivated_at = models.DateTimeField(
        _('Deactivated At'),
        null=True,
        blank=True,
        help_text=_('When the trainer was deactivated')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Trainer')
        verbose_name_plural = _('Trainers')
        ordering = ['organization', 'user__first_name', 'user__last_name']
        unique_together = [['user', 'organization']]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.organization.name if self.organization else 'Independent'}"
    
    def get_display_name(self):
        """Get the trainer's display name."""
        return self.user.get_full_name() or self.user.username
    
    def is_owner(self):
        """Check if the trainer is an organization owner."""
        return self.role == 'owner'
    
    def is_senior(self):
        """Check if the trainer is a senior trainer or higher."""
        return self.role in ['owner', 'senior']
    
    def can_manage_trainers(self):
        """Check if the trainer can manage other trainers."""
        return self.role in ['owner', 'senior']
    
    def can_view_all_data(self):
        """Check if the trainer can view all organization data."""
        return self.role == 'owner'
    
    def deactivate(self):
        """Deactivate the trainer."""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=['is_active', 'deactivated_at'])
    
    def reactivate(self):
        """Reactivate the trainer."""
        self.is_active = True
        self.deactivated_at = None
        self.save(update_fields=['is_active', 'deactivated_at'])


class TrainerInvitation(models.Model):
    """
    Model for managing trainer invitations to join organizations.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
        ('expired', _('Expired')),
    ]
    
    # Invitation details
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('Organization')
    )
    email = models.EmailField(
        _('Email'),
        help_text=_('Email address to send the invitation to')
    )
    first_name = models.CharField(
        _('First Name'),
        max_length=50,
        blank=True
    )
    last_name = models.CharField(
        _('Last Name'),
        max_length=50,
        blank=True
    )
    role = models.CharField(
        _('Intended Role'),
        max_length=20,
        choices=Trainer.ROLE_CHOICES,
        default='trainer'
    )
    
    # Invitation metadata
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
        verbose_name=_('Invited By')
    )
    invitation_code = models.CharField(
        _('Invitation Code'),
        max_length=100,
        unique=True,
        help_text=_('Unique code for accepting the invitation')
    )
    message = models.TextField(
        _('Personal Message'),
        blank=True,
        help_text=_('Optional message to include with the invitation')
    )
    
    # Status tracking
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('Expires At'),
        help_text=_('When this invitation expires')
    )
    accepted_at = models.DateTimeField(
        _('Accepted At'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Trainer Invitation')
        verbose_name_plural = _('Trainer Invitations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"
    
    def is_expired(self):
        """Check if the invitation has expired."""
        return timezone.now() > self.expires_at
    
    def can_accept(self):
        """Check if the invitation can be accepted."""
        return self.status == 'pending' and not self.is_expired()
    
    def accept(self, user):
        """Accept the invitation and create trainer profile."""
        if not self.can_accept():
            raise ValueError("This invitation cannot be accepted")
        
        # Create or update trainer profile
        trainer, created = Trainer.objects.get_or_create(
            user=user,
            defaults={
                'organization': self.organization,
                'role': self.role,
            }
        )
        
        if not created:
            trainer.organization = self.organization
            trainer.role = self.role
            trainer.save()
        
        # Update invitation status
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return trainer
    
    def decline(self):
        """Decline the invitation."""
        self.status = 'declined'
        self.save()
    
    @classmethod
    def check_expired(cls):
        """Mark expired invitations."""
        cls.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        ).update(status='expired')
