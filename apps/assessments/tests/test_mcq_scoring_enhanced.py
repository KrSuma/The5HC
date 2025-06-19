"""
Enhanced tests for MCQ scoring engine using pytest and factories.

Comprehensive test suite following django-test.md guidelines.
"""

import pytest
from decimal import Decimal
from apps.assessments.models import Assessment
from apps.assessments.mcq_scoring_module.mcq_scoring import MCQScoringEngine
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory, 
    MultipleChoiceQuestionFactory, QuestionChoiceFactory, 
    QuestionResponseFactory
)


@pytest.mark.django_db
class TestMCQScoringEngine:
    """Test cases for MCQ scoring engine."""
    
    def test_scoring_engine_initialization(self):
        """Test scoring engine initialization."""
        assessment = AssessmentFactory()
        engine = MCQScoringEngine(assessment)
        
        assert engine.assessment == assessment
        assert engine.category_weights == {
            'Knowledge': Decimal('0.15'),
            'Lifestyle': Decimal('0.15'),
            'Readiness': Decimal('0.10')
        }
    
    def test_calculate_category_score_empty(self):
        """Test category score calculation with no responses."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Knowledge")
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        assert score == 0
    
    def test_calculate_category_score_single_question(self):
        """Test category score with single question."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(
            category=category,
            points=10
        )
        choice = QuestionChoiceFactory(
            question=question,
            points=8
        )
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=8,
            selected_choices=[choice]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        # 8 points out of 10 = 80%
        assert score == 80.0
    
    def test_calculate_category_score_multiple_questions(self):
        """Test category score with multiple questions."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Lifestyle")
        
        # Question 1: 8/10 points
        q1 = MultipleChoiceQuestionFactory(category=category, points=10)
        c1 = QuestionChoiceFactory(question=q1, points=8)
        r1 = QuestionResponseFactory(
            assessment=assessment,
            question=q1,
            points_earned=8,
            selected_choices=[c1]
        )
        
        # Question 2: 6/10 points
        q2 = MultipleChoiceQuestionFactory(category=category, points=10)
        c2 = QuestionChoiceFactory(question=q2, points=6)
        r2 = QuestionResponseFactory(
            assessment=assessment,
            question=q2,
            points_earned=6,
            selected_choices=[c2]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        # (8 + 6) / (10 + 10) * 100 = 70%
        assert score == 70.0
    
    def test_calculate_mcq_scores_all_categories(self):
        """Test complete MCQ scoring for all categories."""
        assessment = AssessmentFactory(overall_score=75.0)
        
        # Knowledge category: 90%
        knowledge_cat = QuestionCategoryFactory(name="Knowledge", weight=Decimal('0.15'))
        k_q = MultipleChoiceQuestionFactory(category=knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=9)
        k_r = QuestionResponseFactory(
            assessment=assessment,
            question=k_q,
            points_earned=9,
            selected_choices=[k_c]
        )
        
        # Lifestyle category: 80%
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle", weight=Decimal('0.15'))
        l_q = MultipleChoiceQuestionFactory(category=lifestyle_cat, points=10)
        l_c = QuestionChoiceFactory(question=l_q, points=8)
        l_r = QuestionResponseFactory(
            assessment=assessment,
            question=l_q,
            points_earned=8,
            selected_choices=[l_c]
        )
        
        # Readiness category: 70%
        readiness_cat = QuestionCategoryFactory(name="Readiness", weight=Decimal('0.10'))
        r_q = MultipleChoiceQuestionFactory(category=readiness_cat, points=10)
        r_c = QuestionChoiceFactory(question=r_q, points=7)
        r_r = QuestionResponseFactory(
            assessment=assessment,
            question=r_q,
            points_earned=7,
            selected_choices=[r_c]
        )
        
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        assert scores['knowledge_score'] == 90.0
        assert scores['lifestyle_score'] == 80.0
        assert scores['readiness_score'] == 70.0
        
        # Comprehensive score calculation:
        # Physical: 75 * 0.60 = 45
        # Knowledge: 90 * 0.15 = 13.5
        # Lifestyle: 80 * 0.15 = 12
        # Readiness: 70 * 0.10 = 7
        # Total: 45 + 13.5 + 12 + 7 = 77.5
        assert scores['comprehensive_score'] == pytest.approx(77.5, rel=0.01)
    
    def test_extract_risk_factors(self):
        """Test risk factor extraction from responses."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Lifestyle")
        
        # Question with risky choices
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_text="How often do you exercise?"
        )
        
        risky_choice = QuestionChoiceFactory(
            question=question,
            choice_text="Never",
            contributes_to_risk=True,
            risk_weight=Decimal('0.9')
        )
        
        safe_choice = QuestionChoiceFactory(
            question=question,
            choice_text="5 times per week",
            contributes_to_risk=False,
            risk_weight=Decimal('0.0')
        )
        
        # Response with risky choice
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            selected_choices=[risky_choice]
        )
        
        engine = MCQScoringEngine(assessment)
        risk_factors = engine.extract_risk_factors()
        
        assert len(risk_factors) == 1
        assert risk_factors[0]['category'] == 'Lifestyle'
        assert risk_factors[0]['question'] == 'How often do you exercise?'
        assert risk_factors[0]['risk_weight'] == 0.9
        assert risky_choice.choice_text in risk_factors[0]['choices']
    
    def test_generate_category_insights(self):
        """Test category insights generation."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가"
        )
        
        # High scoring response
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=9)
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=9,
            selected_choices=[choice]
        )
        
        engine = MCQScoringEngine(assessment)
        insights = engine.generate_category_insights(category, 90.0)
        
        assert insights['category_name'] == "지식 평가"
        assert insights['score'] == 90.0
        assert 'excellent' in insights['level'].lower() or 'outstanding' in insights['level'].lower()
        assert len(insights['recommendations']) > 0


@pytest.mark.django_db
class TestMCQScoringEdgeCases:
    """Test edge cases for MCQ scoring."""
    
    def test_zero_points_response(self):
        """Test scoring with zero points response."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=0)
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=0,
            selected_choices=[choice]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        assert score == 0.0
    
    def test_negative_points_response(self):
        """Test scoring with negative points (penalty)."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        
        # Penalty choice
        penalty_choice = QuestionChoiceFactory(question=question, points=-2)
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=-2,
            selected_choices=[penalty_choice]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        # -2/10 * 100 = -20% (should be clamped to 0)
        assert score == 0.0
    
    def test_assessment_without_physical_score(self):
        """Test comprehensive scoring without physical score."""
        assessment = AssessmentFactory(overall_score=None)
        
        knowledge_cat = QuestionCategoryFactory(name="Knowledge")
        k_q = MultipleChoiceQuestionFactory(category=knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=8)
        k_r = QuestionResponseFactory(
            assessment=assessment,
            question=k_q,
            points_earned=8,
            selected_choices=[k_c]
        )
        
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        # Should handle None physical score
        assert scores['knowledge_score'] == 80.0
        # Comprehensive score should be 0 * 0.6 + 80 * 0.15 = 12.0
        assert scores['comprehensive_score'] == pytest.approx(12.0, rel=0.01)
    
    def test_multiple_responses_same_question(self):
        """Test handling multiple responses for same question."""
        assessment = AssessmentFactory()
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        
        choice1 = QuestionChoiceFactory(question=question, points=8)
        choice2 = QuestionChoiceFactory(question=question, points=6)
        
        # Create response with both choices (multiple choice question)
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=8,  # Should take the actual points_earned value
            selected_choices=[choice1, choice2]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        # Should use points_earned from response, not calculate from choices
        assert score == 80.0
    
    def test_very_high_scores(self):
        """Test scoring with very high point values."""
        assessment = AssessmentFactory(overall_score=95.0)
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=1000)
        choice = QuestionChoiceFactory(question=question, points=950)
        response = QuestionResponseFactory(
            assessment=assessment,
            question=question,
            points_earned=950,
            selected_choices=[choice]
        )
        
        engine = MCQScoringEngine(assessment)
        score = engine.calculate_category_score(category)
        
        assert score == 95.0


@pytest.mark.django_db
class TestMCQScoringIntegration:
    """Test MCQ scoring integration with assessment system."""
    
    def test_mcq_scoring_integration_with_assessment(self):
        """Test MCQ scoring integration with Assessment model."""
        assessment = AssessmentFactory(overall_score=85.0)
        
        # Add MCQ responses
        knowledge_cat = QuestionCategoryFactory(name="Knowledge")
        k_q = MultipleChoiceQuestionFactory(category=knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=8)
        k_r = QuestionResponseFactory(
            assessment=assessment,
            question=k_q,
            points_earned=8,
            selected_choices=[k_c]
        )
        
        # Calculate and save MCQ scores
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        # Update assessment with MCQ scores
        assessment.knowledge_score = scores['knowledge_score']
        assessment.lifestyle_score = scores['lifestyle_score']
        assessment.readiness_score = scores['readiness_score']
        assessment.comprehensive_score = scores['comprehensive_score']
        assessment.save()
        
        # Verify scores are saved
        assessment.refresh_from_db()
        assert assessment.knowledge_score == 80.0
        assert assessment.lifestyle_score == 0
        assert assessment.readiness_score == 0
        assert assessment.comprehensive_score == pytest.approx(63.0, rel=0.01)  # 85*0.6 + 80*0.15
    
    def test_risk_factor_extraction_multiple_categories(self):
        """Test risk factor extraction across multiple categories."""
        assessment = AssessmentFactory()
        
        # Lifestyle risk
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle")
        l_q = MultipleChoiceQuestionFactory(
            category=lifestyle_cat,
            question_text="Sleep hours?"
        )
        l_risky = QuestionChoiceFactory(
            question=l_q,
            choice_text="Less than 5 hours",
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        l_r = QuestionResponseFactory(
            assessment=assessment,
            question=l_q,
            selected_choices=[l_risky]
        )
        
        # Readiness risk
        readiness_cat = QuestionCategoryFactory(name="Readiness")
        r_q = MultipleChoiceQuestionFactory(
            category=readiness_cat,
            question_text="Recent injuries?"
        )
        r_risky = QuestionChoiceFactory(
            question=r_q,
            choice_text="Multiple injuries",
            contributes_to_risk=True,
            risk_weight=Decimal('0.7')
        )
        r_r = QuestionResponseFactory(
            assessment=assessment,
            question=r_q,
            selected_choices=[r_risky]
        )
        
        engine = MCQScoringEngine(assessment)
        risk_factors = engine.extract_risk_factors()
        
        assert len(risk_factors) == 2
        
        # Check lifestyle risk
        lifestyle_risk = next(rf for rf in risk_factors if rf['category'] == 'Lifestyle')
        assert lifestyle_risk['risk_weight'] == 0.8
        
        # Check readiness risk
        readiness_risk = next(rf for rf in risk_factors if rf['category'] == 'Readiness')
        assert readiness_risk['risk_weight'] == 0.7
    
    def test_no_mcq_responses(self):
        """Test handling of assessment with no MCQ responses."""
        assessment = AssessmentFactory(overall_score=75.0)
        
        engine = MCQScoringEngine(assessment)
        scores = engine.calculate_mcq_scores()
        
        assert scores['knowledge_score'] == 0
        assert scores['lifestyle_score'] == 0
        assert scores['readiness_score'] == 0
        # Comprehensive score should equal physical score * 0.6
        assert scores['comprehensive_score'] == 75.0 * 0.6