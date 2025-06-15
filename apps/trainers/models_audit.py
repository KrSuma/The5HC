from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to track important actions within the system for audit purposes.
    """
    ACTION_CHOICES = [
        # Client actions
        ('client_created', _('Client Created')),
        ('client_updated', _('Client Updated')),
        ('client_deleted', _('Client Deleted')),
        
        # Assessment actions
        ('assessment_created', _('Assessment Created')),
        ('assessment_updated', _('Assessment Updated')),
        ('assessment_deleted', _('Assessment Deleted')),
        
        # Session/Package actions
        ('package_created', _('Package Created')),
        ('package_updated', _('Package Updated')),
        ('session_created', _('Session Created')),
        ('session_completed', _('Session Completed')),
        ('session_cancelled', _('Session Cancelled')),
        ('payment_recorded', _('Payment Recorded')),
        
        # Trainer actions
        ('trainer_created', _('Trainer Created')),
        ('trainer_updated', _('Trainer Updated')),
        ('trainer_deactivated', _('Trainer Deactivated')),
        ('trainer_activated', _('Trainer Activated')),
        ('invitation_sent', _('Invitation Sent')),
        ('invitation_accepted', _('Invitation Accepted')),
        ('invitation_declined', _('Invitation Declined')),
        
        # Organization actions
        ('organization_created', _('Organization Created')),
        ('organization_updated', _('Organization Updated')),
        
        # Authentication actions
        ('login_success', _('Login Success')),
        ('login_failed', _('Login Failed')),
        ('logout', _('Logout')),
        ('password_changed', _('Password Changed')),
    ]
    
    # Who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('User')
    )
    
    # Organization context
    organization = models.ForeignKey(
        'trainers.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Organization')
    )
    
    # Action details
    action = models.CharField(
        _('Action'),
        max_length=50,
        choices=ACTION_CHOICES
    )
    
    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional context
    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )
    
    # JSON field for extra data
    extra_data = models.JSONField(
        _('Extra Data'),
        default=dict,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"