"""
Test cases for trainer views.

This module contains comprehensive tests for all trainer views,
including authentication, permissions, HTMX handling, and business logic.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from apps.trainers.models import Trainer, Organization, TrainerInvitation, Notification
from apps.trainers.factories import (
    UserFactory, OrganizationFactory, TrainerFactory,
    TrainerInvitationFactory, NotificationFactory
)
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.sessions.factories import SessionFactory, SessionPackageFactory

User = get_user_model()


class TestTrainerAuthentication:
    """Test authentication requirements for trainer views."""
    
    pytestmark = pytest.mark.django_db
    
    def test_unauthenticated_access_redirects_to_login(self, client):
        """Unauthenticated users should be redirected to login."""
        urls = [
            reverse('trainers:list'),
            reverse('trainers:detail', kwargs={'pk': 1}),
            reverse('trainers:profile_edit'),
            reverse('trainers:organization_edit'),
            reverse('trainers:invite'),
        ]
        
        for url in urls:
            response = client.get(url)
            assert response.status_code == 302
            assert '/accounts/login/' in response.url
    
    def test_user_without_trainer_profile_gets_error(self, client):
        """Users without trainer profiles should see appropriate error."""
        user = UserFactory()
        client.force_login(user)
        
        response = client.get(reverse('trainers:list'))
        assert response.status_code == 200
        assert "트레이너 프로필이 없습니다" in response.content.decode()


class TestTrainerListView:
    """Test cases for trainer list view."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_can_view_organization_trainers(self, client):
        """Trainers should see only trainers in their organization."""
        org = OrganizationFactory()
        trainer1 = TrainerFactory(organization=org)
        trainer2 = TrainerFactory(organization=org)
        other_trainer = TrainerFactory()  # Different org
        
        client.force_login(trainer1.user)
        response = client.get(reverse('trainers:trainer_list'))
        
        assert response.status_code == 200
        content = response.content.decode()
        assert trainer1.user.name in content
        assert trainer2.user.name in content
        assert other_trainer.user.name not in content
    
    def test_trainer_list_search(self, client):
        """Test search functionality in trainer list."""
        org = OrganizationFactory()
        trainer1 = TrainerFactory(organization=org, user__name="김철수")
        trainer2 = TrainerFactory(organization=org, user__name="이영희")
        
        client.force_login(trainer1.user)
        response = client.get(reverse('trainers:trainer_list'), {'search': '영희'})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "이영희" in content
        assert "김철수" not in content
    
    def test_trainer_list_htmx_request(self, client):
        """Test HTMX partial response for trainer list."""
        trainer = TrainerFactory()
        client.force_login(trainer.user)
        
        response = client.get(
            reverse('trainers:trainer_list'),
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='main-content'
        )
        
        assert response.status_code == 200
        assert 'trainers/trainer_list_content.html' in [t.name for t in response.templates]


