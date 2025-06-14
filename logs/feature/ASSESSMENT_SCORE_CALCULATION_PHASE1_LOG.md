# Assessment Score Calculation Implementation - Phase 1 Complete

**Date**: 2025-06-13
**Author**: Claude
**Feature**: Assessment Score Calculation

## Summary
Completed Phase 1 of implementing the assessment score calculation feature. This phase focused on updating the Assessment model to support proper scoring by adding missing fields and preparing the database schema.

## Detailed Changes

### 1. Model Updates (`apps/assessments/models.py`)
- **Removed**: `harvard_step_test_heart_rate` field (single heart rate measurement)
- **Added**: Three separate heart rate fields for Harvard Step Test:
  - `harvard_step_test_hr1` - Heart rate 1-1.5 minutes after exercise (bpm)
  - `harvard_step_test_hr2` - Heart rate 2-2.5 minutes after exercise (bpm)
  - `harvard_step_test_hr3` - Heart rate 3-3.5 minutes after exercise (bpm)
- **Added**: `farmer_carry_time` field (IntegerField for seconds)
- All new fields are nullable to maintain backward compatibility

### 2. Database Migrations
- **Created**: `0002_remove_assessment_harvard_step_test_heart_rate_and_more.py`
  - Removes old heart rate field
  - Adds new fields with proper validators
- **Created**: `0003_migrate_heart_rate_data.py`
  - Custom data migration to handle existing records
  - Sets default values for new fields where needed
- **Applied**: Both migrations successfully to development database

### 3. Form Updates (`apps/assessments/forms.py`)
- Updated field list to include new fields
- Added form widgets with Korean placeholders:
  - Heart rate fields with specific time period labels
  - Farmer carry time field with "초" (seconds) placeholder
- Updated default values for form initialization
- Added Alpine.js x-model bindings for real-time calculations

### 4. Template Updates

#### Assessment Form (`templates/assessments/assessment_form.html`)
- Changed Farmer's Carry grid from 3 to 4 columns
- Replaced single heart rate input with three separate inputs
- Added Alpine.js data properties:
  - `farmerTime`, `harvardHR1`, `harvardHR2`, `harvardHR3`
- Updated `calculateFarmerScore()` to include time parameter
- Added `calculateHarvardScore()` function for client-side feedback

#### Assessment Detail (`templates/assessments/assessment_detail.html`)
- Updated Farmer's Carry display to show time
- Updated Harvard Step Test display to show all three heart rates
- Maintained consistent formatting with existing fields

### 5. View and URL Updates
- **Added**: `calculate_harvard_score_ajax` view in `apps/assessments/views.py`
- **Added**: URL pattern for Harvard score calculation endpoint
- **Updated**: Imports to include `calculate_step_test_score` function
- Harvard endpoint returns both score and PFI (Physical Fitness Index)

## Technical Decisions

1. **Three Heart Rate Fields**: Chose to add three separate fields instead of modifying the scoring function to maintain accuracy with the original FMS (Functional Movement Screen) protocol.

2. **Required Time Field**: Made farmer carry time field required (though nullable for existing records) to ensure proper scoring going forward.

3. **Data Migration Strategy**: Created a separate data migration to handle existing records gracefully with reasonable defaults.

4. **Backward Compatibility**: All new fields are nullable to avoid breaking existing data.

## Testing
- Migrations applied successfully
- Django development server starts without errors
- Forms render correctly with new fields
- AJAX endpoints configured properly

## Known Issues
- The assessment score calculation logic (TODO in `calculate_scores()` method) is not yet implemented
- This will be addressed in Phase 2

## Next Steps
Phase 2 will implement the actual score calculation logic in the Assessment model's `calculate_scores()` method, integrating the scoring functions from `apps/assessments/scoring.py`.

## Files Modified
- `apps/assessments/models.py`
- `apps/assessments/forms.py`
- `apps/assessments/views.py`
- `apps/assessments/urls.py`
- `templates/assessments/assessment_form.html`
- `templates/assessments/assessment_detail.html`

## Files Created
- `apps/assessments/migrations/0002_remove_assessment_harvard_step_test_heart_rate_and_more.py`
- `apps/assessments/migrations/0003_migrate_heart_rate_data.py`