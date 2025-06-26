"""
Tests for model mixins.

This module tests all the model mixins to ensure they work correctly
in isolation and in combination with each other.
"""
import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models

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


# Test models for mixins
class TimestampedTestModel(TimestampedModelMixin, models.Model):
    """Test model for TimestampedModelMixin."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class OrganizationScopedTestModel(OrganizationScopedModelMixin, models.Model):
    """Test model for OrganizationScopedModelMixin."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class AuditableTestModel(AuditableModelMixin, models.Model):
    """Test model for AuditableModelMixin."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class SoftDeleteTestModel(SoftDeleteModelMixin, models.Model):
    """Test model for SoftDeleteModelMixin."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class SluggedTestModel(SluggedModelMixin, models.Model):
    """Test model for SluggedModelMixin."""
    name = models.CharField(max_length=100)
    slug_source_field = 'name'
    
    class Meta:
        app_label = 'core'


class StatusTestModel(StatusModelMixin, models.Model):
    """Test model for StatusModelMixin."""
    name = models.CharField(max_length=100)
    
    # Custom status choices
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('approved', '승인됨'),
        ('rejected', '거절됨'),
    ]
    
    class Meta:
        app_label = 'core'


class OrderableTestModel(OrderableModelMixin, models.Model):
    """Test model for OrderableModelMixin."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


class CompositeTestModel(ScopedAuditMixin, models.Model):
    """Test model using composite mixins."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'core'


@pytest.mark.django_db
class TestTimestampedModelMixin:
    """Test cases for TimestampedModelMixin."""
    
    def test_timestamps_auto_set_on_create(self):
        """Test that timestamps are automatically set when creating a record."""
        before = timezone.now()
        obj = TimestampedTestModel.objects.create(name="Test")
        after = timezone.now()
        
        assert obj.created_at is not None
        assert obj.updated_at is not None
        assert before <= obj.created_at <= after
        assert before <= obj.updated_at <= after
        assert obj.created_at == obj.updated_at
    
    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when saving an existing record."""
        obj = TimestampedTestModel.objects.create(name="Test")
        original_updated = obj.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.1)
        
        obj.name = "Updated"
        obj.save()
        
        assert obj.updated_at > original_updated
        assert obj.created_at < obj.updated_at
    
    def test_indexes_created(self):
        """Test that indexes are created for timestamp fields."""
        # This would require checking the database schema
        # For now, just verify the Meta configuration
        assert any(idx.fields == ['-created_at'] for idx in TimestampedTestModel._meta.indexes)
        assert any(idx.fields == ['-updated_at'] for idx in TimestampedTestModel._meta.indexes)


@pytest.mark.django_db
class TestOrganizationScopedModelMixin:
    """Test cases for OrganizationScopedModelMixin."""
    
    @pytest.fixture
    def setup_organizations(self, db):
        """Set up test organizations and users."""
        from apps.trainers.models import Organization, TrainerProfile
        
        # Create organizations
        org1 = Organization.objects.create(name="Org 1")
        org2 = Organization.objects.create(name="Org 2")
        
        # Create users with trainer profiles
        user1 = User.objects.create_user(username="user1", email="user1@test.com")
        user2 = User.objects.create_user(username="user2", email="user2@test.com")
        superuser = User.objects.create_superuser(username="admin", email="admin@test.com")
        
        TrainerProfile.objects.create(user=user1, organization=org1)
        TrainerProfile.objects.create(user=user2, organization=org2)
        
        return {
            'org1': org1,
            'org2': org2,
            'user1': user1,
            'user2': user2,
            'superuser': superuser
        }
    
    def test_organization_filtering(self, setup_organizations):
        """Test that objects are filtered by organization."""
        org1 = setup_organizations['org1']
        org2 = setup_organizations['org2']
        
        # Create test objects
        obj1 = OrganizationScopedTestModel.objects.create(name="Org1 Object", organization=org1)
        obj2 = OrganizationScopedTestModel.objects.create(name="Org2 Object", organization=org2)
        
        # Test filtering by organization
        org1_objects = OrganizationScopedTestModel.objects.for_organization(org1)
        assert obj1 in org1_objects
        assert obj2 not in org1_objects
        
        org2_objects = OrganizationScopedTestModel.objects.for_organization(org2)
        assert obj1 not in org2_objects
        assert obj2 in org2_objects
    
    def test_user_filtering(self, setup_organizations):
        """Test that objects are filtered by user's organization."""
        org1 = setup_organizations['org1']
        user1 = setup_organizations['user1']
        user2 = setup_organizations['user2']
        
        obj1 = OrganizationScopedTestModel.objects.create(name="User1 Org Object", organization=org1)
        
        # Test filtering by user
        user1_objects = OrganizationScopedTestModel.objects.for_user(user1)
        assert obj1 in user1_objects
        
        user2_objects = OrganizationScopedTestModel.objects.for_user(user2)
        assert obj1 not in user2_objects
    
    def test_accessibility_check(self, setup_organizations):
        """Test the is_accessible_by method."""
        org1 = setup_organizations['org1']
        user1 = setup_organizations['user1']
        user2 = setup_organizations['user2']
        superuser = setup_organizations['superuser']
        
        obj = OrganizationScopedTestModel.objects.create(name="Test Object", organization=org1)
        
        assert obj.is_accessible_by(user1) is True
        assert obj.is_accessible_by(user2) is False
        assert obj.is_accessible_by(superuser) is True  # Superuser can access all