class TestTrainerDetailView:
    """Test cases for trainer detail view."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_can_view_colleague_profile(self, client):
        """Trainers can view profiles of colleagues in same organization."""
        org = OrganizationFactory()
        trainer1 = TrainerFactory(organization=org)
        trainer2 = TrainerFactory(organization=org)
        
        client.force_login(trainer1.user)
        response = client.get(reverse('trainers:detail', kwargs={'pk': trainer2.pk}))
        
        assert response.status_code == 200
        assert trainer2.user.name in response.content.decode()
    
    def test_trainer_cannot_view_other_org_profiles(self, client):
        """Trainers cannot view profiles from other organizations."""
        trainer1 = TrainerFactory()
        trainer2 = TrainerFactory()  # Different org
        
        client.force_login(trainer1.user)
        response = client.get(reverse('trainers:trainer_detail', kwargs={'pk': trainer2.pk}))
        
        assert response.status_code == 404
    
    def test_trainer_detail_shows_statistics(self, client):
        """Trainer detail should show client and session statistics."""
        trainer = TrainerFactory()
        # Create some clients and sessions
        ClientFactory.create_batch(3, trainer=trainer.user)
        SessionFactory.create_batch(5, trainer=trainer.user)
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:trainer_detail', kwargs={'pk': trainer.pk}))
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "3" in content  # Client count
        assert "5" in content  # Session count


class TestTrainerProfileEditView:
    """Test cases for trainer profile editing."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_can_edit_own_profile(self, client):
        """Trainers can edit their own profile."""
        trainer = TrainerFactory()
        client.force_login(trainer.user)
        
        response = client.get(reverse('trainers:profile_edit'))
        assert response.status_code == 200
        
        # Submit profile update
        response = client.post(reverse('trainers:profile_edit'), {
            'bio': 'Updated bio',
            'certifications': 'New certifications',
            'specialties': 'New specialties',
            'phone': '010-1234-5678'
        })
        
        assert response.status_code == 302
        trainer.refresh_from_db()
        assert trainer.bio == 'Updated bio'
        assert trainer.certifications == 'New certifications'
    
    def test_senior_can_edit_junior_profile(self, client):
        """Senior trainers can edit profiles of junior trainers."""
        org = OrganizationFactory()
        senior = TrainerFactory(organization=org, role='senior')
        junior = TrainerFactory(organization=org, role='trainer')
        
        client.force_login(senior.user)
        
        url = reverse('trainers:profile_edit') + f'?trainer_id={junior.pk}'
        response = client.get(url)
        assert response.status_code == 200
        
        # Submit profile update
        response = client.post(url, {
            'bio': 'Updated by senior',
            'certifications': 'Updated certs',
            'specialties': 'Updated specialties',
            'phone': '010-9876-5432'
        })
        
        assert response.status_code == 302
        junior.refresh_from_db()
        assert junior.bio == 'Updated by senior'
    
    def test_regular_trainer_cannot_edit_others(self, client):
        """Regular trainers cannot edit other trainers' profiles."""
        org = OrganizationFactory()
        trainer1 = TrainerFactory(organization=org, role='trainer')
        trainer2 = TrainerFactory(organization=org, role='trainer')
        
        client.force_login(trainer1.user)
        
        url = reverse('trainers:profile_edit') + f'?trainer_id={trainer2.pk}'
        response = client.get(url)
        assert response.status_code == 403
    
    def test_profile_photo_upload(self, client):
        """Test profile photo upload functionality."""
        trainer = TrainerFactory()
        client.force_login(trainer.user)
        
        # Create a simple image file
        photo = SimpleUploadedFile(
            "test_photo.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        response = client.post(reverse('trainers:profile_edit'), {
            'bio': trainer.bio,
            'certifications': trainer.certifications,
            'specialties': trainer.specialties,
            'phone': trainer.phone,
            'photo': photo
        })
        
        assert response.status_code == 302
        trainer.refresh_from_db()
        assert trainer.photo is not None


