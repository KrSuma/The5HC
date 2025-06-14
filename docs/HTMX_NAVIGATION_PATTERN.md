# HTMX Navigation Pattern Guide

## Overview

This document describes the proper pattern for handling HTMX navigation in The5HC project to prevent duplicate header/footer issues.

## The Problem

When using HTMX for navigation (e.g., navbar links), clicking on links that target `#main-content` can cause duplicate headers and footers if views return full pages (extending `base.html`).

## The Solution

Views must detect HTMX navigation requests and return content-only templates when appropriate.

### Detection Pattern

```python
# Check if this is an HTMX navigation request (navbar click)
# HX-Target will be #main-content for navbar navigation
if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
    return render(request, 'template_content.html', context)

# Regular request - return full page
return render(request, 'template.html', context)
```

### Template Structure

For each view that can be accessed via HTMX navigation, create two templates:

1. **Full Page Template** (`template.html`):
   - Extends `base.html`
   - Used for direct URL access or page refresh
   - Contains complete HTML structure

2. **Content-Only Template** (`template_content.html`):
   - Does NOT extend `base.html`
   - Contains only the main content
   - Used for HTMX navigation requests

### Example Implementation

#### View (views.py)
```python
@login_required
def my_view(request):
    context = {'data': 'example'}
    
    # Check for HTMX navigation request
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'main-content':
        return render(request, 'myapp/my_template_content.html', context)
    
    return render(request, 'myapp/my_template.html', context)
```

#### Full Page Template (my_template.html)
```html
{% extends 'base.html' %}

{% block title %}My Page - The5HC{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1>My Page</h1>
    <!-- Page content -->
</div>
{% endblock %}
```

#### Content-Only Template (my_template_content.html)
```html
<!-- No extends statement! -->
<div class="container mx-auto px-4 py-8">
    <h1>My Page</h1>
    <!-- Same content as above, but without base.html -->
</div>
```

## Current Implementations

### Fixed Views:
1. **Assessment List** (`apps/assessments/views.py`)
   - `assessment_list.html` (full page)
   - `assessment_list_content.html` (content only)

2. **Client Add/Edit** (`apps/clients/views.py`)
   - `client_form.html` (full page)
   - `client_form_content.html` (content only)

3. **Client Detail** (`apps/clients/views.py`)
   - `client_detail.html` (full page)
   - `client_detail_content.html` (content only)

## Views That Need This Pattern

Any view that:
1. Can be accessed from the navbar
2. Uses standard page layout (extends base.html)
3. Might be linked from other pages

## Testing

To test if a view handles HTMX navigation correctly:

1. Navigate to the page directly by URL - should show full page
2. Click on the navbar link - should NOT show duplicate headers/footers
3. Use browser's back/forward buttons - should work correctly
4. Refresh the page - should show full page

## Common Mistakes to Avoid

1. **Don't check only for HX-Request**: Form submissions also set this header
2. **Always check HX-Target**: Ensures it's a navigation request, not a partial update
3. **Keep content identical**: The content-only template should have the exact same content, just without base.html
4. **Don't forget Alpine.js init**: If using Alpine.js, ensure scripts are included in content-only template

## Debugging Tips

If you see duplicate headers/footers:
1. Check browser DevTools Network tab for the response
2. Look for the HX-Target header in the request
3. Verify the view is returning the correct template
4. Ensure the content-only template doesn't extend base.html

## Future Considerations

Consider creating a custom decorator or middleware to handle this pattern automatically:

```python
def htmx_navigation_aware(view_func):
    """Decorator to automatically handle HTMX navigation requests."""
    def wrapper(request, *args, **kwargs):
        # Implementation would go here
        pass
    return wrapper
```