"""
Simple tests for MCQ scoring engine.
"""

import pytest
from decimal import Decimal
from apps.assessments.models import Assessment, QuestionCategory, MultipleChoiceQuestion, QuestionChoice, QuestionResponse
from apps.assessments.mcq_scoring_module.mcq_scoring import MCQScoringEngine
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory, 
    MultipleChoiceQuestionFactory, QuestionChoiceFactory, QuestionResponseFactory
)


@pytest.mark.django_db
class TestMCQScoringEngineSimple:
    """Simple test cases for MCQ scoring engine using factories."""
    
    def test_calculate_category_score_perfect(self):
        """Test perfect score calculation for a category."""
        # Create assessment
        assessment = AssessmentFactory(overall_score=75.0)
        
        # Create knowledge category
        knowledge_category = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식",
            weight=Decimal('0.15')
        )
        
        # Create question
        question = MultipleChoiceQuestionFactory(
            category=knowledge_category,
            question_text="What is proper squat form?",
            question_type='single',
            points=10
        )
        
        # Create choices
        correct_choice = QuestionChoiceFactory(
            question=question,
            choice_text="Knees track over toes",
            points=10,
            is_correct=True
        )
        
        wrong_choice = QuestionChoiceFactory(
            question=question,
            choice_text="Knees cave inward",
            points=0,
            is_correct=False
        )
        
        # Create response with correct answer
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=10
        )
        response.selected_choices.add(correct_choice)
        
        # Calculate scores
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        assert scores['knowledge_score'] == 100.0
    
    def test_calculate_comprehensive_score(self):
        """Test comprehensive score calculation."""
        # Create assessment with physical score
        assessment = AssessmentFactory(overall_score=80.0)
        
        # Create categories
        knowledge_cat = QuestionCategoryFactory(name="Knowledge", weight=Decimal('0.15'))
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle", weight=Decimal('0.15'))
        readiness_cat = QuestionCategoryFactory(name="Readiness", weight=Decimal('0.10'))
        
        # Create one question per category with specific scores
        for category, score_percent in [(knowledge_cat, 90), (lifestyle_cat, 80), (readiness_cat, 70)]:
            question = MultipleChoiceQuestionFactory(
                category=category,
                points=100
            )
            
            choice = QuestionChoiceFactory(
                question=question,
                points=score_percent
            )
            
            response = QuestionResponseFactory(
                assessment=assessment,
                question=question,
                points_earned=score_percent
            )
            response.selected_choices.add(choice)
        
        # Calculate scores
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        # Verify individual scores
        assert scores['knowledge_score'] == 90.0
        assert scores['lifestyle_score'] == 80.0
        assert scores['readiness_score'] == 70.0
        
        # Calculate expected comprehensive score
        # Physical: 80 * 0.60 = 48
        # Knowledge: 90 * 0.15 = 13.5
        # Lifestyle: 80 * 0.15 = 12
        # Readiness: 70 * 0.10 = 7
        # Total: 48 + 13.5 + 12 + 7 = 80.5
        expected_comprehensive = 80.5
        
        assert scores['comprehensive_score'] == pytest.approx(expected_comprehensive, rel=0.1)
    
    def test_risk_factor_extraction(self):
        """Test extraction of risk factors from MCQ responses."""
        assessment = AssessmentFactory()
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle")
        
        # Create question about sleep
        question = MultipleChoiceQuestionFactory(
            category=lifestyle_cat,
            question_text="How many hours of sleep do you get?",
            points=10
        )
        
        # Create risk-contributing choice
        risky_choice = QuestionChoiceFactory(
            question=question,
            choice_text="Less than 5 hours",
            points=2,
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        
        # Create response with risky answer
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=2
        )
        response.selected_choices.add(risky_choice)
        
        # Calculate scores
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        # Check risk factors
        risk_factors = scores.get('mcq_risk_factors', [])
        assert len(risk_factors) == 1
        assert risk_factors[0]['category'] == 'Lifestyle'
        assert risk_factors[0]['risk_weight'] == 0.8
    
    def test_no_mcq_responses(self):
        """Test handling of assessment with no MCQ responses."""
        # Assessment with no MCQ responses
        assessment = AssessmentFactory(overall_score=75.0)
        
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        assert scores['knowledge_score'] == 0
        assert scores['lifestyle_score'] == 0
        assert scores['readiness_score'] == 0
        # Comprehensive score should equal physical score * 0.6
        assert scores['comprehensive_score'] == 75.0 * 0.6