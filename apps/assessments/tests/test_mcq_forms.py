"""
Tests for MCQ forms and form processing.

Tests the MCQResponseForm and related form functionality.
"""

import pytest
from django.test import RequestFactory
from apps.assessments.forms.mcq_forms import MCQResponseForm
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory
)


@pytest.mark.django_db
class TestMCQResponseForm:
    """Test cases for MCQ response form."""
    
    def test_form_initialization_empty(self):
        """Test form initialization with no questions."""
        assessment = AssessmentFactory()
        form = MCQResponseForm(assessment=assessment)
        
        assert form.assessment == assessment
        assert len(form.fields) == 0
    
    def test_form_initialization_with_questions(self):
        """Test form initialization with questions."""
        assessment = AssessmentFactory()
        
        # Create categories and questions
        knowledge_cat = QuestionCategoryFactory(name="Knowledge")
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle")
        
        # Single choice question
        single_q = MultipleChoiceQuestionFactory(
            category=knowledge_cat,
            question_type='single',
            is_required=True
        )
        QuestionChoiceFactory.create_batch(3, question=single_q)
        
        # Multiple choice question
        multiple_q = MultipleChoiceQuestionFactory(
            category=lifestyle_cat,
            question_type='multiple',
            is_required=False
        )
        QuestionChoiceFactory.create_batch(4, question=multiple_q)
        
        # Scale question
        scale_q = MultipleChoiceQuestionFactory(
            category=knowledge_cat,
            question_type='scale',
            is_required=True
        )
        for i in range(1, 6):
            QuestionChoiceFactory(
                question=scale_q,
                choice_text=str(i),
                order=i
            )
        
        form = MCQResponseForm(assessment=assessment)
        
        # Should have fields for each question
        assert f'question_{single_q.id}' in form.fields
        assert f'question_{multiple_q.id}' in form.fields
        assert f'question_{scale_q.id}' in form.fields
        
        # Check field types
        single_field = form.fields[f'question_{single_q.id}']
        multiple_field = form.fields[f'question_{multiple_q.id}']
        scale_field = form.fields[f'question_{scale_q.id}']
        
        assert single_field.widget.__class__.__name__ == 'RadioSelect'
        assert multiple_field.widget.__class__.__name__ == 'CheckboxSelectMultiple'
        assert scale_field.widget.__class__.__name__ == 'RadioSelect'
        
        # Check required fields
        assert single_field.required is True
        assert multiple_field.required is False
        assert scale_field.required is True
    
    def test_form_field_choices(self):
        """Test form field choices are correctly set."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single'
        )
        
        # Create choices with specific order
        choice1 = QuestionChoiceFactory(
            question=question,
            choice_text="First choice",
            order=1
        )
        choice3 = QuestionChoiceFactory(
            question=question,
            choice_text="Third choice", 
            order=3
        )
        choice2 = QuestionChoiceFactory(
            question=question,
            choice_text="Second choice",
            order=2
        )
        
        form = MCQResponseForm(assessment=assessment)
        field = form.fields[f'question_{question.id}']
        
        # Choices should be ordered by order field
        expected_choices = [
            (choice1.id, "First choice"),
            (choice2.id, "Second choice"),
            (choice3.id, "Third choice")
        ]
        
        assert list(field.choices) == expected_choices
    
    def test_form_validation_required_fields(self):
        """Test form validation for required fields."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Required question
        required_q = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            is_required=True
        )
        choice1 = QuestionChoiceFactory(question=required_q)
        choice2 = QuestionChoiceFactory(question=required_q)
        
        # Optional question
        optional_q = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            is_required=False
        )
        choice3 = QuestionChoiceFactory(question=optional_q)
        
        form = MCQResponseForm(assessment=assessment)
        
        # Test form without required field
        data = {f'question_{optional_q.id}': choice3.id}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert not form.is_valid()
        assert f'question_{required_q.id}' in form.errors
        
        # Test form with required field
        data = {
            f'question_{required_q.id}': choice1.id,
            f'question_{optional_q.id}': choice3.id
        }
        form = MCQResponseForm(data=data, assessment=assessment)
        assert form.is_valid()
    
    def test_form_validation_multiple_choice(self):
        """Test form validation for multiple choice questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='multiple',
            is_required=True
        )
        choice1 = QuestionChoiceFactory(question=question)
        choice2 = QuestionChoiceFactory(question=question)
        choice3 = QuestionChoiceFactory(question=question)
        
        form = MCQResponseForm(assessment=assessment)
        
        # Test with multiple selections
        data = {f'question_{question.id}': [choice1.id, choice3.id]}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert form.is_valid()
        
        # Test with single selection (should also be valid)
        data = {f'question_{question.id}': [choice2.id]}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert form.is_valid()
        
        # Test with no selection (required field)
        data = {}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert not form.is_valid()
    
    def test_form_save_single_choice(self):
        """Test saving form with single choice questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            points=10
        )
        correct_choice = QuestionChoiceFactory(
            question=question,
            points=8,
            is_correct=True
        )
        wrong_choice = QuestionChoiceFactory(
            question=question,
            points=0,
            is_correct=False
        )
        
        # Submit form with correct choice
        data = {f'question_{question.id}': correct_choice.id}
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Check that response was created
        responses = assessment.question_responses.all()
        assert responses.count() == 1
        
        response = responses.first()
        assert response.question == question
        assert response.points_earned == 8
        assert response.selected_choices.count() == 1
        assert correct_choice in response.selected_choices.all()
    
    def test_form_save_multiple_choice(self):
        """Test saving form with multiple choice questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='multiple',
            points=15
        )
        
        # Create choices with different point values
        choice1 = QuestionChoiceFactory(question=question, points=5)
        choice2 = QuestionChoiceFactory(question=question, points=5)  
        choice3 = QuestionChoiceFactory(question=question, points=5)
        choice4 = QuestionChoiceFactory(question=question, points=0)  # Wrong choice
        
        # Submit form selecting correct choices
        data = {f'question_{question.id}': [choice1.id, choice2.id, choice3.id]}
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Check response
        response = assessment.question_responses.first()
        assert response.question == question
        assert response.points_earned == 15  # 5 + 5 + 5
        assert response.selected_choices.count() == 3
        
        selected_ids = set(response.selected_choices.values_list('id', flat=True))
        expected_ids = {choice1.id, choice2.id, choice3.id}
        assert selected_ids == expected_ids
    
    def test_form_save_scale_question(self):
        """Test saving form with scale questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='scale',
            points=10
        )
        
        # Create scale choices (1-5)
        choices = []
        for i in range(1, 6):
            choice = QuestionChoiceFactory(
                question=question,
                choice_text=str(i),
                points=i * 2,  # 2, 4, 6, 8, 10 points
                order=i
            )
            choices.append(choice)
        
        # Submit form selecting middle value (3)
        data = {f'question_{question.id}': choices[2].id}  # Choice with value 3
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Check response
        response = assessment.question_responses.first()
        assert response.question == question
        assert response.points_earned == 6  # 3 * 2
        assert response.selected_choices.count() == 1
        assert choices[2] in response.selected_choices.all()
    
    def test_form_save_text_question(self):
        """Test saving form with text questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='text',
            points=10
        )
        
        # Text questions don't have choices, just text response
        data = {f'question_{question.id}_text': "This is my text response"}
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Check response
        response = assessment.question_responses.first()
        assert response.question == question
        assert response.response_text == "This is my text response"
        assert response.selected_choices.count() == 0
        # Text responses get default points (could be manual scoring later)
        assert response.points_earned >= 0
    
    def test_form_save_dependency_handling(self):
        """Test saving form handles question dependencies correctly."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Parent question
        parent_q = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single'
        )
        yes_choice = QuestionChoiceFactory(
            question=parent_q,
            choice_text="Yes"
        )
        no_choice = QuestionChoiceFactory(
            question=parent_q,
            choice_text="No"
        )
        
        # Dependent question (only shows if parent is "Yes")
        dependent_q = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            depends_on=parent_q,
            show_when="choice=Yes"
        )
        dep_choice = QuestionChoiceFactory(question=dependent_q)
        
        # Submit form with parent = "Yes" and dependent answered
        data = {
            f'question_{parent_q.id}': yes_choice.id,
            f'question_{dependent_q.id}': dep_choice.id
        }
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Both responses should be saved
        assert assessment.question_responses.count() == 2
        
        # Submit form with parent = "No" (dependent should be ignored)
        assessment.question_responses.all().delete()  # Clear previous responses
        
        data = {
            f'question_{parent_q.id}': no_choice.id,
            f'question_{dependent_q.id}': dep_choice.id  # This should be ignored
        }
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        # Only parent response should be saved
        assert assessment.question_responses.count() == 1
        assert assessment.question_responses.first().question == parent_q


