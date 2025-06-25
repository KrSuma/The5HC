# Delete Button HTMX Attributes Display Fix

**Date**: 2025-06-25
**Author**: Claude
**Issue**: Assessment Detail Delete Button Display

## Problem

The delete button in the assessment detail page was displaying HTMX attributes as text:
- Text appeared: `hx-delete="/assessments/18/...` to the left of the trash icon
- The HTMX attributes were placed outside the button tag

## Root Cause

In `/templates/assessments/assessment_detail_content.html`, the HTMX attributes were incorrectly placed after the closing `>` of the button tag:

```html
<!-- Before (incorrect) -->
<button class="...">
        hx-delete="{% url 'assessments:delete' assessment.pk %}"
        hx-confirm="정말로 이 평가를 삭제하시겠습니까?"
        hx-target="#main-content">
    ...
</button>
```

## Solution

Moved the HTMX attributes inside the button tag's opening element:

```html
<!-- After (correct) -->
<button class="..."
        hx-delete="{% url 'assessments:delete' assessment.pk %}"
        hx-confirm="정말로 이 평가를 삭제하시겠습니까?"
        hx-target="#main-content">
    ...
</button>
```

## Files Modified

- `/templates/assessments/assessment_detail_content.html` - Fixed button syntax

## Testing

- Visual inspection confirms HTMX attributes no longer display as text
- Delete functionality remains intact with confirmation dialog
- HTMX navigation continues to work properly

## Impact

- Minor UI fix with no functional changes
- Improves professional appearance of the application
- No database or backend changes required