@pytest.mark.django_db
class TestAuditableModelMixin:
    """Test cases for AuditableModelMixin."""
    
    def test_audit_fields_on_create(self):
        """Test that audit fields can be set on create."""
        user = User.objects.create_user(username="testuser", email="test@test.com")
        
        obj = AuditableTestModel.objects.create(
            name="Test",
            created_by=user,
            modified_by=user
        )
        
        assert obj.created_by == user
        assert obj.modified_by == user
    
    def test_audit_fields_nullable(self):
        """Test that audit fields can be null."""
        obj = AuditableTestModel.objects.create(name="Test")
        
        assert obj.created_by is None
        assert obj.modified_by is None
    
    def test_save_with_user_kwarg(self):
        """Test that save can accept a user kwarg."""
        user = User.objects.create_user(username="testuser", email="test@test.com")
        
        obj = AuditableTestModel(name="Test")
        obj.save(user=user)
        
        assert obj.created_by == user
        assert obj.modified_by == user


@pytest.mark.django_db
class TestSoftDeleteModelMixin:
    """Test cases for SoftDeleteModelMixin."""
    
    def test_soft_delete(self):
        """Test soft deletion marks record as deleted without removing it."""
        obj = SoftDeleteTestModel.objects.create(name="Test")
        pk = obj.pk
        
        # Soft delete
        obj.delete()
        
        # Object still exists in database
        assert SoftDeleteTestModel.all_objects.filter(pk=pk).exists()
        
        # But not in default queryset
        assert not SoftDeleteTestModel.objects.filter(pk=pk).exists()
        
        # Check fields
        obj.refresh_from_db()
        assert obj.is_deleted is True
        assert obj.deleted_at is not None
    
    def test_soft_delete_with_user(self):
        """Test soft deletion tracks who deleted the record."""
        user = User.objects.create_user(username="testuser", email="test@test.com")
        obj = SoftDeleteTestModel.objects.create(name="Test")
        
        obj.delete(user=user)
        obj.refresh_from_db()
        
        assert obj.deleted_by == user
    
    def test_hard_delete(self):
        """Test hard deletion removes record from database."""
        obj = SoftDeleteTestModel.objects.create(name="Test")
        pk = obj.pk
        
        # Hard delete
        obj.delete(hard_delete=True)
        
        # Object no longer exists
        assert not SoftDeleteTestModel.all_objects.filter(pk=pk).exists()
    
    def test_restore(self):
        """Test restoring a soft-deleted record."""
        obj = SoftDeleteTestModel.objects.create(name="Test")
        obj.delete()
        
        # Restore
        obj.restore()
        
        # Should be visible in default queryset again
        assert SoftDeleteTestModel.objects.filter(pk=obj.pk).exists()
        
        # Check fields
        obj.refresh_from_db()
        assert obj.is_deleted is False
        assert obj.deleted_at is None
        assert obj.deleted_by is None
    
    def test_queryset_methods(self):
        """Test queryset filtering methods."""
        # Create mix of active and deleted objects
        active1 = SoftDeleteTestModel.objects.create(name="Active 1")
        active2 = SoftDeleteTestModel.objects.create(name="Active 2")
        deleted1 = SoftDeleteTestModel.objects.create(name="Deleted 1")
        deleted2 = SoftDeleteTestModel.objects.create(name="Deleted 2")
        
        deleted1.delete()
        deleted2.delete()
        
        # Test default manager
        assert SoftDeleteTestModel.objects.count() == 2
        assert active1 in SoftDeleteTestModel.objects.all()
        assert active2 in SoftDeleteTestModel.objects.all()
        
        # Test all_objects manager
        assert SoftDeleteTestModel.all_objects.count() == 4
        
        # Test deleted_only
        deleted_objs = SoftDeleteTestModel.objects.deleted_only()
        assert deleted_objs.count() == 2
        assert deleted1 in deleted_objs
        assert deleted2 in deleted_objs


@pytest.mark.django_db
class TestSluggedModelMixin:
    """Test cases for SluggedModelMixin."""
    
    def test_slug_auto_generation(self):
        """Test that slug is auto-generated from source field."""
        obj = SluggedTestModel.objects.create(name="Test Product Name")
        assert obj.slug == "test-product-name"
    
    def test_slug_uniqueness(self):
        """Test that slugs are unique."""
        obj1 = SluggedTestModel.objects.create(name="Test Name")
        obj2 = SluggedTestModel.objects.create(name="Test Name")
        
        assert obj1.slug == "test-name"
        assert obj2.slug == "test-name-1"
    
    def test_korean_text_slug(self):
        """Test slug generation with Korean text."""
        obj = SluggedTestModel.objects.create(name="안녕하세요")
        # Korean text might not slugify well, should fall back to UUID
        assert obj.slug is not None
        assert len(obj.slug) > 0
    
    def test_empty_source_field(self):
        """Test slug generation when source field is empty."""
        obj = SluggedTestModel.objects.create(name="")
        # Should use UUID fallback
        assert obj.slug is not None
        assert len(obj.slug) == 8  # UUID prefix length
    
    def test_manual_slug(self):
        """Test that manually set slug is preserved."""
        obj = SluggedTestModel.objects.create(name="Test", slug="custom-slug")
        assert obj.slug == "custom-slug"