@pytest.mark.django_db
class TestMCQFormFieldGeneration:
    """Test MCQ form field generation logic."""
    
    def test_field_generation_widget_types(self):
        """Test correct widget types for different question types."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Test all question types
        question_types = ['single', 'multiple', 'scale', 'text']
        expected_widgets = [
            'RadioSelect',
            'CheckboxSelectMultiple', 
            'RadioSelect',
            'Textarea'
        ]
        
        questions = []
        for q_type in question_types:
            question = MultipleChoiceQuestionFactory(
                category=category,
                question_type=q_type
            )
            if q_type != 'text':
                QuestionChoiceFactory.create_batch(3, question=question)
            questions.append(question)
        
        form = MCQResponseForm(assessment=assessment)
        
        for question, expected_widget in zip(questions, expected_widgets):
            if question.question_type == 'text':
                field_name = f'question_{question.id}_text'
            else:
                field_name = f'question_{question.id}'
            
            assert field_name in form.fields
            widget_class = form.fields[field_name].widget.__class__.__name__
            assert widget_class == expected_widget
    
    def test_field_help_text(self):
        """Test form field help text generation."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            help_text="This is help text",
            help_text_ko="도움말 텍스트입니다"
        )
        choice = QuestionChoiceFactory(question=question)
        
        form = MCQResponseForm(assessment=assessment)
        field = form.fields[f'question_{question.id}']
        
        # Should use Korean help text if available
        assert "도움말 텍스트입니다" in field.help_text
    
    def test_field_css_classes(self):
        """Test form field CSS classes."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            is_required=True
        )
        choice = QuestionChoiceFactory(question=question)
        
        form = MCQResponseForm(assessment=assessment)
        field = form.fields[f'question_{question.id}']
        
        # Check CSS classes in widget
        widget_attrs = field.widget.attrs
        assert 'mcq-question' in widget_attrs.get('class', '')
        assert 'required' in widget_attrs.get('class', '')
    
    def test_field_validation_custom(self):
        """Test custom field validation logic."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Question with specific validation
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='multiple',
            is_required=True
        )
        
        # Create 5 choices
        choices = QuestionChoiceFactory.create_batch(5, question=question)
        
        form = MCQResponseForm(assessment=assessment)
        
        # Test validation with too many choices (if there's a limit)
        data = {f'question_{question.id}': [c.id for c in choices]}
        form = MCQResponseForm(data=data, assessment=assessment)
        
        # Should be valid (no specific limit in basic implementation)
        assert form.is_valid()
        
        # Test validation with empty selection for required multiple choice
        data = {}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert not form.is_valid()
        assert f'question_{question.id}' in form.errors


