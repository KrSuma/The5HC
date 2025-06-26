"""
Model mixins for The5HC Django application.

This module contains reusable model mixins that implement common patterns
across the application. These mixins provide consistent behavior for features
like timestamps, soft deletion, auditing, and multi-tenant data isolation.
"""
import uuid
from typing import Optional, Any, Type
from django.db import models
from django.db.models import QuerySet, Manager
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


User = get_user_model()


class TimestampedModelMixin(models.Model):
    """
    Adds created_at and updated_at timestamp fields to models.
    
    This mixin automatically tracks when records are created and last modified.
    The timestamps are timezone-aware and use the Django TIME_ZONE setting.
    
    Attributes:
        created_at: DateTime when the record was first created (auto-set)
        updated_at: DateTime when the record was last modified (auto-updated)
    
    Example:
        class Article(TimestampedModelMixin, models.Model):
            title = models.CharField(max_length=200)
            content = models.TextField()
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시",
        help_text="레코드가 생성된 일시"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일시",
        help_text="레코드가 마지막으로 수정된 일시"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-updated_at']),
        ]


class OrganizationScopedQuerySet(QuerySet):
    """QuerySet that filters by organization."""
    
    def for_organization(self, organization):
        """Filter queryset for a specific organization."""
        return self.filter(organization=organization)
    
    def for_user(self, user):
        """Filter queryset for a user's organization."""
        if hasattr(user, 'trainer_profile') and user.trainer_profile:
            return self.for_organization(user.trainer_profile.organization)
        return self.none()


class OrganizationScopedManager(Manager):
    """Manager that provides organization-scoped queries."""
    
    def get_queryset(self):
        return OrganizationScopedQuerySet(self.model, using=self._db)
    
    def for_organization(self, organization):
        return self.get_queryset().for_organization(organization)
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)


class OrganizationScopedModelMixin(models.Model):
    """
    Adds organization field and filtering for multi-tenant data isolation.
    
    This mixin ensures data is properly isolated between organizations in
    the multi-tenant system. It provides managers and methods for filtering
    data by organization.
    
    Attributes:
        organization: ForeignKey to Organization model
    
    Managers:
        objects: Default manager with organization filtering methods
        all_objects: Unfiltered manager for admin/superuser access
    
    Example:
        class Client(OrganizationScopedModelMixin, models.Model):
            name = models.CharField(max_length=100)
            
        # Usage:
        clients = Client.objects.for_user(request.user)
        org_clients = Client.objects.for_organization(organization)
    """
    organization = models.ForeignKey(
        'trainers.Organization',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name="조직",
        help_text="이 레코드가 속한 조직"
    )
    
    objects = OrganizationScopedManager()
    all_objects = models.Manager()  # Unfiltered access for admin
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization']),
        ]
    
    def is_accessible_by(self, user) -> bool:
        """Check if this record is accessible by the given user."""
        if user.is_superuser:
            return True
        if hasattr(user, 'trainer_profile') and user.trainer_profile:
            return self.organization == user.trainer_profile.organization
        return False


class AuditableModelMixin(models.Model):
    """
    Tracks who created and last modified records.
    
    This mixin adds fields to track which user created and last modified
    each record. It's useful for audit trails and compliance requirements.
    
    Attributes:
        created_by: User who created the record
        modified_by: User who last modified the record
    
    Example:
        class Document(AuditableModelMixin, TimestampedModelMixin, models.Model):
            title = models.CharField(max_length=200)
            
        # In view:
        document = form.save(commit=False)
        document.created_by = request.user
        document.modified_by = request.user
        document.save()
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name="생성자",
        help_text="이 레코드를 생성한 사용자"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_modified',
        verbose_name="수정자",
        help_text="이 레코드를 마지막으로 수정한 사용자"
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Auto-set modified_by if not explicitly set."""
        # If created_by is not set and this is a new record, try to set it
        if not self.pk and not self.created_by:
            # Check if user was passed in kwargs
            user = kwargs.pop('user', None)
            if user:
                self.created_by = user
                self.modified_by = user
        
        super().save(*args, **kwargs)


