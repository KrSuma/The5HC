# Assessment Form Default Score Fix

**Date**: 2025-06-25
**Issue**: Assessment form score dropdowns defaulting to values before user input
**Reporter**: User reported that 점수 (score) sections showing "3" by default

## Problem Analysis

The issue was caused by default values being set in the Django form initialization for manual score fields:

1. **Root Cause**: In `AssessmentForm.__init__` method, default values were being set:
   - `overhead_squat_score`: defaulted to 2
   - `shoulder_mobility_score`: defaulted to 3

2. **Impact**: These defaults were:
   - Rendered in the HTML select elements
   - Picked up by Alpine.js `initializeScoresFromForm()` method
   - Incorrectly marked as "manually overridden" values
   - Confusing for users who expected empty fields

## Solution Implemented

### 1. Removed Default Values from Form

**File**: `/apps/assessments/forms/assessment_forms.py`

Commented out the default values for manual score fields:
```python
defaults = {
    # 'overhead_squat_score': 2,  # Removed - manual input field
    'push_up_reps': 10,
    'push_up_score': 3,
    # ... other fields ...
    # 'shoulder_mobility_score': 3,  # Removed - manual input field
}
```

### 2. Updated Alpine.js Initialization Logic

**File**: `/templates/assessments/assessment_form.html`

Enhanced the form initialization to:
- Check for empty values more carefully
- Only mark fields as manually overridden for edit forms (not new assessments)
- Use Django template logic to detect if it's an edit form

```javascript
// Only mark as manually overridden if it's an edit form (has assessment ID)
if ({{ 'true' if form.instance.pk else 'false' }}) {
    this.manualOverrides.overheadSquat = true;
}
```

## Testing Required

1. **New Assessment Form**:
   - Overhead Squat 점수 dropdown should show "선택" (no default)
   - Shoulder Mobility 점수 dropdown should show "선택" (no default)
   - Manual override indicators should NOT appear until user selects a value

2. **Edit Assessment Form**:
   - Existing scores should be loaded and displayed
   - Manual override indicators should appear for fields with saved values
   - Changes should still trigger manual override behavior

3. **Score Calculations**:
   - Automatic calculations should still work when movement compensations are checked
   - Manual overrides should prevent automatic calculation overwrites

## Files Modified

1. `/apps/assessments/forms/assessment_forms.py` - Removed default values for manual score fields
2. `/templates/assessments/assessment_form.html` - Updated Alpine.js initialization logic

## Related Issues

- This fix relates to the manual score override feature implemented earlier today
- Ensures better user experience by starting with truly empty fields
- Prevents confusion about whether scores are pre-calculated or user-entered