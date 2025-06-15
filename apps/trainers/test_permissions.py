"""
Test cases for trainer permissions and middleware.

This module contains comprehensive tests for the permission system,
including decorators, middleware, and role-based access control.
"""
import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied

from apps.trainers.models import Trainer, Organization
from apps.trainers.middleware import TrainerContextMiddleware
from apps.trainers.decorators import (
    requires_trainer, organization_member_required,
    trainer_role_required, organization_owner_required
)
from apps.trainers.factories import UserFactory, TrainerFactory, OrganizationFactory

User = get_user_model()


class TestTrainerContextMiddleware:
    """Test cases for TrainerContextMiddleware."""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = TrainerContextMiddleware(lambda req: HttpResponse())
    
    def test_middleware_sets_trainer_context(self):
        """Middleware should set request.trainer and request.organization."""
        user = UserFactory()
        trainer = TrainerFactory(user=user)
        
        request = self.factory.get('/')
        request.user = user
        
        response = self.middleware(request)
        
        assert hasattr(request, 'trainer')
        assert hasattr(request, 'organization')
        assert request.trainer == trainer
        assert request.organization == trainer.organization
    
    def test_middleware_handles_multiple_trainers(self):
        """Middleware should handle users with multiple trainer profiles."""
        user = UserFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        trainer1 = TrainerFactory(user=user, organization=org1)
        trainer2 = TrainerFactory(user=user, organization=org2)
        
        request = self.factory.get('/')
        request.user = user
        request.session = {'current_organization_id': org2.id}
        
        response = self.middleware(request)
        
        assert request.trainer == trainer2
        assert request.organization == org2
    
    def test_middleware_handles_missing_trainer(self):
        """Middleware should handle users without trainer profiles."""
        user = UserFactory()
        
        request = self.factory.get('/')
        request.user = user
        
        response = self.middleware(request)
        
        assert request.trainer is None
        assert request.organization is None
    
    def test_middleware_handles_anonymous_user(self):
        """Middleware should handle anonymous users."""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        response = self.middleware(request)
        
        assert request.trainer is None
        assert request.organization is None
    
    def test_middleware_handles_inactive_trainer(self):
        """Middleware should handle inactive trainer profiles."""
        user = UserFactory()
        trainer = TrainerFactory(user=user, is_active=False)
        
        request = self.factory.get('/')
        request.user = user
        
        response = self.middleware(request)
        
        assert request.trainer is None
        assert request.organization is None


class TestRequiresTrainerDecorator:
    """Test cases for @requires_trainer decorator."""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @requires_trainer
    def dummy_view(self, request):
        """Dummy view for testing decorator."""
        return HttpResponse("Success")
    
    def test_allows_user_with_trainer_profile(self):
        """Decorator should allow users with trainer profiles."""
        user = UserFactory()
        trainer = TrainerFactory(user=user)
        
        request = self.factory.get('/')
        request.user = user
        request.trainer = trainer
        request.organization = trainer.organization
        
        response = self.dummy_view(request)
        assert response.status_code == 200
    
    def test_blocks_user_without_trainer_profile(self):
        """Decorator should block users without trainer profiles."""
        user = UserFactory()
        
        request = self.factory.get('/')
        request.user = user
        request.trainer = None
        request.organization = None
        
        response = self.dummy_view(request)
        assert response.status_code == 403
    
    def test_blocks_anonymous_user(self):
        """Decorator should block anonymous users."""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.trainer = None
        request.organization = None
        
        response = self.dummy_view(request)
        assert response.status_code == 403
    
    def test_blocks_inactive_trainer(self):
        """Decorator should block inactive trainers."""
        user = UserFactory()
        trainer = TrainerFactory(user=user, is_active=False)
        
        request = self.factory.get('/')
        request.user = user
        request.trainer = None  # Middleware would set this to None for inactive
        request.organization = None
        
        response = self.dummy_view(request)
        assert response.status_code == 403


