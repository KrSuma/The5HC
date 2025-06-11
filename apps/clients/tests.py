from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import Client as ClientModel
from .forms import ClientForm, ClientSearchForm

User = get_user_model()


class ClientModelTestCase(TestCase):
    """Test suite for Client model"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.trainer = User.objects.create_user(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        
    def test_client_creation(self):
        """Test client creation with valid data"""
        client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com',
            phone='010-1234-5678',
            date_of_birth=date(1990, 1, 1),
            gender='male',
            height=175.0,
            weight=70.0,
            notes='Test notes'
        )
        self.assertEqual(client.name, 'Test Client')
        self.assertEqual(client.trainer, self.trainer)
        self.assertEqual(client.gender, 'male')
        
    def test_client_str_method(self):
        """Test client string representation"""
        client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com'
        )
        self.assertEqual(str(client), 'Test Client')
        
    def test_client_age_calculation(self):
        """Test age calculation method"""
        birth_date = date.today() - timedelta(days=365 * 25)  # 25 years old
        client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            date_of_birth=birth_date
        )
        self.assertEqual(client.age, 25)
        
    def test_client_bmi_calculation(self):
        """Test BMI calculation method"""
        client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            height=175.0,  # 1.75m
            weight=70.0    # 70kg
        )
        expected_bmi = 70.0 / (1.75 ** 2)  # BMI = weight / (height_in_meters^2)
        self.assertAlmostEqual(client.bmi, expected_bmi, places=2)
        
    def test_client_bmi_with_missing_data(self):
        """Test BMI calculation with missing height or weight"""
        client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            height=175.0,
            weight=None
        )
        self.assertIsNone(client.bmi)
        
    def test_client_ordering(self):
        """Test client default ordering"""
        client1 = ClientModel.objects.create(
            trainer=self.trainer,
            name='B Client'
        )
        client2 = ClientModel.objects.create(
            trainer=self.trainer,
            name='A Client'
        )
        
        clients = list(ClientModel.objects.all())
        self.assertEqual(clients[0].name, 'A Client')
        self.assertEqual(clients[1].name, 'B Client')


class ClientFormTestCase(TestCase):
    """Test suite for Client forms"""
    
    def setUp(self):
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
    def test_client_form_valid_data(self):
        """Test client form with valid data"""
        form_data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'phone': '010-1234-5678',
            'date_of_birth': '1990-01-01',
            'gender': 'male',
            'height': '175.0',
            'weight': '70.0',
            'notes': 'Test notes'
        }
        form = ClientForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_client_form_missing_required_field(self):
        """Test client form with missing required field"""
        form_data = {
            'email': 'client@example.com',
            'phone': '010-1234-5678'
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_client_form_invalid_email(self):
        """Test client form with invalid email"""
        form_data = {
            'name': 'Test Client',
            'email': 'invalid-email',
            'phone': '010-1234-5678'
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
    def test_client_form_invalid_height_weight(self):
        """Test client form with invalid height/weight values"""
        form_data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'height': '50',  # Too low
            'weight': '300'  # Too high
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_client_search_form(self):
        """Test client search form functionality"""
        form_data = {
            'search_query': 'test',
            'gender': 'male',
            'age_min': '20',
            'age_max': '40'
        }
        form = ClientSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class ClientViewTestCase(TestCase):
    """Test suite for Client views"""
    
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
            email='client@example.com',
            phone='010-1234-5678',
            gender='male',
            height=175.0,
            weight=70.0
        )
        
        # Client belonging to other trainer
        self.other_client = ClientModel.objects.create(
            trainer=self.other_trainer,
            name='Other Client',
            email='other@example.com'
        )
        
    def test_client_list_view_requires_login(self):
        """Test client list requires authentication"""
        url = reverse('clients:list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_client_list_view_authenticated(self):
        """Test client list view with authenticated user"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        self.assertNotContains(response, 'Other Client')  # Should not see other trainer's clients
        
    def test_client_list_search_functionality(self):
        """Test client list search functionality"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = self.client_test.get(url, {'search_query': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        
    def test_client_list_htmx_partial(self):
        """Test client list HTMX partial response"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = self.client_test.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        # Should return partial template
        self.assertTemplateUsed(response, 'clients/client_list_partial.html')
        
    def test_client_detail_view(self):
        """Test client detail view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:detail', kwargs={'pk': self.test_client.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        self.assertContains(response, 'client@example.com')
        
    def test_client_detail_unauthorized_access(self):
        """Test client detail view for unauthorized client"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:detail', kwargs={'pk': self.other_client.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_client_add_view_get(self):
        """Test client add view GET request"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:add')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ClientForm)
        
    def test_client_add_view_post_valid(self):
        """Test client add view with valid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:add')
        data = {
            'name': 'New Client',
            'email': 'new@example.com',
            'phone': '010-9876-5432',
            'date_of_birth': '1985-05-15',
            'gender': 'female',
            'height': '165.0',
            'weight': '60.0',
            'notes': 'New client notes'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check client was created
        new_client = ClientModel.objects.get(name='New Client')
        self.assertEqual(new_client.trainer, self.trainer)
        self.assertEqual(new_client.email, 'new@example.com')
        
    def test_client_add_view_post_invalid(self):
        """Test client add view with invalid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:add')
        data = {
            'name': '',  # Missing required field
            'email': 'invalid-email'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        
    def test_client_edit_view(self):
        """Test client edit view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:edit', kwargs={'pk': self.test_client.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, self.test_client)
        
    def test_client_edit_view_post(self):
        """Test client edit view POST request"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:edit', kwargs={'pk': self.test_client.pk})
        data = {
            'name': 'Updated Client',
            'email': 'updated@example.com',
            'phone': '010-1111-2222',
            'gender': 'male',
            'height': '180.0',
            'weight': '75.0'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check client was updated
        updated_client = ClientModel.objects.get(pk=self.test_client.pk)
        self.assertEqual(updated_client.name, 'Updated Client')
        self.assertEqual(updated_client.email, 'updated@example.com')
        
    def test_client_delete_view(self):
        """Test client delete view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:delete', kwargs={'pk': self.test_client.pk})
        response = self.client_test.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Check client was deleted
        with self.assertRaises(ClientModel.DoesNotExist):
            ClientModel.objects.get(pk=self.test_client.pk)
            
    def test_client_delete_unauthorized(self):
        """Test client delete for unauthorized client"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:delete', kwargs={'pk': self.other_client.pk})
        response = self.client_test.post(url)
        self.assertEqual(response.status_code, 404)
        
        # Check client was not deleted
        self.assertTrue(ClientModel.objects.filter(pk=self.other_client.pk).exists())
        
    def test_client_export_view(self):
        """Test client export to CSV"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:export')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename=', response['Content-Disposition'])


class ClientValidationTestCase(TestCase):
    """Test client form validation and HTMX endpoints"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
    def test_email_validation_endpoint(self):
        """Test email validation HTMX endpoint"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:validate_email')
        
        # Test valid email
        response = self.client_test.post(url, {
            'email': 'valid@example.com'
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid')
        
        # Test invalid email
        response = self.client_test.post(url, {
            'email': 'invalid-email'
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid')
        
    def test_phone_validation_endpoint(self):
        """Test phone validation HTMX endpoint"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:validate_phone')
        
        # Test valid phone
        response = self.client_test.post(url, {
            'phone': '010-1234-5678'
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid')
        
        # Test invalid phone
        response = self.client_test.post(url, {
            'phone': '123'
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid')


class ClientFilteringTestCase(TestCase):
    """Test client filtering and search functionality"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
        # Create clients with different attributes
        self.male_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Male Client',
            gender='male',
            date_of_birth=date(1990, 1, 1)  # Age ~34
        )
        
        self.female_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Female Client',
            gender='female',
            date_of_birth=date(1985, 1, 1)  # Age ~39
        )
        
    def test_gender_filtering(self):
        """Test filtering clients by gender"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Filter by male
        response = self.client_test.get(url, {'gender': 'male'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Male Client')
        self.assertNotContains(response, 'Female Client')
        
        # Filter by female
        response = self.client_test.get(url, {'gender': 'female'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Female Client')
        self.assertNotContains(response, 'Male Client')
        
    def test_age_range_filtering(self):
        """Test filtering clients by age range"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Filter by age range that includes only one client
        response = self.client_test.get(url, {
            'age_min': '30',
            'age_max': '35'
        })
        self.assertEqual(response.status_code, 200)
        # Should contain the male client (age ~34) but not female (age ~39)
        self.assertContains(response, 'Male Client')
        
    def test_search_query_filtering(self):
        """Test filtering clients by search query"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Search for "Male"
        response = self.client_test.get(url, {'search_query': 'Male'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Male Client')
        self.assertNotContains(response, 'Female Client')
        
    def test_combined_filtering(self):
        """Test combining multiple filters"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        response = self.client_test.get(url, {
            'search_query': 'Client',
            'gender': 'male',
            'age_min': '30'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Male Client')


class ClientIntegrationTestCase(TestCase):
    """Integration tests for client management workflow"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        
    def test_complete_client_management_workflow(self):
        """Test complete client management workflow"""
        self.client_test.login(username='test_trainer', password='testpass123')
        
        # 1. Create client
        add_url = reverse('clients:add')
        create_data = {
            'name': 'Workflow Client',
            'email': 'workflow@example.com',
            'phone': '010-1111-1111',
            'gender': 'female',
            'height': '160.0',
            'weight': '55.0'
        }
        response = self.client_test.post(add_url, create_data)
        self.assertEqual(response.status_code, 302)
        
        # 2. Verify client appears in list
        list_url = reverse('clients:list')
        response = self.client_test.get(list_url)
        self.assertContains(response, 'Workflow Client')
        
        # 3. View client details
        client = ClientModel.objects.get(name='Workflow Client')
        detail_url = reverse('clients:detail', kwargs={'pk': client.pk})
        response = self.client_test.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'workflow@example.com')
        
        # 4. Edit client
        edit_url = reverse('clients:edit', kwargs={'pk': client.pk})
        edit_data = create_data.copy()
        edit_data['name'] = 'Updated Workflow Client'
        response = self.client_test.post(edit_url, edit_data)
        self.assertEqual(response.status_code, 302)
        
        # 5. Verify update
        updated_client = ClientModel.objects.get(pk=client.pk)
        self.assertEqual(updated_client.name, 'Updated Workflow Client')
        
        # 6. Delete client
        delete_url = reverse('clients:delete', kwargs={'pk': client.pk})
        response = self.client_test.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        # 7. Verify deletion
        with self.assertRaises(ClientModel.DoesNotExist):
            ClientModel.objects.get(pk=client.pk)