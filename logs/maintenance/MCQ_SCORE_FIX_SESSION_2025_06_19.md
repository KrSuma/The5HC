# MCQ Score Persistence and UI Consistency Fixes - Session 15

**Date**: 2025-06-19
**Author**: Claude
**Session**: MCQ Score Fix and Assessment Detail UI Consistency

## Summary

Fixed critical issues with MCQ score persistence and resolved UI inconsistency in assessment detail pages showing different views (radar chart vs bar chart).

## Issues Addressed

### 1. MCQ Scores Not Persisting
- **Problem**: After completing MCQ assessment, scores were calculated but not saved to database
- **Symptom**: Assessment detail page showed "아직 MCQ 평가를 진행하지 않았습니다" despite completing MCQ
- **Root Cause**: `assessment.save()` was missing after `calculate_scores()`

### 2. Category Name Mismatch
- **Problem**: MCQScoringEngine expected "knowledge", "lifestyle", "readiness" but actual categories were "Knowledge Assessment", "Lifestyle Assessment", etc.
- **Root Cause**: Hardcoded category names in scoring engine didn't match database values

### 3. Assessment Detail UI Inconsistency
- **Problem**: Same URL showed different views - radar chart ("능력치 차트") vs bar chart with injury risk assessment
- **Root Cause**: Two different templates served based on request type:
  - Full page load: `assessment_detail.html` (modern view)
  - HTMX navigation: `assessment_detail_partial.html` (outdated view)

### 4. Double Header/Footer Issue
- **Problem**: Assessment detail page showed duplicate headers and footers
- **Root Cause**: Full template with base.html was loaded into HTMX content area

## Changes Made

### 1. Fixed MCQ Score Persistence
**File**: `apps/assessments/views.py`
```python
# Added after line 478
assessment.save()  # Save the calculated MCQ scores to database
```

### 2. Fixed Category Name Handling
**File**: `apps/assessments/mcq_scoring_module/mcq_scoring.py`
```python
# Updated score retrieval to handle both formats
self.assessment.knowledge_score = scores.get('knowledge', scores.get('knowledge assessment', 0))
self.assessment.lifestyle_score = scores.get('lifestyle', scores.get('lifestyle assessment', 0))
self.assessment.readiness_score = scores.get('readiness', scores.get('readiness assessment', 0))
```

### 3. Unified Assessment Detail Templates
**File**: `apps/assessments/views.py`
- Removed use of outdated `assessment_detail_partial.html`
- Created `assessment_detail_content.html` for HTMX requests
- Updated view to serve appropriate template based on request type

### 4. Added Debug Logging
**File**: `apps/assessments/views.py`
```python
# Debug logging to troubleshoot score persistence
print(f"DEBUG - Total responses saved: {response_count}")
print(f"DEBUG - After save: knowledge_score={assessment.knowledge_score}, ...")
```

**File**: `apps/assessments/mcq_scoring_module/mcq_scoring.py`
```python
# Debug logging for category scores
print(f"DEBUG - MCQ Category scores: {scores}")
```

## Files Modified

1. `/apps/assessments/views.py` - Added save() call and debug logging
2. `/apps/assessments/mcq_scoring_module/mcq_scoring.py` - Fixed category name handling
3. `/templates/assessments/assessment_detail_content.html` - Created for HTMX navigation
4. `/templates/assessments/assessment_detail_partial.html.old` - Renamed to prevent use

## Testing Notes

1. MCQ scores now properly persist after completion
2. Assessment detail page shows consistent modern view regardless of navigation method
3. No more double headers/footers on assessment detail page
4. Debug output helps diagnose any remaining issues

## Navigation Instructions

To view assessment details:
1. Click "평가 관리" in navbar to see all assessments
2. Click "상세보기" on any assessment to view details
3. Or from client detail page, click "상세보기" next to assessments

## Status: COMPLETE

All reported issues have been resolved. MCQ scores persist correctly and the assessment detail page shows a consistent modern view with proper HTMX navigation.