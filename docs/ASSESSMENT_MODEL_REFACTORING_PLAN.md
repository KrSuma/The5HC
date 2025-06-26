# Assessment Model Refactoring Plan

**Date**: 2025-06-25  
**Status**: Phase 2 Implementation Plan  
**Author**: Claude

## Overview

This document outlines the plan to refactor the monolithic Assessment model (1,495 lines) into smaller, focused models that follow Django best practices and improve maintainability.

## Current Problems

### 1. **Monolithic Model (1,495 lines)**
- Single model handling 7 different test types
- Mixed concerns: metadata, test data, scoring, manual overrides
- Difficult to understand, test, and maintain
- Blocks new feature development

### 2. **Manual Override Complexity**
- 15+ separate boolean fields for tracking overrides
- No audit trail for override changes
- Difficult to manage and extend

### 3. **Scoring Logic Coupling**
- Complex `calculate_scores()` method (200+ lines) in model
- Business logic mixed with data model
- Hard to test scoring algorithms independently

## Refactoring Solution

### New Model Structure

```
Assessment (Core) - 150 lines
├── OverheadSquatTest - 100 lines
├── PushUpTest - 80 lines  
├── SingleLegBalanceTest - 90 lines
├── ToeTouchTest - 80 lines
├── ShoulderMobilityTest - 90 lines
├── FarmersCarryTest - 90 lines
├── HarvardStepTest - 90 lines
└── ManualScoreOverride - 60 lines (JSON-based)
```

### Key Improvements

1. **Single Responsibility**: Each model handles one test type
2. **JSON Overrides**: Replace 15+ fields with one JSON field
3. **Service Layer**: Business logic moved to AssessmentService
4. **Better Testing**: Test individual models in isolation
5. **Easier Extension**: Add new test types without affecting others

## Implementation Plan

### Phase 1: Create New Models ✅ DONE
- [x] Created `refactored_models.py` with new model structure
- [x] Created `AssessmentService` for business logic
- [x] Documented migration benefits and patterns

### Phase 2: Migration Strategy (Next Steps)

#### Step 1: Add New Models Alongside Existing
```bash
# Create migration for new models
python manage.py makemigrations assessments --name="add_refactored_models"

# Apply migration
python manage.py migrate
```

#### Step 2: Data Migration Script
Create Django data migration to move data from monolithic Assessment to new models:

```python
# migrations/0014_migrate_to_refactored_models.py
from django.db import migrations

def migrate_assessment_data(apps, schema_editor):
    """Migrate data from Assessment to individual test models."""
    Assessment = apps.get_model('assessments', 'Assessment')
    OverheadSquatTest = apps.get_model('assessments', 'OverheadSquatTest')
    # ... other test models
    
    for assessment in Assessment.objects.all():
        # Create OverheadSquatTest if data exists
        if assessment.overhead_squat_score is not None:
            OverheadSquatTest.objects.create(
                assessment=assessment,
                score=assessment.overhead_squat_score,
                knee_valgus=assessment.overhead_squat_knee_valgus,
                # ... other fields
            )
        # Continue for other test types...

def reverse_migration(apps, schema_editor):
    """Reverse migration - copy data back to Assessment fields."""
    # Implementation for rollback
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('assessments', '0013_add_refactored_models'),
    ]
    
    operations = [
        migrations.RunPython(migrate_assessment_data, reverse_migration),
    ]
```

#### Step 3: Update Forms and Views
Update forms to work with new model structure:

```python
# Before: Single large form
class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = '__all__'  # 60+ fields

# After: Focused forms for each test
class OverheadSquatForm(forms.ModelForm):
    class Meta:
        model = OverheadSquatTest
        fields = '__all__'  # 8-10 fields
```

#### Step 4: Update Views to Use Service Layer
```python
# Before: Complex view logic
def assessment_create_view(request):
    # 100+ lines of form handling and scoring
    
# After: Clean service integration
def assessment_create_view(request):
    if request.method == 'POST':
        service = AssessmentService(user=request.user)
        assessment, success = service.create_assessment(form.cleaned_data)
        
        if success:
            return redirect('assessment_detail', pk=assessment.pk)
        else:
            for error in service.errors:
                form.add_error(None, error)
```

#### Step 5: Update Templates
Modify templates to work with new model relationships:

