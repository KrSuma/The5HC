"""
Integration tests for MCQ system.

Tests the complete MCQ workflow from question creation to
assessment completion and score calculation.
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.assessments.models import Assessment, QuestionResponse
from apps.assessments.mcq_scoring_module.mcq_scoring import MCQScoringEngine
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)
from apps.trainers.factories import TrainerFactory, OrganizationFactory
from apps.clients.factories import ClientFactory

User = get_user_model()


@pytest.mark.django_db
class TestMCQCompleteWorkflow:
    """Test complete MCQ assessment workflow."""
    
    def setup_method(self):
        """Set up test data for complete workflow."""
        self.client = Client()
        
        # Create organization and trainer
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=80.0  # Physical score
        )
        
        # Create complete MCQ structure
        self.setup_mcq_categories()
        self.setup_mcq_questions()
        
        # Login
        self.client.force_login(self.trainer.user)
    
    def setup_mcq_categories(self):
        """Set up MCQ categories with proper weights."""
        self.knowledge_cat = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가",
            weight=Decimal('0.15'),
            order=1,
            is_active=True
        )
        
        self.lifestyle_cat = QuestionCategoryFactory(
            name="Lifestyle",
            name_ko="생활습관 평가",
            weight=Decimal('0.15'),
            order=2,
            is_active=True
        )
        
        self.readiness_cat = QuestionCategoryFactory(
            name="Readiness",
            name_ko="준비도 평가",
            weight=Decimal('0.10'),
            order=3,
            is_active=True
        )
    
    def setup_mcq_questions(self):
        """Set up MCQ questions for all categories."""
        # Knowledge questions
        self.k_q1 = MultipleChoiceQuestionFactory(
            category=self.knowledge_cat,
            question_text="What is the primary benefit of strength training?",
            question_text_ko="근력 훈련의 주요 이점은 무엇입니까?",
            question_type='single',
            points=10,
            is_required=True,
            order=1
        )
        self.k_q1_c1 = QuestionChoiceFactory(
            question=self.k_q1,
            choice_text="Increased muscle mass and bone density",
            choice_text_ko="근육량과 골밀도 증가",
            points=10,
            is_correct=True,
            order=1
        )
        self.k_q1_c2 = QuestionChoiceFactory(
            question=self.k_q1,
            choice_text="Only weight loss",
            choice_text_ko="체중 감량만",
            points=0,
            is_correct=False,
            order=2
        )
        
        self.k_q2 = MultipleChoiceQuestionFactory(
            category=self.knowledge_cat,
            question_text="Which exercises improve cardiovascular health?",
            question_text_ko="심혈관 건강을 개선하는 운동은?",
            question_type='multiple',
            points=15,
            is_required=True,
            order=2
        )
        self.k_q2_c1 = QuestionChoiceFactory(
            question=self.k_q2,
            choice_text="Running",
            choice_text_ko="달리기",
            points=5,
            is_correct=True,
            order=1
        )
        self.k_q2_c2 = QuestionChoiceFactory(
            question=self.k_q2,
            choice_text="Swimming",
            choice_text_ko="수영",
            points=5,
            is_correct=True,
            order=2
        )
        self.k_q2_c3 = QuestionChoiceFactory(
            question=self.k_q2,
            choice_text="Cycling",
            choice_text_ko="자전거",
            points=5,
            is_correct=True,
            order=3
        )
        self.k_q2_c4 = QuestionChoiceFactory(
            question=self.k_q2,
            choice_text="Watching TV",
            choice_text_ko="TV 시청",
            points=0,
            is_correct=False,
            order=4
        )
        
        # Lifestyle questions
        self.l_q1 = MultipleChoiceQuestionFactory(
            category=self.lifestyle_cat,
            question_text="How many hours of sleep do you get per night?",
            question_text_ko="하루 밤에 몇 시간 잠을 자십니까?",
            question_type='single',
            points=10,
            is_required=True,
            order=1
        )
        self.l_q1_c1 = QuestionChoiceFactory(
            question=self.l_q1,
            choice_text="7-9 hours",
            choice_text_ko="7-9시간",
            points=10,
            is_correct=True,
            order=1,
            contributes_to_risk=False,
            risk_weight=Decimal('0.0')
        )
        self.l_q1_c2 = QuestionChoiceFactory(
            question=self.l_q1,
            choice_text="Less than 5 hours",
            choice_text_ko="5시간 미만",
            points=2,
            is_correct=False,
            order=2,
            contributes_to_risk=True,
            risk_weight=Decimal('0.8')
        )
        self.l_q1_c3 = QuestionChoiceFactory(
            question=self.l_q1,
            choice_text="More than 10 hours",
            choice_text_ko="10시간 이상",
            points=5,
            is_correct=False,
            order=3,
            contributes_to_risk=True,
            risk_weight=Decimal('0.3')
        )
        
        # Readiness questions
        self.r_q1 = MultipleChoiceQuestionFactory(
            category=self.readiness_cat,
            question_text="Rate your current energy level (1-5)",
            question_text_ko="현재 에너지 수준을 평가하세요 (1-5)",
            question_type='scale',
            points=10,
            is_required=True,
            order=1
        )
        
        # Create scale choices (1-5)
        for i in range(1, 6):
            QuestionChoiceFactory(
                question=self.r_q1,
                choice_text=str(i),
                choice_text_ko=f"{i}점",
                points=i * 2,  # 2, 4, 6, 8, 10 points
                order=i
            )
    
    def test_complete_mcq_assessment_workflow(self):
        """Test complete MCQ assessment from start to finish."""
        # 1. Start MCQ assessment
        mcq_url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(mcq_url)
        
        assert response.status_code == 200
        assert 'mcq_form' in response.context
        
        # Verify all questions are present in form
        form = response.context['mcq_form']
        assert f'question_{self.k_q1.id}' in form.fields
        assert f'question_{self.k_q2.id}' in form.fields
        assert f'question_{self.l_q1.id}' in form.fields
        assert f'question_{self.r_q1.id}' in form.fields
        
        # 2. Submit MCQ responses
        scale_choice = self.r_q1.choices.get(choice_text="4")  # High energy
        
        form_data = {
            # Knowledge Q1: Correct answer
            f'question_{self.k_q1.id}': self.k_q1_c1.id,
            
            # Knowledge Q2: Select 2 out of 3 correct answers
            f'question_{self.k_q2.id}': [self.k_q2_c1.id, self.k_q2_c2.id],
            
            # Lifestyle Q1: Optimal sleep
            f'question_{self.l_q1.id}': self.l_q1_c1.id,
            
            # Readiness Q1: High energy (4/5)
            f'question_{self.r_q1.id}': scale_choice.id
        }
        
        response = self.client.post(mcq_url, form_data)
        assert response.status_code == 302  # Redirect after successful submission
        
        # 3. Verify responses were saved
        responses = QuestionResponse.objects.filter(assessment=self.assessment)
        assert responses.count() == 4
        
        # Check individual responses
        k1_response = responses.get(question=self.k_q1)
        assert k1_response.points_earned == 10
        assert self.k_q1_c1 in k1_response.selected_choices.all()
        
        k2_response = responses.get(question=self.k_q2)
        assert k2_response.points_earned == 10  # 5 + 5
        selected_k2 = list(k2_response.selected_choices.all())
        assert self.k_q2_c1 in selected_k2
        assert self.k_q2_c2 in selected_k2
        assert self.k_q2_c3 not in selected_k2
        
        l1_response = responses.get(question=self.l_q1)
        assert l1_response.points_earned == 10
        assert self.l_q1_c1 in l1_response.selected_choices.all()
        
        r1_response = responses.get(question=self.r_q1)
        assert r1_response.points_earned == 8  # 4 * 2
        
        # 4. Verify MCQ scores were calculated and saved
        self.assessment.refresh_from_db()
        
        # Knowledge: (10 + 10) / (10 + 15) * 100 = 80%
        assert self.assessment.knowledge_score == 80.0
        
        # Lifestyle: 10 / 10 * 100 = 100%
        assert self.assessment.lifestyle_score == 100.0
        
        # Readiness: 8 / 10 * 100 = 80%
        assert self.assessment.readiness_score == 80.0
        
        # Comprehensive: 80*0.6 + 80*0.15 + 100*0.15 + 80*0.10 = 48 + 12 + 15 + 8 = 83%
        expected_comprehensive = 80*0.6 + 80*0.15 + 100*0.15 + 80*0.10
        assert abs(self.assessment.comprehensive_score - expected_comprehensive) < 0.1
        
        # 5. View MCQ assessment results
        detail_url = reverse('assessments:mcq_assessment_detail', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(detail_url)
        
        assert response.status_code == 200
        assert 'mcq_scores' in response.context
        assert 'mcq_responses' in response.context
        
        mcq_scores = response.context['mcq_scores']
        assert mcq_scores['knowledge_score'] == 80.0
        assert mcq_scores['lifestyle_score'] == 100.0
        assert mcq_scores['readiness_score'] == 80.0
        
        # 6. Verify no risk factors (all good choices)
        engine = MCQScoringEngine(self.assessment)
        risk_factors = engine.extract_risk_factors()
        assert len(risk_factors) == 0  # No risky choices selected
    
    def test_mcq_assessment_with_risk_factors(self):
        """Test MCQ assessment that identifies risk factors."""
        # Submit responses with risk factors
        form_data = {
            # Knowledge Q1: Wrong answer
            f'question_{self.k_q1.id}': self.k_q1_c2.id,
            
            # Lifestyle Q1: Poor sleep (risk factor)
            f'question_{self.l_q1.id}': self.l_q1_c2.id,
            
            # Readiness Q1: Low energy
            f'question_{self.r_q1.id}': self.r_q1.choices.get(choice_text="1").id
        }
        
        mcq_url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.post(mcq_url, form_data)
        assert response.status_code == 302
        
        # Check risk factors were identified
        engine = MCQScoringEngine(self.assessment)
        risk_factors = engine.extract_risk_factors()
        
        assert len(risk_factors) == 1
        assert risk_factors[0]['category'] == 'Lifestyle'
        assert risk_factors[0]['risk_weight'] == 0.8
        assert "sleep" in risk_factors[0]['question'].lower()
    
    def test_mcq_assessment_partial_completion(self):
        """Test MCQ assessment with only some questions answered."""
        # Submit only knowledge questions
        form_data = {
            f'question_{self.k_q1.id}': self.k_q1_c1.id,
            # Leave other questions unanswered
        }
        
        mcq_url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.post(mcq_url, form_data)
        
        # Should show validation errors for required fields
        assert response.status_code == 200  # Form redisplayed with errors
        form = response.context['mcq_form']
        assert not form.is_valid()
        
        # Should have errors for missing required fields
        assert f'question_{self.l_q1.id}' in form.errors
        assert f'question_{self.r_q1.id}' in form.errors
    
    def test_mcq_assessment_update_existing_responses(self):
        """Test updating existing MCQ responses."""
        # Create initial response
        initial_response = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.k_q1,
            points_earned=0,
            selected_choices=[self.k_q1_c2]  # Wrong answer initially
        )
        
        # Submit updated response
        form_data = {
            f'question_{self.k_q1.id}': self.k_q1_c1.id,  # Change to correct answer
            f'question_{self.l_q1.id}': self.l_q1_c1.id,
            f'question_{self.r_q1.id}': self.r_q1.choices.get(choice_text="3").id
        }
        
        mcq_url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.post(mcq_url, form_data)
        assert response.status_code == 302
        
        # Should have updated existing response, not created new one
        responses = QuestionResponse.objects.filter(
            assessment=self.assessment,
            question=self.k_q1
        )
        assert responses.count() == 1
        
        updated_response = responses.first()
        assert updated_response.points_earned == 10  # Now correct
        assert self.k_q1_c1 in updated_response.selected_choices.all()
        assert self.k_q1_c2 not in updated_response.selected_choices.all()


@pytest.mark.django_db
class TestMCQScoringIntegration:
    """Test MCQ scoring integration with assessment system."""
    
    def setup_method(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=75.0
        )
        
        # Create categories
        self.knowledge_cat = QuestionCategoryFactory(
            name="Knowledge",
            weight=Decimal('0.15')
        )
        self.lifestyle_cat = QuestionCategoryFactory(
            name="Lifestyle",
            weight=Decimal('0.15')
        )
        self.readiness_cat = QuestionCategoryFactory(
            name="Readiness",
            weight=Decimal('0.10')
        )
    
    def test_mcq_scoring_affects_comprehensive_score(self):
        """Test that MCQ scores properly affect comprehensive score."""
        # Create questions with different performance levels
        
        # Knowledge: High performance (90%)
        k_q = MultipleChoiceQuestionFactory(category=self.knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=9)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=k_q,
            points_earned=9,
            selected_choices=[k_c]
        )
        
        # Lifestyle: Medium performance (70%)
        l_q = MultipleChoiceQuestionFactory(category=self.lifestyle_cat, points=10)
        l_c = QuestionChoiceFactory(question=l_q, points=7)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=l_q,
            points_earned=7,
            selected_choices=[l_c]
        )
        
        # Readiness: Low performance (50%)
        r_q = MultipleChoiceQuestionFactory(category=self.readiness_cat, points=10)
        r_c = QuestionChoiceFactory(question=r_q, points=5)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=r_q,
            points_earned=5,
            selected_choices=[r_c]
        )
        
        # Calculate MCQ scores
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Verify individual category scores
        assert scores['knowledge_score'] == 90.0
        assert scores['lifestyle_score'] == 70.0
        assert scores['readiness_score'] == 50.0
        
        # Verify comprehensive score calculation
        # Physical: 75 * 0.60 = 45
        # Knowledge: 90 * 0.15 = 13.5
        # Lifestyle: 70 * 0.15 = 10.5
        # Readiness: 50 * 0.10 = 5
        # Total: 45 + 13.5 + 10.5 + 5 = 74
        expected_comprehensive = 75*0.6 + 90*0.15 + 70*0.15 + 50*0.10
        assert abs(scores['comprehensive_score'] - expected_comprehensive) < 0.1
        
        # Update assessment and verify persistence
        self.assessment.knowledge_score = scores['knowledge_score']
        self.assessment.lifestyle_score = scores['lifestyle_score']
        self.assessment.readiness_score = scores['readiness_score']
        self.assessment.comprehensive_score = scores['comprehensive_score']
        self.assessment.save()
        
        self.assessment.refresh_from_db()
        assert self.assessment.knowledge_score == 90.0
        assert self.assessment.comprehensive_score == pytest.approx(expected_comprehensive, rel=0.01)
    
    def test_mcq_scores_without_physical_score(self):
        """Test MCQ scoring when no physical assessment exists."""
        self.assessment.overall_score = None
        self.assessment.save()
        
        # Add MCQ responses
        k_q = MultipleChoiceQuestionFactory(category=self.knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=8)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=k_q,
            points_earned=8,
            selected_choices=[k_c]
        )
        
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        assert scores['knowledge_score'] == 80.0
        # Comprehensive should be based only on MCQ scores
        # Physical: 0 * 0.60 = 0
        # Knowledge: 80 * 0.15 = 12
        # Others: 0
        # Total: 12
        assert scores['comprehensive_score'] == 12.0


@pytest.mark.django_db
class TestMCQSystemPerformance:
    """Test MCQ system performance with larger datasets."""
    
    def setup_method(self):
        """Set up performance test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.assessment = AssessmentFactory(trainer=self.trainer)
        
        # Create multiple categories
        self.categories = []
        for i in range(5):
            category = QuestionCategoryFactory(
                name=f"Category {i}",
                weight=Decimal('0.05'),  # Total weight = 0.25
                order=i
            )
            self.categories.append(category)
    
    def test_performance_many_questions(self):
        """Test performance with many questions."""
        # Create 50 questions across categories
        questions = []
        for category in self.categories:
            for j in range(10):  # 10 questions per category
                question = MultipleChoiceQuestionFactory(
                    category=category,
                    question_text=f"Question {j} in {category.name}",
                    points=10
                )
                # Add 4 choices per question
                for k in range(4):
                    QuestionChoiceFactory(
                        question=question,
                        choice_text=f"Choice {k}",
                        points=10 if k == 0 else 0,  # First choice is correct
                        is_correct=(k == 0)
                    )
                questions.append(question)
        
        # Create responses for all questions
        import time
        start_time = time.time()
        
        for i, question in enumerate(questions):
            correct_choice = question.choices.filter(is_correct=True).first()
            QuestionResponseFactory(
                assessment=self.assessment,
                question=question,
                points_earned=10,
                selected_choices=[correct_choice]
            )
        
        response_creation_time = time.time() - start_time
        
        # Test scoring performance
        start_time = time.time()
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        scoring_time = time.time() - start_time
        
        # Verify correctness
        for category in self.categories:
            category_name = category.name.replace(" ", "").lower()
            if f'{category_name}_score' in scores:
                assert scores[f'{category_name}_score'] == 100.0  # All correct
        
        # Performance assertions (should complete within reasonable time)
        assert response_creation_time < 10.0  # Should create 50 responses in < 10 seconds
        assert scoring_time < 5.0  # Should calculate scores in < 5 seconds
        
        print(f"Created 50 responses in {response_creation_time:.2f}s")
        print(f"Calculated scores in {scoring_time:.2f}s")
    
    def test_performance_many_assessments(self):
        """Test performance with many assessments."""
        category = QuestionCategoryFactory(name="Performance Test")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=8)
        
        # Create 100 assessments with responses
        assessments = []
        import time
        start_time = time.time()
        
        for i in range(100):
            assessment = AssessmentFactory(trainer=self.trainer)
            QuestionResponseFactory(
                assessment=assessment,
                question=question,
                points_earned=8,
                selected_choices=[choice]
            )
            assessments.append(assessment)
        
        creation_time = time.time() - start_time
        
        # Test batch scoring performance
        start_time = time.time()
        for assessment in assessments:
            engine = MCQScoringEngine(assessment)
            scores = engine.calculate_mcq_scores()
        
        batch_scoring_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 15.0  # Should create 100 assessments in < 15 seconds
        assert batch_scoring_time < 10.0  # Should score 100 assessments in < 10 seconds
        
        print(f"Created 100 assessments in {creation_time:.2f}s")
        print(f"Scored 100 assessments in {batch_scoring_time:.2f}s")


@pytest.mark.django_db
class TestMCQSystemRobustness:
    """Test MCQ system robustness and error handling."""
    
    def setup_method(self):
        """Set up test data."""
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.assessment = AssessmentFactory(trainer=self.trainer)
    
    def test_mcq_with_missing_categories(self):
        """Test MCQ scoring with missing standard categories."""
        # Create custom category (not Knowledge/Lifestyle/Readiness)
        custom_category = QuestionCategoryFactory(
            name="Custom Category",
            weight=Decimal('0.20')
        )
        
        question = MultipleChoiceQuestionFactory(
            category=custom_category,
            points=10
        )
        choice = QuestionChoiceFactory(question=question, points=8)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=question,
            points_earned=8,
            selected_choices=[choice]
        )
        
        # Scoring should handle missing standard categories gracefully
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Standard categories should be 0
        assert scores['knowledge_score'] == 0
        assert scores['lifestyle_score'] == 0
        assert scores['readiness_score'] == 0
        
        # Comprehensive should still calculate
        assert scores['comprehensive_score'] >= 0
    
    def test_mcq_with_zero_point_questions(self):
        """Test MCQ scoring with zero-point questions."""
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(
            category=category,
            points=0  # Zero points
        )
        choice = QuestionChoiceFactory(question=question, points=0)
        QuestionResponseFactory(
            assessment=self.assessment,
            question=question,
            points_earned=0,
            selected_choices=[choice]
        )
        
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Should handle zero-point questions gracefully
        assert scores['knowledge_score'] == 0
        assert not any(score < 0 for score in scores.values() if isinstance(score, (int, float)))
    
    def test_mcq_with_corrupt_data(self):
        """Test MCQ scoring with potentially corrupt data."""
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=5)
        
        # Create response with inconsistent data
        response = QuestionResponseFactory(
            assessment=self.assessment,
            question=question,
            points_earned=15,  # More than question max points
            selected_choices=[choice]
        )
        
        # Scoring should handle gracefully
        engine = MCQScoringEngine(self.assessment)
        scores = engine.calculate_mcq_scores()
        
        # Should not crash and should produce reasonable scores
        assert isinstance(scores['knowledge_score'], (int, float))
        assert scores['knowledge_score'] >= 0
    
    def test_mcq_concurrent_access(self):
        """Test MCQ system under concurrent access patterns."""
        category = QuestionCategoryFactory(name="Knowledge")
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=8)
        
        # Simulate concurrent response creation and scoring
        responses = []
        for i in range(10):
            response = QuestionResponseFactory(
                assessment=self.assessment,
                question=question,
                points_earned=8,
                selected_choices=[choice]
            )
            responses.append(response)
        
        # Multiple scoring operations should all work
        engines = []
        for i in range(5):
            engine = MCQScoringEngine(self.assessment)
            scores = engine.calculate_mcq_scores()
            engines.append((engine, scores))
        
        # All engines should produce consistent results
        base_scores = engines[0][1]
        for engine, scores in engines[1:]:
            assert scores['knowledge_score'] == base_scores['knowledge_score']
            assert scores['comprehensive_score'] == base_scores['comprehensive_score']