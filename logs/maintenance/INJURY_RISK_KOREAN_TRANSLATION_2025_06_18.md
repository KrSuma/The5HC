# Injury Risk Assessment Korean Translation - 2025-06-18

**Date**: 2025-06-18  
**Author**: Claude  
**Issue**: English text appearing in injury risk assessment and percentile rankings sections

## Summary

Translated all English text in the injury risk assessment (부상 위험도 평가) and percentile rankings (백분위 순위) sections to Korean in the assessment detail view.

## Changes Made

### 1. Updated Assessment Detail Template

**File**: `templates/assessments/assessment_detail.html`

Translated dynamic content in multiple sections:

#### Risk Factor Details Section:
- Category names (Strength → 근력, Mobility → 유연성, Balance → 균형, Cardio → 심폐지구력)
- Movement compensation types:
  - knee_valgus → 무릎 안쪽 굽힘
  - forward_lean → 상체 앞쏠림
  - heel_lift → 발뒤꿈치 들림
  - asymmetric_shift → 비대칭 이동

#### Percentile Rankings Section:
- Added support for both lowercase and uppercase category names
- Ensured all category names display in Korean:
  - strength/Strength → 근력
  - mobility/Mobility → 유연성
  - balance/Balance → 균형
  - cardio/Cardio → 심폐지구력

### 2. Created Korean Risk Calculator

**File**: `apps/assessments/risk_calculator_korean.py`

Created a Korean version of the primary concerns generator that translates:
- "Significant [category] imbalance" → "심각한 [카테고리] 불균형"
- "Shoulder mobility asymmetry" → "어깨 가동성 비대칭"
- "Balance asymmetry" → "균형 비대칭"
- "Movement compensations" → "움직임 보상"
- "Poor mobility in X tests" → "X개 테스트에서 낮은 유연성"
- "Poor balance" → "낮은 균형 능력"

### 3. Updated Assessment Detail View

**File**: `apps/assessments/views.py`

Added automatic translation of primary concerns when displaying assessment details:
```python
# Translate primary concerns to Korean if available
if assessment.risk_factors and 'summary' in assessment.risk_factors:
    from apps.assessments.risk_calculator_korean import get_korean_primary_concerns
    assessment.risk_factors['summary']['primary_concerns'] = get_korean_primary_concerns(assessment.risk_factors)
```

## Result

All text in the injury risk assessment section now displays in Korean, including:
- Static labels and headers (already in Korean)
- Dynamic category names
- Movement compensation descriptions
- Primary concern summaries

The implementation maintains the original data structure while providing Korean translations at the presentation layer.