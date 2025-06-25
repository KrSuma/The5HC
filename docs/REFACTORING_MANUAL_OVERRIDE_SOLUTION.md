# Manual Override System Refactoring

**Date**: 2025-06-25  
**Purpose**: Sustainable solution for manual score override system

## Current Problem

The Assessment model has 15+ separate fields for manual overrides:
```python
# Current approach - unsustainable
push_up_manual_score = models.IntegerField(null=True, blank=True)
plank_manual_score = models.IntegerField(null=True, blank=True)
single_leg_balance_left_manual_score = models.IntegerField(null=True, blank=True)
single_leg_balance_right_manual_score = models.IntegerField(null=True, blank=True)
# ... 11 more fields
```

**Issues**:
- Adding new tests requires database migrations
- Clutters the model with repetitive fields
- Difficult to query and maintain
- Makes forms unnecessarily complex

## Proposed Solution

### Option 1: JSON Field Approach (Recommended)

```python
# apps/assessments/models/overrides.py
class AssessmentOverride(models.Model):
    """Single model to handle all manual overrides"""
    assessment = models.OneToOneField(
        'Assessment', 
        on_delete=models.CASCADE,
        related_name='overrides'
    )
    
    # Store all overrides in structured JSON
    manual_scores = models.JSONField(default=dict, blank=True)
    override_reasons = models.JSONField(default=dict, blank=True)
    
    # Metadata
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    
    def set_override(self, test_name: str, score: int, reason: str = None):
        """Set a manual override for a test"""
        self.manual_scores[test_name] = score
        if reason:
            self.override_reasons[test_name] = reason
        self.save()
    
    def get_override(self, test_name: str) -> Optional[int]:
        """Get manual override for a test"""
        return self.manual_scores.get(test_name)
    
    def clear_override(self, test_name: str):
        """Remove manual override for a test"""
        self.manual_scores.pop(test_name, None)
        self.override_reasons.pop(test_name, None)
        self.save()
    
    def has_override(self, test_name: str) -> bool:
        """Check if test has manual override"""
        return test_name in self.manual_scores
    
    @property
    def override_count(self) -> int:
        """Count of manual overrides"""
        return len(self.manual_scores)
```

### Option 2: EAV Pattern (Entity-Attribute-Value)

```python
# apps/assessments/models/overrides.py
class ManualScoreOverride(models.Model):
    """Individual override records - more flexible but more complex"""
    assessment = models.ForeignKey(
        'Assessment',
        on_delete=models.CASCADE,
        related_name='manual_overrides'
    )
    
    test_name = models.CharField(max_length=50, db_index=True)
    manual_score = models.IntegerField()
    original_score = models.FloatField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['assessment', 'test_name']
        indexes = [
            models.Index(fields=['assessment', 'test_name']),
        ]
```

## Implementation Strategy

### Phase 1: Create New Structure

```python
# Migration to create new model and migrate data
from django.db import migrations

def migrate_manual_overrides(apps, schema_editor):
    Assessment = apps.get_model('assessments', 'Assessment')
    AssessmentOverride = apps.get_model('assessments', 'AssessmentOverride')
    
    override_fields = [
        'push_up_manual_score',
        'plank_manual_score',
        'single_leg_balance_left_manual_score',
        'single_leg_balance_right_manual_score',
        'farmers_carry_manual_score',
        'overhead_squat_manual_score',
        'toe_touch_manual_score',
        'shoulder_mobility_left_manual_score',
        'shoulder_mobility_right_manual_score',
        'harvard_step_test_manual_score',
        'push_up_test_manual_score',
        'toe_touch_test_manual_score',
        'shoulder_mobility_test_manual_score',
        'overhead_squat_compensation_manual_score',
        'mcq_manual_score',
    ]
    
    for assessment in Assessment.objects.all():
        manual_scores = {}
        
        for field in override_fields:
            value = getattr(assessment, field)
            if value is not None:
                # Convert field name to test name
                test_name = field.replace('_manual_score', '')
                manual_scores[test_name] = value
        
        if manual_scores:
            AssessmentOverride.objects.create(
                assessment=assessment,
                manual_scores=manual_scores
            )

class Migration(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='AssessmentOverride',
            fields=[...],
        ),
        migrations.RunPython(migrate_manual_overrides),
    ]
```

### Phase 2: Update Service Layer

```python
# apps/assessments/services/scoring.py
class AssessmentScoringService:
    """Enhanced scoring service with override support"""
    
    def calculate_scores(self, assessment: Assessment) -> Dict[str, float]:
        """Calculate all scores with manual override support"""
        scores = {}
        overrides = getattr(assessment, 'overrides', None)
        
        # Calculate each test score
        for test_name in self.get_test_names():
            # Check for manual override first
            if overrides and overrides.has_override(test_name):
                scores[test_name] = overrides.get_override(test_name)
            else:
                # Calculate automatically
                scores[test_name] = self._calculate_test_score(assessment, test_name)
        
        return scores
    
    def set_manual_score(self, assessment: Assessment, test_name: str, score: int, user: User, reason: str = None):
        """Set a manual override with audit trail"""
        override, created = AssessmentOverride.objects.get_or_create(
            assessment=assessment
        )
        
        # Store original calculated score if first override
        if not override.has_override(test_name):
            original = self._calculate_test_score(assessment, test_name)
            if reason is None:
                reason = f"Original calculated score: {original}"
        
        override.last_modified_by = user
        override.set_override(test_name, score, reason)
        
        # Log the change
        self._log_override_change(assessment, test_name, score, user, reason)
        
        # Recalculate dependent scores
        self._update_category_scores(assessment)
```

