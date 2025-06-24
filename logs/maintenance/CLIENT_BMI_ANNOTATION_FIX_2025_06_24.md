# Client BMI Annotation Conflict Fix

**Date**: 2025-06-24
**Author**: Claude
**Session**: 17 - Client Filtering Implementation

## Issue

When accessing the client list page (`/clients/`), the following error occurred:

```
AttributeError at /clients/
property 'bmi' of 'Client' object has no setter
```

## Root Cause

The Client model has a `@property` decorator for `bmi` that calculates BMI from height and weight:

```python
@property
def bmi(self):
    """Calculate Body Mass Index (BMI)."""
    if self.height and self.weight:
        return self.weight / ((self.height / 100) ** 2)
    return None
```

When we tried to use `annotate(bmi=...)` in the views to add database-level BMI calculations for filtering, Django attempted to set this value on the read-only property, causing the AttributeError.

## Solution

Changed all BMI annotations from `bmi` to `calculated_bmi` to avoid the naming conflict:

### Files Modified

1. **apps/clients/views.py** - `client_list_view` function:
   - Line 36: Changed annotation name from `bmi` to `calculated_bmi`
   - Lines 94-100: Updated all BMI filter references to use `calculated_bmi`

2. **apps/clients/views.py** - `client_export_view` function:
   - Line 360: Changed annotation name from `bmi` to `calculated_bmi`
   - Lines 413-419: Updated all BMI filter references to use `calculated_bmi`

### Code Changes

```python
# Before (causing error):
clients = clients.annotate(
    bmi=ExpressionWrapper(
        F('weight') / (F('height') * F('height') / 10000),
        output_field=FloatField()
    )
)

# After (fixed):
clients = clients.annotate(
    calculated_bmi=ExpressionWrapper(
        F('weight') / (F('height') * F('height') / 10000),
        output_field=FloatField()
    )
)
```

## Important Notes

1. **Template Usage**: Templates correctly use `client.bmi` which refers to the model property, not the annotation. No template changes were needed.

2. **CSV Export**: The CSV export correctly uses `client.bmi` to access the model property for display purposes.

3. **Filtering**: Database filtering now uses `calculated_bmi` for efficient queryset filtering while preserving the original `bmi` property for display.

4. **Assessment Views**: The assessment views also use BMI annotations but don't have this conflict because they annotate the Assessment model, not the Client model.

## Verification

After the fix:
- Client list page loads without errors
- BMI filtering works correctly
- BMI displays properly in the list using the model property
- CSV export includes correct BMI values

## Status

✅ FIXED - The AttributeError has been resolved by using a different annotation name that doesn't conflict with the existing model property.