class SoftDeleteQuerySet(QuerySet):
    """QuerySet that handles soft deletion."""
    
    def delete(self):
        """Soft delete by marking as deleted instead of removing from database."""
        return self.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
    
    def hard_delete(self):
        """Actually delete from database (use with caution)."""
        return super().delete()
    
    def active(self):
        """Return only non-deleted records."""
        return self.filter(is_deleted=False)
    
    def deleted(self):
        """Return only deleted records."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(Manager):
    """Manager that filters out soft-deleted records by default."""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()
    
    def all_with_deleted(self):
        """Return all records including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def deleted_only(self):
        """Return only soft-deleted records."""
        return self.all_with_deleted().deleted()


class SoftDeleteModelMixin(models.Model):
    """
    Implements soft delete functionality.
    
    Instead of permanently deleting records, this mixin marks them as deleted
    and filters them out from normal queries. This allows for data recovery
    and maintains referential integrity.
    
    Attributes:
        is_deleted: Boolean flag for soft deletion
        deleted_at: Timestamp of deletion
        deleted_by: User who deleted the record
    
    Managers:
        objects: Filters out deleted records by default
        all_objects: Includes deleted records
    
    Example:
        class Product(SoftDeleteModelMixin, models.Model):
            name = models.CharField(max_length=100)
            
        # Soft delete:
        product.delete()  # Marks as deleted
        
        # Query active products:
        Product.objects.all()  # Excludes deleted
        
        # Include deleted:
        Product.all_objects.all()
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="삭제됨",
        help_text="소프트 삭제 여부"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="삭제일시",
        help_text="삭제된 일시"
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name="삭제자",
        help_text="삭제한 사용자"
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_deleted']),
            models.Index(fields=['deleted_at']),
        ]
    
    def delete(self, user=None, hard_delete=False):
        """
        Soft delete the record.
        
        Args:
            user: User performing the deletion
            hard_delete: If True, permanently delete from database
        """
        if hard_delete:
            super().delete()
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            if user:
                self.deleted_by = user
            self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class SluggedModelMixin(models.Model):
    """
    Auto-generates URL-friendly slugs from a source field.
    
    This mixin creates unique slugs suitable for URLs. It handles Unicode
    characters properly for Korean text and ensures uniqueness.
    
    Attributes:
        slug: URL-friendly version of the title/name
    
    Example:
        class BlogPost(SluggedModelMixin, models.Model):
            title = models.CharField(max_length=200)
            slug_source_field = 'title'  # Specify source field
            
        # Creates slug from title automatically
        post = BlogPost.objects.create(title="안녕하세요")
        print(post.slug)  # "annyeonghaseyo" or similar
    """
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="슬러그",
        help_text="URL에 사용되는 고유 식별자"
    )
    
    # Override in subclass to specify which field to generate slug from
    slug_source_field = 'name'
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)
    
    def _generate_unique_slug(self) -> str:
        """Generate a unique slug from the source field."""
        source_value = getattr(self, self.slug_source_field, '')
        if not source_value:
            # Fallback to UUID if no source value
            return str(uuid.uuid4())[:8]
        
        base_slug = slugify(source_value, allow_unicode=True)
        if not base_slug:
            # If slugify returns empty (e.g., for Korean text), use UUID
            base_slug = str(uuid.uuid4())[:8]
        
        # Ensure uniqueness
        slug = base_slug
        counter = 1
        while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class StatusModelMixin(models.Model):
    """
    Adds common status field patterns.
    
    This mixin provides a standardized way to track record status with
    predefined choices. It includes methods for status transitions and
    validation.
    
    Attributes:
        status: Current status of the record
        status_changed_at: When the status last changed
        status_changed_by: Who changed the status
    
    Example:
        class Order(StatusModelMixin, models.Model):
            STATUS_CHOICES = [
                ('pending', '대기중'),
                ('approved', '승인됨'),
                ('rejected', '거절됨'),
            ]
            # Will use STATUS_CHOICES from class
    """
    # Default status choices - override in subclass
    STATUS_CHOICES = [
        ('draft', '임시저장'),
        ('active', '활성'),
        ('inactive', '비활성'),
        ('archived', '보관됨'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="상태",
        help_text="현재 상태"
    )
    status_changed_at = models.DateTimeField(
        auto_now=True,
        verbose_name="상태 변경일시",
        help_text="상태가 마지막으로 변경된 일시"
    )
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_status_changes',
        verbose_name="상태 변경자",
        help_text="상태를 변경한 사용자"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['status_changed_at']),
        ]
    
    def change_status(self, new_status: str, user: Optional[User] = None, save: bool = True):
        """
        Change the status with validation and tracking.
        
        Args:
            new_status: The new status value
            user: User making the change
            save: Whether to save immediately
            
        Raises:
            ValidationError: If the status transition is not allowed
        """
        if not self.can_change_status_to(new_status):
            raise ValidationError(
                f"상태를 '{self.get_status_display()}'에서 '{dict(self.STATUS_CHOICES).get(new_status, new_status)}'로 변경할 수 없습니다."
            )
        
        self.status = new_status
        self.status_changed_at = timezone.now()
        if user:
            self.status_changed_by = user
        
        if save:
            self.save(update_fields=['status', 'status_changed_at', 'status_changed_by'])
    
    def can_change_status_to(self, new_status: str) -> bool:
        """
        Check if status can be changed to the new status.
        Override in subclass to implement custom transition rules.
        """
        # By default, allow any valid status transition
        valid_statuses = [choice[0] for choice in self.STATUS_CHOICES]
        return new_status in valid_statuses
    
    @classmethod
    def get_status_choices(cls):
        """Get available status choices."""
        return cls.STATUS_CHOICES


class OrderableModelMixin(models.Model):
    """
    Adds ordering/position functionality for sortable records.
    
    This mixin allows models to be manually ordered. It provides methods
    to move records up/down and maintains consistent ordering.
    
    Attributes:
        position: Integer position for ordering
    
    Example:
        class MenuItem(OrderableModelMixin, models.Model):
            name = models.CharField(max_length=100)
            category = models.ForeignKey(Category, on_delete=models.CASCADE)
            
            class Meta:
                ordering = ['category', 'position']
            
        # Move item up in order:
        item.move_up()
    """
    position = models.IntegerField(
        default=0,
        verbose_name="순서",
        help_text="정렬 순서 (낮을수록 앞에 표시)"
    )
    
    class Meta:
        abstract = True
        ordering = ['position']
        indexes = [
            models.Index(fields=['position']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-assign position if not set."""
        if self.position is None:
            # Get the next position
            max_position = self.__class__.objects.aggregate(
                models.Max('position')
            )['position__max'] or 0
            self.position = max_position + 1
        
        super().save(*args, **kwargs)
    
    def move_to(self, new_position: int):
        """Move to a specific position."""
        old_position = self.position
        
        if new_position == old_position:
            return
        
        # Shift other items
        if new_position < old_position:
            # Moving up - shift items down
            self.__class__.objects.filter(
                position__gte=new_position,
                position__lt=old_position
            ).update(position=models.F('position') + 1)
        else:
            # Moving down - shift items up
            self.__class__.objects.filter(
                position__gt=old_position,
                position__lte=new_position
            ).update(position=models.F('position') - 1)
        
        self.position = new_position
        self.save(update_fields=['position'])
    
    def move_up(self):
        """Move up one position."""
        if self.position > 0:
            self.move_to(self.position - 1)
    
    def move_down(self):
        """Move down one position."""
        self.move_to(self.position + 1)
    
    def get_previous(self):
        """Get the previous item in order."""
        return self.__class__.objects.filter(
            position__lt=self.position
        ).order_by('-position').first()
    
    def get_next(self):
        """Get the next item in order."""
        return self.__class__.objects.filter(
            position__gt=self.position
        ).order_by('position').first()
    
    @classmethod
    def reorder(cls, ids: list):
        """
        Reorder items based on a list of IDs.
        
        Args:
            ids: List of primary keys in desired order
        """
        for position, pk in enumerate(ids):
            cls.objects.filter(pk=pk).update(position=position)


# Composite mixins for common combinations
class FullAuditMixin(TimestampedModelMixin, AuditableModelMixin):
    """Combines timestamp and user tracking."""
    class Meta:
        abstract = True


class ScopedAuditMixin(OrganizationScopedModelMixin, FullAuditMixin):
    """Combines organization scoping with full audit trail."""
    class Meta:
        abstract = True


class DeletableAuditMixin(SoftDeleteModelMixin, FullAuditMixin):
    """Combines soft delete with full audit trail."""
    class Meta:
        abstract = True