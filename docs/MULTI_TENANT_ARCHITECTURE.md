# Multi-Tenant Architecture Documentation

## Overview

The5HC implements a comprehensive multi-tenant architecture that allows multiple fitness training organizations to operate independently within the same application instance. Each organization has complete data isolation while sharing the same codebase and infrastructure.

## Architecture Components

### 1. Core Models

#### Organization Model
```python
class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User, related_name='owned_organizations')
    max_trainers = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
```

#### Trainer Model
```python
class Trainer(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)
    role = models.CharField(choices=[('owner', 'Owner'), ('admin', 'Admin'), ('trainer', 'Trainer')])
    invited_by = models.ForeignKey('self', null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
```

### 2. Data Isolation Strategy

#### Foreign Key Relationships
All data models that contain business data have been updated to reference the Trainer model instead of User:

- `Client.trainer` → ForeignKey to Trainer
- `Assessment.trainer` → ForeignKey to Trainer
- `SessionPackage.trainer` → ForeignKey to Trainer
- `Session.trainer` → ForeignKey to Trainer
- `Payment.trainer` → ForeignKey to Trainer

This ensures that all data is inherently tied to a specific organization through the trainer relationship.

#### Query Filtering
All views filter data by organization:

```python
# Example from client list view
clients = Client.objects.filter(
    trainer__organization=request.organization
).select_related('trainer')
```

### 3. Middleware Architecture

#### TrainerContextMiddleware
The `TrainerContextMiddleware` is the cornerstone of the multi-tenant system:

```python
class TrainerContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trainer = None
        request.organization = None
        
        if request.user.is_authenticated:
            # Get active trainer profile
            active_trainer_id = request.session.get('active_trainer_id')
            
            if active_trainer_id:
                trainer = Trainer.objects.select_related('organization').filter(
                    id=active_trainer_id,
                    user=request.user,
                    is_active=True
                ).first()
            else:
                # Get first active trainer profile
                trainer = Trainer.objects.select_related('organization').filter(
                    user=request.user,
                    is_active=True
                ).first()
            
            if trainer:
                request.trainer = trainer
                request.organization = trainer.organization
                request.session['active_trainer_id'] = trainer.id
        
        response = self.get_response(request)
        return response
```

Key features:
- Automatically sets `request.trainer` and `request.organization`
- Supports multiple trainer profiles per user
- Maintains active trainer in session
- Handles organization switching

### 4. Permission System

#### Decorators
The system uses decorators to enforce access control:

```python
@requires_trainer
def view_function(request):
    # Ensures user has an active trainer profile
    pass

@organization_member_required
def view_function(request):
    # Ensures user belongs to the organization
    pass

@organization_owner_required
def view_function(request):
    # Ensures user is the organization owner
    pass

@organization_role_required(['owner', 'admin'])
def view_function(request):
    # Ensures user has specific roles
    pass
```

#### Implementation Example
```python
@login_required
@requires_trainer
@organization_member_required
def client_detail_view(request, pk):
    # Get client ensuring organization match
    client = get_object_or_404(
        Client, 
        pk=pk, 
        trainer__organization=request.organization
    )
    # Process request...
```

### 5. Organization Switching

For users with multiple trainer profiles:

```python
def organization_switch_view(request):
    if request.method == 'POST':
        organization_id = request.POST.get('organization_id')
        
        # Verify user has access to this organization
        trainer = Trainer.objects.filter(
            user=request.user,
            organization_id=organization_id,
            is_active=True
        ).first()
        
        if trainer:
            request.session['active_trainer_id'] = trainer.id
            return redirect('dashboard')
```

### 6. Audit Logging

