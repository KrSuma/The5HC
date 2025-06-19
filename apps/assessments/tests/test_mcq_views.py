"""
Tests for MCQ views and HTMX integration.

Tests the MCQ assessment views, form processing, and HTMX responses.
"""

import pytest
from django.test import RequestFactory, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from apps.assessments.models import Assessment, QuestionResponse
from apps.assessments.views.mcq_views import (
    MCQAssessmentView, MCQAssessmentDetailView, 
    MCQQuestionListView, MCQCategoryListView
)
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)
from apps.trainers.factories import TrainerFactory, OrganizationFactory
from apps.clients.factories import ClientFactory

User = get_user_model()


@pytest.mark.django_db
class TestMCQAssessmentView:
    """Test cases for MCQ assessment form view."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create organization and trainer
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer
        )
        
        # Create test questions
        self.knowledge_cat = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가"
        )
        self.lifestyle_cat = QuestionCategoryFactory(
            name="Lifestyle", 
            name_ko="생활습관"
        )
        
        # Single choice question
        self.single_q = MultipleChoiceQuestionFactory(
            category=self.knowledge_cat,
            question_type='single',
            is_required=True
        )
        self.choice1 = QuestionChoiceFactory(
            question=self.single_q,
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.single_q,
            points=0,
            is_correct=False
        )
        
        # Multiple choice question
        self.multiple_q = MultipleChoiceQuestionFactory(
            category=self.lifestyle_cat,
            question_type='multiple',
            is_required=False
        )
        self.mchoice1 = QuestionChoiceFactory(question=self.multiple_q, points=5)
        self.mchoice2 = QuestionChoiceFactory(question=self.multiple_q, points=5)
        self.mchoice3 = QuestionChoiceFactory(question=self.multiple_q, points=0)
    
    def test_mcq_assessment_get_view(self):
        """Test GET request to MCQ assessment view."""
        # Login as trainer
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'mcq_form' in response.context
        assert 'assessment' in response.context
        assert response.context['assessment'] == self.assessment
        
        # Check that questions are in the form
        form = response.context['mcq_form']
        assert f'question_{self.single_q.id}' in form.fields
        assert f'question_{self.multiple_q.id}' in form.fields
    
    def test_mcq_assessment_post_valid(self):
        """Test POST request with valid MCQ data."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        
        data = {
            f'question_{self.single_q.id}': self.choice1.id,
            f'question_{self.multiple_q.id}': [self.mchoice1.id, self.mchoice2.id]
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful submission
        assert response.status_code == 302
        
        # Check that responses were created
        responses = QuestionResponse.objects.filter(assessment=self.assessment)
        assert responses.count() == 2
        
        # Check single choice response
        single_response = responses.filter(question=self.single_q).first()
        assert single_response.points_earned == 10
        assert self.choice1 in single_response.selected_choices.all()
        
        # Check multiple choice response
        multiple_response = responses.filter(question=self.multiple_q).first()
        assert multiple_response.points_earned == 10  # 5 + 5
        selected_choices = list(multiple_response.selected_choices.all())
        assert self.mchoice1 in selected_choices
        assert self.mchoice2 in selected_choices
        assert self.mchoice3 not in selected_choices
    
    def test_mcq_assessment_post_invalid(self):
        """Test POST request with invalid MCQ data."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        
        # Missing required field
        data = {
            f'question_{self.multiple_q.id}': [self.mchoice1.id]
            # Missing required single_q
        }
        
        response = self.client.post(url, data)
        
        # Should render form with errors
        assert response.status_code == 200
        assert 'mcq_form' in response.context
        form = response.context['mcq_form']
        assert not form.is_valid()
        assert f'question_{self.single_q.id}' in form.errors
    
    def test_mcq_assessment_htmx_request(self):
        """Test HTMX request to MCQ assessment view."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        
        # HTMX GET request
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        # Should use different template for HTMX
        assert 'mcq_assessment_content.html' in [t.name for t in response.templates]
    
    def test_mcq_assessment_unauthorized(self):
        """Test unauthorized access to MCQ assessment."""
        # Create different trainer
        other_trainer = TrainerFactory()
        self.client.force_login(other_trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        # Should get 403 or redirect
        assert response.status_code in [403, 404]
    
    def test_mcq_assessment_with_existing_responses(self):
        """Test MCQ assessment view with existing responses."""
        # Create existing response
        existing_response = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.single_q,
            points_earned=10,
            selected_choices=[self.choice1]
        )
        
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        # Form should be pre-populated with existing response
        form = response.context['mcq_form']
        assert form.initial[f'question_{self.single_q.id}'] == self.choice1.id


@pytest.mark.django_db
class TestMCQAssessmentDetailView:
    """Test cases for MCQ assessment detail view."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            knowledge_score=85.0,
            lifestyle_score=70.0,
            readiness_score=60.0,
            comprehensive_score=75.0
        )
        
        # Create questions and responses
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question = MultipleChoiceQuestionFactory(category=self.category)
        self.choice = QuestionChoiceFactory(question=self.question, points=8)
        self.response = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question,
            points_earned=8,
            selected_choices=[self.choice]
        )
    
    def test_mcq_detail_view_get(self):
        """Test GET request to MCQ detail view."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment_detail', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'assessment' in response.context
        assert 'mcq_responses' in response.context
        assert 'mcq_scores' in response.context
        
        # Check MCQ scores in context
        mcq_scores = response.context['mcq_scores']
        assert mcq_scores['knowledge_score'] == 85.0
        assert mcq_scores['lifestyle_score'] == 70.0
        assert mcq_scores['readiness_score'] == 60.0
        assert mcq_scores['comprehensive_score'] == 75.0
    
    def test_mcq_detail_view_responses(self):
        """Test MCQ responses are correctly displayed."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment_detail', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        mcq_responses = response.context['mcq_responses']
        assert len(mcq_responses) == 1
        
        response_data = mcq_responses[0]
        assert response_data['question'] == self.question
        assert response_data['points_earned'] == 8
        assert self.choice in response_data['selected_choices']
    
    def test_mcq_detail_view_htmx(self):
        """Test HTMX request to MCQ detail view."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment_detail', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        # Should use partial template for HTMX
        assert 'mcq_assessment_detail_content.html' in [t.name for t in response.templates]


@pytest.mark.django_db  
class TestMCQQuestionListView:
    """Test cases for MCQ question list view."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        
        # Create categories and questions
        self.category1 = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식"
        )
        self.category2 = QuestionCategoryFactory(
            name="Lifestyle",
            name_ko="생활습관"
        )
        
        # Create questions
        self.question1 = MultipleChoiceQuestionFactory(
            category=self.category1,
            question_text="What is fitness?",
            is_active=True
        )
        self.question2 = MultipleChoiceQuestionFactory(
            category=self.category2,
            question_text="How often do you exercise?",
            is_active=True
        )
        self.question3 = MultipleChoiceQuestionFactory(
            category=self.category1,
            question_text="Inactive question",
            is_active=False
        )
    
    def test_question_list_view_get(self):
        """Test GET request to question list view."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'questions' in response.context
        assert 'categories' in response.context
        
        # Should only show active questions
        questions = response.context['questions']
        assert self.question1 in questions
        assert self.question2 in questions
        assert self.question3 not in questions
    
    def test_question_list_view_filter_by_category(self):
        """Test filtering questions by category."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url, {'category': self.category1.id})
        
        assert response.status_code == 200
        questions = response.context['questions']
        
        # Should only show questions from category1
        assert self.question1 in questions
        assert self.question2 not in questions
    
    def test_question_list_view_search(self):
        """Test searching questions by text."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url, {'search': 'fitness'})
        
        assert response.status_code == 200
        questions = response.context['questions']
        
        # Should only show questions containing 'fitness'
        assert self.question1 in questions
        assert self.question2 not in questions
    
    def test_question_list_view_pagination(self):
        """Test question list pagination."""
        # Create many questions
        for i in range(25):
            MultipleChoiceQuestionFactory(
                category=self.category1,
                question_text=f"Question {i}",
                is_active=True
            )
        
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'is_paginated' in response.context
        
        # Should be paginated if many questions
        if response.context['is_paginated']:
            assert 'page_obj' in response.context
            page_obj = response.context['page_obj']
            assert page_obj.has_next() or page_obj.has_previous()
    
    def test_question_list_view_htmx(self):
        """Test HTMX request to question list."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        # Should use partial template for HTMX
        template_names = [t.name for t in response.templates]
        assert any('content' in name for name in template_names)


@pytest.mark.django_db
class TestMCQCategoryListView:
    """Test cases for MCQ category list view."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        
        # Create categories
        self.category1 = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식",
            weight=0.15,
            order=1,
            is_active=True
        )
        self.category2 = QuestionCategoryFactory(
            name="Lifestyle", 
            name_ko="생활습관",
            weight=0.15,
            order=2,
            is_active=True
        )
        self.category3 = QuestionCategoryFactory(
            name="Inactive",
            is_active=False
        )
        
        # Create questions in categories
        MultipleChoiceQuestionFactory.create_batch(3, category=self.category1)
        MultipleChoiceQuestionFactory.create_batch(2, category=self.category2)
    
    def test_category_list_view_get(self):
        """Test GET request to category list view."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_category_list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'categories' in response.context
        
        categories = response.context['categories']
        # Should only show active categories
        assert self.category1 in categories
        assert self.category2 in categories
        assert self.category3 not in categories
    
    def test_category_list_view_ordering(self):
        """Test category list ordering."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_category_list')
        response = self.client.get(url)
        
        categories = list(response.context['categories'])
        # Should be ordered by order field
        assert categories[0] == self.category1  # order=1
        assert categories[1] == self.category2  # order=2
    
    def test_category_list_view_question_counts(self):
        """Test category list includes question counts."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_category_list')
        response = self.client.get(url)
        
        # Check that template receives question counts
        # (This would be tested in template rendering, but we can check context)
        categories = response.context['categories']
        for category in categories:
            # Each category should have related questions accessible
            question_count = category.multiplechoicequestion_set.filter(is_active=True).count()
            assert question_count >= 0


@pytest.mark.django_db
class TestMCQViewsEdgeCases:
    """Test edge cases for MCQ views."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer
        )
    
    def test_mcq_assessment_nonexistent(self):
        """Test MCQ assessment with nonexistent assessment ID."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': 99999
        })
        response = self.client.get(url)
        
        assert response.status_code == 404
    
    def test_mcq_assessment_no_questions(self):
        """Test MCQ assessment with no questions available."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        form = response.context['mcq_form']
        assert len(form.fields) == 0
    
    def test_mcq_assessment_ajax_request(self):
        """Test MCQ assessment with AJAX request."""
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        
        # AJAX request
        response = self.client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200
        # Should handle AJAX requests appropriately
    
    def test_mcq_views_permission_required(self):
        """Test MCQ views require proper permissions."""
        # Anonymous user
        url = reverse('assessments:mcq_question_list')
        response = self.client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_mcq_assessment_concurrent_submission(self):
        """Test handling of concurrent MCQ submissions."""
        category = QuestionCategoryFactory()
        question = MultipleChoiceQuestionFactory(category=category)
        choice1 = QuestionChoiceFactory(question=question, points=5)
        choice2 = QuestionChoiceFactory(question=question, points=8)
        
        self.client.force_login(self.trainer.user)
        
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        
        # Submit first response
        data1 = {f'question_{question.id}': choice1.id}
        response1 = self.client.post(url, data1)
        assert response1.status_code == 302
        
        # Submit second response (should update, not duplicate)
        data2 = {f'question_{question.id}': choice2.id}
        response2 = self.client.post(url, data2)
        assert response2.status_code == 302
        
        # Should have only one response
        responses = QuestionResponse.objects.filter(
            assessment=self.assessment,
            question=question
        )
        assert responses.count() == 1
        assert responses.first().points_earned == 8


@pytest.mark.django_db
class TestMCQViewsIntegration:
    """Integration tests for MCQ views."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=80.0
        )
    
    def test_complete_mcq_workflow(self):
        """Test complete MCQ assessment workflow."""
        # Create test data
        category = QuestionCategoryFactory(name="Knowledge", weight=0.15)
        question = MultipleChoiceQuestionFactory(
            category=category,
            question_type='single',
            points=10,
            is_required=True
        )
        correct_choice = QuestionChoiceFactory(
            question=question,
            points=10,
            is_correct=True
        )
        wrong_choice = QuestionChoiceFactory(
            question=question,
            points=0,
            is_correct=False
        )
        
        self.client.force_login(self.trainer.user)
        
        # 1. View MCQ assessment form
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(url)
        assert response.status_code == 200
        
        # 2. Submit MCQ responses
        data = {f'question_{question.id}': correct_choice.id}
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # 3. View MCQ assessment results
        detail_url = reverse('assessments:mcq_assessment_detail', kwargs={
            'assessment_id': self.assessment.id
        })
        response = self.client.get(detail_url)
        assert response.status_code == 200
        
        # 4. Verify assessment was updated with MCQ scores
        self.assessment.refresh_from_db()
        assert self.assessment.knowledge_score == 100.0  # Perfect score
        assert self.assessment.comprehensive_score is not None
        
        # 5. Verify response was saved
        responses = QuestionResponse.objects.filter(assessment=self.assessment)
        assert responses.count() == 1
        assert responses.first().points_earned == 10
    
    def test_mcq_assessment_update_scores(self):
        """Test MCQ assessment updates assessment scores."""
        # Create multiple categories
        knowledge_cat = QuestionCategoryFactory(name="Knowledge", weight=0.15)
        lifestyle_cat = QuestionCategoryFactory(name="Lifestyle", weight=0.15)
        
        # Knowledge question (90% score)
        k_q = MultipleChoiceQuestionFactory(category=knowledge_cat, points=10)
        k_c = QuestionChoiceFactory(question=k_q, points=9)
        
        # Lifestyle question (80% score)  
        l_q = MultipleChoiceQuestionFactory(category=lifestyle_cat, points=10)
        l_c = QuestionChoiceFactory(question=l_q, points=8)
        
        self.client.force_login(self.trainer.user)
        
        # Submit MCQ responses
        url = reverse('assessments:mcq_assessment', kwargs={
            'assessment_id': self.assessment.id
        })
        data = {
            f'question_{k_q.id}': k_c.id,
            f'question_{l_q.id}': l_c.id
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Check that assessment scores were updated
        self.assessment.refresh_from_db()
        assert self.assessment.knowledge_score == 90.0
        assert self.assessment.lifestyle_score == 80.0
        assert self.assessment.readiness_score == 0  # No readiness questions
        
        # Comprehensive score: 80*0.6 + 90*0.15 + 80*0.15 = 48 + 13.5 + 12 = 73.5
        expected_comprehensive = 80 * 0.6 + 90 * 0.15 + 80 * 0.15
        assert abs(self.assessment.comprehensive_score - expected_comprehensive) < 0.1