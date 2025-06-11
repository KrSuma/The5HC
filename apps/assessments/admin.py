from django.contrib import admin
from .models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Assessment model.
    """
    list_display = [
        'client', 'trainer', 'date', 'overall_score', 
        'strength_score', 'mobility_score', 'balance_score', 
        'cardio_score', 'created_at'
    ]
    list_filter = [
        'date', 'trainer', 'created_at', 'overall_score'
    ]
    search_fields = ['client__name', 'trainer__username', 'trainer__email']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('client', 'trainer', 'date')
        }),
        ('Overhead Squat Test', {
            'fields': ('overhead_squat_score', 'overhead_squat_notes'),
            'classes': ('collapse',)
        }),
        ('Push-up Test', {
            'fields': ('push_up_reps', 'push_up_score', 'push_up_notes'),
            'classes': ('collapse',)
        }),
        ('Single Leg Balance Test', {
            'fields': (
                'single_leg_balance_right_eyes_open',
                'single_leg_balance_left_eyes_open',
                'single_leg_balance_right_eyes_closed',
                'single_leg_balance_left_eyes_closed',
                'single_leg_balance_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Toe Touch Test', {
            'fields': ('toe_touch_distance', 'toe_touch_score', 'toe_touch_notes'),
            'classes': ('collapse',)
        }),
        ('Shoulder Mobility Test', {
            'fields': (
                'shoulder_mobility_right',
                'shoulder_mobility_left',
                'shoulder_mobility_score',
                'shoulder_mobility_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Farmer\'s Carry Test', {
            'fields': (
                'farmer_carry_weight',
                'farmer_carry_distance',
                'farmer_carry_score',
                'farmer_carry_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Harvard Step Test', {
            'fields': (
                'harvard_step_test_heart_rate',
                'harvard_step_test_duration',
                'harvard_step_test_notes'
            ),
            'classes': ('collapse',)
        }),
        ('계산된 점수', {
            'fields': (
                'overall_score', 'strength_score', 'mobility_score',
                'balance_score', 'cardio_score'
            ),
            'description': '테스트 결과에 따라 자동으로 계산된 점수입니다.'
        }),
    )
    
    readonly_fields = [
        'created_at', 'overall_score', 'strength_score',
        'mobility_score', 'balance_score', 'cardio_score'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('client', 'trainer')
    
    def save_model(self, request, obj, form, change):
        """Override to ensure scores are calculated."""
        obj.save()
        
    class Media:
        css = {
            'all': ('admin/css/assessment_admin.css',)
        }
