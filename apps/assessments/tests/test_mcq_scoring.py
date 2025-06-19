"""
Tests for MCQ scoring engine.
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from apps.assessments.models import Assessment, QuestionCategory, MultipleChoiceQuestion, QuestionChoice, QuestionResponse
from apps.assessments.mcq_scoring_module.mcq_scoring import MCQScoringEngine, calculate_mcq_scores_for_assessment
from apps.clients.models import Client
from apps.trainers.models import Trainer, Organization
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


@pytest.mark.django_db
class TestMCQScoringEngine(TestCase):
    """Test cases for MCQ scoring engine."""
    
    def setUp(self):
        """Set up test data."""
        # Create organization and trainer
        self.organization = Organization.objects.create(
            name="Test Gym",
            slug="test-gym"
        )
        
        self.user = User.objects.create_user(
            username="testtrainer",
            email="trainer@test.com",
            password="testpass123"
        )
        
        self.trainer = Trainer.objects.create(
            user=self.user,
            organization=self.organization,
            role='trainer'
        )
        
        # Create client
        self.client_obj = Client.objects.create(
            name="Test Client",
            email="client@test.com",
            trainer=self.trainer,
            gender='male',
            age=30,
            height=175,  # Required field
            weight=70    # Required field
        )
        
        # Create assessment
        self.assessment = Assessment.objects.create(
            client=self.client_obj,
            trainer=self.trainer,
            date=datetime.now(),
            overall_score=75.0  # Physical score
        )
        
        # Create categories with weights
        self.knowledge_category = QuestionCategory.objects.create(
            name="Knowledge",
            name_ko="지식",
            weight=Decimal('0.15'),
            order=1,
            is_active=True
        )
        
        self.lifestyle_category = QuestionCategory.objects.create(
            name="Lifestyle",
            name_ko="생활습관",
            weight=Decimal('0.15'),
            order=2,
            is_active=True
        )
        
        self.readiness_category = QuestionCategory.objects.create(
            name="Readiness",
            name_ko="준비도",
            weight=Decimal('0.10'),
            order=3,
            is_active=True
        )
    
    def test_calculate_category_score_perfect(self):
        """Test perfect score calculation for a category."""
        # Create knowledge question
        question = MultipleChoiceQuestion.objects.create(
            category=self.knowledge_category,
            question_text="What is proper squat form?",
            question_text_ko="올바른 스쿼트 자세는?",
            question_type='single',
            points=10,
            is_required=True
        )
        
        # Create choices
        correct_choice = QuestionChoice.objects.create(
            question=question,
            choice_text="Knees track over toes",
            choice_text_ko="무릎이 발끝 방향으로",
            points=10,
            is_correct=True
        )
        
        wrong_choice = QuestionChoice.objects.create(
            question=question,
            choice_text="Knees cave inward",
            choice_text_ko="무릎이 안쪽으로",
            points=0,
            is_correct=False
        )
        
        # Create response with correct answer
        response = QuestionResponse.objects.create(
            assessment=self.assessment,
            question=question,
            points_earned=10
        )
        response.selected_choices.add(correct_choice)
        
        # Calculate scores
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        self.assertEqual(scores['knowledge_score'], 100.0)
    
    def test_calculate_comprehensive_score(self):
        """Test comprehensive score calculation."""
        # Set physical score
        self.assessment.overall_score = 80.0
        
        # Create questions and perfect responses for each category
        categories = [
            (self.knowledge_category, 90),  # 90% score
            (self.lifestyle_category, 80),   # 80% score
            (self.readiness_category, 70)    # 70% score
        ]
        
        for category, score_percent in categories:
            question = MultipleChoiceQuestion.objects.create(
                category=category,
                question_text=f"Test question for {category.name}",
                question_text_ko=f"테스트 질문 {category.name_ko}",
                question_type='single',
                points=100
            )
            
            choice = QuestionChoice.objects.create(
                question=question,
                choice_text="Answer",
                choice_text_ko="답변",
                points=score_percent
            )
            
            response = QuestionResponse.objects.create(
                assessment=self.assessment,
                question=question,
                points_earned=score_percent
            )
            response.selected_choices.add(choice)
        
        # Calculate scores
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Verify individual scores
        self.assertEqual(scores['knowledge_score'], 90.0)
        self.assertEqual(scores['lifestyle_score'], 80.0)
        self.assertEqual(scores['readiness_score'], 70.0)
        
        # Calculate expected comprehensive score
        # Physical: 80 * 0.60 = 48
        # Knowledge: 90 * 0.15 = 13.5
        # Lifestyle: 80 * 0.15 = 12
        # Readiness: 70 * 0.10 = 7
        # Total: 48 + 13.5 + 12 + 7 = 80.5
        expected_comprehensive = 80.5
        
        self.assertAlmostEqual(scores['comprehensive_score'], expected_comprehensive, places=1)
    
    def test_risk_factor_extraction(self):
        """Test extraction of risk factors from MCQ responses."""
        # Create lifestyle question about sleep
        question = MultipleChoiceQuestion.objects.create(
            category=self.lifestyle_category,
            question_text="How many hours of sleep do you get?",
            question_text_ko="하루 수면 시간은?",
            question_type='single',
            points=10
        )
        
        # Create risk-contributing choice
        risky_choice = QuestionChoice.objects.create(
            question=question,
            choice_text="Less than 5 hours",
            choice_text_ko="5시간 미만",
            points=2,
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        
        good_choice = QuestionChoice.objects.create(
            question=question,
            choice_text="7-8 hours",
            choice_text_ko="7-8시간",
            points=10,
            contributes_to_risk=False
        )
        
        # Create response with risky answer
        response = QuestionResponse.objects.create(
            assessment=self.assessment,
            question=question,
            points_earned=2
        )
        response.selected_choices.add(risky_choice)
        
        # Calculate scores
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Check risk factors
        risk_factors = scores.get('mcq_risk_factors', [])
        self.assertEqual(len(risk_factors), 1)
        self.assertEqual(risk_factors[0]['category'], 'Lifestyle')
        self.assertEqual(risk_factors[0]['risk_weight'], 0.8)
    
    def test_multiple_choice_scoring(self):
        """Test scoring for multiple choice questions."""
        # Create multiple choice question
        question = MultipleChoiceQuestion.objects.create(
            category=self.knowledge_category,
            question_text="Which are benefits of strength training? (select all)",
            question_text_ko="근력 운동의 이점은? (모두 선택)",
            question_type='multiple',
            points=15  # Total possible points
        )
        
        # Create choices
        choices = []
        for i, (text, points) in enumerate([
            ("Increased muscle mass", 5),
            ("Better bone density", 5),
            ("Improved metabolism", 5),
            ("Instant weight loss", 0)  # Wrong answer
        ]):
            choice = QuestionChoice.objects.create(
                question=question,
                choice_text=text,
                choice_text_ko=f"선택지 {i+1}",
                points=points,
                is_correct=points > 0
            )
            choices.append(choice)
        
        # Create response selecting first three (correct ones)
        response = QuestionResponse.objects.create(
            assessment=self.assessment,
            question=question
        )
        response.selected_choices.add(choices[0], choices[1], choices[2])
        response.save()  # This triggers point calculation
        
        # Verify points
        self.assertEqual(response.points_earned, 15)  # All correct answers
    
    def test_scale_question_scoring(self):
        """Test scoring for scale/rating questions."""
        # Create scale question
        question = MultipleChoiceQuestion.objects.create(
            category=self.readiness_category,
            question_text="Rate your current energy level",
            question_text_ko="현재 에너지 수준을 평가하세요",
            question_type='scale',
            points=10
        )
        
        # Create scale choices (1-5)
        for i in range(1, 6):
            QuestionChoice.objects.create(
                question=question,
                choice_text=str(i),
                choice_text_ko=f"{i}점",
                points=i * 2,  # 2, 4, 6, 8, 10 points
                order=i
            )
        
        # Select middle value (3)
        middle_choice = question.choices.get(choice_text="3")
        response = QuestionResponse.objects.create(
            assessment=self.assessment,
            question=question
        )
        response.selected_choices.add(middle_choice)
        response.save()
        
        self.assertEqual(response.points_earned, 6)  # 3 * 2
    
    def test_category_insights(self):
        """Test generation of category insights."""
        # Create low score for knowledge category
        question = MultipleChoiceQuestion.objects.create(
            category=self.knowledge_category,
            question_text="Test",
            question_text_ko="테스트",
            points=100
        )
        
        choice = QuestionChoice.objects.create(
            question=question,
            choice_text="Wrong",
            choice_text_ko="틀림",
            points=30  # Low score
        )
        
        response = QuestionResponse.objects.create(
            assessment=self.assessment,
            question=question,
            points_earned=30
        )
        response.selected_choices.add(choice)
        
        # Get insights
        engine = MCQScoringEngine(self.assessment)
        engine.calculate_mcq_scores()
        insights = engine.get_category_insights()
        
        # Check knowledge insights
        knowledge_insights = insights['knowledge']
        self.assertEqual(knowledge_insights['score'], 30.0)
        self.assertEqual(knowledge_insights['interpretation'], "개선 필요")
        self.assertGreater(len(knowledge_insights['recommendations']), 0)
    
    def test_no_mcq_responses(self):
        """Test handling of assessment with no MCQ responses."""
        # Assessment with no MCQ responses
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        self.assertEqual(scores['knowledge_score'], 0)
        self.assertEqual(scores['lifestyle_score'], 0)
        self.assertEqual(scores['readiness_score'], 0)
        # Comprehensive score should equal physical score * 0.6
        self.assertEqual(scores['comprehensive_score'], 75.0 * 0.6)