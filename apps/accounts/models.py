from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Represents trainers in the system with additional fields for security.
    """
    # Override email to make it unique and required
    email = models.EmailField(unique=True, blank=False)
    
    # Additional fields from trainers table
    name = models.CharField(max_length=200)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'Trainer'
        verbose_name_plural = 'Trainers'
    
    def __str__(self):
        return f"{self.username} - {self.name}"
    
    def is_account_locked(self):
        """Check if account is currently locked due to failed login attempts."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def increment_failed_login_attempts(self):
        """Increment failed login attempts and lock account if threshold reached."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts on successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