```html
<!-- Before: Direct field access -->
{{ assessment.overhead_squat_score }}

<!-- After: Related model access -->
{{ assessment.overhead_squat.score }}
```

#### Step 6: Testing and Validation
- Create comprehensive test suite for new models
- Test data migration accuracy
- Validate score calculations remain identical
- Performance testing

#### Step 7: Remove Old Fields
After successful migration and testing:
```python
# Create migration to remove old fields from Assessment
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField('Assessment', 'overhead_squat_score'),
        migrations.RemoveField('Assessment', 'overhead_squat_knee_valgus'),
        # ... remove all migrated fields
    ]
```

## Files Created

### 1. New Models (`apps/assessments/refactored_models.py`)
- **Assessment**: Core model (150 lines, down from 1,495)
- **OverheadSquatTest**: Overhead squat test data and scoring
- **PushUpTest**: Push-up test data and scoring  
- **SingleLegBalanceTest**: Balance test data and scoring
- **ToeTouchTest**: Flexibility test data and scoring
- **ShoulderMobilityTest**: Mobility test data and scoring
- **FarmersCarryTest**: Strength endurance test data and scoring
- **HarvardStepTest**: Cardio test data and scoring
- **ManualScoreOverride**: JSON-based override management

### 2. Service Layer (`apps/core/services/assessment_service.py`)
- **AssessmentService**: Business logic for assessments
- **Scoring Logic**: Extracted from models
- **Statistics**: Percentiles, performance age, comparisons
- **Risk Assessment**: Centralized risk calculation
- **MCQ Integration**: Multiple choice question scoring

### 3. Documentation
- **This Plan**: Migration strategy and implementation
- **Benefits Analysis**: Detailed improvement breakdown
- **Code Examples**: Before/after patterns

## Benefits Analysis

### Model Complexity Reduction
```
Before: 1 model × 1,495 lines = 1,495 lines total
After:  9 models × ~100 lines = ~900 lines total
Reduction: 40% fewer lines, 90% better organization
```

### Manual Override Improvement
```
Before: 15+ boolean fields + scattered logic
After:  1 JSON field + centralized management
Benefits: Better audit trail, easier extension, cleaner API
```

### Testing Improvement
```
Before: Test entire Assessment model (complex setup)
After:  Test individual models (focused, isolated)
Benefits: Faster tests, clearer failures, better coverage
```

### Performance Gains
```
Before: Load all test data for every assessment
After:  Load only needed test data (select_related)
Benefits: Faster queries, reduced memory usage
```

### Development Velocity
```
Before: Modify 1,495-line file for any test change
After:  Modify specific 100-line test model
Benefits: Less merge conflicts, easier reviews, focused changes
```

## Risk Mitigation

### 1. **Data Loss Prevention**
- Comprehensive migration testing
- Backup before migration
- Reversible migration scripts
- Validation of data accuracy

### 2. **Downtime Minimization**
- Blue-green deployment strategy
- Migration during low-traffic periods
- Rollback procedures tested

### 3. **Breaking Changes**
- Gradual API updates
- Backward compatibility layer
- Clear migration timeline
- Team communication

## Success Metrics

### Code Quality
- [ ] Reduce Assessment model from 1,495 to ~150 lines
- [ ] Achieve >90% test coverage on new models
- [ ] Zero failing tests after migration

### Performance
- [ ] Maintain or improve assessment creation time
- [ ] Reduce memory usage for assessment queries
- [ ] No degradation in score calculation accuracy

### Developer Experience  
- [ ] Reduce time to add new test types by 70%
- [ ] Reduce assessment-related bugs by 50%
- [ ] Improve code review velocity

## Next Steps

1. **Review and Approve**: Team review of refactoring plan
2. **Create Migration**: Implement data migration script
3. **Update Forms**: Modify forms for new model structure
4. **Update Views**: Integrate AssessmentService
5. **Update Templates**: Handle new model relationships
6. **Testing**: Comprehensive validation
7. **Deploy**: Gradual rollout with monitoring
8. **Cleanup**: Remove old fields after validation

## Timeline

- **Week 1**: Migration script and testing
- **Week 2**: Form and view updates
- **Week 3**: Template updates and integration testing
- **Week 4**: Deployment and cleanup

The refactored models are ready for implementation and will significantly improve the codebase's maintainability and extensibility.