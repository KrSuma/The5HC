"""
Forms for Multiple Choice Questions in assessments.
"""

from django import forms
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse
)


class MCQResponseForm(forms.Form):
    """Dynamic form for MCQ responses."""
    
    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop('assessment', None)
        self.category = kwargs.pop('category', None)
        self.questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)
        
        if self.questions:
            self._build_question_fields()
    
    def _build_question_fields(self):
        """Dynamically build form fields based on questions."""
        for question in self.questions:
            field_name = f'question_{question.id}'
            
            # Get choices for this question
            choices = [
                (choice.id, choice.choice_text_ko or choice.choice_text)
                for choice in question.choices.filter(is_active=True).order_by('order')
            ]
            
            # Create appropriate field based on question type
            if question.question_type == 'single':
                self.fields[field_name] = forms.ChoiceField(
                    label=question.question_text_ko or question.question_text,
                    choices=[('', '선택하세요')] + choices,
                    required=question.is_required,
                    widget=forms.RadioSelect(attrs={
                        'class': 'mcq-radio',
                        'x-model': f'responses.question_{question.id}',
                        '@change': 'validateResponse($event)',
                        'data-question-id': question.id,
                        'data-depends-on': question.depends_on_id or ''
                    }),
                    help_text=question.help_text_ko or question.help_text
                )
                
            elif question.question_type == 'multiple':
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.question_text_ko or question.question_text,
                    choices=choices,
                    required=question.is_required,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'mcq-checkbox',
                        'x-model': f'responses.question_{question.id}',
                        '@change': 'validateResponse($event)',
                        'data-question-id': question.id,
                        'data-depends-on': question.depends_on_id or ''
                    }),
                    help_text=question.help_text_ko or question.help_text
                )
                
            elif question.question_type == 'scale':
                # For scale questions, create a range of choices
                scale_choices = [(str(i), str(i)) for i in range(1, 6)]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.question_text_ko or question.question_text,
                    choices=scale_choices,
                    required=question.is_required,
                    widget=forms.RadioSelect(attrs={
                        'class': 'mcq-scale',
                        'x-model': f'responses.question_{question.id}',
                        '@change': 'validateResponse($event)',
                        'data-question-id': question.id,
                        'data-depends-on': question.depends_on_id or ''
                    }),
                    help_text=question.help_text_ko or question.help_text
                )
                
            elif question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.question_text_ko or question.question_text,
                    required=question.is_required,
                    widget=forms.Textarea(attrs={
                        'class': 'form-textarea',
                        'rows': 3,
                        'x-model': f'responses.question_{question.id}',
                        '@input': 'validateResponse($event)',
                        'data-question-id': question.id,
                        'data-depends-on': question.depends_on_id or '',
                        'placeholder': '답변을 입력하세요...'
                    }),
                    help_text=question.help_text_ko or question.help_text
                )
    
    def clean(self):
        """Validate form data and calculate points."""
        cleaned_data = super().clean()
        
        # Validate required fields based on dependencies
        for question in self.questions:
            field_name = f'question_{question.id}'
            
            # Check if question should be shown based on dependencies
            if question.depends_on:
                depends_field_name = f'question_{question.depends_on.id}'
                depends_value = cleaned_data.get(depends_field_name)
                
                # Parse show_when condition
                if question.show_when and depends_value:
                    # Simple evaluation for now - can be enhanced
                    if not self._evaluate_condition(question.show_when, depends_value):
                        # Question shouldn't be shown, skip validation
                        continue
            
            # Validate required questions
            if question.is_required and not cleaned_data.get(field_name):
                self.add_error(field_name, '이 항목은 필수입니다.')
        
        return cleaned_data
    
    def _evaluate_condition(self, condition, value):
        """Evaluate simple conditions for progressive disclosure."""
        # Simple implementation - can be enhanced for complex conditions
        # Format: "choice_id=123" or "points>5"
        if '=' in condition:
            expected_value = condition.split('=')[1].strip()
            return str(value) == expected_value
        elif '>' in condition:
            threshold = int(condition.split('>')[1].strip())
            # For this, we'd need to get the points of the selected choice
            return True  # Simplified for now
        return True
    
    def save(self):
        """Save responses to database."""
        if not self.assessment:
            raise ValueError("Assessment is required to save responses")
        
        responses = []
        
        for question in self.questions:
            field_name = f'question_{question.id}'
            value = self.cleaned_data.get(field_name)
            
            if value:
                # Check if response already exists
                response, created = QuestionResponse.objects.get_or_create(
                    assessment=self.assessment,
                    question=question,
                    defaults={'response_text': ''}
                )
                
                # Clear existing choices
                response.selected_choices.clear()
                
                # Handle different question types
                if question.question_type == 'text':
                    response.response_text = value
                elif question.question_type == 'multiple':
                    # Multiple choice - value is a list
                    choices = QuestionChoice.objects.filter(id__in=value)
                    response.selected_choices.set(choices)
                else:
                    # Single choice or scale
                    choice = QuestionChoice.objects.get(id=value)
                    response.selected_choices.add(choice)
                
                response.save()  # This triggers point calculation
                responses.append(response)
        
        return responses


