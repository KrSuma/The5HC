# UI Consistency Guidelines for The5HC

**Created**: 2025-06-24
**Purpose**: Maintain visual consistency across all pages in The5HC application

## Management Page Layout Standards

All management pages (회원 관리, 평가 관리, 세션 관리, 트레이너, etc.) MUST follow these consistent patterns:

### 1. Container Structure
```html
<div class="container mx-auto px-4 py-8">
    <!-- Page content -->
</div>
```

**Requirements:**
- Use `container mx-auto` for proper max-width constraints
- Use `px-4` for horizontal padding (1rem)
- Use `py-8` for vertical padding (2rem)
- Do NOT use responsive padding variations like `sm:px-6 lg:px-8`

### 2. Page Headers
```html
<h1 class="text-3xl font-bold text-gray-800">페이지 제목</h1>
```

**Requirements:**
- Font size: `text-3xl` (30px)
- Font weight: `font-bold`
- Text color: `text-gray-800`
- Maintain consistency across ALL management pages

### 3. Common Layout Issues to Avoid

#### ❌ Incorrect Examples:
```html
<!-- Missing container -->
<div class="px-4 py-6 sm:px-6 lg:px-8">

<!-- Wrong font size -->
<h1 class="text-2xl font-semibold text-gray-900">트레이너</h1>

<!-- No container wrapper at all -->
<div id="main-content">
    <div class="mb-8">
```

#### ✅ Correct Example:
```html
{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="mb-8 flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-800">회원 관리</h1>
        <button class="...">새 회원 등록</button>
    </div>
    <!-- Rest of content -->
</div>
{% endblock %}
```

## Exceptions

### Form Pages
Form-specific pages may use narrower containers for better readability:
```html
<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
```
This is acceptable for forms that benefit from a narrower reading width.

## Verification Checklist

When creating or modifying management pages:

- [ ] Container uses `container mx-auto px-4 py-8`
- [ ] Main heading uses `text-3xl font-bold text-gray-800`
- [ ] Layout is consistent with other management pages
- [ ] No responsive padding variations unless specifically required
- [ ] Content is properly wrapped within the container

## Recent Fixes (2025-06-24)

Fixed inconsistencies in the following templates:
- `templates/sessions/package_list.html` - Added missing container wrapper
- `templates/sessions/session_list.html` - Added missing container wrapper
- `templates/trainers/trainer_list_content.html` - Fixed padding and font size
- `templates/trainers/trainer_detail_content.html` - Fixed padding
- `templates/trainers/trainer_form_content.html` - Fixed padding
- `templates/trainers/trainer_invite_content.html` - Added missing container wrapper

## Implementation Notes

1. When using HTMX partial templates, ensure the content template includes the container wrapper
2. Check both the main template and content template for consistency
3. Use browser developer tools to verify actual rendered spacing and sizes
4. Test responsive behavior to ensure consistent appearance across devices

## Related Documentation

- [HTMX Navigation Pattern](./HTMX_NAVIGATION_PATTERN.md) - For understanding template structure
- [Code Style Guidelines](./kb/code-style/guidelines.md) - For general coding standards