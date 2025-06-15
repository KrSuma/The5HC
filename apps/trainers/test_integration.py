"""
Integration tests for trainer app.

This module contains end-to-end tests that verify the complete
workflow of trainer-related features including multi-tenancy,
data isolation, and cross-app interactions.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.trainers.models import Trainer, Organization, TrainerInvitation, Notification, AuditLog
from apps.trainers.factories import (
    UserFactory, OrganizationFactory, TrainerFactory,
    TrainerInvitationFactory, NotificationFactory
)
from apps.clients.factories import ClientFactory
from apps.clients.models import Client
from apps.assessments.factories import AssessmentFactory
from apps.assessments.models import Assessment
from apps.sessions.factories import SessionFactory, SessionPackageFactory, PaymentFactory
from apps.sessions.models import Session, SessionPackage, Payment


class TestMultiTenantDataIsolation:
    """Test data isolation between organizations."""
    
    pytestmark = pytest.mark.django_db
    
    def test_complete_data_isolation_between_organizations(self, client):
        """Verify complete data isolation between different organizations."""
        # Create two organizations with trainers
        org1 = OrganizationFactory(name="Gym A")
        org2 = OrganizationFactory(name="Gym B")
        
        trainer1 = TrainerFactory(organization=org1, role='owner')
        trainer2 = TrainerFactory(organization=org2, role='owner')
        
        # Create data for org1
        client1 = ClientFactory(trainer=trainer1)
        assessment1 = AssessmentFactory(client=client1, trainer=trainer1)
        package1 = SessionPackageFactory(client=client1, trainer=trainer1)
        session1 = SessionFactory(
            client=client1,
            trainer=trainer1,
            package=package1
        )
        
        # Create data for org2
        client2 = ClientFactory(trainer=trainer2)
        assessment2 = AssessmentFactory(client=client2, trainer=trainer2)
        
        # Test trainer1 cannot see trainer2's data
        client.force_login(trainer1.user)
        
        # Check clients
        response = client.get(reverse('clients:list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert client1.name in content
        assert client2.name not in content
        
        # Check assessments
        response = client.get(reverse('assessments:list'))
        assert response.status_code == 200
        content = response.content.decode()
        # Check for client names instead of IDs to be more specific
        assert client1.name in content
        assert client2.name not in content
        
        # Try to access org2's client directly - should get 404
        response = client.get(
            reverse('clients:detail', kwargs={'pk': client2.pk})
        )
        assert response.status_code == 404
    
    def test_organization_switching_changes_visible_data(self, client):
        """Test that switching organizations changes visible data."""
        # Create user with access to two organizations
        user = UserFactory()
        org1 = OrganizationFactory(name="Primary Gym")
        org2 = OrganizationFactory(name="Secondary Gym")
        
        trainer1 = TrainerFactory(user=user, organization=org1)
        trainer2 = TrainerFactory(user=user, organization=org2)
        
        # Create different clients in each org
        client_org1 = ClientFactory(trainer=trainer1, name="Client Org1")
        client_org2 = ClientFactory(trainer=trainer2, name="Client Org2")
        
        client.force_login(user)
        
        # Initially should see org1 data (first trainer profile)
        response = client.get(reverse('clients:list'))
        content = response.content.decode()
        assert "Client Org1" in content
        assert "Client Org2" not in content
        
        # Switch to org2
        response = client.post(
            reverse('trainers:organization_switch'),
            {'organization_id': org2.id}
        )
        assert response.status_code == 302
        
        # Now should see org2 data
        response = client.get(reverse('clients:list'))
        content = response.content.decode()
        assert "Client Org1" not in content
        assert "Client Org2" in content


class TestTrainerInvitationWorkflow:
    """Test complete trainer invitation workflow."""
    
    pytestmark = pytest.mark.django_db
    
    def test_complete_invitation_workflow(self, client, mailoutbox):
        """Test the complete flow from invitation to trainer joining."""
        org = OrganizationFactory(name="Test Gym", max_trainers=5)
        owner = TrainerFactory(organization=org, role='owner')
        
        # Step 1: Owner sends invitation
        client.force_login(owner.user)
        response = client.post(reverse('trainers:trainer_invite'), {
            'email': 'newtrainer@example.com',
            'name': '김새롬',
            'role': 'trainer',
            'message': 'Welcome to our gym!'
        })
        
        assert response.status_code == 302
        invitation = TrainerInvitation.objects.get(email='newtrainer@example.com')
        assert invitation.status == 'pending'
        
        # Check notification was created
        assert Notification.objects.filter(
            user=owner.user,
            notification_type='trainer_invited'
        ).exists()
        
        # Check audit log
        assert AuditLog.objects.filter(
            action='trainer_invited',
            user=owner.user
        ).exists()
        
        # Step 2: New user registers with invitation token
        client.logout()
        
        # Simulate registration with invitation token
        # This would normally be handled by accounts app
        new_user = UserFactory(
            email='newtrainer@example.com',
            name='김새롬'
        )
        
        # Step 3: Accept invitation (this would be done after registration)
        invitation.accept(new_user)
        
        # Verify trainer profile was created
        new_trainer = Trainer.objects.get(user=new_user)
        assert new_trainer.organization == org
        assert new_trainer.role == 'trainer'
        assert new_trainer.invited_by == owner
        
        # Check notification for owner
        assert Notification.objects.filter(
            user=owner.user,
            notification_type='trainer_joined'
        ).exists()
        
        # Step 4: New trainer can access the system
        client.force_login(new_user)
        response = client.get(reverse('trainers:list'))
        assert response.status_code == 200
        
        # Can see other trainers in organization
        content = response.content.decode()
        assert owner.user.name in content
        assert new_user.name in content
    
    def test_invitation_expiration_handling(self):
        """Test that expired invitations cannot be accepted."""
        org = OrganizationFactory()
        
        # Create expired invitation
        invitation = TrainerInvitationFactory(
            organization=org,
            created_at=timezone.now() - timedelta(days=8)  # Expires after 7 days
        )
        
        user = UserFactory(email=invitation.email)
        
        # Try to accept expired invitation
        with pytest.raises(ValueError):
            invitation.accept(user)
        
        # Verify no trainer profile was created
        assert not Trainer.objects.filter(user=user).exists()


class TestAuditLogging:
    """Test audit logging functionality."""
    
    pytestmark = pytest.mark.django_db
    
    def test_client_operations_create_audit_logs(self, client):
        """Test that client CRUD operations create audit logs."""
        trainer = TrainerFactory()
        client.force_login(trainer.user)
        
        # Create client
        response = client.post(reverse('clients:add'), {
            'name': 'Test Client',
            'age': '30',
            'gender': 'male',
            'height': '175',
            'weight': '70',
            'email': 'testclient@example.com',
            'phone': '010-1234-5678'
        })
        
        assert response.status_code == 302
        
        # Check audit log was created
        audit_log = AuditLog.objects.filter(
            action='client_created',
            user=trainer.user
        ).first()
        
        assert audit_log is not None
        assert audit_log.organization == trainer.organization
        assert 'Test Client' in audit_log.metadata.get('client_name', '')
    
    def test_trainer_management_creates_audit_logs(self, client):
        """Test that trainer management operations create audit logs."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        trainer = TrainerFactory(organization=org, role='trainer')
        
        client.force_login(owner.user)
        
        # Deactivate trainer
        response = client.post(
            reverse('trainers:trainer_deactivate', kwargs={'pk': trainer.pk})
        )
        
        assert response.status_code == 302
        
        # Check audit log
        audit_log = AuditLog.objects.filter(
            action='trainer_deactivated',
            user=owner.user
        ).first()
        
        assert audit_log is not None
        assert audit_log.metadata.get('trainer_id') == str(trainer.pk)


