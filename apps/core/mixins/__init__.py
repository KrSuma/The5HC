"""
Core mixins for The5HC project.

This module provides reusable mixins for views and models to handle common 
functionality like HTMX responses, organization filtering, permissions, 
timestamps, soft deletion, and more.
"""

# View mixins
from .view_mixins import (
    HtmxResponseMixin,
    OrganizationFilterMixin,
    PermissionRequiredMixin,
    PaginationMixin,
    SearchMixin,
    AuditLogMixin,
)

# Model mixins
from .model_mixins import (
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

__all__ = [
    # View mixins
    'HtmxResponseMixin',
    'OrganizationFilterMixin',
    'PermissionRequiredMixin',
    'PaginationMixin',
    'SearchMixin',
    'AuditLogMixin',
    # Model mixins
    'TimestampedModelMixin',
    'OrganizationScopedModelMixin',
    'AuditableModelMixin',
    'SoftDeleteModelMixin',
    'SluggedModelMixin',
    'StatusModelMixin',
    'OrderableModelMixin',
    'FullAuditMixin',
    'ScopedAuditMixin',
    'DeletableAuditMixin',
]