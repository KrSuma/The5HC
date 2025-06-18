from django.contrib import admin
from .models import Assessment, NormativeData, TestStandard


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


@admin.register(NormativeData)
class NormativeDataAdmin(admin.ModelAdmin):
    """
    Admin configuration for NormativeData model.
    """
    list_display = [
        'test_type', 'gender', 'age_range_display', 'percentile_50',
        'source', 'year', 'sample_size'
    ]
    list_filter = ['test_type', 'gender', 'source', 'year']
    search_fields = ['test_type', 'source', 'notes']
    ordering = ['test_type', 'gender', 'age_min']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('test_type', 'gender', 'age_min', 'age_max')
        }),
        ('백분위 데이터', {
            'fields': (
                'percentile_10', 'percentile_25', 'percentile_50',
                'percentile_75', 'percentile_90'
            )
        }),
        ('메타데이터', {
            'fields': ('source', 'year', 'sample_size', 'notes')
        }),
    )
    
    def age_range_display(self, obj):
        """Display age range in a readable format."""
        return f"{obj.age_min}-{obj.age_max}세"
    age_range_display.short_description = "연령 범위"


@admin.register(TestStandard)
class TestStandardAdmin(admin.ModelAdmin):
    """
    Admin configuration for TestStandard model.
    Enhanced with better usability features.
    """
    list_display = [
        'name', 'test_type', 'gender', 'age_range_display',
        'variation_type', 'conditions', 'threshold_display', 'is_active'
    ]
    list_filter = [
        'test_type', 'gender', 'metric_type', 'variation_type', 
        'is_active', 'source', 'year'
    ]
    search_fields = ['name', 'description', 'source']
    ordering = ['test_type', 'gender', 'age_min', 'variation_type']
    list_editable = ['is_active']  # Allow quick activation/deactivation
    list_per_page = 50  # Show more items per page
    
    fieldsets = (
        ('기본 정보', {
            'fields': (
                'name', 'test_type', 'gender', 'age_min', 'age_max',
                'metric_type', 'variation_type', 'conditions'
            )
        }),
        ('임계값 설정', {
            'fields': (
                'excellent_threshold', 'good_threshold', 
                'average_threshold', 'needs_improvement_threshold'
            ),
            'description': '점수 계산을 위한 기준값들입니다. 우수 > 양호 > 평균 > 개선필요 순서로 설정해주세요.'
        }),
        ('메타데이터', {
            'fields': ('description', 'source', 'year', 'is_active'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created', 'updated']
    
    def age_range_display(self, obj):
        """Display age range in a readable format."""
        return f"{obj.age_min}-{obj.age_max}세"
    age_range_display.short_description = "연령 범위"
    
    def threshold_display(self, obj):
        """Display thresholds in a compact format."""
        return f"{obj.excellent_threshold} / {obj.good_threshold} / {obj.average_threshold}"
    threshold_display.short_description = "임계값 (우수/양호/평균)"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related()
    
    actions = [
        'duplicate_standard', 'activate_standards', 'deactivate_standards',
        'test_standard_scoring', 'export_standards'
    ]
    
    def duplicate_standard(self, request, queryset):
        """Duplicate selected standards with a suffix."""
        duplicated_count = 0
        for standard in queryset:
            # Create a copy
            original_name = standard.name
            standard.pk = None
            standard.name = f"{original_name} (복사본)"
            standard.is_active = False
            try:
                standard.save()
                duplicated_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"'{original_name}' 복사 중 오류: {str(e)}",
                    level='ERROR'
                )
        
        if duplicated_count > 0:
            self.message_user(
                request,
                f"{duplicated_count}개의 기준이 복사되었습니다. 복사본은 비활성 상태입니다."
            )
    duplicate_standard.short_description = "선택된 기준 복사"
    
    def activate_standards(self, request, queryset):
        """Activate selected standards."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated}개의 기준이 활성화되었습니다.")
    activate_standards.short_description = "선택된 기준 활성화"
    
    def deactivate_standards(self, request, queryset):
        """Deactivate selected standards."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated}개의 기준이 비활성화되었습니다.")
    deactivate_standards.short_description = "선택된 기준 비활성화"
    
    def test_standard_scoring(self, request, queryset):
        """Test scoring with selected standards."""
        tested_count = 0
        results = []
        
        for standard in queryset:
            # Test with sample values
            test_values = [
                standard.excellent_threshold + 1,
                standard.good_threshold,
                standard.average_threshold,
                standard.needs_improvement_threshold
            ]
            
            for value in test_values:
                score = standard.get_score_for_value(value)
                grade = standard.get_grade_description(value)
                results.append(f"{standard.name}: 값 {value} → 점수 {score} ({grade})")
            
            tested_count += 1
        
        # Show results
        results_text = "\n".join(results[:20])  # Limit to first 20 results
        self.message_user(
            request,
            f"{tested_count}개 기준 테스트 완료:\n{results_text}",
            level='SUCCESS'
        )
    test_standard_scoring.short_description = "선택된 기준 점수 계산 테스트"
    
    def export_standards(self, request, queryset):
        """Export selected standards as CSV data."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="test_standards.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Test Type', 'Gender', 'Age Min', 'Age Max',
            'Metric Type', 'Variation Type', 'Conditions',
            'Excellent', 'Good', 'Average', 'Needs Improvement',
            'Source', 'Year', 'Active'
        ])
        
        for standard in queryset:
            writer.writerow([
                standard.name,
                standard.test_type,
                standard.gender,
                standard.age_min,
                standard.age_max,
                standard.metric_type,
                standard.variation_type or '',
                standard.conditions or '',
                standard.excellent_threshold,
                standard.good_threshold,
                standard.average_threshold,
                standard.needs_improvement_threshold,
                standard.source,
                standard.year,
                standard.is_active
            ])
        
        self.message_user(
            request,
            f"{queryset.count()}개의 기준을 CSV로 내보냈습니다."
        )
        
        return response
    export_standards.short_description = "선택된 기준 CSV 내보내기"
    
    def save_model(self, request, obj, form, change):
        """Override save to clear cache when standards are modified."""
        super().save_model(request, obj, form, change)
        
        # Clear related cache entries
        from django.core.cache import cache
        cache_pattern = f"test_standard_{obj.test_type}_*"
        # Note: In production, you might want to use a more sophisticated cache invalidation
        cache.clear()  # Clear all cache for simplicity
        
        if change:
            self.message_user(
                request,
                f"기준이 수정되었습니다. 관련 캐시가 초기화되었습니다.",
                level='INFO'
            )
