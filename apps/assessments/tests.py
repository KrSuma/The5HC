from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import Assessment
from .forms import AssessmentForm, AssessmentSearchForm
from apps.clients.models import Client as ClientModel

User = get_user_model()


class AssessmentModelTestCase(TestCase):
    """Test suite for Assessment model"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.trainer = User.objects.create_user(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com'
        )
        
    def test_assessment_creation(self):
        """Test assessment creation with valid data"""
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            assessment_date=date.today(),
            # Physical tests
            height=175.0,
            weight=70.0,
            body_fat_percentage=15.0,
            muscle_mass=55.0,
            # Cardio tests
            resting_heart_rate=60,
            max_heart_rate=180,
            vo2_max=45.0,
            cardio_endurance_time=900,  # 15 minutes
            # Strength tests
            bench_press_1rm=80.0,
            squat_1rm=100.0,
            deadlift_1rm=120.0,
            push_ups=30,
            pull_ups=10,
            plank_time=120,  # 2 minutes
            # Flexibility tests
            sit_and_reach=25.0,
            shoulder_flexibility=20.0,
            # Balance tests
            single_leg_stand_time=45,
            balance_beam_time=30,
            # Agility tests
            sprint_20m_time=3.5,
            agility_ladder_time=12.0,
            cone_drill_time=8.5,
            # Power tests
            vertical_jump=50.0,
            broad_jump=200.0,
            medicine_ball_throw=8.0,
            # Functional tests
            functional_movement_score=18,
            overall_score=85.5
        )
        
        self.assertEqual(assessment.trainer, self.trainer)
        self.assertEqual(assessment.client, self.client)
        self.assertEqual(assessment.overall_score, 85.5)
        
    def test_assessment_str_method(self):
        """Test assessment string representation"""
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            assessment_date=date.today(),
            overall_score=85.0
        )
        expected = f"Assessment for {self.client.name} on {date.today()}"
        self.assertEqual(str(assessment), expected)
        
    def test_assessment_bmi_calculation(self):
        """Test BMI calculation in assessment"""
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            height=175.0,  # 1.75m
            weight=70.0,   # 70kg
            overall_score=85.0
        )
        expected_bmi = 70.0 / (1.75 ** 2)
        self.assertAlmostEqual(assessment.bmi, expected_bmi, places=2)
        
    def test_assessment_default_ordering(self):
        """Test assessment default ordering"""
        yesterday = date.today() - timedelta(days=1)
        
        assessment1 = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            assessment_date=yesterday,
            overall_score=80.0
        )
        assessment2 = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client,
            assessment_date=date.today(),
            overall_score=85.0
        )
        
        assessments = list(Assessment.objects.all())
        # Should be ordered by newest first
        self.assertEqual(assessments[0], assessment2)
        self.assertEqual(assessments[1], assessment1)


class AssessmentFormTestCase(TestCase):
    """Test suite for Assessment forms"""
    
    def setUp(self):
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        
    def test_assessment_form_valid_data(self):
        """Test assessment form with valid data"""
        form_data = {
            'client': self.client.pk,
            'assessment_date': date.today(),
            'height': '175.0',
            'weight': '70.0',
            'body_fat_percentage': '15.0',
            'muscle_mass': '55.0',
            'resting_heart_rate': '60',
            'max_heart_rate': '180',
            'vo2_max': '45.0',
            'cardio_endurance_time': '900',
            'bench_press_1rm': '80.0',
            'squat_1rm': '100.0',
            'deadlift_1rm': '120.0',
            'push_ups': '30',
            'pull_ups': '10',
            'plank_time': '120',
            'sit_and_reach': '25.0',
            'shoulder_flexibility': '20.0',
            'single_leg_stand_time': '45',
            'balance_beam_time': '30',
            'sprint_20m_time': '3.5',
            'agility_ladder_time': '12.0',
            'cone_drill_time': '8.5',
            'vertical_jump': '50.0',
            'broad_jump': '200.0',
            'medicine_ball_throw': '8.0',
            'functional_movement_score': '18',
            'overall_score': '85.5'
        }
        form = AssessmentForm(trainer=self.trainer, data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_assessment_form_missing_required_field(self):
        """Test assessment form with missing required field"""
        form_data = {
            'assessment_date': date.today(),
            'height': '175.0',
            'weight': '70.0'
        }
        form = AssessmentForm(trainer=self.trainer, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('client', form.errors)
        
    def test_assessment_form_invalid_score_range(self):
        """Test assessment form with invalid score values"""
        form_data = {
            'client': self.client.pk,
            'assessment_date': date.today(),
            'overall_score': '150.0'  # Too high (max 100)
        }
        form = AssessmentForm(trainer=self.trainer, data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_assessment_search_form(self):
        """Test assessment search form functionality"""
        form_data = {
            'client': self.client.pk,
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
            'score_min': '80',
            'score_max': '100'
        }
        form = AssessmentSearchForm(trainer=self.trainer, data=form_data)
        self.assertTrue(form.is_valid())


class AssessmentViewTestCase(TestCase):
    """Test suite for Assessment views"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        self.other_trainer = User.objects.create_user(
            username='other_trainer',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test clients
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = ClientModel.objects.create(
            trainer=self.other_trainer,
            name='Other Client',
            email='other@example.com'
        )
        
        # Create test assessment
        self.test_assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            assessment_date=date.today(),
            height=175.0,
            weight=70.0,
            overall_score=85.0
        )
        
        # Assessment belonging to other trainer
        self.other_assessment = Assessment.objects.create(
            trainer=self.other_trainer,
            client=self.other_client,
            assessment_date=date.today(),
            overall_score=80.0
        )
        
    def test_assessment_list_view_requires_login(self):
        """Test assessment list requires authentication"""
        url = reverse('assessments:list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_assessment_list_view_authenticated(self):
        """Test assessment list view with authenticated user"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        # Should not see other trainer's assessments
        self.assertNotContains(response, 'Other Client')
        
    def test_assessment_list_search_functionality(self):
        """Test assessment list search functionality"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        response = self.client_test.get(url, {'client': self.test_client.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        
    def test_assessment_list_htmx_partial(self):
        """Test assessment list HTMX partial response"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        response = self.client_test.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assessments/assessment_list_partial.html')
        
    def test_assessment_detail_view(self):
        """Test assessment detail view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:detail', kwargs={'pk': self.test_assessment.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        self.assertContains(response, '85.0')  # Overall score
        
    def test_assessment_detail_unauthorized_access(self):
        """Test assessment detail view for unauthorized assessment"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:detail', kwargs={'pk': self.other_assessment.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_assessment_add_view_get(self):
        """Test assessment add view GET request"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:add')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AssessmentForm)
        
    def test_assessment_add_view_with_client_param(self):
        """Test assessment add view with client parameter"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:add')
        response = self.client_test.get(url, {'client': self.test_client.pk})
        self.assertEqual(response.status_code, 200)
        # Form should be pre-populated with client
        self.assertEqual(response.context['form'].initial['client'], self.test_client.pk)
        
    def test_assessment_add_view_post_valid(self):
        """Test assessment add view with valid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:add')
        data = {
            'client': self.test_client.pk,
            'assessment_date': date.today(),
            'height': '180.0',
            'weight': '75.0',
            'body_fat_percentage': '12.0',
            'resting_heart_rate': '65',
            'bench_press_1rm': '85.0',
            'push_ups': '35',
            'overall_score': '90.0'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check assessment was created
        new_assessment = Assessment.objects.get(
            client=self.test_client,
            height=180.0
        )
        self.assertEqual(new_assessment.trainer, self.trainer)
        self.assertEqual(new_assessment.overall_score, 90.0)
        
    def test_assessment_add_view_post_invalid(self):
        """Test assessment add view with invalid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:add')
        data = {
            'assessment_date': date.today(),
            'overall_score': '150.0'  # Missing client, invalid score
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'client', 'This field is required.')
        
    def test_assessment_delete_view(self):
        """Test assessment delete view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:delete', kwargs={'pk': self.test_assessment.pk})
        response = self.client_test.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Check assessment was deleted
        with self.assertRaises(Assessment.DoesNotExist):
            Assessment.objects.get(pk=self.test_assessment.pk)
            
    def test_assessment_delete_unauthorized(self):
        """Test assessment delete for unauthorized assessment"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:delete', kwargs={'pk': self.other_assessment.pk})
        response = self.client_test.post(url)
        self.assertEqual(response.status_code, 404)
        
        # Check assessment was not deleted
        self.assertTrue(Assessment.objects.filter(pk=self.other_assessment.pk).exists())


class AssessmentScoringTestCase(TestCase):
    """Test assessment scoring calculations"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        
    def test_score_calculation_endpoint(self):
        """Test AJAX score calculation endpoint"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:calculate_scores')
        
        # Test with some assessment data
        data = {
            'height': '175.0',
            'weight': '70.0',
            'bench_press_1rm': '80.0',
            'push_ups': '30',
            'vo2_max': '45.0'
        }
        response = self.client_test.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Response should contain calculated scores
        json_response = json.loads(response.content)
        self.assertIn('physical_score', json_response)
        self.assertIn('cardio_score', json_response)
        self.assertIn('strength_score', json_response)
        self.assertIn('overall_score', json_response)
        
    def test_score_validation_ranges(self):
        """Test score validation for realistic ranges"""
        assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            height=175.0,
            weight=70.0,
            bench_press_1rm=80.0,
            push_ups=30,
            vo2_max=45.0,
            overall_score=85.0
        )
        
        # Scores should be within expected ranges
        self.assertGreaterEqual(assessment.overall_score, 0)
        self.assertLessEqual(assessment.overall_score, 100)


class AssessmentReportTestCase(TestCase):
    """Test assessment report functionality"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        self.assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            assessment_date=date.today(),
            height=175.0,
            weight=70.0,
            overall_score=85.0
        )
        
    def test_assessment_report_view(self):
        """Test assessment report view (placeholder)"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:report', kwargs={'pk': self.assessment.pk})
        response = self.client_test.get(url)
        # Currently returns 404 as it's a placeholder
        self.assertEqual(response.status_code, 404)


class AssessmentFilteringTestCase(TestCase):
    """Test assessment filtering and search functionality"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
        # Create clients and assessments with different scores and dates
        self.client1 = ClientModel.objects.create(
            trainer=self.trainer,
            name='High Score Client'
        )
        self.client2 = ClientModel.objects.create(
            trainer=self.trainer,
            name='Low Score Client'
        )
        
        self.high_score_assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client1,
            assessment_date=date.today(),
            overall_score=95.0
        )
        
        self.low_score_assessment = Assessment.objects.create(
            trainer=self.trainer,
            client=self.client2,
            assessment_date=date.today() - timedelta(days=30),
            overall_score=70.0
        )
        
    def test_score_range_filtering(self):
        """Test filtering assessments by score range"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        
        # Filter by high scores
        response = self.client_test.get(url, {
            'score_min': '90',
            'score_max': '100'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'High Score Client')
        self.assertNotContains(response, 'Low Score Client')
        
    def test_date_range_filtering(self):
        """Test filtering assessments by date range"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        
        # Filter by recent dates
        response = self.client_test.get(url, {
            'date_from': date.today().strftime('%Y-%m-%d'),
            'date_to': date.today().strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'High Score Client')
        self.assertNotContains(response, 'Low Score Client')
        
    def test_client_specific_filtering(self):
        """Test filtering assessments by specific client"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('assessments:list')
        
        response = self.client_test.get(url, {'client': self.client1.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'High Score Client')
        self.assertNotContains(response, 'Low Score Client')


class AssessmentIntegrationTestCase(TestCase):
    """Integration tests for assessment management workflow"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Integration Test Client',
            email='integration@example.com'
        )
        
    def test_complete_assessment_workflow(self):
        """Test complete assessment management workflow"""
        self.client_test.login(username='test_trainer', password='testpass123')
        
        # 1. Navigate to client detail and create assessment
        client_detail_url = reverse('clients:detail', kwargs={'pk': self.test_client.pk})
        response = self.client_test.get(client_detail_url)
        self.assertEqual(response.status_code, 200)
        
        # 2. Create assessment from client page
        add_url = reverse('assessments:add')
        assessment_data = {
            'client': self.test_client.pk,
            'assessment_date': date.today(),
            'height': '175.0',
            'weight': '70.0',
            'body_fat_percentage': '15.0',
            'resting_heart_rate': '60',
            'bench_press_1rm': '80.0',
            'push_ups': '30',
            'overall_score': '85.0'
        }
        response = self.client_test.post(add_url, assessment_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Verify assessment appears in list
        list_url = reverse('assessments:list')
        response = self.client_test.get(list_url)
        self.assertContains(response, 'Integration Test Client')
        
        # 4. View assessment details
        assessment = Assessment.objects.get(client=self.test_client)
        detail_url = reverse('assessments:detail', kwargs={'pk': assessment.pk})
        response = self.client_test.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '85.0')  # Overall score
        
        # 5. Verify assessment shows up in client detail
        response = self.client_test.get(client_detail_url)
        self.assertContains(response, 'Assessment')
        
        # 6. Delete assessment
        delete_url = reverse('assessments:delete', kwargs={'pk': assessment.pk})
        response = self.client_test.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        # 7. Verify deletion
        with self.assertRaises(Assessment.DoesNotExist):
            Assessment.objects.get(pk=assessment.pk)