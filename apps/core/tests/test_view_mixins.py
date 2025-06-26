"""
Tests for view mixins.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from django.views.generic import ListView, TemplateView, UpdateView
from django.db.models import Q

from apps.core.mixins.view_mixins import (
    HtmxResponseMixin,
    OrganizationFilterMixin,
    PermissionRequiredMixin,
    PaginationMixin,
    SearchMixin,
    AuditLogMixin,
)
from apps.clients.models import Client
from apps.trainers.models import Organization, Trainer

User = get_user_model()


class TestHtmxResponseMixin:
    """Test cases for HtmxResponseMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        
        class TestView(HtmxResponseMixin, TemplateView):
            template_name = 'test.html'
            htmx_template_name = 'test_content.html'
        
        self.view_class = TestView
    
    def test_is_htmx_request_true(self):
        """Test detection of HTMX requests."""
        request = self.factory.get('/', HTTP_HX_REQUEST='true')
        view = self.view_class()
        view.request = request
        
        assert view.is_htmx_request() is True
    
    def test_is_htmx_request_false(self):
        """Test detection of non-HTMX requests."""
        request = self.factory.get('/')
        view = self.view_class()
        view.request = request
        
        assert view.is_htmx_request() is False
    
    def test_get_template_names_htmx(self):
        """Test template selection for HTMX requests."""
        request = self.factory.get('/', HTTP_HX_REQUEST='true')
        view = self.view_class()
        view.request = request
        
        templates = view.get_template_names()
        assert templates == ['test_content.html']
    
    def test_get_template_names_regular(self):
        """Test template selection for regular requests."""
        request = self.factory.get('/')
        view = self.view_class()
        view.request = request
        
        templates = view.get_template_names()
        assert templates == ['test.html']
    
    def test_get_htmx_trigger_name(self):
        """Test getting HTMX trigger name."""
        request = self.factory.get('/', HTTP_HX_TRIGGER_NAME='submit-button')
        view = self.view_class()
        view.request = request
        
        assert view.get_htmx_trigger_name() == 'submit-button'
    
    def test_get_htmx_target(self):
        """Test getting HTMX target."""
        request = self.factory.get('/', HTTP_HX_TARGET='content-area')
        view = self.view_class()
        view.request = request
        
        assert view.get_htmx_target() == 'content-area'


@pytest.mark.django_db
class TestOrganizationFilterMixin:
    """Test cases for OrganizationFilterMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.organization = Organization.objects.create(name='Test Org')
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.trainer = Trainer.objects.create(
            user=self.user,
            organization=self.organization
        )
        
        # Create test clients
        self.org_client = Client.objects.create(
            name='Org Client',
            trainer=self.trainer,
            email='org@example.com',
            phone='010-1234-5678',
            age=30,
            gender='male',
            height=175.0,
            weight=70.0
        )
        
        # Create another org and client
        self.other_org = Organization.objects.create(name='Other Org')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.other_trainer = Trainer.objects.create(
            user=self.other_user,
            organization=self.other_org
        )
        self.other_client = Client.objects.create(
            name='Other Client',
            trainer=self.other_trainer,
            email='other@example.com',
            phone='010-9876-5432',
            age=25,
            gender='female',
            height=165.0,
            weight=55.0
        )
        
        class TestView(OrganizationFilterMixin, ListView):
            model = Client
            organization_field = 'trainer__organization'
        
        self.view_class = TestView
    
    def test_get_organization_from_user(self):
        """Test getting organization from user's trainer profile."""
        request = self.factory.get('/')
        request.user = self.user
        
        view = self.view_class()
        view.request = request
        
        org = view.get_organization()
        assert org == self.organization
    
    def test_get_organization_superuser_no_filter(self):
        """Test superuser sees all data when no org specified."""
        superuser = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@test.com'
        )
        request = self.factory.get('/')
        request.user = superuser
        
        view = self.view_class()
        view.request = request
        
        org = view.get_organization()
        assert org is None
    
    def test_get_organization_superuser_with_filter(self):
        """Test superuser can filter by specific organization."""
        superuser = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@test.com'
        )
        request = self.factory.get(f'/?organization_id={self.organization.id}')
        request.user = superuser
        
        view = self.view_class()
        view.request = request
        
        org = view.get_organization()
        assert org == self.organization
    
    def test_queryset_filtered_by_organization(self):
        """Test queryset is filtered by user's organization."""
        request = self.factory.get('/')
        request.user = self.user
        
        view = self.view_class()
        view.request = request
        view.model = Client
        
        queryset = view.get_queryset()
        assert list(queryset) == [self.org_client]
    
    def test_queryset_superuser_sees_all(self):
        """Test superuser sees all data."""
        superuser = User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@test.com'
        )
        request = self.factory.get('/')
        request.user = superuser
        
        view = self.view_class()
        view.request = request
        view.model = Client
        
        queryset = view.get_queryset()
        assert set(queryset) == {self.org_client, self.other_client}
    
    def test_context_includes_organization(self):
        """Test organization is added to context."""
        request = self.factory.get('/')
        request.user = self.user
        
        view = self.view_class()
        view.request = request
        view.object_list = []  # Required for ListView.get_context_data
        
        context = view.get_context_data()
        assert context['current_organization'] == self.organization


