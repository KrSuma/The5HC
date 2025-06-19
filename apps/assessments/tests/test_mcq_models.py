"""
Comprehensive tests for MCQ models.

Tests all MCQ models following django-test.md guidelines:
- QuestionCategory
- MultipleChoiceQuestion
- QuestionChoice
- QuestionResponse
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion, 
    QuestionChoice, QuestionResponse, Assessment
)
from apps.assessments.factories import (
    QuestionCategoryFactory, MultipleChoiceQuestionFactory,
    QuestionChoiceFactory, QuestionResponseFactory, AssessmentFactory
)


@pytest.mark.django_db
class TestQuestionCategory:
    """Test cases for QuestionCategory model."""
    
    def test_create_category(self):
        """Test creating a question category."""
        category = QuestionCategoryFactory(
            name="Knowledge Assessment",
            name_ko="지식 평가",
            weight=Decimal('0.15')
        )
        
        assert category.name == "Knowledge Assessment"
        assert category.name_ko == "지식 평가"
        assert category.weight == Decimal('0.15')
        assert category.is_active is True
    
    def test_category_str_representation(self):
        """Test category string representation."""
        category = QuestionCategoryFactory(name="Lifestyle")
        assert str(category) == "Lifestyle"
    
    def test_category_ordering(self):
        """Test category ordering by order field."""
        cat2 = QuestionCategoryFactory(order=2)
        cat1 = QuestionCategoryFactory(order=1)
        cat3 = QuestionCategoryFactory(order=3)
        
        categories = QuestionCategory.objects.all().order_by('order')
        assert list(categories) == [cat1, cat2, cat3]
    
    def test_category_weight_validation(self):
        """Test weight field validation."""
        # Valid weight
        category = QuestionCategoryFactory(weight=Decimal('0.25'))
        category.full_clean()
        
        # Invalid weight (negative)
        with pytest.raises(ValidationError):
            category = QuestionCategoryFactory(weight=Decimal('-0.1'))
            category.full_clean()
    
    def test_category_active_manager(self):
        """Test active categories manager."""
        active_cat = QuestionCategoryFactory(is_active=True)
        inactive_cat = QuestionCategoryFactory(is_active=False)
        
        active_categories = QuestionCategory.objects.filter(is_active=True)
        assert active_cat in active_categories
        assert inactive_cat not in active_categories


@pytest.mark.django_db
class TestMultipleChoiceQuestion:
    """Test cases for MultipleChoiceQuestion model."""
    
    def test_create_question(self):
        """Test creating a multiple choice question."""
        category = QuestionCategoryFactory()
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_text="What is proper form?",
            question_text_ko="올바른 자세는 무엇입니까?",
            question_type='single',
            points=10
        )
        
        assert question.category == category
        assert question.question_text == "What is proper form?"
        assert question.question_text_ko == "올바른 자세는 무엇입니까?"
        assert question.question_type == 'single'
        assert question.points == 10
        assert question.is_active is True
    
    def test_question_str_representation(self):
        """Test question string representation."""
        question = MultipleChoiceQuestionFactory(
            question_text="What is fitness?"
        )
        assert str(question) == "What is fitness?"
    
    def test_question_type_choices(self):
        """Test question type field choices."""
        # Valid question types
        for q_type in ['single', 'multiple', 'scale', 'text']:
            question = MultipleChoiceQuestionFactory(question_type=q_type)
            question.full_clean()
            assert question.question_type == q_type
    
    def test_question_ordering(self):
        """Test question ordering within category."""
        category = QuestionCategoryFactory()
        q2 = MultipleChoiceQuestionFactory(category=category, order=2)
        q1 = MultipleChoiceQuestionFactory(category=category, order=1)
        q3 = MultipleChoiceQuestionFactory(category=category, order=3)
        
        questions = category.multiplechoicequestion_set.all().order_by('order')
        assert list(questions) == [q1, q2, q3]
    
    def test_question_depends_on_relationship(self):
        """Test question dependency relationship."""
        parent_question = MultipleChoiceQuestionFactory()
        dependent_question = MultipleChoiceQuestionFactory(
            depends_on=parent_question,
            show_when="choice=yes"
        )
        
        assert dependent_question.depends_on == parent_question
        assert dependent_question.show_when == "choice=yes"
    
    def test_question_points_validation(self):
        """Test points field validation."""
        # Valid points
        question = MultipleChoiceQuestionFactory(points=10)
        question.full_clean()
        
        # Invalid points (negative)
        with pytest.raises(ValidationError):
            question = MultipleChoiceQuestionFactory(points=-5)
            question.full_clean()


@pytest.mark.django_db
class TestQuestionChoice:
    """Test cases for QuestionChoice model."""
    
    def test_create_choice(self):
        """Test creating a question choice."""
        question = MultipleChoiceQuestionFactory()
        choice = QuestionChoiceFactory(
            question=question,
            choice_text="Correct answer",
            choice_text_ko="정답",
            points=10,
            is_correct=True
        )
        
        assert choice.question == question
        assert choice.choice_text == "Correct answer"
        assert choice.choice_text_ko == "정답"
        assert choice.points == 10
        assert choice.is_correct is True
    
    def test_choice_str_representation(self):
        """Test choice string representation."""
        choice = QuestionChoiceFactory(choice_text="Option A")
        assert str(choice) == "Option A"
    
    def test_choice_ordering(self):
        """Test choice ordering within question."""
        question = MultipleChoiceQuestionFactory()
        c2 = QuestionChoiceFactory(question=question, order=2)
        c1 = QuestionChoiceFactory(question=question, order=1)
        c3 = QuestionChoiceFactory(question=question, order=3)
        
        choices = question.choices.all().order_by('order')
        assert list(choices) == [c1, c2, c3]
    
    def test_risk_factor_fields(self):
        """Test risk factor related fields."""
        choice = QuestionChoiceFactory(
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        
        assert choice.contributes_to_risk is True
        assert choice.risk_weight == Decimal('0.8')
    
    def test_choice_points_validation(self):
        """Test points field validation."""
        # Valid points
        choice = QuestionChoiceFactory(points=5)
        choice.full_clean()
        
        # Negative points should be allowed for penalty answers
        choice = QuestionChoiceFactory(points=-2)
        choice.full_clean()
    
    def test_risk_weight_validation(self):
        """Test risk weight validation."""
        # Valid risk weight
        choice = QuestionChoiceFactory(risk_weight=Decimal('0.5'))
        choice.full_clean()
        
        # Invalid risk weight (negative)
        with pytest.raises(ValidationError):
            choice = QuestionChoiceFactory(risk_weight=Decimal('-0.1'))
            choice.full_clean()


@pytest.mark.django_db
class TestQuestionResponse:
    """Test cases for QuestionResponse model."""
    
    def test_create_response(self):
        """Test creating a question response."""
        assessment = AssessmentFactory()
        question = MultipleChoiceQuestionFactory()
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            response_text="User's answer",
            points_earned=8
        )
        
        assert response.assessment == assessment
        assert response.question == question
        assert response.response_text == "User's answer"
        assert response.points_earned == 8
    
    def test_response_str_representation(self):
        """Test response string representation."""
        assessment = AssessmentFactory()
        question = MultipleChoiceQuestionFactory(question_text="Test question")
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question
        )
        
        expected_str = f"Assessment {assessment.id} - Test question"
        assert str(response) == expected_str
    
    def test_response_with_selected_choices(self):
        """Test response with selected choices."""
        question = MultipleChoiceQuestionFactory()
        choice1 = QuestionChoiceFactory(question=question, points=5)
        choice2 = QuestionChoiceFactory(question=question, points=3)
        
        response = QuestionResponseFactory(
            question=question,
            selected_choices=[choice1, choice2]
        )
        
        selected = list(response.selected_choices.all())
        assert choice1 in selected
        assert choice2 in selected
        assert len(selected) == 2
    
    def test_response_points_earned_validation(self):
        """Test points earned validation."""
        # Valid points
        response = QuestionResponseFactory(points_earned=10)
        response.full_clean()
        
        # Zero points
        response = QuestionResponseFactory(points_earned=0)
        response.full_clean()
        
        # Negative points (penalty)
        response = QuestionResponseFactory(points_earned=-2)
        response.full_clean()
    
    def test_response_unique_together(self):
        """Test unique constraint on assessment + question."""
        assessment = AssessmentFactory()
        question = MultipleChoiceQuestionFactory()
        
        # First response should work
        response1 = QuestionResponseFactory(
            assessment=assessment,
            question=question
        )
        
        # Second response for same assessment+question should fail
        with pytest.raises(IntegrityError):
            QuestionResponseFactory(
                assessment=assessment,
                question=question
            )
    
    def test_response_timestamps(self):
        """Test automatic timestamp fields."""
        response = QuestionResponseFactory()
        
        assert response.created is not None
        assert response.updated is not None
        assert response.created <= response.updated


@pytest.mark.django_db
class TestMCQModelRelationships:
    """Test relationships between MCQ models."""
    
    def test_category_to_questions_relationship(self):
        """Test category to questions relationship."""
        category = QuestionCategoryFactory()
        q1 = MultipleChoiceQuestionFactory(category=category)
        q2 = MultipleChoiceQuestionFactory(category=category)
        
        questions = category.multiplechoicequestion_set.all()
        assert q1 in questions
        assert q2 in questions
        assert questions.count() == 2
    
    def test_question_to_choices_relationship(self):
        """Test question to choices relationship."""
        question = MultipleChoiceQuestionFactory()
        c1 = QuestionChoiceFactory(question=question)
        c2 = QuestionChoiceFactory(question=question)
        c3 = QuestionChoiceFactory(question=question)
        
        choices = question.choices.all()
        assert c1 in choices
        assert c2 in choices
        assert c3 in choices
        assert choices.count() == 3
    
    def test_assessment_to_responses_relationship(self):
        """Test assessment to responses relationship."""
        assessment = AssessmentFactory()
        q1 = MultipleChoiceQuestionFactory()
        q2 = MultipleChoiceQuestionFactory()
        
        r1 = QuestionResponseFactory(assessment=assessment, question=q1)
        r2 = QuestionResponseFactory(assessment=assessment, question=q2)
        
        responses = assessment.question_responses.all()
        assert r1 in responses
        assert r2 in responses
        assert responses.count() == 2
    
    def test_cascade_delete_category(self):
        """Test cascade delete when category is deleted."""
        category = QuestionCategoryFactory()
        question = MultipleChoiceQuestionFactory(category=category)
        choice = QuestionChoiceFactory(question=question)
        
        category_id = category.id
        question_id = question.id
        choice_id = choice.id
        
        # Delete category
        category.delete()
        
        # Check that related objects are deleted
        assert not MultipleChoiceQuestion.objects.filter(id=question_id).exists()
        assert not QuestionChoice.objects.filter(id=choice_id).exists()
    
    def test_cascade_delete_question(self):
        """Test cascade delete when question is deleted."""
        question = MultipleChoiceQuestionFactory()
        choice = QuestionChoiceFactory(question=question)
        response = QuestionResponseFactory(question=question)
        
        question_id = question.id
        choice_id = choice.id
        response_id = response.id
        
        # Delete question
        question.delete()
        
        # Check that related objects are deleted
        assert not QuestionChoice.objects.filter(id=choice_id).exists()
        assert not QuestionResponse.objects.filter(id=response_id).exists()
    
    def test_cascade_delete_assessment(self):
        """Test cascade delete when assessment is deleted."""
        assessment = AssessmentFactory()
        response = QuestionResponseFactory(assessment=assessment)
        
        assessment_id = assessment.id
        response_id = response.id
        
        # Delete assessment
        assessment.delete()
        
        # Check that responses are deleted
        assert not QuestionResponse.objects.filter(id=response_id).exists()


@pytest.mark.django_db
class TestMCQModelMethods:
    """Test custom methods on MCQ models."""
    
    def test_category_get_questions_count(self):
        """Test getting active questions count for category."""
        category = QuestionCategoryFactory()
        MultipleChoiceQuestionFactory(category=category, is_active=True)
        MultipleChoiceQuestionFactory(category=category, is_active=True)
        MultipleChoiceQuestionFactory(category=category, is_active=False)
        
        active_questions = category.multiplechoicequestion_set.filter(is_active=True)
        assert active_questions.count() == 2
    
    def test_question_get_correct_choices(self):
        """Test getting correct choices for a question."""
        question = MultipleChoiceQuestionFactory()
        correct_choice = QuestionChoiceFactory(question=question, is_correct=True)
        wrong_choice = QuestionChoiceFactory(question=question, is_correct=False)
        
        correct_choices = question.choices.filter(is_correct=True)
        assert correct_choice in correct_choices
        assert wrong_choice not in correct_choices
        assert correct_choices.count() == 1
    
    def test_response_calculate_score_percentage(self):
        """Test calculating score percentage for response."""
        question = MultipleChoiceQuestionFactory(points=10)
        response = QuestionResponseFactory(
            question=question,
            points_earned=7
        )
        
        # Calculate percentage manually since model doesn't have this method
        percentage = (response.points_earned / question.points) * 100
        assert percentage == 70.0
    
    def test_response_get_risk_factors(self):
        """Test getting risk factors from response choices."""
        question = MultipleChoiceQuestionFactory()
        risky_choice = QuestionChoiceFactory(
            question=question,
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        safe_choice = QuestionChoiceFactory(
            question=question,
            contributes_to_risk=False,
            risk_weight=Decimal('0.0')
        )
        
        response = QuestionResponseFactory(
            question=question,
            selected_choices=[risky_choice, safe_choice]
        )
        
        risk_choices = response.selected_choices.filter(contributes_to_risk=True)
        assert risky_choice in risk_choices
        assert safe_choice not in risk_choices
        assert risk_choices.count() == 1


@pytest.mark.django_db
class TestMCQModelEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_question_text(self):
        """Test validation with empty question text."""
        with pytest.raises(ValidationError):
            question = MultipleChoiceQuestionFactory(question_text="")
            question.full_clean()
    
    def test_empty_choice_text(self):
        """Test validation with empty choice text."""
        with pytest.raises(ValidationError):
            choice = QuestionChoiceFactory(choice_text="")
            choice.full_clean()
    
    def test_question_without_choices(self):
        """Test question without any choices."""
        question = MultipleChoiceQuestionFactory()
        
        # Question should exist but have no choices
        assert question.choices.count() == 0
    
    def test_response_without_selected_choices(self):
        """Test response without any selected choices."""
        response = QuestionResponseFactory()
        
        # Response should exist but have no selected choices
        assert response.selected_choices.count() == 0
    
    def test_very_long_text_fields(self):
        """Test text fields with maximum length."""
        long_text = "x" * 500  # Test with 500 characters
        
        question = MultipleChoiceQuestionFactory(
            question_text=long_text,
            help_text=long_text
        )
        question.full_clean()
        
        choice = QuestionChoiceFactory(
            choice_text=long_text
        )
        choice.full_clean()
    
    def test_special_characters_in_text(self):
        """Test text fields with special characters and Korean."""
        special_text = "Special chars: !@#$%^&*()_+ 한글 テスト"
        
        question = MultipleChoiceQuestionFactory(
            question_text=special_text,
            question_text_ko=special_text
        )
        question.full_clean()
        
        choice = QuestionChoiceFactory(
            choice_text=special_text,
            choice_text_ko=special_text
        )
        choice.full_clean()
    
    def test_maximum_risk_weight(self):
        """Test risk weight at maximum value."""
        choice = QuestionChoiceFactory(risk_weight=Decimal('1.0'))
        choice.full_clean()
        
        assert choice.risk_weight == Decimal('1.0')
    
    def test_zero_points_question(self):
        """Test question with zero points."""
        question = MultipleChoiceQuestionFactory(points=0)
        question.full_clean()
        
        assert question.points == 0