class TestOrganizationManagement:
    """Test cases for organization management views."""
    
    pytestmark = pytest.mark.django_db
    
    def test_only_owner_can_edit_organization(self, client):
        """Only organization owners can edit organization details."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        senior = TrainerFactory(organization=org, role='senior')
        
        # Owner can access
        client.force_login(owner.user)
        response = client.get(reverse('trainers:organization_edit'))
        assert response.status_code == 200
        
        # Non-owner cannot access
        client.force_login(senior.user)
        response = client.get(reverse('trainers:organization_edit'))
        assert response.status_code == 403
    
    def test_organization_edit_form_submission(self, client):
        """Test organization edit form submission."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        
        client.force_login(owner.user)
        response = client.post(reverse('trainers:organization_edit'), {
            'name': 'Updated Gym Name',
            'description': 'Updated description',
            'address': 'New address',
            'phone': '02-1234-5678',
            'business_number': '123-45-67890'
        })
        
        assert response.status_code == 302
        org.refresh_from_db()
        assert org.name == 'Updated Gym Name'
        assert org.description == 'Updated description'
    
    def test_organization_dashboard_access(self, client):
        """Test organization dashboard access control."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        trainer = TrainerFactory(organization=org, role='trainer')
        
        # Owner can access
        client.force_login(owner.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        assert response.status_code == 200
        
        # Regular trainer cannot access
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        assert response.status_code == 403
    
    def test_organization_dashboard_statistics(self, client):
        """Test organization dashboard shows correct statistics."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        
        # Create test data
        TrainerFactory.create_batch(3, organization=org)  # 3 more trainers
        for trainer in org.trainers.all():
            ClientFactory.create_batch(2, trainer=trainer.user)
        
        client.force_login(owner.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "4" in content  # Total trainers (including owner)
        assert "8" in content  # Total clients (4 trainers * 2 clients)


class TestTrainerInvitations:
    """Test cases for trainer invitation system."""
    
    pytestmark = pytest.mark.django_db
    
    def test_senior_can_invite_trainers(self, client):
        """Senior trainers can invite new trainers."""
        org = OrganizationFactory()
        senior = TrainerFactory(organization=org, role='senior')
        
        client.force_login(senior.user)
        response = client.get(reverse('trainers:invite'))
        assert response.status_code == 200
        
        # Submit invitation
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'newtrainer@example.com',
            'name': '새로운 트레이너',
            'role': 'trainer',
            'message': 'Welcome to our gym!'
        })
        
        assert response.status_code == 302
        assert TrainerInvitation.objects.filter(email='newtrainer@example.com').exists()
    
    def test_regular_trainer_cannot_invite(self, client):
        """Regular trainers cannot invite new trainers."""
        trainer = TrainerFactory(role='trainer')
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:trainer_invite'))
        assert response.status_code == 403
    
    def test_cannot_invite_existing_user(self, client):
        """Cannot send invitation to existing user email."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        existing_user = UserFactory(email='existing@example.com')
        
        client.force_login(owner.user)
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'existing@example.com',
            'name': 'Test',
            'role': 'trainer',
            'message': 'Test message'
        })
        
        assert response.status_code == 200  # Form redisplayed
        assert not TrainerInvitation.objects.filter(email='existing@example.com').exists()
    
    def test_invitation_limit_enforcement(self, client):
        """Test invitation limits are enforced."""
        org = OrganizationFactory(max_trainers=2)
        owner = TrainerFactory(organization=org, role='owner')
        
        # Already has 1 trainer (owner), can invite 1 more
        client.force_login(owner.user)
        
        # First invitation should succeed
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'trainer1@example.com',
            'name': 'Trainer 1',
            'role': 'trainer',
            'message': 'Welcome!'
        })
        assert response.status_code == 302
        
        # Create the trainer to fill the slot
        TrainerFactory(organization=org)
        
        # Second invitation should fail (limit reached)
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'trainer2@example.com',
            'name': 'Trainer 2',
            'role': 'trainer',
            'message': 'Welcome!'
        })
        assert response.status_code == 200  # Form redisplayed with error


class TestTrainerDeactivation:
    """Test cases for trainer deactivation."""
    
    pytestmark = pytest.mark.django_db
    
    def test_owner_can_deactivate_trainers(self, client):
        """Owners can deactivate trainers in their organization."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        trainer = TrainerFactory(organization=org, role='trainer')
        
        client.force_login(owner.user)
        response = client.post(reverse('trainers:deactivate', kwargs={'pk': trainer.pk}))
        
        assert response.status_code == 302
        trainer.refresh_from_db()
        assert not trainer.is_active
    
    def test_cannot_deactivate_self(self, client):
        """Trainers cannot deactivate themselves."""
        owner = TrainerFactory(role='owner')
        
        client.force_login(owner.user)
        response = client.post(reverse('trainers:trainer_deactivate', kwargs={'pk': owner.pk}))
        
        assert response.status_code == 200
        owner.refresh_from_db()
        assert owner.is_active  # Should still be active
    
    def test_cannot_deactivate_last_owner(self, client):
        """Cannot deactivate the last owner of an organization."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        senior = TrainerFactory(organization=org, role='senior')
        
        # Create another user who could theoretically deactivate
        admin_user = UserFactory(is_staff=True, is_superuser=True)
        client.force_login(admin_user)
        
        # Try to deactivate the only owner
        response = client.post(reverse('trainers:trainer_deactivate', kwargs={'pk': owner.pk}))
        
        owner.refresh_from_db()
        assert owner.is_active  # Should still be active


class TestNotificationSystem:
    """Test cases for notification system."""
    
    pytestmark = pytest.mark.django_db
    
    def test_notification_list_view(self, client):
        """Test notification list view shows user's notifications."""
        trainer = TrainerFactory()
        notif1 = NotificationFactory(user=trainer.user, title="Test 1")
        notif2 = NotificationFactory(user=trainer.user, title="Test 2")
        other_notif = NotificationFactory(title="Other")  # Different user
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:notifications'))
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test 1" in content
        assert "Test 2" in content
        assert "Other" not in content
    
    def test_mark_notification_read(self, client):
        """Test marking notifications as read."""
        trainer = TrainerFactory()
        notification = NotificationFactory(user=trainer.user, is_read=False)
        
        client.force_login(trainer.user)
        response = client.post(
            reverse('trainers:notification_mark_read', kwargs={'pk': notification.pk})
        )
        
        assert response.status_code == 302
        notification.refresh_from_db()
        assert notification.is_read
    
    def test_notification_badge_count(self, client):
        """Test notification badge shows unread count."""
        trainer = TrainerFactory()
        NotificationFactory.create_batch(3, user=trainer.user, is_read=False)
        NotificationFactory.create_batch(2, user=trainer.user, is_read=True)
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:notification_badge'))
        
        assert response.status_code == 200
        assert b'{"count": 3}' in response.content
    
    def test_notification_auto_creation(self, client):
        """Test notifications are created for important events."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        
        client.force_login(owner.user)
        
        # Invite a trainer - should create notification
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'newtrainer@example.com',
            'name': 'New Trainer',
            'role': 'trainer',
            'message': 'Welcome!'
        })
        
        assert response.status_code == 302
        # Check if notification was created for the owner
        assert Notification.objects.filter(
            user=owner.user,
            notification_type='trainer_invited'
        ).exists()


class TestOrganizationSwitching:
    """Test cases for organization switching functionality."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_with_multiple_orgs_can_switch(self, client):
        """Trainers in multiple organizations can switch between them."""
        user = UserFactory()
        org1 = OrganizationFactory(name="Gym 1")
        org2 = OrganizationFactory(name="Gym 2")
        trainer1 = TrainerFactory(user=user, organization=org1)
        trainer2 = TrainerFactory(user=user, organization=org2)
        
        client.force_login(user)
        
        # Switch to org2
        response = client.post(
            reverse('trainers:organization_switch'),
            {'organization_id': org2.id}
        )
        
        assert response.status_code == 302
        # Check session was updated
        assert client.session.get('current_organization_id') == org2.id
    
    def test_cannot_switch_to_unauthorized_org(self, client):
        """Trainers cannot switch to organizations they don't belong to."""
        trainer = TrainerFactory()
        other_org = OrganizationFactory()
        
        client.force_login(trainer.user)
        
        response = client.post(
            reverse('trainers:organization_switch'),
            {'organization_id': other_org.id}
        )
        
        assert response.status_code == 403


