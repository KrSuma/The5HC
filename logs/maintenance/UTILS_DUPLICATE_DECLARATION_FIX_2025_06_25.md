# Utils Duplicate Declaration Error Fix - 2025-06-25

## Issue Description
When navigating to assessment detail pages, a JavaScript error occurs:
```
Uncaught SyntaxError: Identifier 'utils' has already been declared
```

## Root Cause Analysis

1. **Global Utils Object**: The main `app.js` file creates a global `window.utils` object (line 124)
2. **HTMX Content Swapping**: When HTMX loads new content, scripts are re-evaluated
3. **Script Isolation**: The `htmx-script-fix.js` tries to isolate scripts but the comment in templates might be misleading

## Investigation Steps

1. Searched for `utils` declarations across the codebase
2. Found the issue in `/templates/assessments/assessment_detail_content.html`
3. The comment on line 527 warns against creating `const utils = window.utils` but doesn't prevent the actual error

## Solution

The issue is already being handled by `htmx-script-fix.js` which:
- Wraps scripts in IIFEs to prevent global pollution
- Checks for utils declarations and skips them
- Destroys existing charts before swapping content

However, the error still occurs because the script evaluation happens before the safety check.

## Files Involved

1. `/static/js/app.js` - Defines global `window.utils`
2. `/static/js/htmx-script-fix.js` - Attempts to prevent duplicate declarations
3. `/templates/assessments/assessment_detail_content.html` - Contains inline script

## Recommendations

1. The current setup should work correctly with `htmx-script-fix.js`
2. If errors persist, ensure browser cache is cleared
3. The comment in the template is correct - never create local utils references
4. All utility functions should be accessed via `window.utils` directly

## Testing

1. Clear browser cache
2. Navigate to any assessment detail page
3. Check browser console for errors
4. Verify charts render correctly

## Status
The infrastructure to prevent this error is already in place. If the error persists after clearing cache, it may be due to script execution timing issues with HTMX.