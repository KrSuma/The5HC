"""
Example models demonstrating the usage of model mixins.

This module shows practical examples of how to use the model mixins
in real-world Django models for The5HC project.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.core.mixins.model_mixins import (
    TimestampedModelMixin,
    OrganizationScopedModelMixin,
    AuditableModelMixin,
    SoftDeleteModelMixin,
    SluggedModelMixin,
    StatusModelMixin,
    OrderableModelMixin,
    FullAuditMixin,
    ScopedAuditMixin,
    DeletableAuditMixin,
)

User = get_user_model()


# Example 1: Blog Post with slugs and timestamps
class BlogPost(SluggedModelMixin, TimestampedModelMixin, models.Model):
    """
    Example blog post model with automatic slug generation and timestamps.
    """
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="작성자")
    
    # Tell the slug mixin which field to use
    slug_source_field = 'title'
    
    class Meta:
        verbose_name = "블로그 포스트"
        verbose_name_plural = "블로그 포스트"
        ordering = ['-created_at']  # Newest first
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return f"/blog/{self.slug}/"


# Example 2: Client Record with organization scoping and soft delete
class ClientRecord(
    OrganizationScopedModelMixin,
    SoftDeleteModelMixin,
    FullAuditMixin,
    models.Model
):
    """
    Example client record with multi-tenant isolation, soft delete,
    and full audit trail.
    """
    name = models.CharField(max_length=100, verbose_name="이름")
    email = models.EmailField(unique=True, verbose_name="이메일")
    phone = models.CharField(max_length=20, blank=True, verbose_name="전화번호")
    notes = models.TextField(blank=True, verbose_name="메모")
    
    class Meta:
        verbose_name = "고객 기록"
        verbose_name_plural = "고객 기록"
        ordering = ['name']
        # Unique together within organization
        unique_together = ['organization', 'email']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def delete(self, user=None, hard_delete=False):
        """Override to ensure user is tracked when deleting."""
        if not user and hasattr(self, '_request'):
            user = self._request.user
        super().delete(user=user, hard_delete=hard_delete)


# Example 3: Task with status management and ordering
class Task(
    StatusModelMixin,
    OrderableModelMixin,
    ScopedAuditMixin,
    models.Model
):
    """
    Example task model with status workflow, manual ordering,
    and organization scoping.
    """
    # Custom status choices for tasks
    STATUS_CHOICES = [
        ('todo', '할 일'),
        ('in_progress', '진행중'),
        ('review', '검토중'),
        ('done', '완료'),
        ('cancelled', '취소됨'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="제목")
    description = models.TextField(blank=True, verbose_name="설명")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name="담당자"
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="마감일")
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="프로젝트"
    )
    
    class Meta:
        verbose_name = "작업"
        verbose_name_plural = "작업"
        ordering = ['project', 'position']  # Order by project, then position
    
    def __str__(self):
        return self.title
    
    def can_change_status_to(self, new_status):
        """Custom status transition rules."""
        # Cannot change status of cancelled tasks
        if self.status == 'cancelled':
            return False
        
        # Cannot go back to 'todo' from other statuses
        if new_status == 'todo' and self.status != 'todo':
            return False
        
        # Cannot mark as done without review
        if new_status == 'done' and self.status != 'review':
            return False
        
        return super().can_change_status_to(new_status)


# Example 4: Project with all features
class Project(
    OrganizationScopedModelMixin,
    StatusModelMixin,
    SluggedModelMixin,
    DeletableAuditMixin,
    models.Model
):
    """
    Comprehensive example using multiple mixins together.
    """
    STATUS_CHOICES = [
        ('planning', '계획중'),
        ('active', '진행중'),
        ('on_hold', '보류'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="프로젝트명")
    description = models.TextField(blank=True, verbose_name="설명")
    start_date = models.DateField(verbose_name="시작일")
    end_date = models.DateField(null=True, blank=True, verbose_name="종료일")
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="예산"
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_projects',
        verbose_name="프로젝트 매니저"
    )
    
    # For slug generation
    slug_source_field = 'name'
    
    class Meta:
        verbose_name = "프로젝트"
        verbose_name_plural = "프로젝트"
        ordering = ['-created_at']
        unique_together = ['organization', 'slug']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate project dates."""
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': "종료일은 시작일보다 늦어야 합니다."
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if project is currently active."""
        return self.status == 'active' and not self.is_deleted
    
    @property
    def progress_percentage(self):
        """Calculate project progress based on tasks."""
        total_tasks = self.tasks.count()
        if not total_tasks:
            return 0
        
        completed_tasks = self.tasks.filter(status='done').count()
        return round((completed_tasks / total_tasks) * 100)


# Example 5: Notification with auto-cleanup
class Notification(TimestampedModelMixin, models.Model):
    """
    Simple notification model showing basic mixin usage.
    """
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="수신자"
    )
    title = models.CharField(max_length=200, verbose_name="제목")
    message = models.TextField(verbose_name="메시지")
    is_read = models.BooleanField(default=False, verbose_name="읽음")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="읽은 시간")
    
    class Meta:
        verbose_name = "알림"
        verbose_name_plural = "알림"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


# Example 6: Document with version tracking
class Document(
    OrganizationScopedModelMixin,
    StatusModelMixin,
    FullAuditMixin,
    models.Model
):
    """
    Document model with approval workflow.
    """
    STATUS_CHOICES = [
        ('draft', '초안'),
        ('review', '검토중'),
        ('approved', '승인됨'),
        ('published', '게시됨'),
        ('archived', '보관됨'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    version = models.CharField(max_length=20, default='1.0', verbose_name="버전")
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="첨부파일"
    )
    
    class Meta:
        verbose_name = "문서"
        verbose_name_plural = "문서"
        ordering = ['-updated_at']
        unique_together = ['organization', 'title', 'version']
    
    def __str__(self):
        return f"{self.title} v{self.version}"
    
    def can_change_status_to(self, new_status):
        """Enforce approval workflow."""
        transitions = {
            'draft': ['review'],
            'review': ['draft', 'approved'],
            'approved': ['published', 'archived'],
            'published': ['archived'],
            'archived': [],  # Cannot change from archived
        }
        
        allowed = transitions.get(self.status, [])
        return new_status in allowed


# Example 7: Menu items with categories
class MenuCategory(
    OrganizationScopedModelMixin,
    OrderableModelMixin,
    models.Model
):
    """Category for menu items."""
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    
    class Meta:
        verbose_name = "메뉴 카테고리"
        verbose_name_plural = "메뉴 카테고리"
        ordering = ['position']
    
    def __str__(self):
        return self.name


class MenuItem(
    OrderableModelMixin,
    TimestampedModelMixin,
    models.Model
):
    """
    Menu items that can be reordered within categories.
    """
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="카테고리"
    )
    name = models.CharField(max_length=100, verbose_name="메뉴명")
    description = models.TextField(blank=True, verbose_name="설명")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="가격"
    )
    is_available = models.BooleanField(default=True, verbose_name="판매중")
    
    class Meta:
        verbose_name = "메뉴 항목"
        verbose_name_plural = "메뉴 항목"
        ordering = ['category', 'position']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Ensure position is unique within category."""
        if not self.position:
            # Get next position within category
            max_pos = MenuItem.objects.filter(
                category=self.category
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_pos + 1
        
        super().save(*args, **kwargs)


# Usage Examples in Views
"""
# Example view using these models:

def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            # Set audit fields
            project.created_by = request.user
            project.modified_by = request.user
            # Set organization from user's profile
            project.organization = request.user.trainer_profile.organization
            project.save()
            
            # Change status with tracking
            project.change_status('active', user=request.user)
            
            return redirect('project_detail', slug=project.slug)
    
    return render(request, 'create_project.html', {'form': form})


def task_list(request):
    # Get tasks for user's organization
    tasks = Task.objects.for_user(request.user).select_related(
        'assignee', 'project', 'organization'
    )
    
    # Reorder tasks
    if request.method == 'POST' and 'task_order' in request.POST:
        task_ids = request.POST.getlist('task_order')
        Task.reorder(task_ids)
        
    return render(request, 'task_list.html', {'tasks': tasks})


def delete_client(request, pk):
    # Soft delete with user tracking
    client = get_object_or_404(ClientRecord, pk=pk)
    
    # Check permissions
    if not client.is_accessible_by(request.user):
        raise PermissionDenied
    
    if request.method == 'POST':
        # Soft delete (can be restored later)
        client.delete(user=request.user)
        messages.success(request, "Client deleted successfully")
        return redirect('client_list')
    
    return render(request, 'confirm_delete.html', {'client': client})
"""