#### AuditLog Model
```python
class AuditLog(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Usage
```python
def log_client_action(action, client, request):
    AuditLog.objects.create(
        user=request.user,
        organization=request.organization,
        action=action,
        model_name='Client',
        object_id=str(client.pk),
        metadata={
            'client_name': client.name,
            'trainer_id': str(client.trainer.pk)
        },
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
```

### 7. Notification System

#### Notification Model
```python
class Notification(models.Model):
    user = models.ForeignKey(User)
    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

Notifications are user-specific but contain organization context in metadata.

## Security Considerations

### 1. Data Access Control
- All views must filter by organization
- Direct object access must verify organization ownership
- 404 errors returned for cross-organization access attempts

### 2. URL Security
- Object IDs in URLs don't expose organization structure
- Permission checks at view level, not URL level
- No organization identifiers in public URLs

### 3. Session Security
- Active trainer ID stored in session
- Session validated on each request
- Organization switching requires authentication

### 4. Query Security
```python
# Always filter by organization first
Model.objects.filter(trainer__organization=request.organization)

# Use get_object_or_404 with organization check
get_object_or_404(Model, pk=pk, trainer__organization=request.organization)
```

## Implementation Patterns

### 1. View Pattern
```python
@login_required
@requires_trainer
@organization_member_required
def view_name(request):
    # All queries filtered by organization
    queryset = Model.objects.filter(
        trainer__organization=request.organization
    )
    # Process view...
```

### 2. Form Pattern
```python
class ModelForm(forms.ModelForm):
    def __init__(self, *args, trainer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer:
            # Filter related fields by organization
            self.fields['related_field'].queryset = RelatedModel.objects.filter(
                trainer__organization=trainer.organization
            )
```

### 3. Admin Pattern
```python
class ModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by user's organizations
        return qs.filter(
            trainer__organization__in=request.user.trainer_profiles.values('organization')
        )
```

## Testing Considerations

### 1. Data Isolation Tests
```python
def test_complete_data_isolation_between_organizations(self, client):
    # Create two organizations
    org1 = OrganizationFactory()
    org2 = OrganizationFactory()
    
    # Create data in each
    client1 = ClientFactory(trainer__organization=org1)
    client2 = ClientFactory(trainer__organization=org2)
    
    # Login as org1 trainer
    client.force_login(org1.trainers.first().user)
    
    # Verify can only see org1 data
    response = client.get('/clients/')
    assert client1.name in response.content.decode()
    assert client2.name not in response.content.decode()
```

### 2. Permission Tests
```python
def test_organization_role_permissions(self, client):
    owner = TrainerFactory(role='owner')
    trainer = TrainerFactory(role='trainer', organization=owner.organization)
    
    # Test owner-only access
    client.force_login(trainer.user)
    response = client.get('/organization/settings/')
    assert response.status_code == 403
    
    client.force_login(owner.user)
    response = client.get('/organization/settings/')
    assert response.status_code == 200
```

## Migration Strategy

### From Single-Tenant to Multi-Tenant

1. **Create Organization**: Create default organization for existing data
2. **Create Trainer Profiles**: Convert User records to Trainer profiles
3. **Update Foreign Keys**: Change User FKs to Trainer FKs
4. **Add Middleware**: Enable TrainerContextMiddleware
5. **Update Views**: Add organization filtering to all views
6. **Test Data Isolation**: Verify complete separation

### Database Migration Example
```python
def migrate_to_multi_tenant(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Organization = apps.get_model('trainers', 'Organization')
    Trainer = apps.get_model('trainers', 'Trainer')
    Client = apps.get_model('clients', 'Client')
    
    # Create default organization
    default_org = Organization.objects.create(
        name='Default Organization',
        slug='default-org'
    )
    
    # Create trainer profiles for all users
    for user in User.objects.all():
        trainer = Trainer.objects.create(
            user=user,
            organization=default_org,
            role='owner' if user.is_superuser else 'trainer'
        )
        
        # Update related data
        Client.objects.filter(trainer_id=user.id).update(trainer_id=trainer.id)
```

## Best Practices

1. **Always Filter by Organization**: Never query without organization context
2. **Use Middleware**: Let middleware handle context setting
3. **Verify Permissions**: Use decorators consistently
4. **Handle Edge Cases**: Users with no/multiple profiles
5. **Log Actions**: Maintain audit trail for compliance
6. **Test Thoroughly**: Verify isolation in all scenarios
7. **Document Changes**: Keep architecture docs updated

## Common Pitfalls

1. **Forgetting Organization Filter**: Always include in queries
2. **Direct User References**: Use Trainer model instead
3. **Missing Permission Checks**: Apply decorators to all views
4. **Cross-Organization Leaks**: Test boundary conditions
5. **Session Management**: Handle organization switching properly

## Performance Considerations

1. **Index Foreign Keys**: Add database indexes on trainer_id fields
2. **Select Related**: Use select_related('trainer__organization')
3. **Prefetch Related**: Optimize queries for related data
4. **Cache Organization**: Store in request object via middleware
5. **Minimize Queries**: Filter at database level, not Python

## Conclusion

The multi-tenant architecture provides complete data isolation between organizations while maintaining a single codebase. The combination of foreign key relationships, middleware, decorators, and consistent patterns ensures secure and efficient operation for multiple organizations.