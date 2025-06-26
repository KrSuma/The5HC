# DualTemplateMixin Implementation Guide

**Date**: 2025-06-25  
**Purpose**: Guide for implementing the DualTemplateMixin to solve HTMX dual template issues

## Overview

The DualTemplateMixin automatically handles the HTMX dual template pattern, preventing bugs where features work in one navigation method but not the other.

## Problem It Solves

Currently, when adding features to templates, developers must remember to update BOTH:
- Full page template (e.g., `assessment_form.html`)
- Content template (e.g., `assessment_form_content.html`)

Missing updates in either template causes confusing bugs. The DualTemplateMixin automates this selection.

## Usage Guide

### 1. For Class-Based Views (Recommended Approach)

```python
from django.views.generic import CreateView, UpdateView, ListView
from apps.core.mixins import DualTemplateMixin, TrainerViewMixin
from .models import Assessment
from .forms import AssessmentForm

class AssessmentCreateView(DualTemplateMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = 'assessments/assessment_form.html'
    # No need to specify content_template_name - it's automatic!
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # is_htmx_request is automatically available
        if context['is_htmx_request']:
            # Add any HTMX-specific context
            pass
        return context

# Using convenience mixins
class AssessmentListView(TrainerViewMixin, ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    # Automatically filters by trainer and handles dual templates!
```

### 2. For Function-Based Views (Migration Path)

```python
from django.shortcuts import render
from apps.core.mixins import DualTemplateMixin

class DualTemplateHelper:
    """Helper to use DualTemplateMixin logic in function views"""
    
    def __init__(self, request):
        self.request = request
    
    def get_template_name(self, base_template):
        """Get appropriate template based on request type"""
        if self.request.headers.get('HX-Request'):
            # Transform to content template
            if base_template.endswith('.html'):
                return base_template[:-5] + '_content.html'
        return base_template
    
    def get_context(self, **kwargs):
        """Add standard context variables"""
        kwargs['is_htmx_request'] = bool(self.request.headers.get('HX-Request'))
        kwargs['current_url'] = self.request.get_full_path()
        return kwargs

# Usage in function view
@login_required
def assessment_list_view(request):
    helper = DualTemplateHelper(request)
    
    assessments = Assessment.objects.all()
    
    template = helper.get_template_name('assessments/assessment_list.html')
    context = helper.get_context(
        assessments=assessments,
        # other context...
    )
    
    return render(request, template, context)
```

### 3. Migration Strategy for Existing Views

#### Step 1: Identify Views Using Dual Templates

```bash
# Find all content templates
find templates -name "*_content.html" | sort

# Find views that might need updating
grep -r "template_name" apps/*/views.py
```

#### Step 2: Convert to Class-Based Views (Recommended)

Example conversion:

```python
# OLD: Function-based view
@login_required
def client_list_view(request):
    clients = Client.objects.filter(trainer=request.user)
    
    # Manual template selection
    if request.headers.get('HX-Request'):
        template = 'clients/client_list_content.html'
    else:
        template = 'clients/client_list.html'
    
    return render(request, template, {'clients': clients})

# NEW: Class-based view with DualTemplateMixin
from apps.core.mixins import TrainerViewMixin

class ClientListView(TrainerViewMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    # That's it! Dual templates handled automatically
```

### 4. Template Organization Best Practices

```
templates/
├── assessments/
│   ├── assessment_form.html         # Full page template
│   ├── assessment_form_content.html # Content-only template
│   ├── assessment_list.html
│   └── assessment_list_content.html
├── clients/
│   ├── client_form.html
│   ├── client_form_content.html
│   ├── client_list.html
│   └── client_list_content.html
```

### 5. Testing Dual Templates

```python
# tests/test_dual_templates.py
from django.test import TestCase
from django.urls import reverse

class DualTemplateTestCase(TestCase):
    def test_regular_request_uses_full_template(self):
        response = self.client.get(reverse('assessment:list'))
        self.assertTemplateUsed(response, 'assessments/assessment_list.html')
        self.assertContains(response, '<html')  # Has full HTML structure
    
    def test_htmx_request_uses_content_template(self):
        response = self.client.get(
            reverse('assessment:list'),
            headers={'HX-Request': 'true'}
        )
        self.assertTemplateUsed(response, 'assessments/assessment_list_content.html')
        self.assertNotContains(response, '<html')  # No HTML structure

    def test_context_includes_htmx_flag(self):
        response = self.client.get(
            reverse('assessment:list'),
            headers={'HX-Request': 'true'}
        )
        self.assertTrue(response.context['is_htmx_request'])
```

## Benefits

1. **Automatic Template Selection**: No more manual checking for HX-Request
2. **Prevents Template Drift**: Can't forget to update one template
3. **Consistent Context**: Always have `is_htmx_request` and `current_url`
4. **Easy Migration**: Can be added to existing views incrementally
5. **Better Testing**: Clear pattern for testing both navigation methods

## Common Patterns

### 1. HTMX Response Headers

```python
from apps.core.mixins import HTMXResponseMixin

class AssessmentDeleteView(HTMXResponseMixin, DeleteView):
    model = Assessment
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        
        # Use HTMX-aware redirect
        return self.htmx_redirect(success_url)
```

### 2. Form Success Messages

```python
from apps.core.mixins import FormSuccessMessageMixin

class ClientCreateView(FormSuccessMessageMixin, CreateView):
    model = Client
    success_message = "고객이 성공적으로 등록되었습니다."
    
    # Message automatically sent via HX-Trigger for HTMX
    # or Django messages for regular requests
```

### 3. Organization Filtering

```python
from apps.core.mixins import OrganizationViewMixin

class ClientListView(OrganizationViewMixin, ListView):
    model = Client
    # Automatically filtered by user's organization!
```

## Migration Checklist

- [ ] Add `apps.core` to INSTALLED_APPS
- [ ] Import DualTemplateMixin in views
- [ ] Update views to use the mixin
- [ ] Test both navigation methods
- [ ] Remove manual template selection code
- [ ] Update documentation

## Troubleshooting

### Template Not Found

If you get a template not found error for `*_content.html`:
1. Check that content template exists
2. Verify template naming convention
3. Check template_name in view

### Context Missing

If `is_htmx_request` is not in context:
1. Ensure DualTemplateMixin is before other mixins
2. Call super().get_context_data(**kwargs)

### HTMX Not Working

If HTMX navigation breaks:
1. Check browser dev tools for HX-Request header
2. Verify django_htmx middleware is installed
3. Check HTMX version compatibility

## Next Steps

1. Start with high-traffic views (assessment form, client list)
2. Convert one module at a time
3. Add tests for dual template behavior
4. Remove redundant template selection code
5. Document any custom patterns discovered