class TestTrainerAnalytics:
    """Test cases for trainer analytics view."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_analytics_shows_correct_data(self, client):
        """Trainer analytics should show correct statistics."""
        trainer = TrainerFactory()
        
        # Create test data
        clients = ClientFactory.create_batch(5, trainer=trainer.user)
        for client_obj in clients[:3]:
            AssessmentFactory(client=client_obj, trainer=trainer.user)
        
        # Create sessions with various statuses
        SessionFactory.create_batch(
            3,
            trainer=trainer.user,
            status='completed',
            completed_at=timezone.now()
        )
        SessionFactory.create_batch(
            2,
            trainer=trainer.user,
            status='scheduled',
            scheduled_date=timezone.now().date() + timedelta(days=1)
        )
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:analytics'))
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check if statistics are present
        assert "5" in content  # Total clients
        assert "3" in content  # Assessments or completed sessions
    
    def test_analytics_htmx_refresh(self, client):
        """Test HTMX partial refresh of analytics data."""
        trainer = TrainerFactory()
        
        client.force_login(trainer.user)
        response = client.get(
            reverse('trainers:trainer_analytics'),
            HTTP_HX_REQUEST='true',
            HTTP_HX_TARGET='analytics-content'
        )
        
        assert response.status_code == 200
        assert 'trainers/partials/analytics_content.html' in [t.name for t in response.templates]


class TestPermissionDecorators:
    """Test permission decorators work correctly."""
    
    pytestmark = pytest.mark.django_db
    
    def test_requires_trainer_decorator(self, client):
        """Test @requires_trainer decorator functionality."""
        user_without_trainer = UserFactory()
        user_with_trainer = TrainerFactory().user
        
        # User without trainer profile should get error
        client.force_login(user_without_trainer)
        response = client.get(reverse('trainers:organization_dashboard'))
        assert response.status_code == 403
        
        # User with trainer profile passes first check (but may fail role check)
        client.force_login(user_with_trainer)
        response = client.get(reverse('trainers:organization_dashboard'))
        # Will be 403 due to role check, but passed trainer check
    
    def test_organization_owner_required_decorator(self, client):
        """Test @organization_owner_required decorator."""
        owner = TrainerFactory(role='owner')
        senior = TrainerFactory(role='senior')
        
        # Owner can access
        client.force_login(owner.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        assert response.status_code == 200
        
        # Non-owner cannot access
        client.force_login(senior.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        assert response.status_code == 403
    
    def test_trainer_role_required_decorator(self, client):
        """Test @trainer_role_required decorator with different roles."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        senior = TrainerFactory(organization=org, role='senior')
        trainer = TrainerFactory(organization=org, role='trainer')
        
        # Test view that requires 'senior' role (trainer_invite)
        # Owner can access (higher role)
        client.force_login(owner.user)
        response = client.get(reverse('trainers:trainer_invite'))
        assert response.status_code == 200
        
        # Senior can access
        client.force_login(senior.user)
        response = client.get(reverse('trainers:trainer_invite'))
        assert response.status_code == 200
        
        # Regular trainer cannot access
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:trainer_invite'))
        assert response.status_code == 403


