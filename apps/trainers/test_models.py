"""
Simplified unit tests for trainers app models.
Tests core functionality with minimal setup.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.trainers.models import Organization, Trainer, TrainerInvitation, AuditLog, Notification
from apps.trainers.factories import (
    OrganizationFactory, TrainerFactory, OwnerTrainerFactory,
    TrainerInvitationFactory, AuditLogFactory, NotificationFactory,
    UserFactory
)

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestOrganizationModel:
    """Test cases for Organization model."""
    
    def test_create_organization(self):
        """Test creating a basic organization."""
        org = OrganizationFactory(name="Test Gym", slug="test-gym")
        assert org.name == "Test Gym"
        assert org.slug == "test-gym"
        assert org.max_trainers == 10
        assert str(org) == "Test Gym"
    
    def test_organization_trainer_count(self):
        """Test organization trainer counting."""
        org = OrganizationFactory()
        
        # No trainers initially
        assert org.get_trainer_count() == 0
        
        # Add trainers
        TrainerFactory.create_batch(3, organization=org, is_active=True)
        assert org.get_trainer_count() == 3
        
        # Add inactive trainer (should not count)
        TrainerFactory(organization=org, is_active=False)
        assert org.get_trainer_count() == 3
    
    def test_organization_can_add_trainer(self):
        """Test organization capacity checking."""
        org = OrganizationFactory(max_trainers=3)
        
        # Can add trainers initially
        assert org.can_add_trainer()
        
        # Add trainers up to limit
        TrainerFactory.create_batch(3, organization=org)
        assert not org.can_add_trainer()
    
    def test_organization_unique_slug(self):
        """Test organization slug uniqueness."""
        org1 = Organization.objects.create(
            name="Unique Gym",
            slug="unique-gym"
        )
        
        with pytest.raises(IntegrityError):
            org2 = Organization.objects.create(
                name="Another Gym",
                slug="unique-gym"
            )
    
    def test_organization_deletion_protected(self):
        """Test that organization deletion is protected when trainers exist."""
        org = OrganizationFactory()
        trainer = TrainerFactory(organization=org)
        
        # Should raise ProtectedError when trying to delete org with trainers
        with pytest.raises(ProtectedError):
            org.delete()


class TestTrainerModel:
    """Test cases for Trainer model."""
    
    def test_create_trainer(self):
        """Test creating a basic trainer."""
        user = UserFactory(first_name="John", last_name="Doe")
        org = OrganizationFactory(name="Test Gym")
        trainer = TrainerFactory(user=user, organization=org)
        
        assert trainer.user == user
        assert trainer.organization == org
        assert trainer.role == 'trainer'
        assert trainer.is_active
        assert str(trainer) == "John Doe - Test Gym"
    
    def test_trainer_display_name(self):
        """Test trainer display name."""
        user = UserFactory(first_name="김", last_name="철수")
        trainer = TrainerFactory(user=user)
        assert trainer.get_display_name() == "김 철수"
        
        # Test with username fallback
        user2 = UserFactory(first_name="", last_name="", username="testuser")
        trainer2 = TrainerFactory(user=user2)
        assert trainer2.get_display_name() == "testuser"
    
    def test_trainer_roles(self):
        """Test trainer role checking methods."""
        owner = OwnerTrainerFactory()
        trainer = TrainerFactory()
        
        # Test owner
        assert owner.is_owner()
        assert owner.is_senior()  # owners are also senior
        assert owner.can_manage_trainers()
        assert owner.can_view_all_data()
        
        # Test regular trainer
        assert not trainer.is_owner()
        assert not trainer.is_senior()
        assert not trainer.can_manage_trainers()
        assert not trainer.can_view_all_data()
    
    def test_trainer_deactivation(self):
        """Test trainer deactivation and reactivation."""
        trainer = TrainerFactory()
        
        # Initially active
        assert trainer.is_active
        assert trainer.deactivated_at is None
        
        # Deactivate
        trainer.deactivate()
        assert not trainer.is_active
        assert trainer.deactivated_at is not None
        
        # Reactivate
        trainer.reactivate()
        assert trainer.is_active
        assert trainer.deactivated_at is None
    
    def test_trainer_unique_per_organization(self):
        """Test user can only have one trainer profile per organization."""
        user = UserFactory()
        org = OrganizationFactory()
        
        # Create first trainer
        Trainer.objects.create(
            user=user,
            organization=org,
            role='trainer'
        )
        
        # Try to create another trainer with same user and org
        with pytest.raises(IntegrityError):
            Trainer.objects.create(
                user=user,
                organization=org,
                role='trainer'
            )


class TestTrainerInvitationModel:
    """Test cases for TrainerInvitation model."""
    
    def test_create_invitation(self):
        """Test creating a trainer invitation."""
        org = OrganizationFactory(name="Test Gym")
        invitation = TrainerInvitationFactory(
            organization=org,
            email="newtrainer@example.com"
        )
        
        assert invitation.organization == org
        assert invitation.email == "newtrainer@example.com"
        assert invitation.status == 'pending'
        assert not invitation.is_expired()
        assert str(invitation) == "Invitation to newtrainer@example.com for Test Gym"
    
    def test_invitation_expiry(self):
        """Test invitation expiry checking."""
        # Future expiry
        invitation = TrainerInvitationFactory(
            expires_at=timezone.now() + timedelta(days=7)
        )
        assert not invitation.is_expired()
        
        # Past expiry
        invitation_expired = TrainerInvitationFactory(
            expires_at=timezone.now() - timedelta(days=1)
        )
        assert invitation_expired.is_expired()
    
    def test_invitation_can_accept(self):
        """Test invitation acceptance eligibility."""
        # Valid invitation
        invitation = TrainerInvitationFactory(
            status='pending',
            expires_at=timezone.now() + timedelta(days=1)
        )
        assert invitation.can_accept()
        
        # Expired invitation
        invitation_expired = TrainerInvitationFactory(
            status='pending',
            expires_at=timezone.now() - timedelta(days=1)
        )
        assert not invitation_expired.can_accept()
        
        # Already accepted
        invitation_accepted = TrainerInvitationFactory(status='accepted')
        assert not invitation_accepted.can_accept()


class TestAuditLogModel:
    """Test cases for AuditLog model."""
    
    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        user = UserFactory()
        org = OrganizationFactory()
        
        log = AuditLogFactory(
            user=user,
            organization=org,
            action='login'
        )
        
        assert log.user == user
        assert log.organization == org
        assert log.action == 'login'
        assert log.created_at is not None
    
    def test_audit_log_with_extra_data(self):
        """Test storing extra data in audit log."""
        extra_data = {'ip': '127.0.0.1', 'user_agent': 'Test Browser'}
        log = AuditLogFactory(extra_data=extra_data)
        
        assert log.extra_data == extra_data
        assert log.extra_data['ip'] == '127.0.0.1'
    
    def test_audit_log_ordering(self):
        """Test audit logs are ordered by newest first."""
        # Create logs with slight time differences
        logs = []
        for i in range(3):
            log = AuditLogFactory()
            logs.append(log)
        
        # Query and check ordering
        queryset = AuditLog.objects.all()
        # Most recent should be first
        assert queryset.first().id == logs[-1].id


class TestNotificationModel:
    """Test cases for Notification model."""
    
    def test_create_notification(self):
        """Test creating a notification."""
        user = UserFactory()
        notification = NotificationFactory(
            user=user,
            title="Test Notification",
            notification_type='system'
        )
        
        assert notification.user == user
        assert notification.title == "Test Notification"
        assert notification.notification_type == 'system'
        assert not notification.is_read
        # Notification str is "Type Display - user email"
        assert notification.user.email in str(notification)
        assert "System Notification" in str(notification)
    
    def test_notification_mark_read(self):
        """Test marking notification as read."""
        notification = NotificationFactory()
        
        # Initially unread
        assert not notification.is_read
        assert notification.read_at is None
        
        # Mark as read
        notification.mark_as_read()
        
        assert notification.is_read
        assert notification.read_at is not None
    
    def test_notification_with_action_url(self):
        """Test notification with action URL."""
        notification = NotificationFactory(
            action_url='/trainers/profile/'
        )
        assert notification.action_url == '/trainers/profile/'
    
    def test_notification_bulk_operations(self):
        """Test bulk notification operations."""
        user = UserFactory()
        
        # Create multiple notifications
        NotificationFactory.create_batch(5, user=user, is_read=False)
        NotificationFactory.create_batch(3, user=user, is_read=True)
        
        # Check counts
        total = Notification.objects.filter(user=user).count()
        unread = Notification.objects.filter(user=user, is_read=False).count()
        read = Notification.objects.filter(user=user, is_read=True).count()
        
        assert total == 8
        assert unread == 5
        assert read == 3