@pytest.mark.django_db
class TestPermissionRequiredMixin:
    """Test cases for PermissionRequiredMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
    def test_single_permission_required(self):
        """Test single permission requirement."""
        class TestView(PermissionRequiredMixin, TemplateView):
            permission_required = 'clients.view_client'
        
        view = TestView()
        perms = view.get_permission_required()
        assert perms == ['clients.view_client']
    
    def test_multiple_permissions_required(self):
        """Test multiple permission requirements."""
        class TestView(PermissionRequiredMixin, TemplateView):
            permission_required = ['clients.view_client', 'clients.change_client']
        
        view = TestView()
        perms = view.get_permission_required()
        assert perms == ['clients.view_client', 'clients.change_client']
    
    def test_missing_permission_required_raises_error(self):
        """Test missing permission_required raises ImproperlyConfigured."""
        class TestView(PermissionRequiredMixin, TemplateView):
            pass
        
        view = TestView()
        with pytest.raises(ImproperlyConfigured):
            view.get_permission_required()
    
    def test_has_permission_all_mode(self):
        """Test permission checking in 'all' mode."""
        # Add permissions to user
        view_perm = Permission.objects.get(codename='view_client')
        change_perm = Permission.objects.get(codename='change_client')
        self.user.user_permissions.add(view_perm, change_perm)
        
        class TestView(PermissionRequiredMixin, TemplateView):
            permission_required = ['clients.view_client', 'clients.change_client']
            permission_mode = 'all'
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestView()
        view.request = request
        
        assert view.has_permission() is True
    
    def test_has_permission_any_mode(self):
        """Test permission checking in 'any' mode."""
        # Add only one permission to user
        view_perm = Permission.objects.get(codename='view_client')
        self.user.user_permissions.add(view_perm)
        
        class TestView(PermissionRequiredMixin, TemplateView):
            permission_required = ['clients.view_client', 'clients.change_client']
            permission_mode = 'any'
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestView()
        view.request = request
        
        assert view.has_permission() is True
    
    def test_dispatch_with_permission_denied(self):
        """Test dispatch raises PermissionDenied for unauthorized users."""
        class TestView(PermissionRequiredMixin, TemplateView):
            permission_required = 'clients.view_client'
            template_name = 'test.html'
        
        request = self.factory.get('/')
        request.user = self.user
        
        view = TestView.as_view()
        
        with pytest.raises(PermissionDenied):
            view(request)


class TestPaginationMixin:
    """Test cases for PaginationMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        
        class TestView(PaginationMixin, ListView):
            model = Mock()
            paginate_by = 10
            max_paginate_by = 50
        
        self.view_class = TestView
    
    def test_get_paginate_by_default(self):
        """Test default pagination size."""
        request = self.factory.get('/')
        view = self.view_class()
        view.request = request
        
        assert view.get_paginate_by(Mock()) == 10
    
    def test_get_paginate_by_from_query_param(self):
        """Test pagination size from query parameter."""
        request = self.factory.get('/?page_size=25')
        view = self.view_class()
        view.request = request
        
        assert view.get_paginate_by(Mock()) == 25
    
    def test_get_paginate_by_enforces_maximum(self):
        """Test maximum pagination size is enforced."""
        request = self.factory.get('/?page_size=100')
        view = self.view_class()
        view.request = request
        
        assert view.get_paginate_by(Mock()) == 50
    
    def test_get_paginate_by_invalid_param(self):
        """Test invalid page_size parameter falls back to default."""
        request = self.factory.get('/?page_size=invalid')
        view = self.view_class()
        view.request = request
        
        assert view.get_paginate_by(Mock()) == 10
    
    def test_paginate_queryset(self):
        """Test queryset pagination."""
        # Create a real list that Django paginator can work with
        items = list(range(25))
        
        request = self.factory.get('/?page=2')
        view = self.view_class()
        view.request = request
        
        paginator, page, object_list, is_paginated = view.paginate_queryset(items, 10)
        
        assert paginator.num_pages == 3
        assert page.number == 2
        assert is_paginated is True
        assert len(object_list) == 10


