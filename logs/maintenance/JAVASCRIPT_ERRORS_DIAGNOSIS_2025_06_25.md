# JavaScript Errors Diagnosis and Fixes

**Date**: 2025-06-25
**Issues**: 
1. "Return statements are only valid inside functions" in app.js
2. "Unexpected end of script" at assessments:1606
**Status**: RESOLVED (Issue 1), INVESTIGATING (Issue 2)

## Issue 1: Return Statement Error

### Problem
The app.js file had a `return` statement at the top level (line 3), which is invalid JavaScript:
```javascript
if (window._appJsLoaded) {
    return;  // ERROR: Not inside a function!
}
```

### Root Cause
- Return statements can only be used inside functions
- The script was trying to prevent re-execution with a guard pattern
- The guard itself had invalid syntax

### Solution
Wrapped the entire script in an IIFE (Immediately Invoked Function Expression):
```javascript
(function() {
    'use strict';
    
    if (window._appJsLoaded) {
        return;  // Now valid inside function
    }
    window._appJsLoaded = true;
    
    // ... rest of script
})();
```

### Files Modified
- `/static/js/app.js` - Added IIFE wrapper
- Ran `collectstatic` to update served files

## Issue 2: Unexpected End of Script

### Problem
Error occurring at "assessments:1606" suggesting incomplete script in rendered HTML.

### Analysis
- Line 1606 is beyond template file lengths (assessment_form.html has 953 lines)
- This indicates the error is in the fully rendered HTML, not the template
- Likely caused by:
  1. HTMX dynamically inserting scripts
  2. Script extraction/execution failing
  3. Template rendering issues

### Possible Causes
1. **Dynamic Script Injection**: HTMX may be extracting and re-injecting scripts incorrectly
2. **Template Syntax**: Django template tags inside JavaScript causing parsing issues
3. **Script Concatenation**: Multiple scripts being combined incorrectly
4. **Browser Parsing**: Browser interpreting HTML entities or special characters in scripts

### Investigation Steps Taken
1. Checked all assessment templates for unclosed script tags ✓
2. Verified script closing braces and syntax ✓
3. Fixed app.js return statement issue ✓

## Why These Errors Keep Happening

### 1. HTMX Script Handling
- HTMX extracts scripts from loaded content
- Re-executes them in the global context
- Can fail if scripts have syntax errors or dependencies

### 2. Multiple Script Execution
- Scripts designed for page load get re-executed
- Guard patterns (like `window._appJsLoaded`) need proper syntax
- Scripts conflict when loaded multiple times

### 3. Template Complexity
- Django templates with JavaScript can create parsing issues
- Inline scripts mixed with template variables
- HTMX swapping content with embedded scripts

## Prevention Strategy

### 1. Use External Scripts
Instead of inline scripts, use external JavaScript files:
```html
<!-- Bad: Inline script in template -->
<script>
    // Complex logic here
</script>

<!-- Good: External script -->
<script src="{% static 'js/assessment-form.js' %}"></script>
```

### 2. Proper Guard Patterns
Always use IIFE for scripts that need guards:
```javascript
(function() {
    if (window.moduleLoaded) return;
    window.moduleLoaded = true;
    // Module code
})();
```

### 3. HTMX-Aware Scripts
Design scripts to work with HTMX:
```javascript
// Works with both page load and HTMX
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'my-target') {
        initializeComponent();
    }
});
```

### 4. Error Boundaries
Add global error handlers:
```javascript
window.addEventListener('error', function(event) {
    console.error('Script error:', event.error);
    // Prevent propagation
    event.preventDefault();
});
```

## Next Steps

For the "Unexpected end of script" error:
1. Add debug logging to identify which script is failing
2. Consider moving all inline scripts to external files
3. Add script validation before HTMX processes them
4. Use htmx:beforeProcessNode event to inspect scripts

## Technical Notes

- Browser line numbers in errors refer to the rendered HTML, not template files
- HTMX uses innerHTML which can cause script parsing issues
- Some browsers are stricter about script syntax than others
- Django template rendering can introduce unexpected characters in JavaScript