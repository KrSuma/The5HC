"""
Base service class providing common functionality for all services.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
from django.db import models, transaction
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class providing common patterns for business logic.
    
    Services should inherit from this class and implement specific
    business logic methods.
    """
    
    # Model that this service primarily works with
    model: Optional[Type[models.Model]] = None
    
    def __init__(self, user: Optional[User] = None):
        """
        Initialize service with optional user context.
        
        Args:
            user: The user performing the action (for permissions/auditing)
        """
        self.user = user
        self._errors: List[str] = []
    
    @property
    def organization(self):
        """Get organization from user's trainer profile."""
        if self.user and hasattr(self.user, 'trainer_profile'):
            return self.user.trainer_profile.organization
        return None
    
    def get_queryset(self) -> QuerySet:
        """
        Get base queryset, optionally filtered by organization.
        
        Override this method to add default filters.
        """
        if not self.model:
            raise NotImplementedError("Service must define a model")
        
        queryset = self.model.objects.all()
        
        # Apply organization filter if available
        if self.organization and hasattr(self.model, 'organization'):
            queryset = queryset.filter(organization=self.organization)
        elif self.organization and hasattr(self.model, 'trainer'):
            # Filter by trainer's organization
            queryset = queryset.filter(trainer__organization=self.organization)
        
        return queryset
    
    def get_object(self, pk: Any) -> Optional[models.Model]:
        """
        Get a single object by primary key.
        
        Includes permission checking.
        """
        try:
            obj = self.get_queryset().get(pk=pk)
            if self.check_permission(obj):
                return obj
            else:
                self.add_error("권한이 없습니다.")
                return None
        except self.model.DoesNotExist:
            self.add_error("객체를 찾을 수 없습니다.")
            return None
    
    def check_permission(self, obj: models.Model, action: str = 'view') -> bool:
        """
        Check if user has permission to perform action on object.
        
        Override this method to implement custom permission logic.
        
        Args:
            obj: The object to check permissions for
            action: The action being performed (view, edit, delete)
        
        Returns:
            bool: True if permitted, False otherwise
        """
        # Default: check organization match
        if not self.user:
            return False
            
        # Superusers always have permission
        if self.user.is_superuser:
            return True
        
        # Check organization match
        if hasattr(obj, 'organization'):
            return obj.organization == self.organization
        elif hasattr(obj, 'trainer'):
            return obj.trainer == self.user or (
                hasattr(obj.trainer, 'trainer') and 
                obj.trainer.trainer.organization == self.organization
            )
        
        return True
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self._errors.append(message)
        logger.warning(f"Service error: {message}")
    
    def clear_errors(self) -> None:
        """Clear all error messages."""
        self._errors = []
    
    @property
    def errors(self) -> List[str]:
        """Get list of error messages."""
        return self._errors.copy()
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return bool(self._errors)
    
    def get_errors_string(self) -> str:
        """Get errors as a single string."""
        return " ".join(self._errors)
    
    @transaction.atomic
    def save_with_audit(self, obj: models.Model, action: str = 'update', 
                       metadata: Optional[Dict] = None) -> bool:
        """
        Save object with audit logging.
        
        Args:
            obj: Model instance to save
            action: Type of action (create, update, delete)
            metadata: Additional data to log
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            obj.full_clean()
            obj.save()
            
            # Log audit trail (if audit system exists)
            self._log_audit(obj, action, metadata)
            
            return True
        except ValidationError as e:
            for field, errors in e.error_dict.items():
                for error in errors:
                    self.add_error(f"{field}: {error}")
            return False
        except Exception as e:
            self.add_error(f"저장 중 오류가 발생했습니다: {str(e)}")
            logger.exception("Error saving object")
            return False
    
    def _log_audit(self, obj: models.Model, action: str, 
                   metadata: Optional[Dict] = None) -> None:
        """
        Log audit trail for the action.
        
        This is a placeholder for audit logging integration.
        """
        # Import here to avoid circular imports
        try:
            from apps.trainers.audit import log_audit_action
            
            log_audit_action(
                user=self.user,
                action=action,
                model_name=obj.__class__.__name__,
                object_id=obj.pk,
                metadata=metadata or {}
            )
        except ImportError:
            # Audit system not available
            pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate data before processing.
        
        Override this method to add custom validation logic.
        
        Args:
            data: Dictionary of data to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        return True
    
    def process_batch(self, items: List[Any], 
                     processor_func: callable,
                     batch_size: int = 100) -> Tuple[int, int]:
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            processor_func: Function to process each item
            batch_size: Number of items per batch
        
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            with transaction.atomic():
                for item in batch:
                    try:
                        processor_func(item)
                        successful += 1
                    except Exception as e:
                        failed += 1
                        logger.error(f"Batch processing error: {e}")
        
        return successful, failed