@pytest.mark.django_db
class TestSearchMixin:
    """Test cases for SearchMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        
        # Create a test user and trainer first
        user = User.objects.create_user(username='testuser', password='testpass')
        org = Organization.objects.create(name='Test Org')
        trainer = Trainer.objects.create(user=user, organization=org)
        
        # Create test clients
        Client.objects.create(
            name='John Doe', 
            email='john@example.com',
            phone='010-1111-1111',
            trainer=trainer,
            age=35,
            gender='male',
            height=180.0,
            weight=75.0
        )
        Client.objects.create(
            name='Jane Smith', 
            email='jane@example.com',
            phone='010-2222-2222',
            trainer=trainer,
            age=28,
            gender='female',
            height=165.0,
            weight=58.0
        )
        Client.objects.create(
            name='Bob Johnson', 
            email='bob@example.com',
            phone='010-3333-3333',
            trainer=trainer,
            age=42,
            gender='male',
            height=175.0,
            weight=80.0
        )
        
        class TestView(SearchMixin, ListView):
            model = Client
            search_fields = ['name', 'email']
        
        self.view_class = TestView
    
    def test_get_search_query(self):
        """Test getting search query from request."""
        request = self.factory.get('/?search=john')
        view = self.view_class()
        view.request = request
        
        assert view.get_search_query() == 'john'
    
    def test_apply_search_by_name(self):
        """Test search filtering by name."""
        request = self.factory.get('/?search=john')
        view = self.view_class()
        view.request = request
        view.model = Client
        
        queryset = view.get_queryset()
        names = [c.name for c in queryset]
        assert set(names) == {'John Doe', 'Bob Johnson'}
    
    def test_apply_search_by_email(self):
        """Test search filtering by email."""
        request = self.factory.get('/?search=jane@')
        view = self.view_class()
        view.request = request
        view.model = Client
        
        queryset = view.get_queryset()
        assert queryset.count() == 1
        assert queryset.first().name == 'Jane Smith'
    
    def test_no_search_returns_all(self):
        """Test no search query returns all results."""
        request = self.factory.get('/')
        view = self.view_class()
        view.request = request
        view.model = Client
        
        queryset = view.get_queryset()
        assert queryset.count() == 3
    
    def test_search_context(self):
        """Test search information is added to context."""
        request = self.factory.get('/?search=test')
        view = self.view_class()
        view.request = request
        view.object_list = []
        
        context = view.get_context_data()
        assert context['search_query'] == 'test'
        assert context['search_query_param'] == 'search'
        assert context['search_fields'] == ['name', 'email']


class TestAuditLogMixin:
    """Test cases for AuditLogMixin."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        class TestView(AuditLogMixin, UpdateView):
            model = Mock()
            audit_action = 'update'
            audit_message_template = 'Updated {object} by {user}'
        
        self.view_class = TestView
    
    def test_get_audit_action(self):
        """Test getting audit action."""
        view = self.view_class()
        assert view.get_audit_action() == 'update'
    
    def test_get_audit_message(self):
        """Test building audit message."""
        view = self.view_class()
        view.request = Mock()
        view.request.user = self.user
        view.object = Mock()
        view.object.__str__ = Mock(return_value='TestObject')
        
        message = view.get_audit_message()
        assert message == f'Updated TestObject by {self.user}'
    
    def test_get_client_ip_direct(self):
        """Test getting client IP from REMOTE_ADDR."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        view = self.view_class()
        view.request = request
        
        assert view.get_client_ip() == '192.168.1.1'
    
    def test_get_client_ip_forwarded(self):
        """Test getting client IP from X-Forwarded-For."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        
        view = self.view_class()
        view.request = request
        
        assert view.get_client_ip() == '10.0.0.1'
    
    @patch('apps.core.mixins.view_mixins.logger')
    def test_create_audit_log(self, mock_logger):
        """Test audit log creation."""
        request = self.factory.get('/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        view = self.view_class()
        view.request = request
        view.object = Mock()
        view.object.__str__ = Mock(return_value='TestObject')
        
        view.create_audit_log(extra_field='extra_value')
        
        # Check logger was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert 'Updated TestObject by' in call_args[0][0]
        assert call_args[1]['extra']['user'] == self.user.id
        assert call_args[1]['extra']['ip_address'] == '192.168.1.1'
        assert call_args[1]['extra']['extra_field'] == 'extra_value'