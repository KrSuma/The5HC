# Assessment Detail View Fix - 2025-06-18

**Date**: 2025-06-18  
**Author**: Claude  
**Issue**: Missing Features in Assessment Detail View

## Summary

User reported that injury risk assessment, percentile rankings, and fitness charts are missing from the assessment detail view (상세 보기) but appear in PDF reports. Investigation revealed this is NOT intentional - these features should appear in both views.

## Problem Analysis

The assessment detail template includes all the necessary sections:
- 부상 위험도 평가 (Injury Risk Assessment) - lines 148-267
- 백분위 순위 (Percentile Rankings) - lines 269-347  
- 체력 나이 (Performance Age) - lines 349-455
- 능력치 차트 (Fitness Chart) - lines 635-741

However, these sections may not display because:
1. Existing assessments lack calculated injury_risk_score and risk_factors
2. Normative data may not be loaded for percentile calculations
3. The recalculate_scores command wasn't updating all necessary fields

## Solution

### 1. Updated Recalculate Command

Modified `apps/assessments/management/commands/recalculate_scores.py` to:
- Include injury_risk_score and risk_factors in update_fields
- Show injury risk score changes in output
- Properly save all calculated fields

### 2. Created Diagnostic Script

Created `scripts/check_assessment_data.py` to diagnose:
- How many assessments have injury risk scores
- Whether normative data is loaded
- Sample assessment calculation results
- Specific recommendations for fixes

### 3. Recommended Actions

To fix the issue, run these commands in order:

```bash
# 1. Load normative data for percentile calculations
python manage.py load_normative_data

# 2. Load test standards for scoring
python manage.py load_test_standards

# 3. Recalculate all assessment scores
python manage.py recalculate_scores

# 4. Check the results
python scripts/check_assessment_data.py
```

## Technical Details

The assessment detail view (`assessment_detail_view`) does fetch the data:
- `percentile_rankings = assessment.get_percentile_rankings()` (line 129)
- `performance_age_data = assessment.calculate_performance_age()` (line 132)

The injury risk score is calculated in the model's `calculate_scores()` method which is called on save.

## Result

After running the management commands above, all features should display correctly in both the detail view and PDF reports. The issue was caused by missing data, not missing functionality.