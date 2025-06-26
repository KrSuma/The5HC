"""
Template tags for rendering form fields with Alpine.js attributes.
This allows us to maintain Django form validation while having full control
over the HTML output for Alpine.js integration.
"""
from django import template
from django.forms import BoundField
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def render_field(field, **attrs):
    """
    Render a form field with custom attributes, including Alpine.js directives.
    
    Usage:
        {% render_field form.overhead_squat_score x-model="overheadSquatScore" @change="calculateScore()" %}
    """
    if not isinstance(field, BoundField):
        return ''
    
    # Get the widget and update its attributes
    widget = field.field.widget
    
    # Merge existing widget attrs with new attrs
    merged_attrs = widget.attrs.copy()
    merged_attrs.update(attrs)
    
    # Render the field with updated attributes
    rendered = field.as_widget(attrs=merged_attrs)
    return mark_safe(rendered)


@register.simple_tag
def field_value(field):
    """Get the current value of a form field."""
    if hasattr(field, 'value'):
        return field.value() or ''
    return ''


@register.simple_tag
def field_errors(field):
    """Render field errors in a consistent format."""
    if not field.errors:
        return ''
    
    error_html = '<div class="text-red-600 text-sm mt-1">'
    for error in field.errors:
        error_html += f'<p>{error}</p>'
    error_html += '</div>'
    
    return mark_safe(error_html)


@register.simple_tag
def render_select_field(field, alpine_model=None, alpine_change=None, alpine_class=None, **attrs):
    """
    Manually render a select field with Alpine.js attributes.
    This gives us full control over the HTML output.
    """
    if not isinstance(field, BoundField):
        return ''
    
    # Build attributes string
    attr_list = []
    
    # Add standard attributes
    attr_list.append(f'name="{field.html_name}"')
    attr_list.append(f'id="id_{field.html_name}"')
    
    # Add CSS classes
    css_classes = attrs.get('class', 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500')
    attr_list.append(f'class="{css_classes}"')
    
    # Add Alpine.js attributes
    if alpine_model:
        attr_list.append(f'x-model="{alpine_model}"')
    if alpine_change:
        attr_list.append(f'@change="{alpine_change}"')
    if alpine_class:
        attr_list.append(f':class="{alpine_class}"')
    
    # Add any other attributes
    for key, value in attrs.items():
        if key not in ['class']:  # Already handled
            attr_list.append(f'{key}="{value}"')
    
    # Build options
    options_html = []
    current_value = field.value()
    
    for choice_value, choice_label in field.field.choices:
        selected = 'selected' if str(choice_value) == str(current_value) else ''
        if choice_value is None:
            options_html.append(f'<option value="" {selected}>{choice_label}</option>')
        else:
            options_html.append(f'<option value="{choice_value}" {selected}>{choice_label}</option>')
    
    # Build final HTML
    attrs_string = ' '.join(attr_list)
    options_string = '\n    '.join(options_html)
    
    html = f'''<select {attrs_string}>
    {options_string}
</select>'''
    
    return mark_safe(html)


@register.simple_tag  
def render_input_field(field, alpine_model=None, alpine_input=None, **attrs):
    """
    Manually render an input field with Alpine.js attributes.
    """
    if not isinstance(field, BoundField):
        return ''
    
    # Determine input type
    input_type = attrs.get('type', 'text')
    if hasattr(field.field.widget, 'input_type'):
        input_type = field.field.widget.input_type
    
    # Build attributes
    attr_list = []
    attr_list.append(f'type="{input_type}"')
    attr_list.append(f'name="{field.html_name}"')
    attr_list.append(f'id="id_{field.html_name}"')
    
    # Add value
    value = field.value() or ''
    if value:
        attr_list.append(f'value="{value}"')
    
    # Add CSS classes
    css_classes = attrs.get('class', 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500')
    attr_list.append(f'class="{css_classes}"')
    
    # Add Alpine.js attributes
    if alpine_model:
        attr_list.append(f'x-model="{alpine_model}"')
    if alpine_input:
        attr_list.append(f'@input="{alpine_input}"')
    
    # Add placeholder
    if 'placeholder' in attrs:
        attr_list.append(f'placeholder="{attrs["placeholder"]}"')
    
    # Add numeric constraints
    for attr in ['min', 'max', 'step']:
        if attr in attrs:
            attr_list.append(f'{attr}="{attrs[attr]}"')
    
    # Add any other attributes
    for key, value in attrs.items():
        if key not in ['class', 'type', 'placeholder', 'min', 'max', 'step']:
            attr_list.append(f'{key}="{value}"')
    
    attrs_string = ' '.join(attr_list)
    html = f'<input {attrs_string}>'
    
    return mark_safe(html)


@register.simple_tag
def render_checkbox_field(field, alpine_model=None, alpine_change=None, **attrs):
    """
    Manually render a checkbox field with Alpine.js attributes.
    """
    if not isinstance(field, BoundField):
        return ''
    
    # Build attributes
    attr_list = []
    attr_list.append('type="checkbox"')
    attr_list.append(f'name="{field.html_name}"')
    attr_list.append(f'id="id_{field.html_name}"')
    
    # Add checked state
    if field.value():
        attr_list.append('checked')
    
    # Add CSS classes
    css_classes = attrs.get('class', 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded')
    attr_list.append(f'class="{css_classes}"')
    
    # Add Alpine.js attributes
    if alpine_model:
        attr_list.append(f'x-model="{alpine_model}"')
    if alpine_change:
        attr_list.append(f'@change="{alpine_change}"')
    
    attrs_string = ' '.join(attr_list)
    html = f'<input {attrs_string}>'
    
    return mark_safe(html)