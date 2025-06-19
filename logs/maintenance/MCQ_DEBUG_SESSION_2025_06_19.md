# MCQ System Debug Session - 2025-06-19

**Date**: 2025-06-19
**Author**: Claude
**Session**: MCQ Debug and Cleanup

## Summary

Fixed critical issues with the MCQ (종합 건강 평가) system that was "hard broken". The issues were caused by multiple layers of technical debt including JavaScript conflicts, database integrity issues, and UI problems.

## Issues Identified and Fixed

### 1. JavaScript/Alpine.js Conflicts
- **Problem**: Complex JavaScript attempting to fix navbar navigation was breaking Alpine.js initialization
- **Solution**: Reverted problematic uncommitted changes using `git stash`
- **Files affected**: 
  - `templates/base.html`
  - `templates/assessments/mcq_assessment.html`
  - `static/js/mcq-assessment-fixed.js`
  - `static/js/app.js`

### 2. UNIQUE Constraint Failed Error (Critical)
- **Problem**: QuestionResponse model's save() method was performing double-saves
  ```python
  # Problematic code:
  if not self.pk:
      super().save()  # Save 1
  self.calculate_points()
  super().save()      # Save 2 - UNIQUE constraint error!
  ```
- **Root Cause**: Second save attempted to INSERT with existing ID instead of UPDATE
- **Solution**: 
  - Modified save() method to prevent double saves
  - Added M2M signal handler for points calculation
  - Updated `mcq_save_view` to use `get_or_create()` pattern
- **Files modified**:
  - `apps/assessments/models.py` (QuestionResponse.save() method)
  - `apps/assessments/views.py` (mcq_save_view function)

### 3. Test Data Cleanup
- **Problem**: Placeholder categories "카테고리 0" and "카테고리 1" in database
- **Solution**: Removed test categories and associated data
- **Data deleted**:
  - 2 categories
  - 1 question
  - 1 response

### 4. UI/UX Improvements
- **Problem**: Scale questions had poor visual hierarchy and non-updating value displays
- **Solution**: 
  - Enhanced scale question styling with distinct background
  - Added JavaScript to update scale values dynamically
  - Improved label prominence and help text display
- **Files modified**:
  - `static/css/mcq-styles.css`
  - `templates/assessments/components/mcq_question.html`
  - `templates/assessments/mcq_assessment_simple.html`

## Technical Details

### Database Fix Script
Created and executed a script to fix SQLite sequence issues:
- Reset autoincrement sequence for assessments_questionresponse
- Verified data integrity

### Signal Handler Implementation
```python
@receiver(m2m_changed, sender=QuestionResponse.selected_choices.through)
def update_question_response_points(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.calculate_points()
        QuestionResponse.objects.filter(pk=instance.pk).update(
            points_earned=instance.points_earned
        )
```

## Results
- ✅ MCQ assessment page now loads correctly
- ✅ Responses save without UNIQUE constraint errors
- ✅ Scale values update dynamically
- ✅ Clean UI without test data
- ✅ Simplified template working reliably

## Lessons Learned
1. Over-engineering JavaScript to fix simple problems creates complexity
2. Database model save() methods need careful testing with M2M relationships
3. Test data cleanup is important for production systems
4. Simpler solutions (like the simplified template) are often more reliable

## Next Steps
- Monitor for any recurring issues
- Consider fully migrating to simplified template if Alpine.js issues persist
- Add integration tests for MCQ save functionality