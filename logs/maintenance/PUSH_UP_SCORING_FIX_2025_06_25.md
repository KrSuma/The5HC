# Push-up Scoring System Fix - Score Range 1-4

**Date**: 2025-06-25
**Author**: Claude
**Issue**: Push-up score showing 4 for 100 reps instead of 5

## Problem Analysis

The user reported that entering 100 push-ups resulted in a score of 4, not 5. Investigation revealed:

1. **Backend Scoring System**: The scoring algorithms are designed to return scores from 1-4 only:
   - Score 4 = Excellent (우수) - highest possible score
   - Score 3 = Good (양호)
   - Score 2 = Average (평균)
   - Score 1 = Needs Improvement (개선 필요)

2. **Frontend UI Mismatch**: The manual score override dropdowns were showing options 0-5, which didn't match the backend system.

3. **Standards Based on ACSM**: The scoring follows ACSM (American College of Sports Medicine) guidelines which define only 4 performance tiers.

## Root Cause

- For males age 18-29: 36+ push-ups = Excellent (Score 4)
- There is no higher tier beyond "Excellent" in the fitness assessment standards
- The UI was incorrectly showing score options up to 5

## Solution Implemented

### 1. Updated Form Dropdowns (assessment_forms.py)

Changed all score dropdowns from 0-5 scale to proper ranges:

**Standard Tests (1-4 scale):**
- push_up_score: `[(1, '1 - 개선 필요'), (2, '2 - 평균'), (3, '3 - 양호'), (4, '4 - 우수')]`
- toe_touch_score: Same as above
- farmer_carry_score: Same as above
- single_leg_balance_score_manual: Same as above
- harvard_step_test_score_manual: Same as above

**FMS Tests (0-3 scale):**
- overhead_squat_score: `[(0, '0 - 통증'), (1, '1 - 불가'), (2, '2 - 보상동작'), (3, '3 - 완벽')]`
- shoulder_mobility_score: `[(0, '0 - 통증'), (1, '1 - 2주먹 이상'), (2, '2 - 1.5주먹'), (3, '3 - 1주먹 이내')]`

### 2. Updated Model Validators

Updated all score field validators to match actual scoring ranges:
- Standard tests: MinValueValidator(1), MaxValueValidator(4)
- FMS tests: MinValueValidator(0), MaxValueValidator(3)

### 3. Fixed Score Normalization Logic

Updated scoring.py to properly normalize FMS scores (0-3) to calculation scale (1-4):
```python
# Before: Incorrectly assumed 0-5 scale
# After: Correctly handles 0-3 scale
if shoulder_mobility_score == 0:
    shoulder_mobility_normalized = 1
else:
    # Map 1-3 to 2-4 range
    shoulder_mobility_normalized = 1 + shoulder_mobility_score
```

### 4. Created Migration

Generated migration `0013_update_score_validators.py` to update database constraints.

## Files Modified

1. `/apps/assessments/forms/assessment_forms.py` - Updated dropdown choices
2. `/apps/assessments/models.py` - Updated field validators
3. `/apps/assessments/scoring.py` - Fixed score normalization
4. `/apps/assessments/migrations/0013_update_score_validators.py` - New migration

## Impact

- Users will now see correct score ranges in dropdowns
- No confusion about why score 5 can't be achieved
- Maintains consistency with established fitness standards
- Existing data remains valid (scores were already 1-4)

## Testing Recommendations

1. Test manual score entry for all assessment types
2. Verify automatic scoring still works correctly
3. Check that existing assessments display properly
4. Confirm migration runs successfully on production

## Deployment Steps

1. Deploy code changes
2. Run migration: `python manage.py migrate`
3. Clear browser caches to ensure updated dropdowns appear
4. Test manual score entry functionality