@pytest.mark.django_db  
class TestMCQFormEdgeCases:
    """Test edge cases for MCQ forms."""
    
    def test_form_with_inactive_questions(self):
        """Test form ignores inactive questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Active question
        active_q = MultipleChoiceQuestionFactory(
            category=category,
            is_active=True
        )
        choice1 = QuestionChoiceFactory(question=active_q)
        
        # Inactive question
        inactive_q = MultipleChoiceQuestionFactory(
            category=category,
            is_active=False
        )
        choice2 = QuestionChoiceFactory(question=inactive_q)
        
        form = MCQResponseForm(assessment=assessment)
        
        # Only active question should have field
        assert f'question_{active_q.id}' in form.fields
        assert f'question_{inactive_q.id}' not in form.fields
    
    def test_form_with_no_choices(self):
        """Test form handles questions with no choices."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        # Question with no choices
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single'
        )
        # Don't create any choices
        
        form = MCQResponseForm(assessment=assessment)
        
        # Field should still be created but with empty choices
        assert f'question_{question.id}' in form.fields
        field = form.fields[f'question_{question.id}']
        assert len(field.choices) == 0
    
    def test_form_save_replaces_existing_responses(self):
        """Test form save replaces existing responses for same question."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single'
        )
        choice1 = QuestionChoiceFactory(question=question, points=5)
        choice2 = QuestionChoiceFactory(question=question, points=8)
        
        # Create initial response
        data = {f'question_{question.id}': choice1.id}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert form.is_valid()
        form.save()
        
        # Verify initial response
        assert assessment.question_responses.count() == 1
        response = assessment.question_responses.first()
        assert response.points_earned == 5
        
        # Submit form again with different choice
        data = {f'question_{question.id}': choice2.id}
        form = MCQResponseForm(data=data, assessment=assessment)
        assert form.is_valid()
        form.save()
        
        # Should still have only one response, but updated
        assert assessment.question_responses.count() == 1
        response = assessment.question_responses.first()
        assert response.points_earned == 8
        assert choice2 in response.selected_choices.all()
        assert choice1 not in response.selected_choices.all()
    
    def test_form_with_very_long_text(self):
        """Test form handles very long text responses."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory()
        
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='text'
        )
        
        # Very long text (2000 characters)
        long_text = "x" * 2000
        
        data = {f'question_{question.id}_text': long_text}
        form = MCQResponseForm(data=data, assessment=assessment)
        
        assert form.is_valid()
        form.save()
        
        response = assessment.question_responses.first()
        assert response.response_text == long_text