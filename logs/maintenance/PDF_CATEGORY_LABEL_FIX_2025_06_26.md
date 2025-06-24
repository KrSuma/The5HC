# PDF Report Category Label Fix

**Date**: 2025-06-26
**Author**: Claude
**Issue**: PDF output format broken - 카테고리별 점수 graph showing incorrect label

## Summary

Fixed the PDF report template to display the correct category label "기동성" (mobility) instead of "유연성" (flexibility) in the category scores graph. This aligns with the category reorganization completed in Session 18.

## Problem

The user reported that the PDF output format had a broken "카테고리별 점수" (category scores) graph. Investigation revealed that the template was still using the old terminology "유연성" (flexibility) instead of the updated "기동성" (mobility).

## Changes Made

### 1. Updated Category Label in Score Display
**File**: `/templates/reports/assessment_report.html`
- Line 461: Changed "유연성" to "기동성" in the category scores section
- This ensures the PDF displays the correct label in the progress bar chart

### 2. Updated Suggestion Title
**File**: `/templates/reports/assessment_report.html`
- Line 577: Changed "유연성 개선" to "기동성 개선" in the suggestions section
- This maintains consistency throughout the PDF report

## Technical Details

The issue was a result of incomplete updates from the Session 18 category reorganization. While the assessment forms and display templates were updated, the PDF report template was missed.

The report service (`/apps/reports/services.py`) was already correctly passing `mobility_score` and `mobility_pct` data, so only the template labels needed updating.

## Testing Verification

After these changes:
1. The PDF report will correctly display "기동성" in the category scores graph
2. The suggestions section will show "기동성 개선" for mobility-related recommendations
3. All data continues to flow correctly from the assessment to the PDF

## Notes

- No backend changes were required
- The service layer was already using the correct field names
- This was purely a display label issue in the PDF template
- The fix maintains consistency with the category reorganization from Session 18