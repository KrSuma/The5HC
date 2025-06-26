# The5HC View Mixins

This directory contains reusable view mixins for The5HC project. These mixins provide common functionality that can be easily combined to create feature-rich views with minimal code.

## Available Mixins

### 1. HtmxResponseMixin
Handles HTMX requests and responses, automatically selecting the appropriate template based on whether the request is from HTMX.

**Features:**
- Detects HTMX requests via headers
- Automatically uses content-only templates for HTMX
- Provides helper methods for HTMX-specific data

**Usage:**
```python
class MyView(HtmxResponseMixin, TemplateView):
    template_name = 'myapp/page.html'
    htmx_template_name = 'myapp/page_content.html'
```

### 2. OrganizationFilterMixin
Filters querysets by organization based on the current user's trainer profile. Essential for multi-tenant data isolation.

**Features:**
- Automatic queryset filtering by organization
- Supports related field filtering
- Superuser override capability
- Empty queryset for users without organization

**Usage:**
```python
class ClientListView(OrganizationFilterMixin, ListView):
    model = Client
    organization_field = 'trainer__organization'
    allow_superuser_access = True
```

### 3. PermissionRequiredMixin
Enhanced permission checking with support for multiple permissions and custom logic.

**Features:**
- Single or multiple permission requirements
- 'all' or 'any' permission modes
- Custom permission logic via `has_permission()` method
- Korean error messages

**Usage:**
```python
class MyView(PermissionRequiredMixin, View):
    permission_required = ['app.view_model', 'app.change_model']
    permission_mode = 'any'
    permission_denied_message = '권한이 없습니다.'
```

### 4. PaginationMixin
Provides consistent pagination across list views with customizable page sizes.

**Features:**
- Configurable page size with query parameter override
- Maximum page size enforcement
- Orphan handling
- Pagination context variables

**Usage:**
```python
class MyListView(PaginationMixin, ListView):
    paginate_by = 20
    max_paginate_by = 100
    page_query_param = 'page'
```

### 5. SearchMixin
Adds search functionality to list views with support for multiple fields and related field searches.

**Features:**
- Search across multiple fields
- Related field search support
- Case-insensitive search by default
- Search query preprocessing

**Usage:**
```python
class ClientListView(SearchMixin, ListView):
    model = Client
    search_fields = ['name', 'email', 'trainer__name']
    search_query_param = 'q'
```

### 6. AuditLogMixin
Automatically logs view actions for audit trails and compliance.

**Features:**
- Automatic action logging
- IP address tracking
- Custom log messages
- Optional database logging
- Only logs successful actions

**Usage:**
```python
class ClientUpdateView(AuditLogMixin, UpdateView):
    audit_action = 'update'
    audit_message_template = 'Updated client {object} by {user}'
```

## Combining Mixins

Mixins can be combined to create feature-rich views. The order matters - generally follow this pattern:

```python
class MyView(
    LoginRequiredMixin,              # Django's auth mixin
    PermissionRequiredMixin,         # Permission checking
    OrganizationFilterMixin,         # Organization filtering
    SearchMixin,                     # Search functionality
    PaginationMixin,                 # Pagination
    AuditLogMixin,                   # Audit logging
    HtmxResponseMixin,               # HTMX support
    ListView                         # Base view class
):
    # View configuration
    pass
```

## Real-World Examples

See `examples.py` for comprehensive examples of how to use these mixins in real views, including:

- Client list with all features
- Assessment creation with audit logging
- Advanced search with related fields
- Custom permission logic
- HTMX-specific response handling

## Testing

All mixins have comprehensive test coverage in `apps.core.tests.test_view_mixins.py`. Run tests with:

```bash
pytest apps/core/tests/test_view_mixins.py -v
```

## Best Practices

1. **Mixin Order**: Place mixins that might affect the queryset (like `OrganizationFilterMixin`) before those that use it (like `SearchMixin`)

2. **Permission Checks**: Always include `LoginRequiredMixin` and appropriate permission mixins for secure views

3. **Organization Filtering**: Use `OrganizationFilterMixin` for all views that display organization-specific data

4. **HTMX Templates**: Always provide both regular and HTMX templates when using `HtmxResponseMixin`

5. **Audit Logging**: Use `AuditLogMixin` for any views that modify data

6. **Search Fields**: Be careful with related field searches as they can impact performance

## Performance Considerations

- **Select Related**: Always use `select_related()` and `prefetch_related()` in `get_queryset()` to avoid N+1 queries
- **Search Performance**: Index frequently searched fields
- **Pagination**: Set reasonable default page sizes and maximum limits
- **Organization Filtering**: Ensure foreign key indexes exist for organization relationships