# PDF Report Improvements Log

**Date**: 2025-06-15
**Author**: Claude
**Issues Fixed**: 
1. Summary and detailed reports were identical
2. PDF content was cut off on the right side
3. Content not properly aligned/centered

## Summary

Fixed PDF report generation issues including implementing differentiation between summary and detailed reports, and fixing page layout/alignment problems.

## Issues Addressed

### 1. Report Type Differentiation
**Problem**: Both "요약 보고서" (summary report) and "상세 보고서" (detailed report) were generating identical content.

**Solution**: 
- Added `report_type` and `is_summary` to the template context
- Added conditional sections in the template:
  - Summary reports exclude "세부 측정 결과" (detailed test results)
  - Summary reports show only first 2 improvement suggestions per category
  - Summary reports exclude "맞춤형 운동 프로그램" (customized exercise program)
- Updated header to show report type (요약/상세)

### 2. PDF Alignment and Cut-off Issues
**Problem**: PDF content was cut off on the right side and not properly centered on the page.

**Root Cause**: The template had fixed width (210mm) and padding that didn't account for WeasyPrint's page margins.

**Solution**:
- Changed `.page` CSS from fixed width to 100% width
- Added proper `@page` CSS rule with A4 size and 15mm margins
- Removed fixed dimensions and let WeasyPrint handle page layout
- Added page margin settings in the CSS generation

## Files Modified

1. **`apps/reports/services.py`**:
   - Added `report_type` and `is_summary` to template context
   - Updated CSS in `_html_to_pdf()` to include proper page setup

2. **`templates/reports/assessment_report.html`**:
   - Changed page layout CSS to use 100% width
   - Added conditional blocks for summary vs detailed reports
   - Fixed date field references (assessment_date → date)
   - Updated header to show report type

3. **`apps/reports/models.py`** (previously):
   - Fixed filename property to use correct date field

## CSS Changes

```css
/* Before */
.page {
    width: 210mm;
    height: 297mm;
    margin: 0 auto;
    padding: 10mm;
}

/* After */
.page {
    width: 100%;
    margin: 0;
    padding: 0;
}

@page {
    size: A4;
    margin: 15mm;
}
```

## Template Logic Added

```django
{% if is_summary %}
    {# Show limited content for summary reports #}
{% else %}
    {# Show full content for detailed reports #}
{% endif %}
```

## Testing Instructions

1. Run the server with WeasyPrint support:
   ```bash
   ./run_with_weasyprint.sh
   ```

2. Generate both report types:
   - Go to an assessment detail page
   - Click "PDF 보고서 생성"
   - Try both "요약 보고서" and "상세 보고서"

3. Verify:
   - Summary reports are shorter with less detail
   - Detailed reports include all test results and training programs
   - PDFs are properly centered with no cut-off content
   - Content fits within A4 page boundaries

## Summary vs Detailed Report Differences

### Summary Report (요약 보고서) includes:
- Basic client information
- Category scores with visual progress bars
- Overall score and rating
- Limited improvement suggestions (max 2 per category)
- Follow-up dates

### Detailed Report (상세 보고서) includes everything above plus:
- Detailed test results table with all measurements
- Complete list of improvement suggestions
- Customized exercise program with phases
- Full assessment data

## Additional Notes

- The WeasyPrint CSS now properly handles Korean fonts (NanumGothic)
- Page margins ensure content is readable when printed
- The report type is stored in the database for future reference