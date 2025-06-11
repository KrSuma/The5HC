from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin configuration for Client model.
    """
    list_display = [
        'name', 'age', 'gender', 'trainer', 'bmi', 'bmi_category', 
        'phone', 'email', 'created_at'
    ]
    list_filter = [
        'gender', 'trainer', 'created_at', 'age'
    ]
    search_fields = ['name', 'email', 'phone']
    ordering = ['-created_at', 'name']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('trainer', 'name', 'age', 'gender')
        }),
        ('신체 정보', {
            'fields': ('height', 'weight'),
            'description': 'Height in cm, Weight in kg'
        }),
        ('연락처 정보', {
            'fields': ('email', 'phone')
        }),
    )
    
    readonly_fields = ['created_at', 'bmi', 'bmi_category']
    
    def bmi(self, obj):
        """Display calculated BMI."""
        return obj.bmi
    bmi.short_description = 'BMI'
    
    def bmi_category(self, obj):
        """Display BMI category."""
        return obj.bmi_category
    bmi_category.short_description = 'BMI 카테고리'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('trainer')
