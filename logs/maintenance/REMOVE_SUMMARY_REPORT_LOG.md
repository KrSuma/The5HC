# Remove Summary Report Type Log

**Date**: 2025-06-15
**Author**: Claude
**Task**: Remove summary report type and simplify to only detailed reports

## Summary

Removed the summary report type option from the PDF report generation system. The system now only generates detailed reports, eliminating the need for users to choose between report types.

## Changes Made

### 1. View Simplification
**File**: `apps/reports/views.py`
- Modified `generate_report` to skip the report selection page
- Now directly generates a detailed report when accessed
- Removed the intermediate form/template rendering

### 2. Model Update
**File**: `apps/reports/models.py`
- Removed `('summary', '요약 보고서')` from `REPORT_TYPES` choices
- Now only has `('detailed', '상세 보고서')` option

### 3. Template Cleanup
**File**: `templates/reports/assessment_report.html`
- Removed all conditional `{% if is_summary %}` blocks
- Removed report type from the header title
- All reports now show full content:
  - Detailed test results table
  - Complete improvement suggestions
  - Full training program

### 4. Service Cleanup
**File**: `apps/reports/services.py`
- Removed `report_type` and `is_summary` from template context
- Report always generates as detailed type

### 5. Migration Created
**File**: `apps/reports/migrations/0003_remove_summary_report_type.py`
- Added data migration to convert any existing summary reports to detailed
- Updated model field choices

### 6. Template Date Field Fixes
**File**: `templates/reports/generate_report.html`
- Fixed `assessment_date` references to use `date` field
- (Though this template is no longer used due to direct generation)

## User Experience Changes

### Before:
1. User clicks "PDF 리포트" on assessment detail page
2. Goes to report generation page
3. Selects report type from dropdown (요약/상세)
4. Clicks "보고서 생성"
5. Report downloads

### After:
1. User clicks "PDF 리포트" on assessment detail page
2. Report generates immediately and downloads

## Migration Instructions

Run the migration to update the database:
```bash
python manage.py migrate reports
```

This will:
- Convert any existing summary reports to detailed type
- Update the model field to remove the summary option

## Testing Instructions

1. Navigate to an assessment detail page
2. Click "PDF 리포트" button
3. Report should generate immediately without showing a selection page
4. Downloaded report should contain all detailed information
5. Check that the PDF layout is correct with proper margins

## Benefits

1. **Simplified UX**: One less step for users
2. **Reduced Confusion**: No need to explain difference between report types
3. **Consistent Output**: All reports have the same comprehensive content
4. **Less Code**: Removed conditional logic and templates

## Notes

- The generate_report.html template is preserved but no longer used
- Could be deleted in future cleanup if confirmed not needed
- All existing summary reports will be converted to detailed type during migration