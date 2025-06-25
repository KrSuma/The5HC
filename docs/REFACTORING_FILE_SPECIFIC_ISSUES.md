# File-Specific Refactoring Issues

**Date**: 2025-06-25  
**Purpose**: Detailed list of files requiring refactoring with specific issues

## Critical Files (Highest Priority)

### 1. `apps/assessments/models.py` (1,495 lines)
**Issues**:
- Fat model anti-pattern
- 227-line calculate_scores() method
- 55+ fields in single model
- Business logic in model
- Auto-calculation in save() method

**Action**: Split into 4-5 smaller models, extract scoring to service

### 2. `apps/assessments/views.py` (837 lines)
**Issues**:
- Repeated HTMX response patterns
- Complex post() methods (100+ lines)
- Business logic in views
- Duplicate organization filtering

**Action**: Convert to CBVs with mixins, extract business logic

### 3. `apps/assessments/forms/assessment_forms.py` (500+ lines)
**Issues**:
- JavaScript mixed in widget definitions
- Repeated Alpine.js bindings
- Complex form initialization

**Action**: Create widget factory, separate JS from Python

### 4. `apps/api/views/assessments.py`
**Issues**:
- Function-based views with complex logic
- Manual permission checking
- Duplicate filtering code

**Action**: Convert to ViewSets with proper permissions

## High Priority Files

### 5. `apps/sessions/views.py`
**Issues**:
- Fee calculation logic in views
- Repeated HTMX patterns
- Complex form handling

**Action**: Extract PaymentService, use mixins

### 6. `apps/clients/views.py`
**Issues**:
- BMI calculation in views
- Duplicate queryset filtering
- Mixed concerns

**Action**: Create ClientService, use OrganizationFilterMixin

### 7. `templates/assessments/assessment_form.html`
**Issues**:
- 500+ lines of Alpine.js inline
- Complex component definition
- Business logic in template

**Action**: Extract to separate JS file

### 8. `templates/assessments/assessment_detail.html`
**Issues**:
- Duplicate Chart.js code
- Inline JavaScript
- Complex template logic

**Action**: Create reusable chart component

## Medium Priority Files

### 9. `apps/api/serializers/assessments.py`
**Issues**:
- Complex nested serializers
- Business logic in serializers
- Duplicate validation

**Action**: Simplify with SerializerMethodField

### 10. `apps/trainers/models.py`
**Issues**:
- Organization filtering repeated
- Missing model managers
- No query optimization

**Action**: Add custom managers with common queries

### 11. `apps/accounts/views.py`
**Issues**:
- Rate limiting logic in view
- Session management complexity
- No class-based views

**Action**: Extract RateLimitMixin, convert to CBVs

### 12. `the5hc/settings/__init__.py`
**Issues**:
- Redundant with settings.py
- Confusing import structure

**Action**: Remove redundancy, clarify imports

## Template Files Needing Attention

### 13. `templates/base.html`
**Issues**:
- Global Alpine.js components
- Inline JavaScript
- No component structure

**Action**: Create proper component architecture

### 14. `templates/dashboard/dashboard.html`
**Issues**:
- Complex statistics calculations
- Duplicate query logic
- Performance issues

**Action**: Pre-calculate in view, add caching

### 15. Multiple `*_content.html` files
**Issues**:
- Inconsistent HTMX patterns
- No clear template inheritance
- Duplicate code blocks

**Action**: Create base HTMX templates

## Test Files Issues

### 16. `apps/assessments/tests.py` + `test_*.py`
**Issues**:
- Mixed file structure
- Some tests in root, some in tests/
- Inconsistent naming

**Action**: Move all to tests/ subdirectory

### 17. `apps/api/tests/` directory
**Issues**:
- Incomplete test coverage
- No service layer tests
- Missing integration tests

**Action**: Add comprehensive test suite

## Configuration Files

### 18. `requirements.txt`
**Issues**:
- No version pinning for some packages
- Development dependencies mixed in
- No requirements-dev.txt

**Action**: Split into base and dev requirements

### 19. `.gitignore`
**Issues**:
- Not ignoring __pycache__
- Missing common IDE files
- Incomplete Python ignores

**Action**: Update with comprehensive Python gitignore

## JavaScript/Static Files

### 20. `static/js/assessments/`
**Issues**:
- No modular structure
- Inline in templates instead
- No build process

**Action**: Create proper JS modules

## Specific Code Smells by Category

### Long Methods (>50 lines)
1. `Assessment.calculate_scores()` - 227 lines
2. `AssessmentCreateView.post()` - 95 lines
3. `SessionPackageCreateView.form_valid()` - 73 lines
4. `ClientService.export_to_csv()` - 68 lines

### Duplicate Code Blocks
1. HTMX response handling - 20+ occurrences
2. Organization filtering - 15+ occurrences
3. Permission checking - 10+ occurrences
4. Fee calculations - 5+ occurrences

### Complex Conditionals
1. `Assessment.calculate_scores()` - Nested if/elif chains
2. `AssessmentForm.clean()` - Multiple validation rules
3. Template files - Complex {% if %} blocks

### Magic Numbers
1. VAT rate (0.1) - Hardcoded in multiple places
2. Card fee (0.035) - Repeated in views
3. Score thresholds - Scattered in models

### Missing Abstractions
1. No base model class for common fields
2. No base form class for common widgets
3. No base serializer for common patterns
4. No base view class for HTMX handling

## Database Performance Issues

### Missing Indexes
```python
# apps/assessments/models.py
# Needs: Index on (client, date)
# Needs: Index on (trainer, created_at)

# apps/sessions/models.py  
# Needs: Index on (package, date)
# Needs: Index on (client, is_completed)
```

### N+1 Query Problems
1. Assessment list view - Client data
2. Session list view - Package data
3. Dashboard view - Multiple aggregations
4. API list endpoints - Related data

## Security Concerns

### 1. SQL Construction
- Some raw SQL without parameterization
- String formatting in queries

### 2. Permission Gaps
- Some views missing permission checks
- Inconsistent organization filtering

### 3. Input Validation
- File upload validation incomplete
- API input sanitization missing

## File Cleanup Needed

### Delete These Files
1. `apps/api/serializers_original.py`
2. `apps/api/views_original.py`
3. `the5hc/settings.py` (redundant)
4. Old migration files (squash migrations)

### Archive These Logs
1. 60+ log files in logs/
2. Old phase completion logs
3. Duplicate documentation

## Quick Win Files (Easy Fixes)

1. **Add to .gitignore**: __pycache__, *.pyc
2. **Update requirements.txt**: Pin versions
3. **Fix imports**: Remove unused imports (30+ files)
4. **Add docstrings**: Missing in 50+ methods
5. **Remove commented code**: Found in 20+ files

## Estimation by File

| File | Priority | Effort | Risk |
|------|----------|--------|------|
| assessments/models.py | Critical | 2 days | High |
| assessments/views.py | Critical | 1 day | Medium |
| assessments/forms.py | High | 1 day | Low |
| api/views/*.py | High | 2 days | Medium |
| Template files | Medium | 2 days | Low |
| Test files | Low | 1 day | Low |

Total Estimated Effort: 10-15 days for complete refactoring