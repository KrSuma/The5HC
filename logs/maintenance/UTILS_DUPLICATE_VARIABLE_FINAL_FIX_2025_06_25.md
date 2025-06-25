# Utils Duplicate Variable Error - Final Fix

**Date**: 2025-06-25
**Issue**: JavaScript error "Can't create duplicate variable that shadows a global property: 'utils'"
**Status**: RESOLVED

## Problem Summary

The error was occurring when navigating between assessment pages using HTMX due to conflicting JavaScript variable declarations for `utils`.

## Root Cause

Multiple factors contributed to the issue:
1. Outdated static files being served by Django
2. Complex property definitions causing conflicts between scripts
3. HTMX script re-execution causing redeclaration attempts

## Final Solution

Simplified the entire utils system with a clean, conflict-free approach:

### 1. Simplified app.js
```javascript
// Simple assignment to avoid conflicts
window.utils = window.utils || {};

// Add utility functions
Object.assign(window.utils, {
    formatDate(dateString) { ... },
    formatCurrency(amount) { ... },
    debounce(func, wait) { ... }
});
```

### 2. Added simple-utils-fix.js
- Intercepts `eval()` and `Function()` calls
- Automatically converts `const utils =` to `window.utils =`
- Prevents any script from declaring utils as a local variable

### 3. Removed Complex Solutions
- Removed utils-guard.js (was causing property conflicts)
- Removed htmx-script-fix.js (too complex for the issue)
- Simplified Object.defineProperty approach

## Files Modified

1. `/static/js/app.js` - Simplified utils definition
2. `/static/js/simple-utils-fix.js` - Prevents utils conflicts via script interception
3. `/templates/base.html` - Load simple-utils-fix.js early
4. Updated static files via `collectstatic`

## Files Removed

- `/static/js/utils-guard.js`
- `/static/js/htmx-script-fix.js`

## Testing

1. Navigate to any assessment detail page
2. Click between different assessment records
3. Verify no JavaScript errors in console
4. Confirm charts and functionality work correctly

## Key Lessons

1. **Keep it simple** - Complex property definitions caused more problems
2. **Static files matter** - Always run `collectstatic` after JS changes
3. **Script interception works** - Overriding `eval()` can prevent declaration conflicts
4. **HTMX script handling** - Be careful with global variable declarations in HTMX content

## Prevention Guidelines

1. Use `window.utils = window.utils || {}` pattern for global objects
2. Avoid `const`, `let`, or `var` for global utilities
3. Always run `collectstatic` after JavaScript modifications
4. Test navigation extensively after JS changes

This final solution is simple, robust, and should prevent all future utils-related conflicts.