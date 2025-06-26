# Model Mixins Usage Guide

This guide explains how to use the model mixins provided by The5HC project. These mixins implement common patterns and behaviors that can be reused across different Django models.

## Table of Contents

1. [TimestampedModelMixin](#timestampedmodelmixin)
2. [OrganizationScopedModelMixin](#organizationscopedmodelmixin)
3. [AuditableModelMixin](#auditablemodelmixin)
4. [SoftDeleteModelMixin](#softdeletemodelmixin)
5. [SluggedModelMixin](#sluggedmodelmixin)
6. [StatusModelMixin](#statusmodelmixin)
7. [OrderableModelMixin](#orderablemodelmixin)
8. [Composite Mixins](#composite-mixins)
9. [Best Practices](#best-practices)

## TimestampedModelMixin

Automatically tracks when records are created and last modified.

### Usage

```python
from apps.core.mixins.model_mixins import TimestampedModelMixin

class Article(TimestampedModelMixin, models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
```

### Features

- `created_at`: Automatically set when record is created
- `updated_at`: Automatically updated on every save
- Indexes created for both fields for efficient querying

### Example

```python
# Creating a record
article = Article.objects.create(title="Hello", content="World")
print(article.created_at)  # 2025-01-25 10:30:00
print(article.updated_at)  # 2025-01-25 10:30:00

# Updating a record
article.title = "Updated"
article.save()
print(article.updated_at)  # 2025-01-25 10:31:00 (changed)
print(article.created_at)  # 2025-01-25 10:30:00 (unchanged)
```

## OrganizationScopedModelMixin

Provides multi-tenant data isolation by organization.

### Usage

```python
from apps.core.mixins.model_mixins import OrganizationScopedModelMixin

class Client(OrganizationScopedModelMixin, models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
```

### Features

- Automatic organization field
- Custom managers for filtering by organization
- Security methods to check access permissions

### Example

```python
# Filter by organization
org_clients = Client.objects.for_organization(organization)

# Filter by user's organization
user_clients = Client.objects.for_user(request.user)

# Check if user can access a record
client = Client.objects.get(pk=1)
if client.is_accessible_by(request.user):
    # User can access this client
    pass

# Unfiltered access (for admin)
all_clients = Client.all_objects.all()
```

## AuditableModelMixin

Tracks who created and last modified each record.

### Usage

```python
from apps.core.mixins.model_mixins import AuditableModelMixin

class Document(AuditableModelMixin, models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
```

### Features

- `created_by`: User who created the record
- `modified_by`: User who last modified the record
- Automatic tracking with user parameter

### Example

```python
# In a view
def create_document(request):
    document = Document(title="Important Doc")
    document.created_by = request.user
    document.modified_by = request.user
    document.save()
    
    # Or use the user parameter
    document = Document(title="Another Doc")
    document.save(user=request.user)
```

## SoftDeleteModelMixin

Implements soft deletion - records are marked as deleted but not removed from database.

### Usage

```python
from apps.core.mixins.model_mixins import SoftDeleteModelMixin

class Product(SoftDeleteModelMixin, models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### Features

- Soft delete by default
- Option for hard delete
- Restore capability
- Filtered managers

### Example

```python
# Soft delete a product
product = Product.objects.get(pk=1)
product.delete()  # Marks as deleted, still in database

# Delete with user tracking
product.delete(user=request.user)

# Query active products (excludes deleted)
active_products = Product.objects.all()

# Include deleted products
all_products = Product.all_objects.all()

# Query only deleted products
deleted_products = Product.objects.deleted_only()

# Restore a deleted product
deleted_product = Product.all_objects.get(pk=1)
deleted_product.restore()

# Hard delete (permanent)
product.delete(hard_delete=True)
```

## SluggedModelMixin

Auto-generates URL-friendly slugs from a source field.

### Usage

```python
from apps.core.mixins.model_mixins import SluggedModelMixin

class BlogPost(SluggedModelMixin, models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Specify which field to generate slug from
    slug_source_field = 'title'
```

### Features

- Automatic slug generation
- Handles uniqueness
- Unicode support (Korean text)
- UUID fallback for non-sluggable text

### Example

```python
# Automatic slug generation
post = BlogPost.objects.create(
    title="My First Blog Post",
    content="Content here"
)
print(post.slug)  # "my-first-blog-post"

# Handles duplicates
post2 = BlogPost.objects.create(
    title="My First Blog Post",
    content="Different content"
)
print(post2.slug)  # "my-first-blog-post-1"

# Korean text (falls back to UUID if not sluggable)
post3 = BlogPost.objects.create(
    title="안녕하세요",
    content="Korean content"
)
print(post3.slug)  # UUID-based slug like "a1b2c3d4"
```

## StatusModelMixin

Provides standardized status tracking with transition management.

### Usage

```python
from apps.core.mixins.model_mixins import StatusModelMixin

class Order(StatusModelMixin, models.Model):
    # Define custom status choices
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('processing', '처리중'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
    ]
    
    order_number = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=10, decimal_places=2)
```

### Features

- Configurable status choices
- Status change tracking
- Validation of status transitions
- User tracking for status changes

### Example

```python
# Create with default status
order = Order.objects.create(
    order_number="ORD-001",
    total=50000
)
print(order.status)  # 'pending'

# Change status
order.change_status('processing', user=request.user)
print(order.status)  # 'processing'
print(order.status_changed_by)  # User who changed it

# Check if transition is allowed
if order.can_change_status_to('completed'):
    order.change_status('completed')

# Invalid status raises ValidationError
try:
    order.change_status('invalid_status')
except ValidationError as e:
    print(e)  # Status transition error
```

### Custom Transition Rules

```python
class Order(StatusModelMixin, models.Model):
    # ... fields ...
    
    def can_change_status_to(self, new_status):
        """Custom transition rules."""
        if self.status == 'cancelled':
            # Cannot change from cancelled
            return False
        
        if self.status == 'completed' and new_status != 'cancelled':
            # Can only cancel completed orders
            return False
            
        return super().can_change_status_to(new_status)
```

## OrderableModelMixin

Enables manual ordering of records with position management.

### Usage

```python
from apps.core.mixins.model_mixins import OrderableModelMixin

class MenuItem(OrderableModelMixin, models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['category', 'position']
```

### Features

- Automatic position assignment
- Move up/down functionality
- Reordering support
- Navigation between items

### Example

```python
# Create items with auto-positioning
item1 = MenuItem.objects.create(name="Pizza", category=cat)     # position: 1
item2 = MenuItem.objects.create(name="Pasta", category=cat)     # position: 2
item3 = MenuItem.objects.create(name="Salad", category=cat)     # position: 3

# Move item up/down
item3.move_up()    # Salad now position 2, Pasta position 3
item1.move_down()  # Pizza now position 2, Salad position 1

# Move to specific position
item3.move_to(3)   # Back to position 3

# Get adjacent items
prev_item = item2.get_previous()
next_item = item2.get_next()

# Reorder multiple items
MenuItem.reorder([item3.pk, item1.pk, item2.pk])
# Now: Salad(0), Pizza(1), Pasta(2)
```

## Composite Mixins

Pre-built combinations of commonly used mixins.

### FullAuditMixin

Combines `TimestampedModelMixin` and `AuditableModelMixin`.

```python
from apps.core.mixins.model_mixins import FullAuditMixin

class Contract(FullAuditMixin, models.Model):
    title = models.CharField(max_length=200)
    # Has: created_at, updated_at, created_by, modified_by
```

### ScopedAuditMixin

Combines `OrganizationScopedModelMixin` and `FullAuditMixin`.

```python
from apps.core.mixins.model_mixins import ScopedAuditMixin

class Project(ScopedAuditMixin, models.Model):
    name = models.CharField(max_length=100)
    # Has: organization, created_at, updated_at, created_by, modified_by
```

### DeletableAuditMixin

Combines `SoftDeleteModelMixin` and `FullAuditMixin`.

```python
from apps.core.mixins.model_mixins import DeletableAuditMixin

class Task(DeletableAuditMixin, models.Model):
    title = models.CharField(max_length=200)
    # Has: is_deleted, deleted_at, deleted_by, created_at, updated_at, created_by, modified_by
```

## Best Practices

### 1. Mixin Order

When using multiple mixins, order matters. Place mixins before models.Model:

```python
# Correct
class MyModel(Mixin1, Mixin2, models.Model):
    pass

# Incorrect
class MyModel(models.Model, Mixin1, Mixin2):
    pass
```

### 2. Combining Mixins

Choose mixins that complement each other:

```python
class Document(
    OrganizationScopedModelMixin,  # Multi-tenant
    SoftDeleteModelMixin,          # Soft delete
    TimestampedModelMixin,         # Timestamps
    AuditableModelMixin,           # User tracking
    models.Model
):
    title = models.CharField(max_length=200)
    content = models.TextField()
```

### 3. Database Migrations

Remember to create and run migrations after adding mixins:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Admin Configuration

Configure admin to show mixin fields:

```python
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'created_by', 'created_at', 'is_deleted']
    list_filter = ['organization', 'is_deleted', 'status']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'modified_by']
    
    def get_queryset(self, request):
        # Include soft-deleted records in admin
        return self.model.all_objects.all()
```

### 5. Form Integration

Update forms to handle mixin fields:

```python
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        exclude = ['created_by', 'modified_by', 'organization']
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if not instance.pk:
            instance.created_by = user
        instance.modified_by = user
        if hasattr(user, 'trainer_profile'):
            instance.organization = user.trainer_profile.organization
        if commit:
            instance.save()
        return instance
```

### 6. Testing

Test mixin functionality in your models:

```python
@pytest.mark.django_db
def test_document_soft_delete():
    doc = Document.objects.create(title="Test")
    doc.delete()
    
    # Not in default queryset
    assert not Document.objects.filter(pk=doc.pk).exists()
    
    # But still in database
    assert Document.all_objects.filter(pk=doc.pk).exists()
```

### 7. Performance Considerations

- Use select_related/prefetch_related for foreign keys in mixins
- Consider adding indexes for frequently queried mixin fields
- Be aware of the additional database columns added by mixins

```python
# Efficient querying with organization mixin
documents = Document.objects.select_related(
    'organization',
    'created_by',
    'modified_by'
).for_user(request.user)
```

## Common Patterns

### Multi-tenant Model

```python
class TenantModel(
    OrganizationScopedModelMixin,
    TimestampedModelMixin,
    models.Model
):
    """Base for all tenant-scoped models."""
    class Meta:
        abstract = True
```

### Audited Content Model

```python
class ContentModel(
    SoftDeleteModelMixin,
    TimestampedModelMixin,
    AuditableModelMixin,
    models.Model
):
    """Base for all content that needs audit trail."""
    class Meta:
        abstract = True
```

### Publishable Model

```python
class PublishableModel(
    StatusModelMixin,
    SluggedModelMixin,
    TimestampedModelMixin,
    models.Model
):
    """Base for publishable content."""
    STATUS_CHOICES = [
        ('draft', '임시저장'),
        ('published', '게시됨'),
        ('archived', '보관됨'),
    ]
    
    class Meta:
        abstract = True
```