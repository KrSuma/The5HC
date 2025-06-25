# Utils Duplicate Variable Error Fix

**Date**: 2025-06-25
**Issue**: JavaScript error when navigating between assessment pages using HTMX
**Error**: "SyntaxError: Can't create duplicate variable: 'utils'"

## Problem Description

When navigating between assessment detail pages using HTMX, a JavaScript error occurred:
```
[Error] JavaScript error:
SyntaxError: Can't create duplicate variable: 'utils'
    (anonymous function) (app.js:214)
```

This error appeared consistently when clicking between different assessment records.

## Root Cause Analysis

1. **Global utils object**: The app.js file declares `window.utils` as a global utility object
2. **HTMX script execution**: When HTMX swaps content, inline scripts are re-executed
3. **Scope conflicts**: Somewhere in the execution context, there was likely an attempt to declare a local `utils` variable that conflicted with existing declarations

## Solutions Implemented

### 1. Enhanced Script Isolation
- Added strict mode to catch errors earlier
- Wrapped scripts in properly parameterized IIFEs
- Removed any potential for local utils references

### 2. Improved Prototype Extension
- Changed from direct assignment to Object.defineProperty for Number.prototype methods
- Made prototype extensions more robust and configurable

### 3. Assessment Detail Fix Script
- Created assessment-detail-fix.js to handle HTMX-specific cleanup
- Ensures proper chart destruction before content swap
- Monitors for potential utils conflicts

### 4. Documentation and Guards
- Added clear comments warning against creating local utils references
- Added defensive programming patterns

## Files Modified

1. `/templates/assessments/assessment_detail_content.html`
   - Enhanced IIFE with strict mode and explicit parameters
   - Improved prototype extension method using Object.defineProperty
   - Added guards against re-execution
   - Removed any potential for local utils references

2. `/static/js/app.js`
   - Added warning comments about not creating local utils references

3. `/static/js/htmx-script-fix.js` (new)
   - Comprehensive HTMX script isolation
   - Automatic script wrapping in IIFEs
   - Chart cleanup before content swaps
   - Prevents duplicate variable declarations

4. `/templates/base.html`
   - Added htmx-script-fix.js script inclusion
   - Removed duplicate Chart.js loading

5. `/templates/assessments/assessment_detail.html`
   - Removed duplicate Chart.js script tag (already loaded in base.html)

## Testing Steps

1. Navigate to any assessment detail page
2. Click on different assessment records using HTMX navigation
3. Check browser console for errors
4. Verify charts render correctly
5. Confirm no duplicate variable errors

## Prevention Guidelines

1. Never create local references to window.utils (e.g., `const utils = window.utils`)
2. Always use window.utils directly when accessing utility functions
3. Wrap all inline scripts in proper IIFEs with strict mode
4. Clean up resources (charts, event listeners) before HTMX swaps

## Additional Notes

The error was particularly tricky because:
- The error location (app.js:214) was in the error handler, not the actual source
- The utils declaration wasn't visible in direct code inspection
- HTMX's script evaluation context can maintain state between page loads
- Duplicate Chart.js loading was causing source map errors

### Final Solution
The complete fix involved multiple steps:

1. **htmx-script-fix.js** provides script isolation by:
   - Wrapping all HTMX-loaded scripts in IIFEs automatically
   - Cleaning up charts and resources before content swaps
   - Preventing any script from declaring global variables
   - Providing proper error handling for script execution

2. **utils-guard.js** prevents the error at the source by:
   - Creating a non-configurable utils property early
   - Preventing any redeclaration of utils
   - Protecting the global namespace

3. **Static files update** - The root cause was outdated static files:
   - The staticfiles/js/app.js had an old version with `const utils = {`
   - Running `python manage.py collectstatic` updated the cached files
   - This removed the source of the duplicate declaration

### Key Findings
- The error was caused by Django serving outdated static files
- The browser was loading an old version of app.js with `const utils`
- HTMX was then loading the new version, causing the duplicate declaration
- Always run `collectstatic` after JavaScript changes in production

This fix ensures proper isolation and cleanup for all HTMX page navigations.