class CategoryMCQFormSet(forms.Form):
    """Container form for managing multiple categories of MCQ forms."""
    
    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop('assessment', None)
        self.categories = kwargs.pop('categories', None)
        super().__init__(*args, **kwargs)
        
        # Create a form for each category
        self.category_forms = {}
        if self.categories:
            for category in self.categories:
                questions = MultipleChoiceQuestion.objects.filter(
                    category=category,
                    is_active=True
                ).order_by('order')
                
                if questions.exists():
                    form = MCQResponseForm(
                        data=self.data if self.is_bound else None,
                        assessment=self.assessment,
                        category=category,
                        questions=questions,
                        prefix=f'category_{category.id}'
                    )
                    self.category_forms[category.id] = form
    
    def is_valid(self):
        """Check if all category forms are valid."""
        valid = True
        for form in self.category_forms.values():
            if not form.is_valid():
                valid = False
        return valid
    
    def save(self):
        """Save all category forms."""
        all_responses = []
        for form in self.category_forms.values():
            responses = form.save()
            all_responses.extend(responses)
        return all_responses


class QuickMCQForm(forms.Form):
    """Simplified form for quick MCQ entry during assessment."""
    
    # Knowledge questions
    exercise_knowledge = forms.ChoiceField(
        label="운동 지식 수준",
        choices=[
            ('beginner', '초급 (운동 경험 1년 미만)'),
            ('intermediate', '중급 (운동 경험 1-3년)'),
            ('advanced', '고급 (운동 경험 3년 이상)'),
            ('expert', '전문가 (트레이너/선수 경력)')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    # Lifestyle questions
    sleep_hours = forms.ChoiceField(
        label="평균 수면 시간",
        choices=[
            ('less_5', '5시간 미만'),
            ('5_6', '5-6시간'),
            ('6_7', '6-7시간'),
            ('7_8', '7-8시간'),
            ('more_8', '8시간 이상')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    nutrition_quality = forms.ChoiceField(
        label="영양 관리 수준",
        choices=[
            ('poor', '관리 안함'),
            ('fair', '가끔 신경씀'),
            ('good', '규칙적 식사'),
            ('excellent', '체계적 관리')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    # Readiness questions
    motivation_level = forms.IntegerField(
        label="운동 동기 수준 (1-10)",
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'type': 'range',
            'min': '1',
            'max': '10'
        })
    )
    
    injury_history = forms.MultipleChoiceField(
        label="부상 이력 (해당사항 모두 선택)",
        choices=[
            ('none', '없음'),
            ('muscle', '근육 부상'),
            ('joint', '관절 부상'),
            ('spine', '척추 부상'),
            ('chronic', '만성 통증')
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop('assessment', None)
        super().__init__(*args, **kwargs)
    
    def save(self):
        """Convert quick form data to MCQ responses."""
        # This is a simplified version - in production, this would map
        # to actual MCQ questions in the database
        pass