@pytest.mark.django_db
class TestStatusModelMixin:
    """Test cases for StatusModelMixin."""
    
    def test_default_status(self):
        """Test that default status is set correctly."""
        obj = StatusTestModel.objects.create(name="Test")
        assert obj.status == 'pending'  # First choice in custom STATUS_CHOICES
    
    def test_status_change(self):
        """Test changing status."""
        user = User.objects.create_user(username="testuser", email="test@test.com")
        obj = StatusTestModel.objects.create(name="Test")
        
        original_time = obj.status_changed_at
        
        # Wait to ensure time difference
        import time
        time.sleep(0.1)
        
        obj.change_status('approved', user=user)
        
        assert obj.status == 'approved'
        assert obj.status_changed_by == user
        assert obj.status_changed_at > original_time
    
    def test_invalid_status_change(self):
        """Test that invalid status changes raise ValidationError."""
        obj = StatusTestModel.objects.create(name="Test")
        
        with pytest.raises(ValidationError):
            obj.change_status('invalid_status')
    
    def test_status_change_without_save(self):
        """Test status change without immediate save."""
        obj = StatusTestModel.objects.create(name="Test")
        
        obj.change_status('approved', save=False)
        
        # Status changed in memory
        assert obj.status == 'approved'
        
        # But not in database
        obj_from_db = StatusTestModel.objects.get(pk=obj.pk)
        assert obj_from_db.status == 'pending'
    
    def test_custom_transition_rules(self):
        """Test that can_change_status_to can be overridden."""
        obj = StatusTestModel.objects.create(name="Test")
        
        # By default, all valid transitions are allowed
        assert obj.can_change_status_to('approved') is True
        assert obj.can_change_status_to('rejected') is True
        assert obj.can_change_status_to('invalid') is False


@pytest.mark.django_db
class TestOrderableModelMixin:
    """Test cases for OrderableModelMixin."""
    
    def test_auto_position_assignment(self):
        """Test that position is auto-assigned."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        obj3 = OrderableTestModel.objects.create(name="Third")
        
        assert obj1.position == 1
        assert obj2.position == 2
        assert obj3.position == 3
    
    def test_move_to_position(self):
        """Test moving to a specific position."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        obj3 = OrderableTestModel.objects.create(name="Third")
        
        # Move third to first position
        obj3.move_to(1)
        
        # Refresh from database
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        obj3.refresh_from_db()
        
        assert obj3.position == 1
        assert obj1.position == 2
        assert obj2.position == 3
    
    def test_move_up(self):
        """Test moving up one position."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        
        obj2.move_up()
        
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        
        assert obj2.position == 0
        assert obj1.position == 2
    
    def test_move_down(self):
        """Test moving down one position."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        
        obj1.move_down()
        
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        
        assert obj1.position == 2
        assert obj2.position == 1
    
    def test_get_previous_next(self):
        """Test getting previous and next items."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        obj3 = OrderableTestModel.objects.create(name="Third")
        
        assert obj2.get_previous() == obj1
        assert obj2.get_next() == obj3
        assert obj1.get_previous() is None
        assert obj3.get_next() is None
    
    def test_reorder(self):
        """Test reordering multiple items."""
        obj1 = OrderableTestModel.objects.create(name="First")
        obj2 = OrderableTestModel.objects.create(name="Second")
        obj3 = OrderableTestModel.objects.create(name="Third")
        
        # Reverse order
        OrderableTestModel.reorder([obj3.pk, obj2.pk, obj1.pk])
        
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        obj3.refresh_from_db()
        
        assert obj3.position == 0
        assert obj2.position == 1
        assert obj1.position == 2


@pytest.mark.django_db
class TestCompositeMixins:
    """Test cases for composite mixins."""
    
    def test_scoped_audit_mixin(self, db):
        """Test that ScopedAuditMixin combines features correctly."""
        from apps.trainers.models import Organization, TrainerProfile
        
        org = Organization.objects.create(name="Test Org")
        user = User.objects.create_user(username="testuser", email="test@test.com")
        TrainerProfile.objects.create(user=user, organization=org)
        
        obj = CompositeTestModel.objects.create(
            name="Test",
            organization=org,
            created_by=user,
            modified_by=user
        )
        
        # Has timestamp fields
        assert obj.created_at is not None
        assert obj.updated_at is not None
        
        # Has audit fields
        assert obj.created_by == user
        assert obj.modified_by == user
        
        # Has organization scoping
        assert obj.organization == org
        assert obj.is_accessible_by(user) is True