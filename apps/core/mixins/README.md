# The5HC Mixins

This directory contains reusable mixins for The5HC project, including both view mixins and model mixins. These mixins provide common functionality that can be easily combined to create feature-rich views and models with minimal code.

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

---

# Model Mixins

The5HC also provides a comprehensive set of model mixins for common patterns in Django models.

## Available Model Mixins

### 1. TimestampedModelMixin
Automatically tracks creation and modification times.

**Fields Added:**
- `created_at` - Auto-set on creation
- `updated_at` - Auto-updated on save

**Usage:**
```python
class Article(TimestampedModelMixin, models.Model):
    title = models.CharField(max_length=200)
```

### 2. OrganizationScopedModelMixin
Provides multi-tenant data isolation with custom managers.

**Fields Added:**
- `organization` - ForeignKey to Organization

**Managers:**
- `objects` - Filtered manager with organization methods
- `all_objects` - Unfiltered access

**Usage:**
```python
class Client(OrganizationScopedModelMixin, models.Model):
    name = models.CharField(max_length=100)

# Query examples
Client.objects.for_user(request.user)
Client.objects.for_organization(org)
```

### 3. AuditableModelMixin
Tracks who created and modified records.

**Fields Added:**
- `created_by` - User who created
- `modified_by` - User who last modified

**Usage:**
```python
class Document(AuditableModelMixin, models.Model):
    title = models.CharField(max_length=200)
```

### 4. SoftDeleteModelMixin
Implements soft deletion (marking as deleted instead of removing).

**Fields Added:**
- `is_deleted` - Boolean flag
- `deleted_at` - Deletion timestamp
- `deleted_by` - User who deleted

**Managers:**
- `objects` - Excludes deleted records
- `all_objects` - Includes deleted records

**Usage:**
```python
class Product(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=100)

# Soft delete
product.delete()  
# Restore
product.restore()
# Hard delete
product.delete(hard_delete=True)
```

### 5. SluggedModelMixin
Auto-generates URL-friendly slugs.

**Fields Added:**
- `slug` - Unique slug field

**Configuration:**
- Set `slug_source_field` on your model

**Usage:**
```python
class BlogPost(SluggedModelMixin, models.Model):
    title = models.CharField(max_length=200)
    slug_source_field = 'title'
```

### 6. StatusModelMixin
Provides status field with transition tracking.

**Fields Added:**
- `status` - Configurable choices
- `status_changed_at` - Change timestamp
- `status_changed_by` - User who changed

**Usage:**
```python
class Order(StatusModelMixin, models.Model):
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('approved', '승인됨'),
    ]
    
# Change status
order.change_status('approved', user=request.user)
```

### 7. OrderableModelMixin
Enables manual ordering with position management.

**Fields Added:**
- `position` - Integer for ordering

**Methods:**
- `move_up()`, `move_down()`, `move_to(position)`
- `get_previous()`, `get_next()`

**Usage:**
```python
class MenuItem(OrderableModelMixin, models.Model):
    name = models.CharField(max_length=100)
    
# Reorder items
MenuItem.reorder([id3, id1, id2])
```

### Composite Mixins

**FullAuditMixin**: Combines TimestampedModelMixin + AuditableModelMixin

**ScopedAuditMixin**: Combines OrganizationScopedModelMixin + FullAuditMixin

**DeletableAuditMixin**: Combines SoftDeleteModelMixin + FullAuditMixin

## Model Mixin Documentation

For comprehensive documentation on model mixins, see:
- `MODEL_MIXINS_USAGE.md` - Detailed usage guide
- `model_examples.py` - Example models using mixins
- `test_model_mixins.py` - Test cases showing all features

## Model Mixin Best Practices

1. **Mixin Order**: Place mixins before `models.Model`
2. **Field Conflicts**: Be aware of field name conflicts when combining mixins
3. **Migrations**: Always create migrations after adding mixins
4. **Admin Integration**: Update admin classes to show mixin fields
5. **Form Integration**: Handle mixin fields appropriately in forms
6. **Performance**: Consider indexes for frequently queried mixin fields