class TestFormValidation:
    """Test form validation and error handling."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_profile_form_validation(self, client):
        """Test trainer profile form validation."""
        trainer = TrainerFactory()
        client.force_login(trainer.user)
        
        # Submit with invalid phone number
        response = client.post(reverse('trainers:profile_edit'), {
            'bio': 'Test bio',
            'certifications': 'Test cert',
            'specialties': 'Test spec',
            'phone': 'invalid-phone'  # Invalid format
        })
        
        assert response.status_code == 200  # Form redisplayed
        assert "올바른 전화번호 형식" in response.content.decode()
    
    def test_organization_form_validation(self, client):
        """Test organization form validation."""
        owner = TrainerFactory(role='owner')
        client.force_login(owner.user)
        
        # Submit with empty required field
        response = client.post(reverse('trainers:organization_edit'), {
            'name': '',  # Required field
            'description': 'Test',
            'address': 'Test address',
            'phone': '02-1234-5678'
        })
        
        assert response.status_code == 200  # Form redisplayed
        assert "필수" in response.content.decode()
    
    def test_invitation_form_duplicate_email(self, client):
        """Test invitation form prevents duplicate pending invitations."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        
        # Create existing invitation
        TrainerInvitationFactory(
            organization=org,
            email='duplicate@example.com',
            status='pending'
        )
        
        client.force_login(owner.user)
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'duplicate@example.com',
            'name': 'Test',
            'role': 'trainer',
            'message': 'Test'
        })
        
        assert response.status_code == 200  # Form redisplayed
        assert "이미 초대" in response.content.decode()