# Report Filename Field Fix Log

**Date**: 2025-06-15
**Author**: Claude
**Issue**: AttributeError when downloading assessment reports - 'Assessment' object has no attribute 'assessment_date'

## Summary

Fixed an error in the AssessmentReport model's filename property that was trying to access a non-existent field `assessment_date` on the Assessment model. The correct field name is `date`.

## Issue Description

When attempting to download an assessment report at `/reports/2/download/`, the following error occurred:
```
AttributeError: 'Assessment' object has no attribute 'assessment_date'
```

This was happening in the `filename` property of the AssessmentReport model, which generates a user-friendly filename for downloads.

## Root Cause

The AssessmentReport model was trying to access `self.assessment.assessment_date`, but the Assessment model uses `date` as the field name for the assessment date.

## Solution Implemented

Updated the `filename` property in `apps/reports/models.py`:

```python
# Changed from:
date_str = self.assessment.assessment_date.strftime('%Y%m%d')

# To:
date_str = self.assessment.date.strftime('%Y%m%d')
```

## Files Modified

- `apps/reports/models.py` - Fixed the field reference in the filename property

## Testing Instructions

1. Ensure WeasyPrint is working locally by running:
   ```bash
   ./run_with_weasyprint.sh
   ```
2. Navigate to an assessment detail page
3. Click the "PDF 보고서 다운로드" button
4. The report should generate and download successfully with a filename like:
   `fitness_assessment_ClientName_20250615.pdf`

## Additional Notes

This issue likely occurred because the field naming was inconsistent between the original Streamlit implementation and the Django migration. The Assessment model correctly uses `date` as the field name, which is more concise and appropriate.