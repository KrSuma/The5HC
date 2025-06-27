# The5HC Refactoring Action Plan

**Date**: 2025-06-25  
**Purpose**: Step-by-step implementation guide for safe refactoring

## Quick Wins (Can be done immediately with minimal risk)

### 1. Clean Up Compiled Files (5 minutes)
```bash
# Add to .gitignore
__pycache__/
*.pyc
*.pyo
*.pyd

# Clean existing files
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 2. Standardize Test Structure (1 hour)
```bash
# Move all tests to consistent structure
apps/assessments/tests/
├── __init__.py
├── test_models.py
├── test_views.py
├── test_forms.py
├── test_api.py
└── test_services.py
```

### 3. Remove Redundant Files (30 minutes)
- Delete `the5hc/settings.py` (use settings/ directory only)
- Clean up `apps/api/serializers_original.py` and `views_original.py`
- Consolidate duplicate log files

## Phase 1: Foundation (Low Risk)

### Week 1 - Service Layer Implementation

#### Day 1: Create Base Infrastructure
```python
# apps/core/services/__init__.py
# apps/core/services/base.py
# apps/core/views/mixins.py
# apps/core/models/mixins.py
```

#### Day 2-3: Implement Service Classes
Start with least complex apps:
1. `ClientService` - Simple CRUD operations
2. `PaymentService` - Fee calculations
3. `ReportService` - Already partially exists

#### Day 4-5: Add Tests for Services
- Unit tests for each service method
- No changes to existing functionality yet

### Implementation Example:
```python
# apps/clients/services.py
class ClientService:
    def get_client_with_stats(self, client_id: int) -> dict:
        """New method that doesn't change existing code"""
        client = Client.objects.get(id=client_id)
        return {
            'client': client,
            'stats': self._calculate_stats(client)
        }
```

## Phase 2: Gradual Migration (Medium Risk)

### Week 2 - Move Business Logic

#### Day 1-2: Extract Model Methods
```python
# Start with Assessment.calculate_scores()
# 1. Copy method to AssessmentService
# 2. Update model method to call service
# 3. Test thoroughly
# 4. Eventually remove from model

class Assessment(models.Model):
    def calculate_scores(self):
        """Temporary: calls service"""
        from apps.assessments.services import AssessmentService
        service = AssessmentService()
        return service.calculate_scores(self)
```

#### Day 3-4: Implement Mixins
```python
# Add mixins without changing existing views
class AssessmentListView(OrganizationFilterMixin, HTMXResponseMixin, View):
    # Existing view code remains
```

#### Day 5: Update Templates Gradually
- Create reusable components
- Update one template at a time
- Test HTMX functionality

## Phase 3: Optimization (Higher Risk)

### Week 3 - Performance and Structure

#### Day 1-2: Add Database Indexes
```python
# Create migration for indexes
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='assessment',
            index=models.Index(fields=['client', '-date'], name='idx_client_date'),
        ),
    ]
```

#### Day 3: Implement Caching
```python
# Start with read-only data
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### Day 4-5: Query Optimization
- Add select_related() and prefetch_related()
- Use Django Debug Toolbar to identify slow queries

## Safety Checklist for Each Change

### Before Starting:
- [ ] Create feature branch
- [ ] Run full test suite
- [ ] Document current behavior

### During Implementation:
- [ ] Write tests for new code first
- [ ] Keep old code working
- [ ] Add deprecation warnings
- [ ] Update documentation

### Before Merging:
- [ ] All tests passing
- [ ] Manual testing completed
- [ ] Code review done
- [ ] Performance benchmarked

## Rollback Plan

### For Each Phase:
1. **Service Layer**: Simply don't use new services
2. **Model Changes**: Keep old methods temporarily
3. **View Changes**: Use feature flags
4. **Database Changes**: Migrations are reversible

### Feature Flag Example:
```python
# settings.py
FEATURE_FLAGS = {
    'use_assessment_service': False,
    'use_htmx_mixins': False,
    'enable_caching': False,
}

# In code
if settings.FEATURE_FLAGS.get('use_assessment_service'):
    service = AssessmentService()
    scores = service.calculate_scores(assessment)
else:
    scores = assessment.calculate_scores()  # Old way
```

## Monitoring During Refactoring

### Key Metrics to Track:
1. **Response Times**: Should improve or stay same
2. **Error Rates**: Should not increase
3. **Test Coverage**: Should increase
4. **Code Complexity**: Should decrease

### Tools:
```python
# Add to requirements.txt
django-debug-toolbar==4.2.0
django-silk==5.0.3  # Performance profiling
coverage==7.3.2
pylint==3.0.2
```

## Risk Matrix

| Change | Risk | Impact | Effort |
|--------|------|--------|--------|
| Clean compiled files | Low | Low | 5 min |
| Create services | Low | High | 2 days |
| Move business logic | Medium | High | 3 days |
| Split models | High | High | 2 days |
| Add caching | Medium | Medium | 1 day |
| Query optimization | Low | High | 1 day |

## Communication Plan

### For Development Team:
1. Daily standup on refactoring progress
2. Document decisions in ADRs (Architecture Decision Records)
3. Update team on breaking changes

### For Stakeholders:
1. No user-facing changes
2. Performance improvements expected
3. Easier feature development afterward

## Success Criteria

### Quantitative:
- [ ] 90%+ test coverage
- [ ] 30% reduction in response times
- [ ] 50% reduction in code duplication
- [ ] Zero functionality regressions

### Qualitative:
- [ ] Easier to onboard new developers
- [ ] Clearer code organization
- [ ] Better separation of concerns
- [ ] Improved maintainability

## Next Steps

1. **Immediate** (Today):
   - Clean up compiled files
   - Fix test structure
   - Create service layer directory

2. **This Week**:
   - Implement first service (ClientService)
   - Add HTMXResponseMixin
   - Start moving simple business logic

3. **Next Sprint**:
   - Continue service implementation
   - Begin model refactoring
   - Add performance monitoring

## Important Notes

- **No Big Bang**: All changes are incremental
- **Always Backward Compatible**: Old code keeps working
- **Test First**: Write tests before refactoring
- **Measure Impact**: Track metrics throughout
- **Document Everything**: Future developers will thank you

Remember: The goal is better code, not different functionality. If users notice any changes, we've failed.