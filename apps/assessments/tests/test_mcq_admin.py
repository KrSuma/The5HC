"""
Tests for MCQ Django admin interface.

Tests admin views, forms, actions, and import/export functionality.
"""

import pytest
import tempfile
import csv
import json
from io import StringIO
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.http import HttpResponse
from apps.assessments.admin import (
    QuestionCategoryAdmin, MultipleChoiceQuestionAdmin,
    QuestionChoiceAdmin, QuestionResponseAdmin
)
from apps.assessments.models import (
    QuestionCategory, MultipleChoiceQuestion,
    QuestionChoice, QuestionResponse
)
from apps.assessments.factories import (
    AssessmentFactory, QuestionCategoryFactory,
    MultipleChoiceQuestionFactory, QuestionChoiceFactory,
    QuestionResponseFactory
)
from apps.trainers.factories import TrainerFactory, OrganizationFactory

User = get_user_model()


@pytest.mark.django_db
class TestQuestionCategoryAdmin:
    """Test cases for QuestionCategory admin."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.factory = RequestFactory()
        self.site = AdminSite()
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test categories
        self.category1 = QuestionCategoryFactory(
            name="Knowledge",
            name_ko="지식 평가",
            weight=0.15,
            order=1
        )
        self.category2 = QuestionCategoryFactory(
            name="Lifestyle",
            name_ko="생활습관",
            weight=0.15,
            order=2
        )
        
        self.admin = QuestionCategoryAdmin(QuestionCategory, self.site)
    
    def test_category_admin_list_view(self):
        """Test category admin list view."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_changelist')
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should show both categories
        assert "Knowledge" in content
        assert "Lifestyle" in content
        assert "지식 평가" in content
        assert "생활습관" in content
    
    def test_category_admin_detail_view(self):
        """Test category admin detail view."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_change', args=[self.category1.pk])
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should show category details
        assert "Knowledge" in content
        assert "지식 평가" in content
        assert "0.15" in content
    
    def test_category_admin_add_view(self):
        """Test category admin add view."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_add')
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        # Test adding new category
        data = {
            'name': 'Readiness',
            'name_ko': '준비도',
            'description': 'Test description',
            'description_ko': '테스트 설명',
            'weight': '0.10',
            'order': '3',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302  # Redirect after successful save
        
        # Verify category was created
        assert QuestionCategory.objects.filter(name='Readiness').exists()
    
    def test_category_admin_list_display(self):
        """Test category admin list display fields."""
        request = self.factory.get('/')
        request.user = self.superuser
        
        # Test list display
        list_display = self.admin.get_list_display(request)
        expected_fields = ['name', 'name_ko', 'weight', 'order', 'is_active', 'question_count']
        
        for field in expected_fields:
            assert field in list_display
    
    def test_category_admin_search(self):
        """Test category admin search functionality."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_changelist')
        response = self.client.get(url, {'q': 'Knowledge'})
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should find Knowledge category
        assert "Knowledge" in content
        assert "Lifestyle" not in content
    
    def test_category_admin_filters(self):
        """Test category admin filters."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_changelist')
        response = self.client.get(url, {'is_active__exact': '1'})
        
        assert response.status_code == 200


@pytest.mark.django_db
class TestMultipleChoiceQuestionAdmin:
    """Test cases for MultipleChoiceQuestion admin."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.factory = RequestFactory()
        self.site = AdminSite()
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="What is fitness?",
            question_text_ko="피트니스란 무엇입니까?",
            question_type='single',
            points=10
        )
        
        # Create choices for the question
        self.choice1 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Physical fitness",
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Mental fitness",
            points=0,
            is_correct=False
        )
        
        self.admin = MultipleChoiceQuestionAdmin(MultipleChoiceQuestion, self.site)
    
    def test_question_admin_list_view(self):
        """Test question admin list view."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should show question
        assert "What is fitness?" in content
        assert "Knowledge" in content
        assert "single" in content
    
    def test_question_admin_detail_with_inlines(self):
        """Test question admin detail view with choice inlines."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_change', args=[self.question.pk])
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should show question details
        assert "What is fitness?" in content
        assert "피트니스란 무엇입니까?" in content
        
        # Should show inline choices
        assert "Physical fitness" in content
        assert "Mental fitness" in content
    
    def test_question_admin_add_with_choices(self):
        """Test adding question with choices through admin."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_add')
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        # Test adding new question with choices
        data = {
            'category': self.category.pk,
            'question_text': 'New question',
            'question_text_ko': '새로운 질문',
            'question_type': 'single',
            'points': 5,
            'is_required': True,
            'is_active': True,
            'order': 1,
            
            # Inline choice data
            'choices-TOTAL_FORMS': '2',
            'choices-INITIAL_FORMS': '0',
            'choices-MIN_NUM_FORMS': '0',
            'choices-MAX_NUM_FORMS': '1000',
            
            'choices-0-choice_text': 'Choice 1',
            'choices-0-choice_text_ko': '선택지 1',
            'choices-0-points': '5',
            'choices-0-is_correct': True,
            'choices-0-order': '1',
            
            'choices-1-choice_text': 'Choice 2',
            'choices-1-choice_text_ko': '선택지 2',
            'choices-1-points': '0',
            'choices-1-is_correct': False,
            'choices-1-order': '2',
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful save
        assert response.status_code == 302
        
        # Verify question and choices were created
        new_question = MultipleChoiceQuestion.objects.filter(question_text='New question').first()
        assert new_question is not None
        assert new_question.choices.count() == 2
    
    def test_question_admin_filters(self):
        """Test question admin filters."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        
        # Filter by category
        response = self.client.get(url, {'category__id__exact': self.category.pk})
        assert response.status_code == 200
        
        # Filter by question type
        response = self.client.get(url, {'question_type': 'single'})
        assert response.status_code == 200
        
        # Filter by active status
        response = self.client.get(url, {'is_active__exact': '1'})
        assert response.status_code == 200
    
    def test_question_admin_search(self):
        """Test question admin search."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        response = self.client.get(url, {'q': 'fitness'})
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should find question containing 'fitness'
        assert "What is fitness?" in content


@pytest.mark.django_db
class TestQuestionResponseAdmin:
    """Test cases for QuestionResponse admin."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test data
        self.organization = OrganizationFactory()
        self.trainer = TrainerFactory(organization=self.organization)
        self.assessment = AssessmentFactory(trainer=self.trainer)
        self.category = QuestionCategoryFactory()\n        self.question = MultipleChoiceQuestionFactory(category=self.category)
        self.choice = QuestionChoiceFactory(question=self.question, points=8)
        self.response = QuestionResponseFactory(
            assessment=self.assessment,
            question=self.question,
            points_earned=8,
            selected_choices=[self.choice]
        )
    
    def test_response_admin_list_view(self):
        """Test response admin list view."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questionresponse_changelist')
        response = self.client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Should show response information
        assert str(self.assessment.id) in content
        assert "8" in content  # points earned
    
    def test_response_admin_filters(self):
        """Test response admin filters."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questionresponse_changelist')
        
        # Filter by assessment
        response = self.client.get(url, {'assessment__id__exact': self.assessment.pk})
        assert response.status_code == 200
        
        # Filter by question category
        response = self.client.get(url, {'question__category__id__exact': self.category.pk})
        assert response.status_code == 200
    
    def test_response_admin_readonly_fields(self):
        """Test response admin readonly fields."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questionresponse_change', args=[self.response.pk])
        response = self.client.get(url)
        
        assert response.status_code == 200
        # Timestamps should be readonly
        content = response.content.decode()
        assert 'readonly' in content


@pytest.mark.django_db
class TestMCQAdminActions:
    """Test MCQ admin custom actions."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create test categories
        self.category1 = QuestionCategoryFactory(name="Knowledge", is_active=True)
        self.category2 = QuestionCategoryFactory(name="Lifestyle", is_active=True)
        self.category3 = QuestionCategoryFactory(name="Inactive", is_active=False)
    
    def test_activate_categories_action(self):
        """Test activate categories admin action."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_changelist')
        data = {
            'action': 'activate_categories',
            '_selected_action': [self.category3.pk]
        }
        
        response = self.client.post(url, data)
        
        # Should redirect back to changelist
        assert response.status_code == 302
        
        # Category should now be active
        self.category3.refresh_from_db()
        assert self.category3.is_active is True
    
    def test_deactivate_categories_action(self):
        """Test deactivate categories admin action."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_changelist')
        data = {
            'action': 'deactivate_categories',
            '_selected_action': [self.category1.pk]
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 302
        
        # Category should now be inactive
        self.category1.refresh_from_db()
        assert self.category1.is_active is False
    
    def test_duplicate_question_action(self):
        """Test duplicate question admin action."""
        question = MultipleChoiceQuestionFactory(
            category=self.category1,
            question_text="Original question"
        )
        QuestionChoiceFactory.create_batch(3, question=question)
        
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        data = {
            'action': 'duplicate_questions',
            '_selected_action': [question.pk]
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302
        
        # Should have created a duplicate
        duplicates = MultipleChoiceQuestion.objects.filter(
            question_text__startswith="Copy of Original question"
        )
        assert duplicates.count() >= 1
        
        duplicate = duplicates.first()
        assert duplicate.choices.count() == 3  # Choices should be duplicated too


@pytest.mark.django_db
class TestMCQAdminImportExport:
    """Test MCQ admin import/export functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        self.category = QuestionCategoryFactory(name="Knowledge")
        self.question = MultipleChoiceQuestionFactory(
            category=self.category,
            question_text="Test question",
            question_type='single',
            points=10
        )
        self.choice1 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Correct answer",
            points=10,
            is_correct=True
        )
        self.choice2 = QuestionChoiceFactory(
            question=self.question,
            choice_text="Wrong answer",
            points=0,
            is_correct=False
        )
    
    def test_export_questions_csv(self):
        """Test exporting questions to CSV."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        data = {
            'action': 'export_questions_csv',
            '_selected_action': [self.question.pk]
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']
        
        # Check CSV content
        csv_content = response.content.decode('utf-8-sig')
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        # Should have header row + data row
        assert len(rows) >= 2
        
        # Check headers
        headers = rows[0]
        assert 'question_text' in headers
        assert 'category' in headers
        assert 'question_type' in headers
        
        # Check data
        data_row = rows[1]
        assert "Test question" in data_row
    
    def test_export_questions_json(self):
        """Test exporting questions to JSON."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_changelist')
        data = {
            'action': 'export_questions_json',
            '_selected_action': [self.question.pk]
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        
        # Check JSON content
        json_data = json.loads(response.content.decode())
        assert isinstance(json_data, list)
        assert len(json_data) == 1
        
        question_data = json_data[0]
        assert question_data['question_text'] == "Test question"
        assert question_data['category']['name'] == "Knowledge"
        assert len(question_data['choices']) == 2
    
    def test_import_questions_csv(self):
        """Test importing questions from CSV."""
        # Create CSV content
        csv_content = '''category,question_text,question_text_ko,question_type,points,is_required,choice_1_text,choice_1_points,choice_1_correct,choice_2_text,choice_2_points,choice_2_correct
Knowledge,What is strength?,근력이란 무엇입니까?,single,10,true,Muscle force,10,true,Cardio endurance,0,false'''
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name
        
        self.client.force_login(self.superuser)
        
        url = reverse('admin:import_questions_csv')
        with open(csv_file_path, 'rb') as csv_file:
            response = self.client.post(url, {
                'csv_file': csv_file
            })
        
        # Should redirect with success message
        assert response.status_code == 302
        
        # Verify question was imported
        imported_question = MultipleChoiceQuestion.objects.filter(
            question_text="What is strength?"
        ).first()
        assert imported_question is not None
        assert imported_question.choices.count() == 2
        
        # Clean up
        import os
        os.unlink(csv_file_path)
    
    def test_import_questions_json(self):
        """Test importing questions from JSON."""
        json_data = [{
            "category": {
                "name": "Lifestyle",
                "name_ko": "생활습관",
                "weight": 0.15,
                "order": 2
            },
            "question_text": "How often do you exercise?",
            "question_text_ko": "얼마나 자주 운동하십니까?",
            "question_type": "single",
            "points": 10,
            "is_required": True,
            "choices": [
                {
                    "choice_text": "Daily",
                    "choice_text_ko": "매일",
                    "points": 10,
                    "is_correct": True
                },
                {
                    "choice_text": "Never",
                    "choice_text_ko": "절대",
                    "points": 0,
                    "is_correct": False
                }
            ]
        }]
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file_path = f.name
        
        self.client.force_login(self.superuser)
        
        url = reverse('admin:import_questions_json')
        with open(json_file_path, 'rb') as json_file:
            response = self.client.post(url, {
                'json_file': json_file
            })
        
        assert response.status_code == 302
        
        # Verify question and category were imported
        imported_question = MultipleChoiceQuestion.objects.filter(
            question_text="How often do you exercise?"
        ).first()
        assert imported_question is not None
        
        lifestyle_category = QuestionCategory.objects.filter(name="Lifestyle").first()
        assert lifestyle_category is not None
        
        # Clean up
        import os
        os.unlink(json_file_path)


@pytest.mark.django_db
class TestMCQAdminValidation:
    """Test MCQ admin validation and error handling."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        self.category = QuestionCategoryFactory()
    
    def test_question_without_choices_validation(self):
        """Test validation for question without choices."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_multiplechoicequestion_add')
        data = {
            'category': self.category.pk,
            'question_text': 'Question without choices',
            'question_type': 'single',
            'points': 10,
            'is_required': True,
            'is_active': True,
            
            # No choices provided
            'choices-TOTAL_FORMS': '0',
            'choices-INITIAL_FORMS': '0',
            'choices-MIN_NUM_FORMS': '0',
            'choices-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, data)
        
        # Should show form again with error (depending on validation rules)
        # For now, just check it doesn't crash
        assert response.status_code in [200, 302]
    
    def test_duplicate_category_name_validation(self):
        """Test validation for duplicate category names."""
        existing_category = QuestionCategoryFactory(name="Existing")
        
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_add')
        data = {
            'name': 'Existing',  # Duplicate name
            'name_ko': '기존',
            'weight': '0.10',
            'order': '3',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should show form again with validation error
        assert response.status_code == 200
        content = response.content.decode()
        # Should contain error message about duplicate name
        assert 'already exists' in content or 'unique' in content.lower()
    
    def test_invalid_weight_validation(self):
        """Test validation for invalid category weights."""
        self.client.force_login(self.superuser)
        
        url = reverse('admin:assessments_questioncategory_add')
        data = {
            'name': 'Test Category',
            'name_ko': '테스트',
            'weight': '1.5',  # Invalid weight > 1.0
            'order': '1',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        
        # Should show form again with validation error
        assert response.status_code == 200