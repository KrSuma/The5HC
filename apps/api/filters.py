"""
API filters for enhanced query capabilities.
"""

import django_filters
from django.db.models import Q

from apps.assessments.models import MultipleChoiceQuestion


class QuestionFilter(django_filters.FilterSet):
    """Filter for multiple choice questions."""
    
    category = django_filters.CharFilter(field_name='category__slug')
    type = django_filters.ChoiceFilter(
        field_name='question_type',
        choices=[
            ('single', 'Single Choice'),
            ('multiple', 'Multiple Choice'),
            ('scale', 'Scale'),
            ('text', 'Text')
        ]
    )
    required = django_filters.BooleanFilter(field_name='is_required')
    search = django_filters.CharFilter(method='search_filter')
    has_dependency = django_filters.BooleanFilter(
        method='filter_has_dependency',
        label='Has dependency'
    )
    
    class Meta:
        model = MultipleChoiceQuestion
        fields = ['category', 'type', 'required', 'search', 'has_dependency']
    
    def search_filter(self, queryset, name, value):
        """Search in question text and help text."""
        return queryset.filter(
            Q(question_text__icontains=value) |
            Q(question_text_ko__icontains=value) |
            Q(help_text__icontains=value) |
            Q(help_text_ko__icontains=value)
        )
    
    def filter_has_dependency(self, queryset, name, value):
        """Filter questions that have dependencies."""
        if value:
            return queryset.exclude(depends_on__isnull=True)
        else:
            return queryset.filter(depends_on__isnull=True)