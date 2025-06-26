"""
Comprehensive tests for BaseService class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.services.base import BaseService
from apps.trainers.factories import OrganizationFactory, TrainerFactory
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

User = get_user_model()


# Create a test model class for testing BaseService
class TestModel(models.Model):
    """Test model for BaseService tests."""
    name = models.CharField(max_length=100)
    organization = models.ForeignKey('trainers.Organization', on_delete=models.CASCADE, null=True)
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    
    class Meta:
        app_label = 'core'
        
    def full_clean(self):
        """Mock full_clean for testing."""
        if not self.name:
            raise ValidationError({'name': ['This field is required.']})


class TestService(BaseService):
    """Test service implementation for testing BaseService."""
    model = TestModel


@pytest.mark.django_db
class TestBaseService:
    """Test cases for BaseService functionality."""
    
    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return OrganizationFactory()
    
    @pytest.fixture
    def trainer_user(self, organization):
        """Create user with trainer profile."""
        user = UserFactory()
        TrainerFactory(user=user, organization=organization)
        return user
    
    @pytest.fixture
    def regular_user(self):
        """Create regular user without trainer profile."""
        return UserFactory()
    
    @pytest.fixture
    def superuser(self):
        """Create superuser."""
        return UserFactory(is_superuser=True)
    
    @pytest.fixture
    def service(self, trainer_user):
        """Create test service instance."""
        return TestService(user=trainer_user)
    
    @pytest.fixture
    def service_no_user(self):
        """Create service instance without user."""
        return TestService()
    
    def test_init_with_user(self, trainer_user):
        """Test service initialization with user."""
        service = TestService(user=trainer_user)
        assert service.user == trainer_user
        assert service._errors == []
    
    def test_init_without_user(self):
        """Test service initialization without user."""
        service = TestService()
        assert service.user is None
        assert service._errors == []
    
    def test_organization_property_with_trainer(self, service, organization):
        """Test organization property returns trainer's organization."""
        assert service.organization == organization
    
    def test_organization_property_without_trainer(self, regular_user):
        """Test organization property returns None for non-trainer user."""
        service = TestService(user=regular_user)
        assert service.organization is None
    
    def test_organization_property_no_user(self, service_no_user):
        """Test organization property returns None when no user."""
        assert service_no_user.organization is None
    
    def test_get_queryset_no_model(self):
        """Test get_queryset raises error when model not defined."""
        class NoModelService(BaseService):
            pass
        
        service = NoModelService()
        with pytest.raises(NotImplementedError, match="Service must define a model"):
            service.get_queryset()
    
    @patch('apps.core.services.base.BaseService.model')
    def test_get_queryset_with_organization_field(self, mock_model, service, organization):
        """Test get_queryset filters by organization when model has organization field."""
        mock_queryset = Mock()
        mock_model.objects.all.return_value = mock_queryset
        mock_model._meta.get_field.return_value = Mock()  # Has organization field
        
        # Set model to have organization field
        setattr(mock_model, 'organization', Mock())
        
        service.get_queryset()
        
        mock_queryset.filter.assert_called_once_with(organization=organization)
    
    @patch('apps.core.services.base.BaseService.model')
    def test_get_queryset_with_trainer_field(self, mock_model, service, organization):
        """Test get_queryset filters by trainer's organization when model has trainer field."""
        mock_queryset = Mock()
        mock_model.objects.all.return_value = mock_queryset
        
        # Remove organization field, add trainer field
        delattr(mock_model, 'organization') if hasattr(mock_model, 'organization') else None
        setattr(mock_model, 'trainer', Mock())
        
        service.get_queryset()
        
        mock_queryset.filter.assert_called_once_with(
            trainer__trainer__organization=organization
        )
    
    def test_get_object_success(self, service, organization):
        """Test get_object returns object when found and permitted."""
        # Create mock object with proper attributes
        mock_obj = Mock()
        mock_obj.organization = organization
        
        with patch.object(service, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.return_value = mock_obj
            mock_get_queryset.return_value = mock_queryset
            
            result = service.get_object(1)
            
            assert result == mock_obj
            mock_queryset.get.assert_called_once_with(pk=1)
            assert not service.has_errors
    
    def test_get_object_not_found(self, service):
        """Test get_object handles DoesNotExist exception."""
        with patch.object(service, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.side_effect = TestModel.DoesNotExist
            mock_get_queryset.return_value = mock_queryset
            
            result = service.get_object(999)
            
            assert result is None
            assert service.has_errors
            assert "객체를 찾을 수 없습니다." in service.errors
    
    def test_get_object_no_permission(self, service):
        """Test get_object returns None when permission denied."""
        mock_obj = Mock()
        
        with patch.object(service, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.return_value = mock_obj
            mock_get_queryset.return_value = mock_queryset
            
            with patch.object(service, 'check_permission', return_value=False):
                result = service.get_object(1)
                
                assert result is None
                assert service.has_errors
                assert "권한이 없습니다." in service.errors
    
    def test_check_permission_no_user(self, service_no_user):
        """Test check_permission returns False when no user."""
        mock_obj = Mock()
        assert service_no_user.check_permission(mock_obj) is False
    
    def test_check_permission_superuser(self, superuser):
        """Test check_permission returns True for superuser."""
        service = TestService(user=superuser)
        mock_obj = Mock()
        assert service.check_permission(mock_obj) is True
    
    def test_check_permission_organization_match(self, service, organization):
        """Test check_permission returns True when organization matches."""
        mock_obj = Mock()
        mock_obj.organization = organization
        assert service.check_permission(mock_obj) is True
    
    def test_check_permission_organization_mismatch(self, service):
        """Test check_permission returns False when organization doesn't match."""
        mock_obj = Mock()
        mock_obj.organization = OrganizationFactory()  # Different organization
        assert service.check_permission(mock_obj) is False
    
    def test_check_permission_trainer_match(self, service, trainer_user):
        """Test check_permission returns True when trainer matches."""
        mock_obj = Mock()
        mock_obj.trainer = trainer_user
        delattr(mock_obj, 'organization') if hasattr(mock_obj, 'organization') else None
        assert service.check_permission(mock_obj) is True
    
    def test_add_error(self, service):
        """Test add_error adds message to errors list."""
        service.add_error("Test error message")
        assert "Test error message" in service.errors
        assert service.has_errors
    
    def test_clear_errors(self, service):
        """Test clear_errors removes all errors."""
        service.add_error("Error 1")
        service.add_error("Error 2")
        assert len(service.errors) == 2
        
        service.clear_errors()
        assert len(service.errors) == 0
        assert not service.has_errors
    
    def test_errors_property_returns_copy(self, service):
        """Test errors property returns a copy of errors list."""
        service.add_error("Test error")
        errors = service.errors
        errors.append("Another error")
        
        # Original should not be modified
        assert len(service.errors) == 1
    
    def test_has_errors_property(self, service):
        """Test has_errors property."""
        assert not service.has_errors
        
        service.add_error("Error")
        assert service.has_errors
        
        service.clear_errors()
        assert not service.has_errors
    
    def test_get_errors_string(self, service):
        """Test get_errors_string joins errors."""
        service.add_error("Error 1")
        service.add_error("Error 2")
        service.add_error("Error 3")
        
        result = service.get_errors_string()
        assert result == "Error 1 Error 2 Error 3"
    
    @patch('apps.core.services.base.transaction.atomic')
    def test_save_with_audit_success(self, mock_atomic, service):
        """Test save_with_audit successful save."""
        mock_obj = Mock()
        mock_obj.full_clean.return_value = None
        mock_obj.save.return_value = None
        
        with patch.object(service, '_log_audit') as mock_log_audit:
            result = service.save_with_audit(mock_obj, action='update', metadata={'test': 'data'})
            
            assert result is True
            mock_obj.full_clean.assert_called_once()
            mock_obj.save.assert_called_once()
            mock_log_audit.assert_called_once_with(mock_obj, 'update', {'test': 'data'})
            assert not service.has_errors
    
    @patch('apps.core.services.base.transaction.atomic')
    def test_save_with_audit_validation_error(self, mock_atomic, service):
        """Test save_with_audit handles ValidationError."""
        mock_obj = Mock()
        error_dict = {'field1': ['Error 1'], 'field2': ['Error 2']}
        mock_obj.full_clean.side_effect = ValidationError(error_dict)
        
        result = service.save_with_audit(mock_obj)
        
        assert result is False
        assert service.has_errors
        assert any('field1' in error for error in service.errors)
        assert any('field2' in error for error in service.errors)
    
    @patch('apps.core.services.base.transaction.atomic')
    def test_save_with_audit_general_exception(self, mock_atomic, service):
        """Test save_with_audit handles general exceptions."""
        mock_obj = Mock()
        mock_obj.full_clean.side_effect = Exception("Database error")
        
        result = service.save_with_audit(mock_obj)
        
        assert result is False
        assert service.has_errors
        assert any("저장 중 오류가 발생했습니다" in error for error in service.errors)
    
    @patch('apps.trainers.audit.log_audit_action')
    def test_log_audit_success(self, mock_log_audit, service, trainer_user):
        """Test _log_audit successfully logs action."""
        mock_obj = Mock()
        mock_obj.__class__.__name__ = 'TestModel'
        mock_obj.pk = 123
        
        service._log_audit(mock_obj, 'create', {'test': 'metadata'})
        
        mock_log_audit.assert_called_once_with(
            user=trainer_user,
            action='create',
            model_name='TestModel',
            object_id=123,
            metadata={'test': 'metadata'}
        )
    
    def test_log_audit_import_error(self, service):
        """Test _log_audit handles ImportError gracefully."""
        mock_obj = Mock()
        
        with patch('builtins.__import__', side_effect=ImportError):
            # Should not raise exception
            service._log_audit(mock_obj, 'create')
    
    def test_validate_data_default(self, service):
        """Test validate_data default implementation returns True."""
        result = service.validate_data({'test': 'data'})
        assert result is True
    
    @patch('apps.core.services.base.transaction.atomic')
    def test_process_batch_success(self, mock_atomic, service):
        """Test process_batch processes items successfully."""
        items = [1, 2, 3, 4, 5]
        processed = []
        
        def processor(item):
            processed.append(item)
        
        successful, failed = service.process_batch(items, processor, batch_size=2)
        
        assert successful == 5
        assert failed == 0
        assert processed == items
    
    @patch('apps.core.services.base.transaction.atomic')
    def test_process_batch_with_failures(self, mock_atomic, service):
        """Test process_batch handles failures."""
        items = [1, 2, 3, 4, 5]
        processed = []
        
        def processor(item):
            if item == 3:
                raise Exception("Processing error")
            processed.append(item)
        
        successful, failed = service.process_batch(items, processor, batch_size=2)
        
        assert successful == 4
        assert failed == 1
        assert 3 not in processed
    
    def test_process_batch_respects_batch_size(self, service):
        """Test process_batch respects batch size parameter."""
        items = list(range(10))
        batch_sizes_used = []
        
        def processor(item):
            pass
        
        with patch('apps.core.services.base.transaction.atomic') as mock_atomic:
            # Track how many times atomic is called (one per batch)
            service.process_batch(items, processor, batch_size=3)
            
            # Should be called 4 times: 3+3+3+1
            assert mock_atomic.call_count == 4
    
    @pytest.mark.parametrize("action,expected", [
        ('view', True),
        ('edit', True),
        ('delete', True),
        ('custom', True),
    ])
    def test_check_permission_different_actions(self, service, organization, action, expected):
        """Test check_permission with different actions."""
        mock_obj = Mock()
        mock_obj.organization = organization
        
        result = service.check_permission(mock_obj, action=action)
        assert result == expected
    
    def test_edge_cases(self, service):
        """Test various edge cases."""
        # Empty errors string
        assert service.get_errors_string() == ""
        
        # Process empty batch
        successful, failed = service.process_batch([], lambda x: x)
        assert successful == 0
        assert failed == 0
        
        # Validate empty data
        assert service.validate_data({}) is True
        
        # Multiple error additions
        for i in range(100):
            service.add_error(f"Error {i}")
        assert len(service.errors) == 100