class TestOrganizationDashboardMetrics:
    """Test organization dashboard metrics calculation."""
    
    pytestmark = pytest.mark.django_db
    
    def test_dashboard_shows_accurate_metrics(self, client):
        """Test that organization dashboard shows accurate metrics."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        
        # Create test data
        trainers = TrainerFactory.create_batch(3, organization=org)
        all_trainers = [owner] + trainers
        
        # Create clients for each trainer
        total_clients = 0
        for trainer in all_trainers:
            clients = ClientFactory.create_batch(2, trainer=trainer)
            total_clients += 2
            
            # Create assessments for some clients
            AssessmentFactory(client=clients[0], trainer=trainer)
        
        # Create sessions this month
        current_month_sessions = 0
        for trainer in all_trainers[:2]:  # Only first 2 trainers
            # Need to create packages first for sessions
            for client in Client.objects.filter(trainer=trainer)[:1]:
                package = SessionPackageFactory(client=client, trainer=trainer)
                SessionFactory.create_batch(
                    3,
                    client=client,
                    trainer=trainer,
                    package=package,
                    status='completed',
                    completed_at=timezone.now()
                )
                current_month_sessions += 3
        
        client.force_login(owner.user)
        response = client.get(reverse('trainers:organization_dashboard'))
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Check metrics
        assert str(len(all_trainers)) in content  # Total trainers
        assert str(total_clients) in content  # Total clients
        assert str(current_month_sessions) in content  # Sessions this month


class TestNotificationSystem:
    """Test notification system integration."""
    
    pytestmark = pytest.mark.django_db
    
    def test_notifications_created_for_key_events(self, client):
        """Test that notifications are created for important events."""
        trainer = TrainerFactory()
        client_obj = ClientFactory(trainer=trainer)
        
        client.force_login(trainer.user)
        
        # Create assessment - should trigger notification
        response = client.post(
            reverse('assessments:add', kwargs={'client_id': client_obj.pk}),
            {
                'date': timezone.now().date().isoformat(),
                # Add minimum required fields for assessment
                'overhead_squat_score': '3',
                'push_up_reps': '20',
                'single_leg_balance_left': '30',
                'single_leg_balance_right': '30',
                # Final step submission
                'step': '6',
                'save': 'true'
            }
        )
        
        # Check notification was created
        notification = Notification.objects.filter(
            user=trainer.user,
            notification_type='assessment_completed'
        ).first()
        
        assert notification is not None
        assert client_obj.name in notification.message
    
    def test_notification_badge_updates_dynamically(self, client):
        """Test that notification badge updates as notifications are read."""
        trainer = TrainerFactory()
        
        # Create unread notifications
        NotificationFactory.create_batch(
            5,
            user=trainer.user,
            is_read=False
        )
        
        client.force_login(trainer.user)
        
        # Check initial count
        response = client.get(reverse('trainers:notification_badge'))
        assert b'{"count": 5}' in response.content
        
        # Mark one as read
        notification = Notification.objects.filter(user=trainer.user).first()
        response = client.post(
            reverse('trainers:notification_mark_read', kwargs={'pk': notification.pk})
        )
        
        # Check updated count
        response = client.get(reverse('trainers:notification_badge'))
        assert b'{"count": 4}' in response.content


class TestTrainerAnalyticsIntegration:
    """Test trainer analytics integration with other apps."""
    
    pytestmark = pytest.mark.django_db
    
    def test_analytics_aggregates_data_correctly(self, client):
        """Test that analytics view aggregates data from multiple sources."""
        trainer = TrainerFactory()
        
        # Create diverse test data
        clients = ClientFactory.create_batch(10, trainer=trainer)
        
        # Assessments for 7 clients
        for client_obj in clients[:7]:
            AssessmentFactory(
                client=client_obj,
                trainer=trainer.user,
                assessment_date=timezone.now().date()
            )
        
        # Session packages
        active_packages = []
        for client_obj in clients[:5]:
            package = SessionPackageFactory(
                client=client_obj,
                trainer=trainer.user,
                total_sessions=10,
                remaining_sessions=5
            )
            active_packages.append(package)
        
        # Completed sessions this month
        for package in active_packages[:3]:
            SessionFactory.create_batch(
                2,
                client=package.client,
                trainer=trainer.user,
                package=package,
                status='completed',
                completed_at=timezone.now()
            )
        
        # Payments this month
        total_revenue = 0
        for package in active_packages:
            payment = PaymentFactory(
                package=package,
                trainer=trainer.user,
                amount=100000,
                payment_date=timezone.now().date()
            )
            total_revenue += payment.amount
        
        client.force_login(trainer.user)
        response = client.get(reverse('trainers:trainer_analytics'))
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Verify metrics are present
        assert "10" in content  # Total clients
        assert "7" in content   # Clients with assessments
        assert "5" in content   # Active packages
        assert "6" in content   # Completed sessions (3 packages * 2 sessions)


class TestPermissionIntegration:
    """Test permission system integration across the app."""
    
    pytestmark = pytest.mark.django_db
    
    def test_role_based_menu_visibility(self, client):
        """Test that navigation menu shows appropriate options based on role."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        trainer = TrainerFactory(organization=org, role='trainer')
        
        # Check owner sees all menu items
        client.force_login(owner.user)
        response = client.get(reverse('dashboard'))
        content = response.content.decode()
        
        assert "조직 관리" in content  # Organization management
        assert "트레이너 초대" in content  # Trainer invitation
        assert "대시보드" in content  # Dashboard
        
        # Check regular trainer sees limited menu
        client.force_login(trainer.user)
        response = client.get(reverse('dashboard'))
        content = response.content.decode()
        
        assert "조직 관리" not in content  # No organization management
        assert "트레이너 초대" not in content  # No trainer invitation
        assert "대시보드" in content  # Can see dashboard
    
    def test_data_access_respects_organization_boundaries(self, client):
        """Test that all data access respects organization boundaries."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        
        trainer1 = TrainerFactory(organization=org1)
        trainer2 = TrainerFactory(organization=org2)
        
        # Create data in org1
        client1 = ClientFactory(trainer=trainer1)
        assessment1 = AssessmentFactory(client=client1, trainer=trainer1.user)
        package1 = SessionPackageFactory(client=client1, trainer=trainer1.user)
        
        # Try to access org1 data as org2 trainer
        client.force_login(trainer2.user)
        
        # All these should return 404
        urls_to_test = [
            reverse('clients:client_detail', kwargs={'pk': client1.pk}),
            reverse('assessments:assessment_detail', kwargs={'pk': assessment1.pk}),
            reverse('sessions:package_detail', kwargs={'pk': package1.pk}),
        ]
        
        for url in urls_to_test:
            response = client.get(url)
            assert response.status_code == 404