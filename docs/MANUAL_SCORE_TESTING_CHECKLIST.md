# Manual Score Field Testing Checklist

**Date**: 2025-06-25
**Feature**: Manual Score Field Fixes (Phases 1-5)
**Session**: 18

## Pre-Testing Setup

- [ ] Clear browser cache
- [ ] Run development server: `python manage.py runserver`
- [ ] Login as test trainer
- [ ] Have test client ready

## 1. New Assessment Creation Flow

### Initial Form Load
- [ ] Navigate to new assessment form
- [ ] Verify overhead_squat_score dropdown shows options 0-5
- [ ] Verify shoulder_mobility_score dropdown shows options 0-5
- [ ] Verify both fields have proper Korean labels

### Manual Score Entry
- [ ] Select manual score for overhead squat (e.g., 3)
- [ ] Verify blue ring appears around field (`ring-2 ring-blue-500`)
- [ ] Verify "수동 입력됨" badge appears above field
- [ ] Verify "자동 계산으로 재설정" link appears

### Movement Compensation Interaction
- [ ] Check some movement compensations (knee valgus, forward lean)
- [ ] Verify manual score is NOT overwritten
- [ ] Verify overall scores still calculate correctly

### Reset Functionality
- [ ] Click "자동 계산으로 재설정" on overhead squat
- [ ] Verify manual score clears
- [ ] Verify blue ring disappears
- [ ] Verify badge disappears
- [ ] Verify automatic calculation resumes based on compensations

### Form Submission
- [ ] Save assessment with manual scores
- [ ] Verify success message appears
- [ ] Verify no validation errors

## 2. Edit Assessment Flow

### Loading Existing Assessment
- [ ] Open assessment that has manual scores saved
- [ ] Verify manual scores display correctly in dropdowns
- [ ] Verify blue rings show on manually entered fields
- [ ] Verify badges show "수동 입력됨"
- [ ] Verify other scores load correctly

### Modifying Manual Scores
- [ ] Change manual score value
- [ ] Verify visual indicators remain
- [ ] Verify overall scores recalculate
- [ ] Save changes
- [ ] Reload page and verify persistence

### Mixed Manual/Automatic
- [ ] Have one manual score (overhead squat)
- [ ] Have one automatic score (shoulder mobility)
- [ ] Verify only manual field shows indicators
- [ ] Toggle between manual and automatic for each

## 3. Edge Cases Testing

### Score Value 0 (Pain)
- [ ] Select 0 for overhead squat
- [ ] Verify it's treated as manual override
- [ ] Verify visual indicators appear
- [ ] Verify score calculations handle 0 correctly

### Score Value 5 (Excellent)
- [ ] Select 5 for shoulder mobility
- [ ] Verify visual indicators appear
- [ ] Verify normalization works (should map to 4.0)
- [ ] Verify category scores calculate correctly

### Rapid Changes
- [ ] Quickly switch between manual scores
- [ ] Verify no UI glitches
- [ ] Verify calculations keep up
- [ ] Verify no console errors

### Form Validation
- [ ] Submit form with only manual scores (no automatic calculations)
- [ ] Verify form validates correctly
- [ ] Verify all required fields are checked

## 4. Visual Feedback Testing

### CSS Transitions
- [ ] Verify smooth fade-in for badges (300ms)
- [ ] Verify smooth appearance of blue ring
- [ ] Verify no layout shift when indicators appear

### Responsive Design
- [ ] Test on mobile viewport (375px)
- [ ] Verify badges don't overlap on small screens
- [ ] Verify reset button is easily tappable
- [ ] Test on tablet viewport (768px)
- [ ] Test on desktop viewport (1024px+)

### Dark Mode (if applicable)
- [ ] Switch to dark mode
- [ ] Verify blue ring remains visible
- [ ] Verify badge colors have sufficient contrast

## 5. Integration Testing

### HTMX Navigation
- [ ] Navigate to assessment form via HTMX
- [ ] Verify Alpine.js initializes correctly
- [ ] Enter manual scores
- [ ] Navigate away and back
- [ ] Verify state is maintained

### Multi-Step Form
- [ ] Enter manual scores in balance/coordination step
- [ ] Navigate to other steps
- [ ] Return to balance step
- [ ] Verify manual scores and indicators persist

### Overall Score Display
- [ ] Complete assessment with manual scores
- [ ] View assessment detail page
- [ ] Verify scores display correctly
- [ ] Verify radar chart shows accurate data

## 6. Performance Testing

### Page Load
- [ ] Measure time to interactive with manual scores
- [ ] Verify no JavaScript errors in console
- [ ] Check for memory leaks in DevTools

### Multiple Assessments
- [ ] Open list with many assessments
- [ ] Verify page remains responsive
- [ ] Edit multiple assessments in sequence

## 7. Cross-Browser Testing

### Chrome (Latest)
- [ ] All visual indicators work
- [ ] Transitions smooth
- [ ] No console errors

### Firefox (Latest)
- [ ] All visual indicators work
- [ ] Transitions smooth
- [ ] No console errors

### Safari (Latest)
- [ ] All visual indicators work
- [ ] Transitions smooth
- [ ] No console errors

### Edge (Latest)
- [ ] All visual indicators work
- [ ] Transitions smooth
- [ ] No console errors

## 8. Accessibility Testing

### Keyboard Navigation
- [ ] Tab through form fields
- [ ] Use spacebar to open dropdowns
- [ ] Use arrow keys to select options
- [ ] Verify focus indicators visible

### Screen Reader
- [ ] Test with NVDA/JAWS (Windows) or VoiceOver (Mac)
- [ ] Verify manual override status is announced
- [ ] Verify reset button is accessible
- [ ] Verify form labels are clear

## 9. Data Validation

### Database Check
- [ ] Check database directly for saved manual scores
- [ ] Verify overhead_squat_score saved correctly (0-5)
- [ ] Verify shoulder_mobility_score saved correctly (0-5)
- [ ] Verify other fields unaffected

### API Response
- [ ] Check API endpoint returns manual scores
- [ ] Verify scoring calculations in API response
- [ ] Verify no data corruption

## 10. Regression Testing

### Existing Features
- [ ] Automatic calculations still work for other fields
- [ ] PDF generation includes manual scores
- [ ] Client filtering/search unaffected
- [ ] Dashboard statistics accurate

### Other Assessment Types
- [ ] MCQ assessments unaffected
- [ ] Movement quality fields still work
- [ ] Risk scoring calculations correct

## Sign-off

- [ ] All checklist items completed
- [ ] No critical bugs found
- [ ] Performance acceptable
- [ ] Ready for Phase 7 (Documentation and Deployment)

**Tested by**: _________________
**Date**: _________________
**Notes**: _________________