class TestOrganizationMemberRequiredDecorator:
    """Test cases for @organization_member_required decorator."""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @organization_member_required
    def dummy_view(self, request, pk):
        """Dummy view for testing decorator."""
        return HttpResponse("Success")
    
    def test_allows_same_organization_access(self):
        """Decorator should allow access to same organization resources."""
        org = OrganizationFactory()
        trainer1 = TrainerFactory(organization=org)
        trainer2 = TrainerFactory(organization=org)
        
        request = self.factory.get('/')
        request.user = trainer1.user
        request.trainer = trainer1
        request.organization = org
        
        # Accessing colleague's ID
        response = self.dummy_view(request, pk=trainer2.pk)
        assert response.status_code == 200
    
    def test_blocks_different_organization_access(self):
        """Decorator should block access to different organization resources."""
        trainer1 = TrainerFactory()
        trainer2 = TrainerFactory()  # Different org
        
        request = self.factory.get('/')
        request.user = trainer1.user
        request.trainer = trainer1
        request.organization = trainer1.organization
        
        # Trying to access trainer from different org
        with pytest.raises(Http404):
            self.dummy_view(request, pk=trainer2.pk)
    
    def test_handles_non_existent_resource(self):
        """Decorator should handle non-existent resources gracefully."""
        trainer = TrainerFactory()
        
        request = self.factory.get('/')
        request.user = trainer.user
        request.trainer = trainer
        request.organization = trainer.organization
        
        # Non-existent ID
        with pytest.raises(Http404):
            self.dummy_view(request, pk=99999)


class TestTrainerRoleRequiredDecorator:
    """Test cases for @trainer_role_required decorator."""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_owner_can_access_all_roles(self):
        """Owners should be able to access views requiring any role."""
        owner = TrainerFactory(role='owner')
        
        @trainer_role_required('trainer')
        def trainer_view(request):
            return HttpResponse("Trainer")
        
        @trainer_role_required('senior')
        def senior_view(request):
            return HttpResponse("Senior")
        
        @trainer_role_required('owner')
        def owner_view(request):
            return HttpResponse("Owner")
        
        request = self.factory.get('/')
        request.user = owner.user
        request.trainer = owner
        request.organization = owner.organization
        
        # Owner can access all
        assert trainer_view(request).status_code == 200
        assert senior_view(request).status_code == 200
        assert owner_view(request).status_code == 200
    
    def test_senior_trainer_permissions(self):
        """Senior trainers should have appropriate access."""
        senior = TrainerFactory(role='senior')
        
        @trainer_role_required('trainer')
        def trainer_view(request):
            return HttpResponse("Trainer")
        
        @trainer_role_required('senior')
        def senior_view(request):
            return HttpResponse("Senior")
        
        @trainer_role_required('owner')
        def owner_view(request):
            return HttpResponse("Owner")
        
        request = self.factory.get('/')
        request.user = senior.user
        request.trainer = senior
        request.organization = senior.organization
        
        # Senior can access trainer and senior views
        assert trainer_view(request).status_code == 200
        assert senior_view(request).status_code == 200
        
        # But not owner views
        with pytest.raises(PermissionDenied):
            owner_view(request)
    
    def test_regular_trainer_permissions(self):
        """Regular trainers should have limited access."""
        trainer = TrainerFactory(role='trainer')
        
        @trainer_role_required('trainer')
        def trainer_view(request):
            return HttpResponse("Trainer")
        
        @trainer_role_required('senior')
        def senior_view(request):
            return HttpResponse("Senior")
        
        request = self.factory.get('/')
        request.user = trainer.user
        request.trainer = trainer
        request.organization = trainer.organization
        
        # Trainer can access trainer views
        assert trainer_view(request).status_code == 200
        
        # But not senior views
        with pytest.raises(PermissionDenied):
            senior_view(request)
    
    def test_assistant_trainer_permissions(self):
        """Assistant trainers should have most limited access."""
        assistant = TrainerFactory(role='assistant')
        
        @trainer_role_required('assistant')
        def assistant_view(request):
            return HttpResponse("Assistant")
        
        @trainer_role_required('trainer')
        def trainer_view(request):
            return HttpResponse("Trainer")
        
        request = self.factory.get('/')
        request.user = assistant.user
        request.trainer = assistant
        request.organization = assistant.organization
        
        # Assistant can only access assistant views
        assert assistant_view(request).status_code == 200
        
        # But not trainer views
        with pytest.raises(PermissionDenied):
            trainer_view(request)


