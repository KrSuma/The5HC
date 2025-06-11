from django.contrib import admin
from .models import AssessmentReport


@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'report_type', 'generated_by', 'generated_at', 'file_size']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['assessment__client__name', 'assessment__client__email']
    readonly_fields = ['generated_at', 'file_size']
    date_hierarchy = 'generated_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assessment__client',
            'generated_by'
        )
