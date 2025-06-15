from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """
    In-app notification system for trainers.
    """
    NOTIFICATION_TYPES = [
        ('client_added', _('New Client Added')),
        ('assessment_completed', _('Assessment Completed')),
        ('session_scheduled', _('Session Scheduled')),
        ('payment_received', _('Payment Received')),
        ('trainer_invited', _('Trainer Invitation')),
        ('trainer_joined', _('Trainer Joined Organization')),
        ('organization_update', _('Organization Update')),
        ('system', _('System Notification')),
    ]
    
    # Recipient
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Recipient')
    )
    
    # Notification details
    notification_type = models.CharField(
        _('Type'),
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(
        _('Title'),
        max_length=200
    )
    message = models.TextField(
        _('Message')
    )
    
    # Related object (optional)
    related_object_type = models.CharField(
        _('Related Object Type'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('Type of related object (e.g., client, assessment)')
    )
    related_object_id = models.IntegerField(
        _('Related Object ID'),
        blank=True,
        null=True,
        help_text=_('ID of the related object')
    )
    
    # Action URL (optional)
    action_url = models.CharField(
        _('Action URL'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('URL to navigate when notification is clicked')
    )
    
    # Status
    is_read = models.BooleanField(
        _('Read'),
        default=False
    )
    read_at = models.DateTimeField(
        _('Read At'),
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, 
                          related_object_type=None, related_object_id=None, 
                          action_url=None):
        """
        Create a new notification.
        """
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            action_url=action_url
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user."""
        return cls.objects.filter(user=user, is_read=False).count()