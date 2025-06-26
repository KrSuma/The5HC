"""
Test models demonstrating the use of model mixins.
These are example models showing how to integrate the mixins.
"""
from django.db import models
from django.contrib.auth import get_user_model

from apps.core.mixins import (
    TimestampedModelMixin,
    OrganizationScopedModelMixin,
    AuditableModelMixin,
    SoftDeleteModelMixin,
    SluggedModelMixin,
    StatusModelMixin,
    OrderableModelMixin,
    FullAuditMixin,
    ScopedAuditMixin,
)

User = get_user_model()


class TestArticle(TimestampedModelMixin, SluggedModelMixin, models.Model):
    """
    Example model using timestamp and slug mixins.
    Demonstrates basic mixin usage.
    """
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='작성자')
    
    # SluggedModelMixin will use this field
    slug_source_field = 'title'
    
    class Meta:
        verbose_name = '테스트 글'
        verbose_name_plural = '테스트 글 목록'
        ordering = ['-created_at']  # Using TimestampedModelMixin field
    
    def __str__(self):
        return self.title


class TestTask(StatusModelMixin, OrderableModelMixin, AuditableModelMixin, models.Model):
    """
    Example model using status, ordering, and audit mixins.
    Demonstrates multiple mixin composition.
    """
    title = models.CharField(max_length=200, verbose_name='작업명')
    description = models.TextField(blank=True, verbose_name='설명')
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks',
        verbose_name='담당자'
    )
    
    # Status choices for StatusModelMixin
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('in_progress', '진행중'),
        ('review', '검토중'),
        ('completed', '완료'),
        ('cancelled', '취소됨'),
    ]
    
    # Valid transitions for StatusModelMixin
    VALID_TRANSITIONS = {
        'pending': ['in_progress', 'cancelled'],
        'in_progress': ['review', 'cancelled'],
        'review': ['in_progress', 'completed', 'cancelled'],
        'completed': [],  # Cannot transition from completed
        'cancelled': ['pending'],  # Can restart cancelled tasks
    }
    
    class Meta:
        verbose_name = '테스트 작업'
        verbose_name_plural = '테스트 작업 목록'
        ordering = ['position']  # Using OrderableModelMixin field
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class TestClientRecord(ScopedAuditMixin, SoftDeleteModelMixin, models.Model):
    """
    Example model using organization scoping, soft delete, and full audit.
    This demonstrates the composite mixin (ScopedAuditMixin).
    """
    name = models.CharField(max_length=100, verbose_name='이름')
    email = models.EmailField(verbose_name='이메일')
    phone = models.CharField(max_length=20, blank=True, verbose_name='전화번호')
    notes = models.TextField(blank=True, verbose_name='메모')
    
    # Additional fields for testing
    is_vip = models.BooleanField(default=False, verbose_name='VIP 고객')
    credit_limit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name='신용한도'
    )
    
    class Meta:
        verbose_name = '테스트 고객 기록'
        verbose_name_plural = '테스트 고객 기록 목록'
        # Note: OrganizationScopedModelMixin adds organization to unique_together
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class TestProject(FullAuditMixin, models.Model):
    """
    Example model using the full audit mixin.
    This includes timestamps, audit fields, and soft delete.
    """
    name = models.CharField(max_length=200, verbose_name='프로젝트명')
    description = models.TextField(blank=True, verbose_name='설명')
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(null=True, blank=True, verbose_name='종료일')
    budget = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name='예산'
    )
    
    # Status tracking
    is_active = models.BooleanField(default=True, verbose_name='활성')
    completion_percentage = models.IntegerField(default=0, verbose_name='완료율')
    
    class Meta:
        verbose_name = '테스트 프로젝트'
        verbose_name_plural = '테스트 프로젝트 목록'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_overdue(self):
        """Check if project is overdue."""
        if self.end_date and not self.is_deleted:
            from django.utils import timezone
            return timezone.now().date() > self.end_date and self.completion_percentage < 100
        return False
    
    @property
    def days_remaining(self):
        """Calculate days remaining until end date."""
        if self.end_date and not self.is_deleted:
            from django.utils import timezone
            delta = self.end_date - timezone.now().date()
            return delta.days
        return None