# Comprehensive Plan: Adding Multiple Choice Questions to The5HC Fitness Assessment System

## Overview

This document outlines a comprehensive plan to integrate multiple choice questions (MCQs) into The5HC Fitness Assessment System. The implementation will enhance the existing physical assessment tests with knowledge-based, lifestyle, and readiness evaluations to provide a more holistic fitness assessment.

## Table of Contents

1. [Phase 1: Database Schema Design](#phase-1-database-schema-design)
2. [Phase 2: Scoring System Integration](#phase-2-scoring-system-integration)
3. [Phase 3: Forms and UI Implementation](#phase-3-forms-and-ui-implementation)
4. [Phase 4: Templates and UI Components](#phase-4-templates-and-ui-components)
5. [Phase 5: API Implementation](#phase-5-api-implementation)
6. [Phase 6: Admin Interface](#phase-6-admin-interface)
7. [Phase 7: Management Commands](#phase-7-management-commands)
8. [Phase 8: Testing Implementation](#phase-8-testing-implementation)
9. [Phase 9: PDF Report Updates](#phase-9-pdf-report-updates)
10. [Phase 10: Migration and Deployment](#phase-10-migration-and-deployment)
11. [Scoring System Recommendation](#scoring-system-recommendation)

## Phase 1: Database Schema Design (2-3 days)

### 1.1 Create Multiple Choice Question Models

Create new models in `apps/assessments/models.py`:

```python
# Question Categories
class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    name_ko = models.CharField(max_length=100, help_text="Korean name")
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0, 
                                 help_text="Weight factor for scoring (0.0-1.0)")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Question Categories"

# Multiple Choice Questions
class MultipleChoiceQuestion(models.Model):
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('scale', 'Scale/Rating'),
    ]
    
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_text_ko = models.TextField(help_text="Korean translation")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    points = models.IntegerField(default=1, help_text="Maximum points for this question")
    is_required = models.BooleanField(default=True)
    help_text = models.TextField(blank=True)
    help_text_ko = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # For conditional questions
    depends_on = models.ForeignKey('self', null=True, blank=True, 
                                   on_delete=models.SET_NULL, 
                                   related_name='dependent_questions')
    depends_on_answer = models.ForeignKey('QuestionChoice', null=True, blank=True,
                                          on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['category', 'order', 'id']

# Answer Choices
class QuestionChoice(models.Model):
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE, 
                                related_name='choices')
    choice_text = models.CharField(max_length=200)
    choice_text_ko = models.CharField(max_length=200)
    points = models.IntegerField(default=0, help_text="Points awarded for this choice")
    is_correct = models.BooleanField(default=False, help_text="For knowledge questions")
    order = models.IntegerField(default=0)
    
    # Risk factors (similar to existing system)
    contributes_to_risk = models.BooleanField(default=False)
    risk_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    class Meta:
        ordering = ['order', 'id']

# User Responses
class QuestionResponse(models.Model):
    assessment = models.ForeignKey('Assessment', on_delete=models.CASCADE, 
                                  related_name='question_responses')
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(QuestionChoice)
    response_text = models.TextField(blank=True, help_text="For open-ended follow-ups")
    points_earned = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['assessment', 'question']
```

### 1.2 Update Assessment Model

Add fields to `apps/assessments/models.py`:

```python
class Assessment(models.Model):
    # ... existing fields ...
    
    # MCQ scoring fields
    knowledge_score = models.IntegerField(null=True, blank=True, 
                                         help_text="Score from knowledge questions (0-100)")
    lifestyle_score = models.IntegerField(null=True, blank=True,
                                         help_text="Score from lifestyle questions (0-100)")
    readiness_score = models.IntegerField(null=True, blank=True,
                                         help_text="Exercise readiness score (0-100)")
    
    # Composite scores
    comprehensive_score = models.IntegerField(null=True, blank=True,
                                            help_text="Combined physical + MCQ score (0-100)")
    
    def calculate_mcq_scores(self):
        """Calculate scores from multiple choice questions"""
        # Implementation in Phase 2
```

## Phase 2: Scoring System Integration (2 days)

### 2.1 Scoring Algorithm Design

Create a new scoring module `apps/assessments/scoring/mcq_scoring.py`:

```python
from decimal import Decimal
from django.core.cache import cache

class MCQScoringEngine:
    """Handles scoring for multiple choice questions"""
    
    def calculate_category_score(self, assessment, category):
        """Calculate score for a specific question category"""
        responses = assessment.question_responses.filter(
            question__category=category,
            question__is_active=True
        )
        
        if not responses.exists():
            return None
            
        total_points = 0
        max_points = 0
        
        for response in responses:
            total_points += response.points_earned
            max_points += response.question.points
            
        if max_points == 0:
            return 0
            
        # Apply category weight
        raw_score = (total_points / max_points) * 100
        weighted_score = raw_score * float(category.weight)
        
        return int(weighted_score)
    
    def calculate_comprehensive_score(self, assessment):
        """
        Combine physical assessment scores with MCQ scores
        
        Proposed weighting:
        - Physical tests: 60%
        - Knowledge questions: 15%
        - Lifestyle assessment: 15%
        - Readiness evaluation: 10%
        """
        weights = {
            'physical': 0.60,
            'knowledge': 0.15,
            'lifestyle': 0.15,
            'readiness': 0.10
        }
        
        scores = {
            'physical': assessment.total_score or 0,
            'knowledge': assessment.knowledge_score or 0,
            'lifestyle': assessment.lifestyle_score or 0,
            'readiness': assessment.readiness_score or 0
        }
        
        # Calculate weighted comprehensive score
        comprehensive = sum(scores[key] * weights[key] for key in scores)
        
        return int(comprehensive)
    
    def calculate_mcq_risk_factors(self, assessment):
        """Calculate additional risk factors from MCQ responses"""
        risk_factors = []
        
        responses = assessment.question_responses.select_related(
            'question'
        ).prefetch_related('selected_choices')
        
        for response in responses:
            for choice in response.selected_choices.filter(contributes_to_risk=True):
                risk_factors.append({
                    'factor': f"{response.question.question_text}: {choice.choice_text}",
                    'weight': float(choice.risk_weight)
                })
                
        return risk_factors
```

### 2.2 Integration with Existing Scoring

Update `apps/assessments/models.py`:

```python
def calculate_scores(self):
    """Enhanced to include MCQ scoring"""
    # Existing physical test scoring
    super().calculate_scores()
    
    # Calculate MCQ scores
    from .scoring.mcq_scoring import MCQScoringEngine
    mcq_engine = MCQScoringEngine()
    
    # Category-based scoring
    knowledge_cat = QuestionCategory.objects.filter(name='Knowledge').first()
    if knowledge_cat:
        self.knowledge_score = mcq_engine.calculate_category_score(self, knowledge_cat)
        
    lifestyle_cat = QuestionCategory.objects.filter(name='Lifestyle').first()
    if lifestyle_cat:
        self.lifestyle_score = mcq_engine.calculate_category_score(self, lifestyle_cat)
        
    readiness_cat = QuestionCategory.objects.filter(name='Readiness').first()
    if readiness_cat:
        self.readiness_score = mcq_engine.calculate_category_score(self, readiness_cat)
    
    # Calculate comprehensive score
    self.comprehensive_score = mcq_engine.calculate_comprehensive_score(self)
    
    # Add MCQ risk factors to existing risk assessment
    mcq_risks = mcq_engine.calculate_mcq_risk_factors(self)
    if hasattr(self, 'risk_factors') and self.risk_factors:
        self.risk_factors.extend(mcq_risks)
    
    self.save()
```

## Phase 3: Forms and UI Implementation (3-4 days)

### 3.1 Create MCQ Forms

Create `apps/assessments/forms/mcq_forms.py`:

```python
from django import forms
from django.forms import formset_factory
from django.utils.translation import get_language

class QuestionResponseForm(forms.Form):
    """Dynamic form for a single MCQ"""
    
    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if question:
            self.question = question
            
            if question.question_type == 'single':
                self.fields['answer'] = forms.ChoiceField(
                    label=question.question_text_ko if get_language() == 'ko' 
                          else question.question_text,
                    choices=[(c.id, c.choice_text_ko if get_language() == 'ko' 
                             else c.choice_text) 
                             for c in question.choices.all()],
                    widget=forms.RadioSelect(attrs={
                        'x-model': f'question_{question.id}',
                        'class': 'text-blue-600 focus:ring-blue-500'
                    }),
                    required=question.is_required,
                    help_text=question.help_text_ko if get_language() == 'ko' 
                              else question.help_text
                )
                
            elif question.question_type == 'multiple':
                self.fields['answer'] = forms.MultipleChoiceField(
                    label=question.question_text_ko if get_language() == 'ko' 
                          else question.question_text,
                    choices=[(c.id, c.choice_text_ko if get_language() == 'ko' 
                             else c.choice_text) 
                             for c in question.choices.all()],
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'x-model': f'question_{question.id}',
                        'class': 'rounded text-blue-600 focus:ring-blue-500'
                    }),
                    required=question.is_required
                )
                
            elif question.question_type == 'scale':
                # Rating scale (1-5 or 1-10)
                max_scale = question.choices.count()
                self.fields['answer'] = forms.ChoiceField(
                    label=question.question_text_ko if get_language() == 'ko' 
                          else question.question_text,
                    choices=[(str(i), str(i)) for i in range(1, max_scale + 1)],
                    widget=forms.RadioSelect(attrs={
                        'class': 'inline-flex',
                        'x-model': f'question_{question.id}'
                    }),
                    required=question.is_required
                )
```

### 3.2 Update Assessment Form

Modify `apps/assessments/forms.py`:

```python
class AssessmentForm(forms.ModelForm):
    # ... existing fields ...
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add dynamic MCQ fields
        self.mcq_forms = []
        categories = QuestionCategory.objects.filter(is_active=True)
        
        for category in categories:
            questions = MultipleChoiceQuestion.objects.filter(
                category=category,
                is_active=True
            ).select_related('category').prefetch_related('choices')
            
            for question in questions:
                form = QuestionResponseForm(
                    data=self.data if self.is_bound else None,
                    question=question,
                    prefix=f'mcq_{question.id}'
                )
                self.mcq_forms.append({
                    'category': category,
                    'question': question,
                    'form': form
                })
```

## Phase 4: Templates and UI Components (2-3 days)

### 4.1 Create MCQ Template Components

Create `templates/assessments/components/mcq_section.html`:

```html
<div class="mcq-section space-y-8" x-data="mcqHandler()">
    {% for category, questions in mcq_by_category.items %}
    <div class="bg-white shadow-sm rounded-lg p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
            {{ category.name_ko|default:category.name }}
        </h3>
        
        <div class="space-y-6">
            {% for item in questions %}
            <div class="question-item" 
                 {% if item.question.depends_on %}
                 x-show="shouldShowQuestion({{ item.question.id }}, {{ item.question.depends_on_id }}, {{ item.question.depends_on_answer_id }})"
                 x-transition
                 {% endif %}>
                 
                <div class="mb-3">
                    <label class="text-sm font-medium text-gray-700">
                        {{ item.form.answer.label }}
                        {% if item.question.is_required %}
                        <span class="text-red-500">*</span>
                        {% endif %}
                    </label>
                    
                    {% if item.form.answer.help_text %}
                    <p class="mt-1 text-sm text-gray-500">
                        {{ item.form.answer.help_text }}
                    </p>
                    {% endif %}
                </div>
                
                <div class="{% if item.question.question_type == 'scale' %}flex space-x-4{% else %}space-y-2{% endif %}">
                    {{ item.form.answer }}
                </div>
                
                {% if item.form.answer.errors %}
                <div class="mt-2 text-sm text-red-600">
                    {{ item.form.answer.errors }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
    
    <!-- Real-time score preview -->
    <div class="mt-6 p-4 bg-blue-50 rounded-lg" x-show="hasAnswers">
        <h4 class="text-sm font-medium text-blue-900">예상 점수</h4>
        <div class="mt-2 grid grid-cols-3 gap-4 text-sm">
            <div>
                <span class="text-gray-600">지식 평가:</span>
                <span class="font-medium" x-text="scores.knowledge + '%'"></span>
            </div>
            <div>
                <span class="text-gray-600">라이프스타일:</span>
                <span class="font-medium" x-text="scores.lifestyle + '%'"></span>
            </div>
            <div>
                <span class="text-gray-600">운동 준비도:</span>
                <span class="font-medium" x-text="scores.readiness + '%'"></span>
            </div>
        </div>
    </div>
</div>

<script>
function mcqHandler() {
    return {
        answers: {},
        scores: {
            knowledge: 0,
            lifestyle: 0,
            readiness: 0
        },
        
        get hasAnswers() {
            return Object.keys(this.answers).length > 0;
        },
        
        shouldShowQuestion(questionId, dependsOnId, dependsOnAnswerId) {
            if (!dependsOnId) return true;
            return this.answers[dependsOnId] == dependsOnAnswerId;
        },
        
        init() {
            // Listen for answer changes
            this.$watch('answers', () => {
                this.calculateScores();
            });
        },
        
        calculateScores() {
            // Client-side score calculation for preview
            // Actual calculation happens server-side
            // This is just for UX feedback
        }
    }
}
</script>
```

## Phase 5: API Implementation (2 days)

### 5.1 Create MCQ API Endpoints

Create `apps/api/views/mcq_views.py`:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class MultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for MCQs"""
    serializer_class = MultipleChoiceQuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MultipleChoiceQuestion.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('choices')
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get questions grouped by category"""
        categories = QuestionCategory.objects.filter(is_active=True)
        data = []
        
        for category in categories:
            questions = self.get_queryset().filter(category=category)
            data.append({
                'category': QuestionCategorySerializer(category).data,
                'questions': self.get_serializer(questions, many=True).data
            })
            
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def validate_responses(self, request):
        """Validate MCQ responses and calculate scores"""
        serializer = MCQResponseSerializer(data=request.data, many=True)
        if serializer.is_valid():
            scores = self.calculate_scores(serializer.validated_data)
            return Response(scores)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 5.2 Create Serializers

Create `apps/api/serializers/mcq_serializers.py`:

```python
from rest_framework import serializers
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse
)

class QuestionChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionChoice
        fields = ['id', 'choice_text', 'choice_text_ko', 'order', 'points']

class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    choices = QuestionChoiceSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MultipleChoiceQuestion
        fields = [
            'id', 'category', 'category_name', 'question_text', 
            'question_text_ko', 'question_type', 'points', 
            'is_required', 'help_text', 'help_text_ko', 
            'choices', 'depends_on', 'depends_on_answer'
        ]

class MCQResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_choice_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    
    def validate(self, attrs):
        question = MultipleChoiceQuestion.objects.get(id=attrs['question_id'])
        
        if question.question_type == 'single' and len(attrs['selected_choice_ids']) > 1:
            raise serializers.ValidationError(
                "Single choice questions can only have one answer"
            )
            
        # Validate choice IDs belong to the question
        valid_choices = question.choices.values_list('id', flat=True)
        for choice_id in attrs['selected_choice_ids']:
            if choice_id not in valid_choices:
                raise serializers.ValidationError(
                    f"Invalid choice ID: {choice_id}"
                )
                
        return attrs
```

## Phase 6: Admin Interface (1 day)

### 6.1 Create Admin Configuration

Create `apps/assessments/admin/mcq_admin.py`:

```python
from django.contrib import admin
from django.utils.html import format_html
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse
)

class QuestionChoiceInline(admin.TabularInline):
    model = QuestionChoice
    extra = 3
    fields = ['choice_text', 'choice_text_ko', 'points', 'is_correct', 
              'contributes_to_risk', 'risk_weight', 'order']

@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'category', 'question_type', 
                    'points', 'is_required', 'is_active', 'order']
    list_filter = ['category', 'question_type', 'is_required', 'is_active']
    search_fields = ['question_text', 'question_text_ko']
    inlines = [QuestionChoiceInline]
    
    fieldsets = (
        ('Question Content', {
            'fields': ('category', 'question_text', 'question_text_ko', 
                      'help_text', 'help_text_ko')
        }),
        ('Question Settings', {
            'fields': ('question_type', 'points', 'is_required', 
                      'order', 'is_active')
        }),
        ('Conditional Display', {
            'fields': ('depends_on', 'depends_on_answer'),
            'classes': ('collapse',)
        })
    )
    
    def question_preview(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.question_text,
            obj.question_text[:50] + '...' if len(obj.question_text) > 50 
            else obj.question_text
        )
    question_preview.short_description = 'Question'

@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_ko', 'weight', 'order', 'is_active']
    list_editable = ['weight', 'order', 'is_active']
```

## Phase 7: Management Commands (1 day)

### 7.1 Create Data Loading Commands

Create `apps/assessments/management/commands/load_mcq_questions.py`:

```python
from django.core.management.base import BaseCommand
from apps.assessments.models import QuestionCategory, MultipleChoiceQuestion, QuestionChoice

class Command(BaseCommand):
    help = 'Load default MCQ questions for assessments'
    
    def handle(self, *args, **options):
        # Create categories
        categories = [
            {
                'name': 'Knowledge',
                'name_ko': '지식 평가',
                'weight': 1.0,
                'description': 'Fitness and health knowledge assessment'
            },
            {
                'name': 'Lifestyle',
                'name_ko': '라이프스타일',
                'weight': 1.0,
                'description': 'Lifestyle and habits assessment'
            },
            {
                'name': 'Readiness',
                'name_ko': '운동 준비도',
                'weight': 1.0,
                'description': 'Exercise readiness evaluation'
            }
        ]
        
        for cat_data in categories:
            category, created = QuestionCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            
            if created:
                self.stdout.write(f"Created category: {category.name}")
                
        # Load sample questions
        self.load_knowledge_questions()
        self.load_lifestyle_questions()
        self.load_readiness_questions()
        
    def load_knowledge_questions(self):
        """Load fitness knowledge assessment questions"""
        category = QuestionCategory.objects.get(name='Knowledge')
        
        questions = [
            {
                'text': 'What is the recommended minimum weekly exercise for adults?',
                'text_ko': '성인의 권장 최소 주간 운동량은?',
                'type': 'single',
                'points': 2,
                'choices': [
                    {'text': '75 minutes of vigorous activity', 
                     'text_ko': '75분의 격렬한 활동', 'points': 1},
                    {'text': '150 minutes of moderate activity', 
                     'text_ko': '150분의 중간 강도 활동', 'points': 2, 'is_correct': True},
                    {'text': '30 minutes daily', 
                     'text_ko': '매일 30분', 'points': 1},
                    {'text': 'No specific recommendation', 
                     'text_ko': '특정 권장사항 없음', 'points': 0}
                ]
            },
            {
                'text': 'Which nutrient is most important for muscle recovery?',
                'text_ko': '근육 회복에 가장 중요한 영양소는?',
                'type': 'single',
                'points': 2,
                'choices': [
                    {'text': 'Carbohydrates', 'text_ko': '탄수화물', 'points': 1},
                    {'text': 'Protein', 'text_ko': '단백질', 'points': 2, 'is_correct': True},
                    {'text': 'Fat', 'text_ko': '지방', 'points': 0},
                    {'text': 'Vitamins', 'text_ko': '비타민', 'points': 1}
                ]
            }
        ]
        
        self.create_questions(category, questions)
        
    def load_lifestyle_questions(self):
        """Load lifestyle assessment questions"""
        category = QuestionCategory.objects.get(name='Lifestyle')
        
        questions = [
            {
                'text': 'How many hours of sleep do you get on average?',
                'text_ko': '평균 수면 시간은?',
                'type': 'single',
                'points': 5,
                'choices': [
                    {'text': 'Less than 5 hours', 'text_ko': '5시간 미만', 
                     'points': 0, 'contributes_to_risk': True, 'risk_weight': 0.3},
                    {'text': '5-6 hours', 'text_ko': '5-6시간', 
                     'points': 2, 'contributes_to_risk': True, 'risk_weight': 0.2},
                    {'text': '7-8 hours', 'text_ko': '7-8시간', 'points': 5},
                    {'text': 'More than 9 hours', 'text_ko': '9시간 이상', 'points': 3}
                ]
            },
            {
                'text': 'How would you rate your current stress level?',
                'text_ko': '현재 스트레스 수준은?',
                'type': 'scale',
                'points': 5,
                'help_text': '1 = Very Low, 5 = Very High',
                'help_text_ko': '1 = 매우 낮음, 5 = 매우 높음'
            }
        ]
        
        self.create_questions(category, questions)
        
    def load_readiness_questions(self):
        """Load exercise readiness questions"""
        category = QuestionCategory.objects.get(name='Readiness')
        
        questions = [
            {
                'text': 'Do you currently have any injuries or pain?',
                'text_ko': '현재 부상이나 통증이 있습니까?',
                'type': 'single',
                'points': 5,
                'choices': [
                    {'text': 'No pain or injuries', 'text_ko': '통증이나 부상 없음', 
                     'points': 5},
                    {'text': 'Minor discomfort', 'text_ko': '경미한 불편함', 
                     'points': 3, 'contributes_to_risk': True, 'risk_weight': 0.2},
                    {'text': 'Moderate pain', 'text_ko': '중간 정도의 통증', 
                     'points': 1, 'contributes_to_risk': True, 'risk_weight': 0.4},
                    {'text': 'Severe pain/injury', 'text_ko': '심한 통증/부상', 
                     'points': 0, 'contributes_to_risk': True, 'risk_weight': 0.6}
                ]
            }
        ]
        
        self.create_questions(category, questions)
        
    def create_questions(self, category, questions_data):
        """Helper method to create questions and choices"""
        for q_data in questions_data:
            question = MultipleChoiceQuestion.objects.create(
                category=category,
                question_text=q_data['text'],
                question_text_ko=q_data['text_ko'],
                question_type=q_data['type'],
                points=q_data['points'],
                help_text=q_data.get('help_text', ''),
                help_text_ko=q_data.get('help_text_ko', '')
            )
            
            if 'choices' in q_data:
                for idx, choice_data in enumerate(q_data['choices']):
                    QuestionChoice.objects.create(
                        question=question,
                        choice_text=choice_data['text'],
                        choice_text_ko=choice_data['text_ko'],
                        points=choice_data.get('points', 0),
                        is_correct=choice_data.get('is_correct', False),
                        contributes_to_risk=choice_data.get('contributes_to_risk', False),
                        risk_weight=choice_data.get('risk_weight', 0.0),
                        order=idx
                    )
            
            self.stdout.write(f"Created question: {question.question_text}")
```

## Phase 8: Testing Implementation (2 days)

### 8.1 Create Comprehensive Tests

Create `tests/test_mcq_system.py`:

```python
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.assessments.models import (
    MultipleChoiceQuestion, QuestionChoice, 
    QuestionResponse, Assessment, QuestionCategory
)
from apps.trainers.models import Trainer, Organization
from apps.clients.models import Client

User = get_user_model()

class MCQScoringTestCase(TestCase):
    """Test MCQ scoring functionality"""
    
    def setUp(self):
        # Create test data
        self.organization = Organization.objects.create(
            name="Test Org",
            slug="test-org"
        )
        
        self.user = User.objects.create_user(
            username="trainer1",
            email="trainer@test.com",
            password="testpass123"
        )
        
        self.trainer = Trainer.objects.create(
            user=self.user,
            organization=self.organization,
            role='trainer'
        )
        
        self.client = Client.objects.create(
            trainer=self.trainer,
            name="Test Client",
            email="client@test.com"
        )
        
        self.category = QuestionCategory.objects.create(
            name='Test Category',
            weight=1.0
        )
        
        self.question = MultipleChoiceQuestion.objects.create(
            category=self.category,
            question_text='Test question',
            question_type='single',
            points=5
        )
        
        self.correct_choice = QuestionChoice.objects.create(
            question=self.question,
            choice_text='Correct answer',
            points=5,
            is_correct=True
        )
        
        self.wrong_choice = QuestionChoice.objects.create(
            question=self.question,
            choice_text='Wrong answer',
            points=0,
            is_correct=False
        )
        
    def test_single_choice_scoring(self):
        """Test scoring for single choice questions"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer
        )
        
        response = QuestionResponse.objects.create(
            assessment=assessment,
            question=self.question,
            points_earned=5
        )
        response.selected_choices.add(self.correct_choice)
        
        # Calculate scores
        from apps.assessments.scoring.mcq_scoring import MCQScoringEngine
        engine = MCQScoringEngine()
        
        score = engine.calculate_category_score(assessment, self.category)
        self.assertEqual(score, 100)  # Perfect score
        
    def test_comprehensive_score_calculation(self):
        """Test combined physical and MCQ scoring"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer,
            total_score=80,  # Physical score
            knowledge_score=90,
            lifestyle_score=70,
            readiness_score=85
        )
        
        from apps.assessments.scoring.mcq_scoring import MCQScoringEngine
        engine = MCQScoringEngine()
        
        comprehensive = engine.calculate_comprehensive_score(assessment)
        
        # Expected: (80*0.6) + (90*0.15) + (70*0.15) + (85*0.1) = 80.5
        self.assertEqual(comprehensive, 80)
        
    def test_risk_factor_extraction(self):
        """Test extraction of risk factors from MCQ responses"""
        assessment = Assessment.objects.create(
            client=self.client,
            trainer=self.trainer
        )
        
        # Create a risk choice
        risk_choice = QuestionChoice.objects.create(
            question=self.question,
            choice_text='High risk choice',
            points=0,
            contributes_to_risk=True,
            risk_weight=0.5
        )
        
        response = QuestionResponse.objects.create(
            assessment=assessment,
            question=self.question
        )
        response.selected_choices.add(risk_choice)
        
        from apps.assessments.scoring.mcq_scoring import MCQScoringEngine
        engine = MCQScoringEngine()
        
        risk_factors = engine.calculate_mcq_risk_factors(assessment)
        
        self.assertEqual(len(risk_factors), 1)
        self.assertEqual(risk_factors[0]['weight'], 0.5)

@pytest.mark.django_db
class TestMCQAPI:
    """Test MCQ API endpoints"""
    
    def test_get_questions_by_category(self, api_client, trainer):
        """Test retrieving questions grouped by category"""
        api_client.force_authenticate(user=trainer.user)
        
        response = api_client.get('/api/v1/mcq/by-category/')
        assert response.status_code == 200
        
    def test_validate_responses(self, api_client, trainer):
        """Test MCQ response validation"""
        api_client.force_authenticate(user=trainer.user)
        
        # Create test question
        category = QuestionCategory.objects.create(name='Test')
        question = MultipleChoiceQuestion.objects.create(
            category=category,
            question_text='Test',
            question_type='single'
        )
        choice = QuestionChoice.objects.create(
            question=question,
            choice_text='Answer'
        )
        
        data = [{
            'question_id': question.id,
            'selected_choice_ids': [choice.id]
        }]
        
        response = api_client.post('/api/v1/mcq/validate-responses/', data)
        assert response.status_code == 200

class TestMCQForms(TestCase):
    """Test MCQ form functionality"""
    
    def test_question_response_form_single_choice(self):
        """Test single choice question form"""
        from apps.assessments.forms.mcq_forms import QuestionResponseForm
        
        category = QuestionCategory.objects.create(name='Test')
        question = MultipleChoiceQuestion.objects.create(
            category=category,
            question_text='Test question',
            question_type='single'
        )
        
        choice1 = QuestionChoice.objects.create(
            question=question,
            choice_text='Choice 1'
        )
        choice2 = QuestionChoice.objects.create(
            question=question,
            choice_text='Choice 2'
        )
        
        form = QuestionResponseForm(
            data={'answer': choice1.id},
            question=question
        )
        
        self.assertTrue(form.is_valid())
        
    def test_question_response_form_multiple_choice(self):
        """Test multiple choice question form"""
        from apps.assessments.forms.mcq_forms import QuestionResponseForm
        
        category = QuestionCategory.objects.create(name='Test')
        question = MultipleChoiceQuestion.objects.create(
            category=category,
            question_text='Test question',
            question_type='multiple'
        )
        
        choice1 = QuestionChoice.objects.create(
            question=question,
            choice_text='Choice 1'
        )
        choice2 = QuestionChoice.objects.create(
            question=question,
            choice_text='Choice 2'
        )
        
        form = QuestionResponseForm(
            data={'answer': [choice1.id, choice2.id]},
            question=question
        )
        
        self.assertTrue(form.is_valid())
```

## Phase 9: PDF Report Updates (1 day)

### 9.1 Update Report Generation

Modify `apps/reports/services.py`:

```python
def generate_assessment_report(assessment):
    """Enhanced to include MCQ results"""
    
    # Existing report generation code...
    
    # Add MCQ section
    context['mcq_scores'] = {
        'knowledge': assessment.knowledge_score,
        'lifestyle': assessment.lifestyle_score,
        'readiness': assessment.readiness_score,
        'comprehensive': assessment.comprehensive_score
    }
    
    # Get MCQ responses for detailed report
    context['mcq_responses'] = assessment.question_responses.select_related(
        'question__category'
    ).prefetch_related('selected_choices').order_by(
        'question__category__order', 'question__order'
    )
    
    # Group responses by category
    mcq_by_category = {}
    for response in context['mcq_responses']:
        category = response.question.category
        if category not in mcq_by_category:
            mcq_by_category[category] = []
        mcq_by_category[category].append(response)
    
    context['mcq_by_category'] = mcq_by_category
    
    return render_to_pdf('reports/assessment_report.html', context)
```

### 9.2 Update Report Template

Add to `templates/reports/assessment_report.html`:

```html
<!-- MCQ Results Section -->
<div class="mcq-results-section">
    <h2>종합 평가 결과</h2>
    
    <!-- Score Summary -->
    <div class="score-summary">
        <h3>점수 요약</h3>
        <table class="scores-table">
            <tr>
                <td>신체 평가:</td>
                <td>{{ assessment.total_score }}%</td>
            </tr>
            <tr>
                <td>지식 평가:</td>
                <td>{{ mcq_scores.knowledge }}%</td>
            </tr>
            <tr>
                <td>라이프스타일:</td>
                <td>{{ mcq_scores.lifestyle }}%</td>
            </tr>
            <tr>
                <td>운동 준비도:</td>
                <td>{{ mcq_scores.readiness }}%</td>
            </tr>
            <tr class="total-row">
                <td>종합 점수:</td>
                <td>{{ mcq_scores.comprehensive }}%</td>
            </tr>
        </table>
    </div>
    
    <!-- Detailed MCQ Responses -->
    <div class="mcq-responses">
        <h3>상세 응답</h3>
        {% for category, responses in mcq_by_category.items %}
        <div class="category-section">
            <h4>{{ category.name_ko|default:category.name }}</h4>
            {% for response in responses %}
            <div class="question-response">
                <p class="question">{{ response.question.question_text_ko }}</p>
                <p class="answer">
                    {% for choice in response.selected_choices.all %}
                    • {{ choice.choice_text_ko }}<br>
                    {% endfor %}
                </p>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
</div>
```

## Phase 10: Migration and Deployment (1 day)

### 10.1 Create and Apply Migrations

```bash
# Create migrations
python manage.py makemigrations assessments

# Test migrations locally
python manage.py migrate --fake

# Apply migrations
python manage.py migrate

# Load initial MCQ data
python manage.py load_mcq_questions

# Test the system
python manage.py runserver
```

### 10.2 Update Requirements and Deploy

No new dependencies are needed as the implementation uses existing Django and Django REST Framework features.

### 10.3 Deployment Steps

```bash
# Commit changes
git add .
git commit -m "Add multiple choice questions to assessment system"

# Push to Heroku
git push heroku main

# Run migrations on production
heroku run python manage.py migrate

# Load MCQ data on production
heroku run python manage.py load_mcq_questions

# Verify deployment
heroku logs --tail
```

## Scoring System Recommendation

### Proposed Scoring Structure

The comprehensive scoring system integrates physical assessments with knowledge-based evaluations:

1. **Physical Assessment (60%)** - Existing fitness tests
   - Movement quality scores
   - Performance metrics
   - Injury risk assessment

2. **Knowledge Assessment (15%)** - Understanding of fitness principles
   - Exercise form and technique
   - Nutrition basics
   - Recovery principles
   - Injury prevention

3. **Lifestyle Assessment (15%)** - Daily habits and health factors
   - Sleep quality and duration
   - Stress management
   - Dietary habits
   - Hydration
   - Physical activity outside training

4. **Readiness Assessment (10%)** - Current state evaluation
   - Current pain or discomfort levels
   - Recovery status
   - Mental readiness
   - Time availability
   - Motivation levels

### Benefits of This Integrated Approach

1. **Comprehensive Client Evaluation**
   - 360-degree view of client fitness
   - Identifies gaps in knowledge that may limit progress
   - Captures lifestyle factors affecting performance

2. **Enhanced Risk Assessment**
   - MCQs identify lifestyle risk factors
   - Combines with physical assessment for complete risk profile
   - Enables preventive interventions

3. **Personalized Programming**
   - Better data for customized fitness plans
   - Identifies education needs alongside physical training
   - Targets lifestyle modifications

4. **Progress Tracking**
   - Multiple dimensions to track improvement
   - Shows progress beyond physical metrics
   - Motivates clients through knowledge gains

5. **Client Engagement**
   - Interactive assessment increases buy-in
   - Educational component empowers clients
   - Regular reassessment shows holistic progress

### Implementation Timeline

- **Week 1**: Database schema and core models (Phases 1-2)
- **Week 2**: Forms, UI, and API implementation (Phases 3-5)
- **Week 3**: Admin, testing, and reporting (Phases 6-9)
- **Week 4**: Final testing, deployment, and training (Phase 10)

### Post-Implementation Considerations

1. **Trainer Training**
   - Create documentation for trainers
   - Provide sample questions and scoring guidelines
   - Train on interpreting comprehensive scores

2. **Question Bank Expansion**
   - Regularly add new questions
   - Update based on latest fitness research
   - Customize for different client populations

3. **Analytics and Insights**
   - Track common knowledge gaps
   - Identify lifestyle patterns affecting performance
   - Generate population-level insights

4. **Client Communication**
   - Create client-friendly score explanations
   - Develop educational materials based on gaps
   - Regular progress reports including all dimensions

This comprehensive MCQ system will transform The5HC from a physical assessment tool into a complete fitness evaluation platform, providing trainers with unprecedented insights into their clients' overall fitness readiness and needs.