# Translation Fixes - Korean Terminology

**Date**: 2025-06-25
**Author**: Claude
**Type**: Translation corrections

## Summary

Fixed two translation issues in the assessment system to use more appropriate Korean terminology.

## Changes Made

### 1. Fixed "보정동작" → "보상동작" (Compensatory Movement)
- **Location**: `apps/assessments/forms/assessment_forms.py` line 72
- **Context**: Overhead squat score choice options
- **Reason**: "보상동작" (compensatory movement) is the correct term for movement faults/compensations, not "보정동작" (corrective movement)

### 2. Fixed "수정된" → "보정된" (Modified/Adapted Push-up)
- **Locations**: 
  - `apps/assessments/models.py` line 230 (push_up_type choices)
  - `apps/assessments/management/commands/load_test_standards.py` lines 285, 289
  - `docs/TEST_VARIATION_GUIDELINES_KO.md` lines 19, 105
  - `docs/MANUAL_SCORE_OVERRIDE_USER_GUIDE.md` line 81
- **Context**: Push-up variation terminology
- **Reason**: "보정된" better conveys the adapted/adjusted nature of modified push-ups, while "수정된" is too generic

## Technical Impact
- These are display-only changes that affect Korean UI labels
- No database migration needed (only affects choice display values)
- No functional changes to scoring or calculations

## User Impact
- More accurate and professional Korean terminology
- Better alignment with fitness assessment standards
- Clearer communication of movement patterns and exercise variations