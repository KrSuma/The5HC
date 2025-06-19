"""
Tests for MCQ API endpoints.

Tests the MCQ-related API views, serializers, and authentication.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.assessments.models import QuestionResponse
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)
from apps.trainers.factories import TrainerFactory, OrganizationFactory
from apps.clients.factories import ClientFactory


@pytest.mark.django_db
class TestMCQCategoryAPI:
    """Test cases for MCQ category API endpoints."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.trainer.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test categories
        self.category1 = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가",
            weight=Decimal('0.15'),
            order=1,
            is_active=True
        )
        self.category2 = QuestionCategoryFactory(
            name="Lifestyle",
            name_ko="생활습관",
            weight=Decimal('0.15'),
            order=2,
            is_active=True
        )
        self.category3 = QuestionCategoryFactory(
            name="Inactive",
            is_active=False
        )
    
    def test_list_categories(self):
        """Test listing MCQ categories."""
        url = reverse('api:questioncategory-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only return active categories
        assert len(data['results']) == 2
        
        # Check ordering
        assert data['results'][0]['name'] == 'Knowledge'
        assert data['results'][1]['name'] == 'Lifestyle'
        
        # Check fields
        category_data = data['results'][0]
        assert 'id' in category_data
        assert 'name' in category_data
        assert 'name_ko' in category_data
        assert 'weight' in category_data
        assert 'order' in category_data
        assert category_data['name_ko'] == "지식 평가"
    
    def test_retrieve_category(self):
        """Test retrieving a specific category."""
        url = reverse('api:questioncategory-detail', kwargs={'pk': self.category1.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['name'] == 'Knowledge'
        assert data['name_ko'] == "지식 평가"
        assert float(data['weight']) == 0.15
        assert data['order'] == 1
    
    def test_filter_categories_by_active(self):
        """Test filtering categories by active status."""
        url = reverse('api:questioncategory-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only return active categories
        assert len(data['results']) == 2
        for category in data['results']:
            assert category['is_active'] is True
    
    def test_unauthorized_access(self):
        """Test unauthorized access to category API."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('api:questioncategory-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMCQQuestionAPI:
    """Test cases for MCQ question API endpoints."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        
        # Authentication
        refresh = RefreshToken.for_user(self.trainer.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test data
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question1 = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="What is fitness?",
            question_text_ko="피트니스란 무엇입니까?",
            question_type='single',
            points=10,
            is_required=True,
            is_active=True
        )
        self.question2 = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="Multiple choice question",
            question_type='multiple',
            points=15,
            is_active=True
        )
        self.inactive_question = MultipleChoiceQuestionFactory(
            category=self.category,
            is_active=False
        )
        
        # Create choices for questions
        self.choice1 = QuestionChoiceFactory(
            question=self.question1,
            choice_text="Physical fitness",
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question1,
            choice_text="Mental fitness",
            points=0,
            is_correct=False
        )
    
    def test_list_questions(self):
        """Test listing MCQ questions."""
        url = reverse('api:multiplechoicequestion-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only return active questions
        assert len(data['results']) == 2
        
        # Check fields
        question_data = data['results'][0]
        assert 'id' in question_data
        assert 'question_text' in question_data
        assert 'question_text_ko' in question_data
        assert 'question_type' in question_data
        assert 'points' in question_data
        assert 'category' in question_data
        assert 'choices' in question_data
    
    def test_retrieve_question_with_choices(self):
        """Test retrieving a question with its choices."""
        url = reverse('api:multiplechoicequestion-detail', kwargs={'pk': self.question1.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['question_text'] == "What is fitness?"
        assert data['question_text_ko'] == "피트니스란 무엇입니까?"
        assert data['question_type'] == 'single'
        assert data['points'] == 10
        assert data['is_required'] is True
        
        # Check choices are included
        assert 'choices' in data
        assert len(data['choices']) == 2
        
        choice_data = data['choices'][0]
        assert 'id' in choice_data
        assert 'choice_text' in choice_data
        assert 'points' in choice_data
        assert 'is_correct' in choice_data
    
    def test_filter_questions_by_category(self):
        """Test filtering questions by category."""
        # Create another category with questions
        other_category = QuestionCategoryFactory(name="Lifestyle")
        other_question = MultipleChoiceQuestionFactory(category=other_category)
        
        url = reverse('api:multiplechoicequestion-list')
        response = self.client.get(url, {'category': self.category.pk})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only return questions from specified category
        for question in data['results']:
            assert question['category']['id'] == self.category.pk
    
    def test_filter_questions_by_type(self):
        """Test filtering questions by type."""
        url = reverse('api:multiplechoicequestion-list')
        response = self.client.get(url, {'question_type': 'single'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only return single choice questions
        for question in data['results']:
            assert question['question_type'] == 'single'
    
    def test_search_questions(self):
        """Test searching questions by text."""
        url = reverse('api:multiplechoicequestion-list')
        response = self.client.get(url, {'search': 'fitness'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return questions containing 'fitness'
        assert len(data['results']) >= 1
        assert any('fitness' in q['question_text'].lower() for q in data['results'])


@pytest.mark.django_db
class TestMCQResponseAPI:
    """Test cases for MCQ response API endpoints."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer
        )
        
        # Authentication
        refresh = RefreshToken.for_user(self.trainer.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test questions
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question1 = MultipleChoiceQuestionFactory(
            category=self.category,
            question_type='single',
            points=10
        )
        self.choice1 = QuestionChoiceFactory(
            question=self.question1,
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question1,
            points=0,
            is_correct=False
        )
        
        self.question2 = MultipleChoiceQuestionFactory(
            category=self.category,
            question_type='multiple',
            points=15
        )
        self.mchoice1 = QuestionChoiceFactory(question=self.question2, points=5)
        self.mchoice2 = QuestionChoiceFactory(question=self.question2, points=5)
        self.mchoice3 = QuestionChoiceFactory(question=self.question2, points=5)
    
    def test_list_responses_for_assessment(self):
        """Test listing responses for a specific assessment."""
        # Create some responses
        response1 = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question1,
            points_earned=10,
            selected_choices=[self.choice1]
        )
        response2 = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question2,
            points_earned=10,
            selected_choices=[self.mchoice1, self.mchoice2]
        )
        
        url = reverse('api:questionresponse-list')
        response = self.client.get(url, {'assessment': self.assessment.pk})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data['results']) == 2
        
        # Check response data
        response_data = data['results'][0]
        assert 'id' in response_data
        assert 'question' in response_data
        assert 'points_earned' in response_data
        assert 'selected_choices' in response_data
        assert 'response_text' in response_data
    
    def test_create_single_choice_response(self):
        """Test creating a single choice response via API."""
        url = reverse('api:questionresponse-list')
        data = {
            'assessment': self.assessment.pk,
            'question': self.question1.pk,
            'selected_choices': [self.choice1.pk],
            'response_text': ''
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        
        assert response_data['points_earned'] == 10
        assert len(response_data['selected_choices']) == 1
        assert response_data['selected_choices'][0]['id'] == self.choice1.pk
        
        # Verify in database
        db_response = QuestionResponse.objects.get(pk=response_data['id'])
        assert db_response.assessment == self.assessment
        assert db_response.question == self.question1
        assert db_response.points_earned == 10
    
    def test_create_multiple_choice_response(self):
        """Test creating a multiple choice response via API."""
        url = reverse('api:questionresponse-list')
        data = {
            'assessment': self.assessment.pk,
            'question': self.question2.pk,
            'selected_choices': [self.mchoice1.pk, self.mchoice2.pk],
            'response_text': ''
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        
        assert response_data['points_earned'] == 10  # 5 + 5
        assert len(response_data['selected_choices']) == 2
        
        # Verify selected choices
        selected_ids = {choice['id'] for choice in response_data['selected_choices']}
        expected_ids = {self.mchoice1.pk, self.mchoice2.pk}
        assert selected_ids == expected_ids
    
    def test_update_existing_response(self):
        """Test updating an existing response via API."""
        # Create initial response
        existing_response = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question1,
            points_earned=0,
            selected_choices=[self.choice2]
        )
        
        url = reverse('api:questionresponse-detail', kwargs={'pk': existing_response.pk})
        data = {
            'assessment': self.assessment.pk,
            'question': self.question1.pk,
            'selected_choices': [self.choice1.pk],  # Change to correct answer
            'response_text': ''
        }
        
        response = self.client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        assert response_data['points_earned'] == 10  # Updated to correct answer
        assert response_data['selected_choices'][0]['id'] == self.choice1.pk
    
    def test_bulk_create_responses(self):
        """Test bulk creating multiple responses."""
        url = reverse('api:questionresponse-bulk-create')
        data = {
            'responses': [
                {
                    'question_id': self.question1.pk,
                    'selected_choices': [self.choice1.pk]
                },
                {
                    'question_id': self.question2.pk,
                    'selected_choices': [self.mchoice1.pk, self.mchoice2.pk]
                }
            ],
            'assessment_id': self.assessment.pk
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        
        assert 'responses' in response_data
        assert len(response_data['responses']) == 2
        
        # Verify responses were created
        assert QuestionResponse.objects.filter(assessment=self.assessment).count() == 2
    
    def test_delete_response(self):
        """Test deleting a response via API."""
        response_obj = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question1
        )
        
        url = reverse('api:questionresponse-detail', kwargs={'pk': response_obj.pk})
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify response was deleted
        assert not QuestionResponse.objects.filter(pk=response_obj.pk).exists()
    
    def test_response_validation(self):
        """Test response validation via API."""
        url = reverse('api:questionresponse-list')
        
        # Test with invalid question ID
        data = {
            'assessment': self.assessment.pk,
            'question': 99999,  # Non-existent question
            'selected_choices': [self.choice1.pk]
        }
        
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test with choices from different question
        other_question = MultipleChoiceQuestionFactory(category=self.category)
        other_choice = QuestionChoiceFactory(question=other_question)
        
        data = {
            'assessment': self.assessment.pk,
            'question': self.question1.pk,
            'selected_choices': [other_choice.pk]  # Choice from different question
        }
        
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMCQAssessmentScoresAPI:
    """Test cases for MCQ assessment scores API."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.client_obj = ClientFactory(trainer=self.trainer)
        self.assessment = AssessmentFactory(
            client=self.client_obj,
            trainer=self.trainer,
            overall_score=80.0,
            knowledge_score=90.0,
            lifestyle_score=75.0,
            readiness_score=65.0,
            comprehensive_score=78.5
        )
        
        # Authentication
        refresh = RefreshToken.for_user(self.trainer.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_assessment_mcq_scores(self):
        """Test getting MCQ scores for an assessment."""
        url = reverse('api:assessment-mcq-scores', kwargs={'pk': self.assessment.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'knowledge_score' in data
        assert 'lifestyle_score' in data
        assert 'readiness_score' in data
        assert 'comprehensive_score' in data
        
        assert data['knowledge_score'] == 90.0
        assert data['lifestyle_score'] == 75.0
        assert data['readiness_score'] == 65.0
        assert data['comprehensive_score'] == 78.5
    
    def test_calculate_assessment_mcq_scores(self):
        """Test calculating MCQ scores for an assessment."""
        # Create MCQ responses
        category = QuestionCategoryFactory(name="Knowledge", weight=Decimal('0.15'))
        question = MultipleChoiceQuestionFactory(category=category, points=10)
        choice = QuestionChoiceFactory(question=question, points=8)
        
        QuestionResponseFactory(
            assessment=self.assessment,
            question=question,
            points_earned=8,
            selected_choices=[choice]
        )
        
        url = reverse('api:assessment-calculate-mcq-scores', kwargs={'pk': self.assessment.pk})
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'scores' in data
        scores = data['scores']
        
        # Knowledge score should be 80% (8/10)
        assert scores['knowledge_score'] == 80.0
        
        # Comprehensive score should be recalculated
        assert 'comprehensive_score' in scores
        
        # Verify assessment was updated
        self.assessment.refresh_from_db()
        assert self.assessment.knowledge_score == 80.0
    
    def test_get_assessment_mcq_insights(self):
        """Test getting MCQ insights for an assessment."""
        url = reverse('api:assessment-mcq-insights', kwargs={'pk': self.assessment.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert 'insights' in data
        insights = data['insights']
        
        # Should have insights for each category with scores
        assert 'knowledge' in insights
        assert 'lifestyle' in insights
        assert 'readiness' in insights
        
        # Check insight structure
        knowledge_insight = insights['knowledge']
        assert 'score' in knowledge_insight
        assert 'level' in knowledge_insight
        assert 'recommendations' in knowledge_insight


@pytest.mark.django_db
class TestMCQAPIPermissions:
    """Test MCQ API permissions and security."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create two different organizations
        self.org1 = OrganizationFactory()
        self.org2 = OrganizationFactory()
        
        self.trainer1 = TrainerFactory(organization=self.org1)
        self.trainer2 = TrainerFactory(organization=self.org2)
        
        self.client1_obj = ClientFactory(trainer=self.trainer1)
        self.client2_obj = ClientFactory(trainer=self.trainer2)
        
        self.assessment1 = AssessmentFactory(
            client=self.client1_obj,
            trainer=self.trainer1
        )
        self.assessment2 = AssessmentFactory(
            client=self.client2_obj,
            trainer=self.trainer2
        )
    
    def test_trainer_can_only_access_own_data(self):
        """Test trainers can only access their own organization's data."""
        # Login as trainer1
        refresh = RefreshToken.for_user(self.trainer1.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Should be able to access own assessment
        url = reverse('api:assessment-mcq-scores', kwargs={'pk': self.assessment1.pk})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Should not be able to access other trainer's assessment
        url = reverse('api:assessment-mcq-scores', kwargs={'pk': self.assessment2.pk})
        response = self.client.get(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied."""
        # No authentication
        self.client.credentials()
        
        url = reverse('api:questioncategory-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        url = reverse('api:multiplechoicequestion-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        url = reverse('api:questionresponse-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_token_access_denied(self):
        """Test access with invalid token is denied."""
        # Invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        url = reverse('api:questioncategory-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMCQAPIErrorHandling:
    """Test MCQ API error handling."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        
        # Authentication
        refresh = RefreshToken.for_user(self.trainer.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    def test_nonexistent_resource_404(self):
        """Test 404 for nonexistent resources."""
        # Nonexistent category
        url = reverse('api:questioncategory-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Nonexistent question
        url = reverse('api:multiplechoicequestion-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Nonexistent response
        url = reverse('api:questionresponse-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_invalid_data_400(self):
        """Test 400 for invalid data."""
        category = QuestionCategoryFactory()
        question = MultipleChoiceQuestionFactory(category=category)
        assessment = AssessmentFactory(trainer=self.trainer)
        
        url = reverse('api:questionresponse-list')
        
        # Missing required fields
        data = {
            'question': question.pk
            # Missing assessment
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Invalid data types
        data = {
            'assessment': 'invalid',  # Should be integer
            'question': question.pk,
            'selected_choices': []
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_method_not_allowed_405(self):
        """Test 405 for unsupported HTTP methods."""
        category = QuestionCategoryFactory()
        
        # Categories are read-only in this API
        url = reverse('api:questioncategory-list')
        response = self.client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        url = reverse('api:questioncategory-detail', kwargs={'pk': category.pk})
        response = self.client.put(url, {}, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED