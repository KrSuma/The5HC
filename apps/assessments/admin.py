from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction, models
import csv
import json
from .models import (
    Assessment, NormativeData, TestStandard,
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse
)


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


# MCQ Admin Classes

class QuestionChoiceInline(admin.TabularInline):
    """Inline admin for question choices."""
    model = QuestionChoice
    extra = 4  # Show 4 empty forms by default
    fields = ['choice_text', 'choice_text_ko', 'points', 'risk_factor', 'order', 'is_correct']
    ordering = ['order']


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Question Categories.
    """
    list_display = [
        'name_ko', 'name', 'weight', 'order', 
        'question_count', 'is_active', 'created'
    ]
    list_filter = ['is_active', 'created']
    search_fields = ['name', 'name_ko', 'description', 'description_ko']
    ordering = ['order', 'name']
    list_editable = ['weight', 'order', 'is_active']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'name_ko', 'order', 'is_active')
        }),
        ('설명', {
            'fields': ('description', 'description_ko')
        }),
        ('설정', {
            'fields': ('weight',),
            'description': '점수 계산 시 이 카테고리의 가중치 (0.0 ~ 1.0)'
        }),
    )
    
    def question_count(self, obj):
        """Count of active questions in this category."""
        return obj.questions.filter(is_active=True).count()
    question_count.short_description = "활성 질문 수"
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        return qs.annotate(
            active_question_count=models.Count(
                'questions',
                filter=models.Q(questions__is_active=True)
            )
        )


@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Multiple Choice Questions.
    Enhanced with import/export functionality.
    """
    list_display = [
        'question_text_ko_truncated', 'category', 'question_type', 
        'is_required', 'points', 'order', 'is_active', 'depends_on'
    ]
    list_filter = [
        'category', 'question_type', 'is_required', 'is_active',
        ('depends_on', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'question_text', 'question_text_ko', 'help_text', 'help_text_ko'
    ]
    ordering = ['category__order', 'order']
    list_editable = ['order', 'is_active', 'is_required']
    list_per_page = 50
    inlines = [QuestionChoiceInline]
    autocomplete_fields = ['depends_on']
    
    fieldsets = (
        ('질문 내용', {
            'fields': (
                'category', 'question_text', 'question_text_ko',
                'question_type', 'is_required', 'points', 'order'
            )
        }),
        ('도움말', {
            'fields': ('help_text', 'help_text_ko'),
            'classes': ('collapse',)
        }),
        ('조건부 표시', {
            'fields': ('depends_on', 'depends_on_answer'),
            'classes': ('collapse',),
            'description': '이 질문이 표시되려면 선행 질문의 특정 답변이 선택되어야 합니다.'
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
    )
    
    def question_text_ko_truncated(self, obj):
        """Truncated Korean question text for list display."""
        text = obj.question_text_ko or obj.question_text
        return text[:50] + '...' if len(text) > 50 else text
    question_text_ko_truncated.short_description = "질문"
    
    def get_urls(self):
        """Add custom URLs for import/export."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-csv/',
                self.admin_site.admin_view(self.import_csv_view),
                name='assessments_multiplechoicequestion_import_csv',
            ),
            path(
                'export-csv/',
                self.admin_site.admin_view(self.export_csv_view),
                name='assessments_multiplechoicequestion_export_csv',
            ),
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='assessments_multiplechoicequestion_import_json',
            ),
            path(
                'export-json/',
                self.admin_site.admin_view(self.export_json_view),
                name='assessments_multiplechoicequestion_export_json',
            ),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Add import/export buttons to changelist."""
        extra_context = extra_context or {}
        extra_context['has_import_export'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def import_csv_view(self, request):
        """Handle CSV import of questions."""
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            
            try:
                # Decode CSV file
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                imported_count = 0
                with transaction.atomic():
                    for row in reader:
                        # Get or create category
                        category, _ = QuestionCategory.objects.get_or_create(
                            name=row.get('category_name', 'General'),
                            defaults={
                                'name_ko': row.get('category_name_ko', '일반'),
                                'weight': float(row.get('category_weight', 0.25)),
                                'order': int(row.get('category_order', 0))
                            }
                        )
                        
                        # Create question
                        question = MultipleChoiceQuestion.objects.create(
                            category=category,
                            question_text=row['question_text'],
                            question_text_ko=row.get('question_text_ko', row['question_text']),
                            question_type=row.get('question_type', 'single'),
                            is_required=row.get('is_required', 'True').lower() == 'true',
                            points=int(row.get('points', 1)),
                            help_text=row.get('help_text', ''),
                            help_text_ko=row.get('help_text_ko', ''),
                            order=int(row.get('order', 0)),
                            is_active=row.get('is_active', 'True').lower() == 'true'
                        )
                        
                        # Import choices if present
                        for i in range(1, 6):  # Support up to 5 choices
                            choice_text = row.get(f'choice_{i}_text')
                            if choice_text:
                                QuestionChoice.objects.create(
                                    question=question,
                                    choice_text=choice_text,
                                    choice_text_ko=row.get(f'choice_{i}_text_ko', choice_text),
                                    points=int(row.get(f'choice_{i}_points', 0)),
                                    risk_factor=row.get(f'choice_{i}_risk_factor', ''),
                                    order=i,
                                    is_correct=row.get(f'choice_{i}_is_correct', 'False').lower() == 'true'
                                )
                        
                        imported_count += 1
                
                messages.success(request, f'{imported_count}개의 질문을 성공적으로 가져왔습니다.')
                return redirect('admin:assessments_multiplechoicequestion_changelist')
                
            except Exception as e:
                messages.error(request, f'CSV 가져오기 중 오류 발생: {str(e)}')
        
        context = {
            'title': 'CSV 질문 가져오기',
            'opts': self.model._meta,
        }
        return render(request, 'admin/mcq_import.html', context)
    
    def export_csv_view(self, request):
        """Export questions as CSV."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="mcq_questions.csv"'
        response.write('\ufeff')  # UTF-8 BOM for Excel
        
        writer = csv.writer(response)
        
        # Header row
        headers = [
            'category_name', 'category_name_ko', 'category_weight', 'category_order',
            'question_text', 'question_text_ko', 'question_type',
            'is_required', 'points', 'help_text', 'help_text_ko',
            'order', 'is_active'
        ]
        
        # Add choice headers
        for i in range(1, 6):
            headers.extend([
                f'choice_{i}_text', f'choice_{i}_text_ko', 
                f'choice_{i}_points', f'choice_{i}_risk_factor',
                f'choice_{i}_is_correct'
            ])
        
        writer.writerow(headers)
        
        # Export questions
        questions = MultipleChoiceQuestion.objects.select_related(
            'category'
        ).prefetch_related('choices').order_by('category__order', 'order')
        
        for question in questions:
            row = [
                question.category.name,
                question.category.name_ko,
                float(question.category.weight),
                question.category.order,
                question.question_text,
                question.question_text_ko,
                question.question_type,
                question.is_required,
                question.points,
                question.help_text,
                question.help_text_ko,
                question.order,
                question.is_active
            ]
            
            # Add choices
            choices = list(question.choices.order_by('order'))
            for i in range(5):
                if i < len(choices):
                    choice = choices[i]
                    row.extend([
                        choice.choice_text,
                        choice.choice_text_ko,
                        choice.points,
                        choice.risk_factor,
                        choice.is_correct
                    ])
                else:
                    row.extend(['', '', '', '', ''])
            
            writer.writerow(row)
        
        return response
    
    def import_json_view(self, request):
        """Handle JSON import of questions."""
        if request.method == 'POST' and request.FILES.get('json_file'):
            json_file = request.FILES['json_file']
            
            try:
                # Parse JSON file
                data = json.load(json_file)
                
                imported_count = 0
                with transaction.atomic():
                    for item in data:
                        # Get or create category
                        cat_data = item.get('category', {})
                        category, _ = QuestionCategory.objects.get_or_create(
                            name=cat_data.get('name', 'General'),
                            defaults={
                                'name_ko': cat_data.get('name_ko', '일반'),
                                'weight': cat_data.get('weight', 0.25),
                                'order': cat_data.get('order', 0)
                            }
                        )
                        
                        # Create question
                        question = MultipleChoiceQuestion.objects.create(
                            category=category,
                            question_text=item['question_text'],
                            question_text_ko=item.get('question_text_ko', item['question_text']),
                            question_type=item.get('question_type', 'single'),
                            is_required=item.get('is_required', True),
                            points=item.get('points', 1),
                            help_text=item.get('help_text', ''),
                            help_text_ko=item.get('help_text_ko', ''),
                            order=item.get('order', 0),
                            is_active=item.get('is_active', True)
                        )
                        
                        # Import choices
                        for choice_data in item.get('choices', []):
                            QuestionChoice.objects.create(
                                question=question,
                                choice_text=choice_data['choice_text'],
                                choice_text_ko=choice_data.get('choice_text_ko', choice_data['choice_text']),
                                points=choice_data.get('points', 0),
                                risk_factor=choice_data.get('risk_factor', ''),
                                order=choice_data.get('order', 0),
                                is_correct=choice_data.get('is_correct', False)
                            )
                        
                        imported_count += 1
                
                messages.success(request, f'{imported_count}개의 질문을 성공적으로 가져왔습니다.')
                return redirect('admin:assessments_multiplechoicequestion_changelist')
                
            except Exception as e:
                messages.error(request, f'JSON 가져오기 중 오류 발생: {str(e)}')
        
        context = {
            'title': 'JSON 질문 가져오기',
            'opts': self.model._meta,
        }
        return render(request, 'admin/mcq_import.html', context)
    
    def export_json_view(self, request):
        """Export questions as JSON."""
        questions = MultipleChoiceQuestion.objects.select_related(
            'category'
        ).prefetch_related('choices').order_by('category__order', 'order')
        
        data = []
        for question in questions:
            choices = []
            for choice in question.choices.order_by('order'):
                choices.append({
                    'choice_text': choice.choice_text,
                    'choice_text_ko': choice.choice_text_ko,
                    'points': choice.points,
                    'risk_factor': choice.risk_factor,
                    'order': choice.order,
                    'is_correct': choice.is_correct
                })
            
            data.append({
                'category': {
                    'name': question.category.name,
                    'name_ko': question.category.name_ko,
                    'weight': float(question.category.weight),
                    'order': question.category.order
                },
                'question_text': question.question_text,
                'question_text_ko': question.question_text_ko,
                'question_type': question.question_type,
                'is_required': question.is_required,
                'points': question.points,
                'help_text': question.help_text,
                'help_text_ko': question.help_text_ko,
                'order': question.order,
                'is_active': question.is_active,
                'choices': choices
            })
        
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="mcq_questions.json"'
        return response
    
    actions = [
        'duplicate_questions', 'activate_questions', 'deactivate_questions',
        'bulk_change_category', 'bulk_change_required'
    ]
    
    def duplicate_questions(self, request, queryset):
        """Duplicate selected questions."""
        duplicated = 0
        for question in queryset:
            # Store original data
            original_id = question.id
            original_text = question.question_text_ko
            choices = list(question.choices.all())
            
            # Create duplicate
            question.pk = None
            question.question_text_ko = f"{original_text} (복사본)"
            question.is_active = False
            question.save()
            
            # Duplicate choices
            for choice in choices:
                choice.pk = None
                choice.question = question
                choice.save()
            
            duplicated += 1
        
        messages.success(request, f'{duplicated}개의 질문이 복사되었습니다.')
    duplicate_questions.short_description = "선택된 질문 복사"
    
    def activate_questions(self, request, queryset):
        """Activate selected questions."""
        updated = queryset.update(is_active=True)
        messages.success(request, f'{updated}개의 질문이 활성화되었습니다.')
    activate_questions.short_description = "선택된 질문 활성화"
    
    def deactivate_questions(self, request, queryset):
        """Deactivate selected questions."""
        updated = queryset.update(is_active=False)
        messages.success(request, f'{updated}개의 질문이 비활성화되었습니다.')
    deactivate_questions.short_description = "선택된 질문 비활성화"
    
    def bulk_change_category(self, request, queryset):
        """Change category for selected questions."""
        # This would need a custom form - simplified for now
        if 'apply' in request.POST:
            category_id = request.POST.get('category')
            if category_id:
                category = QuestionCategory.objects.get(pk=category_id)
                updated = queryset.update(category=category)
                messages.success(request, f'{updated}개의 질문 카테고리가 변경되었습니다.')
            return redirect(request.get_full_path())
        
        categories = QuestionCategory.objects.filter(is_active=True)
        context = {
            'title': '카테고리 일괄 변경',
            'queryset': queryset,
            'categories': categories,
            'opts': self.model._meta,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }
        return render(request, 'admin/bulk_change_category.html', context)
    bulk_change_category.short_description = "카테고리 일괄 변경"
    
    def bulk_change_required(self, request, queryset):
        """Toggle required status for selected questions."""
        for question in queryset:
            question.is_required = not question.is_required
            question.save()
        
        messages.success(request, f'{queryset.count()}개의 질문 필수 여부가 변경되었습니다.')
    bulk_change_required.short_description = "필수 여부 토글"


@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    """
    Admin configuration for Question Responses.
    Read-only view for monitoring responses.
    """
    list_display = [
        'assessment_info', 'question_info', 'response_preview',
        'points_earned', 'created'
    ]
    list_filter = [
        'question__category', 'question__question_type',
        'created', 'assessment__trainer'
    ]
    search_fields = [
        'assessment__client__name', 'question__question_text_ko',
        'response_text'
    ]
    ordering = ['-created']
    date_hierarchy = 'created'
    
    readonly_fields = [
        'assessment', 'question', 'response_text', 'selected_choices',
        'points_earned', 'created', 'updated'
    ]
    
    def assessment_info(self, obj):
        """Display assessment info."""
        return f"{obj.assessment.client.name} - {obj.assessment.date}"
    assessment_info.short_description = "평가 정보"
    
    def question_info(self, obj):
        """Display question category and type."""
        return f"{obj.question.category.name_ko} - {obj.question.get_question_type_display()}"
    question_info.short_description = "질문 정보"
    
    def response_preview(self, obj):
        """Preview of the response."""
        if obj.response_text:
            return obj.response_text[:50] + '...' if len(obj.response_text) > 50 else obj.response_text
        elif obj.selected_choices.exists():
            choices = list(obj.selected_choices.values_list('choice_text_ko', flat=True))
            return ', '.join(choices[:3]) + ('...' if len(choices) > 3 else '')
        return '-'
    response_preview.short_description = "응답"
    
    def has_add_permission(self, request):
        """Disable add permission - responses are created via assessment flow."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission - responses should not be edited."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete responses."""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'assessment', 'assessment__client', 'assessment__trainer',
            'question', 'question__category'
        ).prefetch_related('selected_choices')
