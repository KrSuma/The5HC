# Dual Template Migration Checklist

**Date**: 2025-06-25  
**Purpose**: Step-by-step guide for migrating existing views to use DualTemplateMixin

## Migration Overview

This checklist helps migrate from manual HTMX template handling to automatic handling via DualTemplateMixin.

## Pre-Migration Checklist

- [ ] Backup current code
- [ ] Identify all views with dual templates
- [ ] Test current functionality
- [ ] Review DualTemplateMixin documentation

## Step 1: Identify Views to Migrate

Run these commands to find candidates:

```bash
# Find all content templates
find templates -name "*_content.html" | sort

# Find views with manual HTMX checks
grep -r "HX-Request" apps/*/views.py
grep -r "_content.html" apps/*/views.py

# Find template_name assignments
grep -r "template_name =" apps/*/views.py
```

## Step 2: Add Core App

```python
# the5hc/settings/base.py
LOCAL_APPS = [
    'apps.core',  # Add this line
    'apps.accounts',
    'apps.trainers',
    # ... rest of apps
]
```

## Step 3: Convert Views

### Pattern 1: Simple Function View

**Before:**
```python
@login_required
def client_list_view(request):
    clients = Client.objects.all()
    
    # Manual template selection
    if request.headers.get('HX-Request'):
        template = 'clients/client_list_content.html'
    else:
        template = 'clients/client_list.html'
    
    return render(request, template, {'clients': clients})
```

**After:**
```python
from django.views.generic import ListView
from apps.core.mixins import DualTemplateMixin, TrainerFilterMixin

class ClientListView(TrainerFilterMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
```

### Pattern 2: Form View

**Before:**
```python
@login_required
def client_add_view(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.trainer = request.user
            client.save()
            messages.success(request, "고객이 등록되었습니다.")
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm()
    
    template = 'clients/client_form_content.html' if request.headers.get('HX-Request') else 'clients/client_form.html'
    return render(request, template, {'form': form})
```

**After:**
```python
from django.views.generic import CreateView
from apps.core.mixins import DualTemplateMixin, FormSuccessMessageMixin

class ClientCreateView(DualTemplateMixin, FormSuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_message = "고객이 등록되었습니다."
    
    def form_valid(self, form):
        form.instance.trainer = self.request.user
        return super().form_valid(form)
```

### Pattern 3: Delete View with HTMX

**Before:**
```python
@require_http_methods(['DELETE'])
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk, trainer=request.user)
    client.delete()
    
    response = HttpResponse()
    if request.headers.get('HX-Request'):
        response['HX-Redirect'] = reverse('clients:list')
    else:
        return redirect('clients:list')
    return response
```

**After:**
```python
from django.views.generic import DeleteView
from apps.core.mixins import DualTemplateMixin, HTMXResponseMixin

class ClientDeleteView(DualTemplateMixin, HTMXResponseMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return self.htmx_redirect(reverse('clients:list'))
```

## Step 4: Update URLs

**Before:**
```python
from . import views

urlpatterns = [
    path('', views.client_list_view, name='list'),
    path('add/', views.client_add_view, name='add'),
    path('<int:pk>/delete/', views.client_delete_view, name='delete'),
]
```

**After:**
```python
from . import views

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('add/', views.ClientCreateView.as_view(), name='add'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
]
```

## Step 5: Test Both Navigation Methods

Create test file for each migrated module:

```python
# apps/clients/test_dual_templates.py
from django.test import TestCase
from django.urls import reverse

class ClientDualTemplateTest(TestCase):
    def test_list_regular_request(self):
        response = self.client.get(reverse('clients:list'))
        self.assertTemplateUsed(response, 'clients/client_list.html')
    
    def test_list_htmx_request(self):
        response = self.client.get(
            reverse('clients:list'),
            HTTP_HX_REQUEST='true'
        )
        self.assertTemplateUsed(response, 'clients/client_list_content.html')
```

## Step 6: Clean Up

- [ ] Remove manual HTMX checks from views
- [ ] Remove duplicate template logic
- [ ] Update documentation
- [ ] Remove unused imports

## Common Issues and Solutions

### Issue: Template Not Found

**Solution**: Ensure content template exists and follows naming convention:
- Full: `template_name.html`
- Content: `template_name_content.html`

### Issue: Context Variables Missing

**Solution**: Ensure calling `super().get_context_data(**kwargs)`:
```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Add your context
    return context
```

### Issue: Permissions Not Working

**Solution**: Use proper mixin order (permissions first):
```python
class MyView(LoginRequiredMixin, PermissionMixin, DualTemplateMixin, UpdateView):
    # Correct order
```

### Issue: Forms Not Showing Messages

**Solution**: Include FormSuccessMessageMixin:
```python
class MyFormView(DualTemplateMixin, FormSuccessMessageMixin, CreateView):
    success_message = "저장되었습니다."
```

## Module-by-Module Migration Plan

### Phase 1: Core Views (Week 1)
- [ ] Clients module
- [ ] Assessments module
- [ ] Sessions module

### Phase 2: Supporting Views (Week 2)
- [ ] Reports module
- [ ] Analytics module
- [ ] API views (if applicable)

### Phase 3: Admin and Utilities (Week 3)
- [ ] Trainer management
- [ ] Admin customizations
- [ ] Helper views

## Verification Checklist

After migrating each module:

- [ ] All tests pass
- [ ] Direct URL navigation works
- [ ] HTMX navigation works
- [ ] Forms submit correctly
- [ ] Success messages appear
- [ ] Permissions enforced
- [ ] No duplicate templates needed
- [ ] Performance maintained

## Benefits After Migration

1. **No more template drift** - Can't forget to update one template
2. **Cleaner code** - No manual HTMX checks
3. **Consistent behavior** - All views handle HTMX the same way
4. **Easier testing** - Clear patterns for testing both modes
5. **Better maintainability** - New developers understand pattern immediately

## Next Steps

After completing migration:

1. Remove old function-based views
2. Update developer documentation
3. Create code review checklist
4. Set up linting rules
5. Train team on new patterns