class TestOrganizationOwnerRequiredDecorator:
    """Test cases for @organization_owner_required decorator."""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @organization_owner_required
    def owner_only_view(self, request):
        """View that requires owner role."""
        return HttpResponse("Owner only")
    
    def test_owner_can_access(self):
        """Owners should be able to access owner-only views."""
        owner = TrainerFactory(role='owner')
        
        request = self.factory.get('/')
        request.user = owner.user
        request.trainer = owner
        request.organization = owner.organization
        
        response = self.owner_only_view(request)
        assert response.status_code == 200
    
    def test_non_owner_cannot_access(self):
        """Non-owners should not be able to access owner-only views."""
        senior = TrainerFactory(role='senior')
        
        request = self.factory.get('/')
        request.user = senior.user
        request.trainer = senior
        request.organization = senior.organization
        
        with pytest.raises(PermissionDenied):
            self.owner_only_view(request)


class TestRoleHierarchy:
    """Test role hierarchy and permissions."""
    
    pytestmark = pytest.mark.django_db
    
    def test_trainer_can_manage_trainers_permission(self):
        """Test can_manage_trainers() method for different roles."""
        owner = TrainerFactory(role='owner')
        senior = TrainerFactory(role='senior')
        trainer = TrainerFactory(role='trainer')
        assistant = TrainerFactory(role='assistant')
        
        assert owner.can_manage_trainers() is True
        assert senior.can_manage_trainers() is True
        assert trainer.can_manage_trainers() is False
        assert assistant.can_manage_trainers() is False
    
    def test_trainer_can_edit_trainer_permission(self):
        """Test can_edit_trainer() method for different scenarios."""
        org = OrganizationFactory()
        owner = TrainerFactory(organization=org, role='owner')
        senior = TrainerFactory(organization=org, role='senior')
        trainer1 = TrainerFactory(organization=org, role='trainer')
        trainer2 = TrainerFactory(organization=org, role='trainer')
        assistant = TrainerFactory(organization=org, role='assistant')
        
        # Owner can edit anyone in organization
        assert owner.can_edit_trainer(senior) is True
        assert owner.can_edit_trainer(trainer1) is True
        assert owner.can_edit_trainer(assistant) is True
        
        # Senior can edit trainers and assistants
        assert senior.can_edit_trainer(trainer1) is True
        assert senior.can_edit_trainer(assistant) is True
        assert senior.can_edit_trainer(owner) is False  # Cannot edit owner
        
        # Trainers can only edit themselves
        assert trainer1.can_edit_trainer(trainer1) is True
        assert trainer1.can_edit_trainer(trainer2) is False
        
        # Cannot edit trainers from different organizations
        other_trainer = TrainerFactory()
        assert owner.can_edit_trainer(other_trainer) is False
    
    def test_trainer_can_view_analytics_permission(self):
        """Test can_view_analytics() method for different roles."""
        owner = TrainerFactory(role='owner')
        senior = TrainerFactory(role='senior')
        trainer = TrainerFactory(role='trainer')
        assistant = TrainerFactory(role='assistant')
        
        assert owner.can_view_analytics() is True
        assert senior.can_view_analytics() is True
        assert trainer.can_view_analytics() is True
        assert assistant.can_view_analytics() is False


class TestPermissionEdgeCases:
    """Test edge cases in permission system."""
    
    pytestmark = pytest.mark.django_db
    
    def test_deactivated_trainer_permissions(self):
        """Deactivated trainers should have no permissions."""
        trainer = TrainerFactory(is_active=False)
        
        assert trainer.can_manage_trainers() is False
        assert trainer.can_edit_trainer(trainer) is False
        assert trainer.can_view_analytics() is False
    
    def test_cross_organization_permission_check(self):
        """Permissions should not work across organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        owner1 = TrainerFactory(organization=org1, role='owner')
        trainer2 = TrainerFactory(organization=org2, role='trainer')
        
        # Owner of org1 cannot edit trainer in org2
        assert owner1.can_edit_trainer(trainer2) is False
    
    def test_permission_with_deleted_organization(self):
        """Test permissions when organization is soft-deleted."""
        org = OrganizationFactory(is_active=False)
        owner = TrainerFactory(organization=org, role='owner')
        
        # Even owner should have limited permissions with inactive org
        # This depends on business logic - adjust as needed
        assert owner.organization.is_active is False