### Phase 3: Update Forms and UI

```python
# apps/assessments/forms/widgets.py
class ManualOverrideWidget(forms.Select):
    """Custom widget for manual score override"""
    
    template_name = 'widgets/manual_override_select.html'
    
    def __init__(self, test_name, *args, **kwargs):
        self.test_name = test_name
        super().__init__(*args, **kwargs)
        
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['test_name'] = self.test_name
        context['widget']['has_override'] = value is not None
        return context

# apps/assessments/forms/assessment_forms.py
class AssessmentManualOverrideForm(forms.Form):
    """Dynamic form for manual overrides"""
    
    def __init__(self, *args, assessment=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get current overrides
        overrides = {}
        if assessment and hasattr(assessment, 'overrides'):
            overrides = assessment.overrides.manual_scores
        
        # Create fields dynamically
        for test_name in AssessmentScoringService.get_test_names():
            field_name = f'{test_name}_override'
            self.fields[field_name] = forms.ChoiceField(
                required=False,
                choices=[('', '자동 계산')] + [(i, i) for i in range(6)],
                widget=ManualOverrideWidget(test_name),
                initial=overrides.get(test_name, '')
            )
```

### Phase 4: Update Templates

```django
{# templates/assessments/components/manual_override_field.html #}
<div class="manual-override-field" 
     x-data="{ 
         hasOverride: {{ override.has_override|yesno:'true,false' }},
         score: '{{ override.score|default:'' }}'
     }">
    
    <select name="{{ field_name }}"
            x-model="score"
            @change="hasOverride = (score !== '')"
            class="form-select"
            :class="{ 'ring-2 ring-blue-500': hasOverride }">
        <option value="">자동 계산</option>
        {% for i in "012345"|make_list %}
            <option value="{{ i }}">{{ i }}</option>
        {% endfor %}
    </select>
    
    <button type="button"
            x-show="hasOverride"
            @click="score = ''; hasOverride = false"
            class="ml-2 text-sm text-red-600 hover:text-red-800">
        초기화
    </button>
    
    <span x-show="hasOverride" class="ml-2 text-xs text-blue-600">
        수동 입력됨
    </span>
</div>
```

## Benefits of New Approach

### 1. **Scalability**
- Add new tests without migrations
- No model bloat
- Easy to extend

### 2. **Maintainability**
- Single source of truth for overrides
- Clean separation of concerns
- Easier to test

### 3. **Auditability**
- Track who made changes
- Store reasons for overrides
- Full history available

### 4. **Performance**
- Single query for all overrides
- JSON field indexed in PostgreSQL
- Efficient storage

### 5. **Flexibility**
- Easy to add metadata
- Can store additional context
- Simple to query

## Migration Plan

### Step 1: Parallel Running (Week 1)
1. Create new models/structure
2. Update service to check both old and new
3. Start logging to new structure
4. No user-facing changes

### Step 2: UI Migration (Week 2)
1. Update forms to use new structure
2. Migrate existing data
3. Test thoroughly
4. Deploy with feature flag

### Step 3: Cleanup (Week 3)
1. Remove old fields from models
2. Update all references
3. Clean up forms
4. Final testing

### Step 4: Optimization
1. Add database indexes
2. Implement caching
3. Add analytics

## Code Examples

### Using the New System

```python
# Setting a manual override
service = AssessmentScoringService()
service.set_manual_score(
    assessment=assessment,
    test_name='push_up',
    score=4,
    user=request.user,
    reason='Client performed modified push-ups'
)

# Checking for overrides
if assessment.overrides.has_override('push_up'):
    score = assessment.overrides.get_override('push_up')
    reason = assessment.overrides.override_reasons.get('push_up')

# Bulk operations
overrides_data = {
    'push_up': 4,
    'plank': 3,
    'squat': 5
}
assessment.overrides.manual_scores = overrides_data
assessment.overrides.save()

# Querying assessments with overrides
Assessment.objects.filter(
    overrides__manual_scores__has_key='push_up'
).select_related('overrides')
```

### API Integration

```python
# apps/api/views/assessments.py
class AssessmentOverrideViewSet(viewsets.ModelViewSet):
    """API endpoint for managing overrides"""
    
    @action(detail=True, methods=['post'])
    def set_override(self, request, pk=None):
        assessment = self.get_object()
        test_name = request.data.get('test_name')
        score = request.data.get('score')
        reason = request.data.get('reason', '')
        
        service = AssessmentScoringService()
        service.set_manual_score(
            assessment, test_name, score, request.user, reason
        )
        
        return Response({'status': 'success'})
```

## Testing Strategy

```python
# tests/test_manual_overrides.py
class TestManualOverrides:
    def test_override_persistence(self):
        assessment = AssessmentFactory()
        
        # Set override
        assessment.overrides.set_override('push_up', 4, 'Test reason')
        
        # Verify persistence
        assessment.refresh_from_db()
        assert assessment.overrides.get_override('push_up') == 4
        assert assessment.overrides.override_reasons['push_up'] == 'Test reason'
    
    def test_scoring_with_override(self):
        assessment = AssessmentFactory(push_up_count=10)
        service = AssessmentScoringService()
        
        # Calculate without override
        scores = service.calculate_scores(assessment)
        original_score = scores['push_up']
        
        # Set override
        assessment.overrides.set_override('push_up', 5)
        
        # Recalculate with override
        scores = service.calculate_scores(assessment)
        assert scores['push_up'] == 5
        assert scores['push_up'] != original_score
```

This solution provides a clean, scalable approach to manual overrides that will grow with the application.