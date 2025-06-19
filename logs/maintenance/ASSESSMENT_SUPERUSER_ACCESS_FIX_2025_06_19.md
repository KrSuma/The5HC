# Assessment Superuser Access Fix - Session 16 (Continued)

**Date**: 2025-06-19
**Author**: Claude
**Session**: Assessment View Access for Admin Users

## Summary

Fixed issue where admin (superuser) users without a trainer profile could not access assessment views through "평가관리 > 상세보기" link. Updated decorators and views to allow superusers to view all assessments without requiring a trainer profile.

## Issue Reported

User reported: "평가관리 > 상세보기 link is still not working" - similar issue to the trainer views, but for assessments.

## Root Cause

1. **Decorator Requirements**: The `@requires_trainer` and `@organization_member_required` decorators were blocking superuser access
2. **Organization Filtering**: Views were filtering by `request.organization` which doesn't exist for superusers
3. **Trainer Assignment**: Assessment creation was trying to use `request.trainer` which doesn't exist for superusers

## Changes Made

### 1. Updated Decorators to Allow Superusers
**File**: `apps/trainers/decorators.py`

Updated both `requires_trainer` and `organization_member_required` decorators:

```python
def requires_trainer(view_func):
    """
    Decorator to ensure user has a trainer profile.
    Allows superusers to bypass this requirement.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Allow superusers to bypass trainer requirement
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # ... rest of the logic

def organization_member_required(view_func):
    """
    Decorator to ensure user belongs to an organization.
    Allows superusers to bypass this requirement.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Allow superusers to bypass organization requirement
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # ... rest of the logic
```

### 2. Updated Assessment List View
**File**: `apps/assessments/views.py`

```python
# For superusers, show all assessments
if request.user.is_superuser:
    assessments = Assessment.objects.all().select_related('client', 'trainer')
else:
    # Filter assessments by organization
    assessments = Assessment.objects.filter(
        trainer__organization=request.organization
    ).select_related('client', 'trainer')
```

### 3. Updated Assessment Detail View
**File**: `apps/assessments/views.py`

```python
# For superusers, allow viewing any assessment
if request.user.is_superuser:
    assessment = get_object_or_404(
        Assessment.objects.select_related('client', 'trainer'),
        pk=pk
    )
else:
    # Ensure assessment belongs to the same organization
    assessment = get_object_or_404(
        Assessment.objects.select_related('client', 'trainer'),
        pk=pk,
        trainer__organization=request.organization
    )
```

### 4. Updated Assessment Add View
**File**: `apps/assessments/views.py`

Fixed client access and trainer assignment for superusers:

```python
# For superusers, allow accessing any client
if request.user.is_superuser:
    client = get_object_or_404(Client, pk=client_id)
else:
    # Ensure client belongs to the same organization
    client = get_object_or_404(
        Client, 
        pk=client_id, 
        trainer__organization=request.organization
    )

# For trainer assignment
if request.user.is_superuser and not hasattr(request, 'trainer'):
    # Use the client's trainer
    assessment.trainer = assessment.client.trainer
else:
    assessment.trainer = request.trainer
```

### 5. Updated Assessment Delete View
**File**: `apps/assessments/views.py`

```python
# For superusers, allow deleting any assessment
if request.user.is_superuser:
    assessment = get_object_or_404(Assessment, pk=pk)
else:
    # Ensure assessment belongs to the same organization
    assessment = get_object_or_404(
        Assessment, 
        pk=pk, 
        trainer__organization=request.organization
    )
```

## Result

Admin users (superusers) can now:
- View the assessment list showing all assessments from all organizations
- Click the "상세보기" (view details) link to see assessment details
- Add new assessments for any client
- Delete any assessment
- Access all assessment-related pages without having a trainer profile

## Files Modified

1. `/apps/trainers/decorators.py` - Updated decorators to allow superuser bypass
2. `/apps/assessments/views.py` - Updated multiple views for superuser access:
   - `assessment_list_view`
   - `assessment_detail_view`
   - `assessment_add_view`
   - `assessment_delete_view`

## Notes

- The decorators now universally allow superusers to bypass trainer/organization requirements
- This maintains security for regular users while providing appropriate access for admins
- When superusers create assessments, the system uses the client's trainer for the assessment