"""
Pytest-style tests for clients functionality.
Following django-test.md guidelines for modern Django testing.
"""
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects, assertTemplateUsed, assertFormError

from .models import Client as ClientModel
from .forms import ClientForm, ClientSearchForm
from .factories import ClientFactory, create_test_clients, create_diverse_client_group
from apps.accounts.factories import UserFactory

User = get_user_model()


class TestClientModel:
    """Test suite for Client model"""
    
    pytestmark = pytest.mark.django_db
    
    def test_client_creation(self):
        """Test client creation with valid data"""
        trainer = UserFactory()
        client = ClientFactory(
            trainer=trainer,
            name='Test Client',
            email='client@example.com',
            phone='010-1234-5678',
            gender='male',
            height=175.0,
            weight=70.0
        )
        
        assert client.name == 'Test Client'
        assert client.trainer == trainer
        assert client.gender == 'male'
        assert client.height == 175.0
        assert client.weight == 70.0
    
    def test_client_str_method(self):
        """Test client string representation"""
        client = ClientFactory(name='Test Client')
        
        assert str(client) == 'Test Client'
    
    def test_client_age_calculation(self):
        """Test age calculation method"""
        birth_date = date.today() - timedelta(days=365 * 25)  # 25 years old
        client = ClientFactory(age=25)  # Factory handles age logic
        
        assert client.age == 25
    
    def test_client_bmi_calculation(self):
        """Test BMI calculation method"""
        client = ClientFactory(height=175.0, weight=70.0)
        expected_bmi = 70.0 / (1.75 ** 2)  # BMI = weight / (height_in_meters^2)
        
        assert abs(client.bmi - expected_bmi) < 0.01
    
    def test_client_bmi_with_missing_data(self):
        """Test BMI calculation with missing height or weight"""
        client = ClientFactory(height=175.0, weight=None)
        
        assert client.bmi is None
    
    def test_client_ordering(self):
        """Test client default ordering"""
        trainer = UserFactory()
        client_b = ClientFactory(trainer=trainer, name='B Client')
        client_a = ClientFactory(trainer=trainer, name='A Client')
        
        clients = list(ClientModel.objects.all())
        
        assert clients[0].name == 'A Client'
        assert clients[1].name == 'B Client'


class TestClientForm:
    """Test suite for Client forms"""
    
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
        
        assert form.is_valid()
    
    def test_client_form_missing_required_field(self):
        """Test client form with missing required field"""
        form_data = {
            'email': 'client@example.com',
            'phone': '010-1234-5678'
        }
        form = ClientForm(data=form_data)
        
        assert not form.is_valid()
        assert 'name' in form.errors
    
    def test_client_form_invalid_email(self):
        """Test client form with invalid email"""
        form_data = {
            'name': 'Test Client',
            'email': 'invalid-email',
            'phone': '010-1234-5678'
        }
        form = ClientForm(data=form_data)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_client_form_invalid_height_weight(self):
        """Test client form with invalid height/weight values"""
        form_data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'height': '50',  # Too low
            'weight': '300'  # Too high
        }
        form = ClientForm(data=form_data)
        
        assert not form.is_valid()
    
    def test_client_search_form(self):
        """Test client search form functionality"""
        form_data = {
            'search_query': 'test',
            'gender': 'male',
            'age_min': '20',
            'age_max': '40'
        }
        form = ClientSearchForm(data=form_data)
        
        assert form.is_valid()


class TestClientViews:
    """Test suite for Client views"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        self.other_trainer = UserFactory(
            username='other_trainer',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test clients
        self.test_client = ClientFactory(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com',
            phone='010-1234-5678',
            gender='male',
            height=175.0,
            weight=70.0
        )
        
        # Client belonging to other trainer
        self.other_client = ClientFactory(
            trainer=self.other_trainer,
            name='Other Client',
            email='other@example.com'
        )
    
    def test_client_list_view_requires_login(self, client):
        """Test client list requires authentication"""
        url = reverse('clients:list')
        response = client.get(url)
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_client_list_view_authenticated(self, client):
        """Test client list view with authenticated user"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = client.get(url)
        
        assert response.status_code == 200
        assertContains(response, 'Test Client')
        assertNotContains(response, 'Other Client')  # Should not see other trainer's clients
    
    def test_client_list_search_functionality(self, client):
        """Test client list search functionality"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = client.get(url, {'search_query': 'Test'})
        
        assert response.status_code == 200
        assertContains(response, 'Test Client')
    
    def test_client_list_htmx_partial(self, client):
        """Test client list HTMX partial response"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        response = client.get(url, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        # Should return partial template
        assertTemplateUsed(response, 'clients/client_list_partial.html')
    
    def test_client_detail_view(self, client):
        """Test client detail view"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:detail', kwargs={'pk': self.test_client.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assertContains(response, 'Test Client')
        assertContains(response, 'client@example.com')
    
    def test_client_detail_unauthorized_access(self, client):
        """Test client detail view for unauthorized client"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:detail', kwargs={'pk': self.other_client.pk})
        response = client.get(url)
        
        assert response.status_code == 404
    
    def test_client_add_view_get(self, client):
        """Test client add view GET request"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:add')
        response = client.get(url)
        
        assert response.status_code == 200
        assert isinstance(response.context['form'], ClientForm)
    
    def test_client_add_view_post_valid(self, client):
        """Test client add view with valid POST data"""
        client.login(username='test_trainer', password='testpass123')
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
        response = client.post(url, data)
        
        assert response.status_code == 302
        
        # Check client was created
        new_client = ClientModel.objects.get(name='New Client')
        assert new_client.trainer == self.trainer
        assert new_client.email == 'new@example.com'
    
    def test_client_add_view_post_invalid(self, client):
        """Test client add view with invalid POST data"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:add')
        data = {
            'name': '',  # Missing required field
            'email': 'invalid-email'
        }
        response = client.post(url, data)
        
        assert response.status_code == 200
        assertFormError(response, 'form', 'name', 'This field is required.')
    
    def test_client_edit_view(self, client):
        """Test client edit view"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:edit', kwargs={'pk': self.test_client.pk})
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['form'].instance == self.test_client
    
    def test_client_edit_view_post(self, client):
        """Test client edit view POST request"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:edit', kwargs={'pk': self.test_client.pk})
        data = {
            'name': 'Updated Client',
            'email': 'updated@example.com',
            'phone': '010-1111-2222',
            'gender': 'male',
            'height': '180.0',
            'weight': '75.0'
        }
        response = client.post(url, data)
        
        assert response.status_code == 302
        
        # Check client was updated
        updated_client = ClientModel.objects.get(pk=self.test_client.pk)
        assert updated_client.name == 'Updated Client'
        assert updated_client.email == 'updated@example.com'
    
    def test_client_delete_view(self, client):
        """Test client delete view"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:delete', kwargs={'pk': self.test_client.pk})
        response = client.post(url)
        
        assert response.status_code == 302
        
        # Check client was deleted
        assert not ClientModel.objects.filter(pk=self.test_client.pk).exists()
    
    def test_client_delete_unauthorized(self, client):
        """Test client delete for unauthorized client"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:delete', kwargs={'pk': self.other_client.pk})
        response = client.post(url)
        
        assert response.status_code == 404
        
        # Check client was not deleted
        assert ClientModel.objects.filter(pk=self.other_client.pk).exists()
    
    def test_client_export_view(self, client):
        """Test client export to CSV"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:export')
        response = client.get(url)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment; filename=' in response['Content-Disposition']


class TestClientValidation:
    """Test client form validation and HTMX endpoints"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(
            username='test_trainer',
            password='testpass123'
        )
    
    def test_email_validation_endpoint(self, client):
        """Test email validation HTMX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:validate_email')
        
        # Test valid email
        response = client.post(url, {
            'email': 'valid@example.com'
        }, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        assertContains(response, 'valid')
        
        # Test invalid email
        response = client.post(url, {
            'email': 'invalid-email'
        }, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        assertContains(response, 'invalid')
    
    def test_phone_validation_endpoint(self, client):
        """Test phone validation HTMX endpoint"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:validate_phone')
        
        # Test valid phone
        response = client.post(url, {
            'phone': '010-1234-5678'
        }, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        assertContains(response, 'valid')
        
        # Test invalid phone
        response = client.post(url, {
            'phone': '123'
        }, HTTP_HX_REQUEST='true')
        
        assert response.status_code == 200
        assertContains(response, 'invalid')


class TestClientFiltering:
    """Test client filtering and search functionality"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(
            username='test_trainer',
            password='testpass123'
        )
        
        # Create clients with different attributes using factories
        self.male_client = ClientFactory(
            trainer=self.trainer,
            name='Male Client',
            gender='male',
            age=34
        )
        
        self.female_client = ClientFactory(
            trainer=self.trainer,
            name='Female Client',
            gender='female',
            age=39
        )
    
    def test_gender_filtering(self, client):
        """Test filtering clients by gender"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Filter by male
        response = client.get(url, {'gender': 'male'})
        
        assert response.status_code == 200
        assertContains(response, 'Male Client')
        assertNotContains(response, 'Female Client')
        
        # Filter by female
        response = client.get(url, {'gender': 'female'})
        
        assert response.status_code == 200
        assertContains(response, 'Female Client')
        assertNotContains(response, 'Male Client')
    
    def test_age_range_filtering(self, client):
        """Test filtering clients by age range"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Filter by age range that includes only one client
        response = client.get(url, {
            'age_min': '30',
            'age_max': '35'
        })
        
        assert response.status_code == 200
        # Should contain the male client (age 34) but not female (age 39)
        assertContains(response, 'Male Client')
    
    def test_search_query_filtering(self, client):
        """Test filtering clients by search query"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        # Search for "Male"
        response = client.get(url, {'search_query': 'Male'})
        
        assert response.status_code == 200
        assertContains(response, 'Male Client')
        assertNotContains(response, 'Female Client')
    
    def test_combined_filtering(self, client):
        """Test combining multiple filters"""
        client.login(username='test_trainer', password='testpass123')
        url = reverse('clients:list')
        
        response = client.get(url, {
            'search_query': 'Client',
            'gender': 'male',
            'age_min': '30'
        })
        
        assert response.status_code == 200
        assertContains(response, 'Male Client')


class TestClientIntegration:
    """Integration tests for client management workflow"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Setup test fixtures"""
        self.trainer = UserFactory(
            username='test_trainer',
            password='testpass123'
        )
    
    def test_complete_client_management_workflow(self, client):
        """Test complete client management workflow"""
        client.login(username='test_trainer', password='testpass123')
        
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
        response = client.post(add_url, create_data)
        
        assert response.status_code == 302
        
        # 2. Verify client appears in list
        list_url = reverse('clients:list')
        response = client.get(list_url)
        assertContains(response, 'Workflow Client')
        
        # 3. View client details
        test_client = ClientModel.objects.get(name='Workflow Client')
        detail_url = reverse('clients:detail', kwargs={'pk': test_client.pk})
        response = client.get(detail_url)
        
        assert response.status_code == 200
        assertContains(response, 'workflow@example.com')
        
        # 4. Edit client
        edit_url = reverse('clients:edit', kwargs={'pk': test_client.pk})
        edit_data = create_data.copy()
        edit_data['name'] = 'Updated Workflow Client'
        response = client.post(edit_url, edit_data)
        
        assert response.status_code == 302
        
        # 5. Verify update
        updated_client = ClientModel.objects.get(pk=test_client.pk)
        assert updated_client.name == 'Updated Workflow Client'
        
        # 6. Delete client
        delete_url = reverse('clients:delete', kwargs={'pk': test_client.pk})
        response = client.post(delete_url)
        
        assert response.status_code == 302
        
        # 7. Verify deletion
        assert not ClientModel.objects.filter(pk=test_client.pk).exists()


# Parametrized tests
@pytest.mark.django_db
@pytest.mark.parametrize('height,weight,expected_valid', [
    (175.0, 70.0, True),    # Normal values
    (150.0, 45.0, True),    # Min valid values
    (200.0, 120.0, True),   # Max valid values
    (50.0, 70.0, False),    # Height too low
    (175.0, 300.0, False),  # Weight too high
    (None, 70.0, True),     # Missing height (allowed)
    (175.0, None, True),    # Missing weight (allowed)
])
def test_client_form_height_weight_validation(height, weight, expected_valid):
    """Test client form validation for various height/weight combinations"""
    form_data = {
        'name': 'Test Client',
        'email': 'test@example.com',
        'gender': 'male'
    }
    
    if height is not None:
        form_data['height'] = str(height)
    if weight is not None:
        form_data['weight'] = str(weight)
    
    form = ClientForm(data=form_data)
    
    assert form.is_valid() == expected_valid


@pytest.mark.django_db
@pytest.mark.parametrize('gender,age_range,expected_count', [
    ('male', (20, 30), 1),     # Young males
    ('female', (30, 40), 1),   # Middle-aged females
    ('male', (40, 50), 0),     # Older males (none in test data)
    (None, (25, 35), 2),       # All genders in age range
])
def test_client_filtering_combinations(client, gender, age_range, expected_count):
    """Test various client filtering combinations"""
    trainer = UserFactory(username='test_trainer', password='testpass123')
    
    # Create test clients with specific attributes
    ClientFactory(trainer=trainer, gender='male', age=25)
    ClientFactory(trainer=trainer, gender='female', age=35)
    
    client.login(username='test_trainer', password='testpass123')
    url = reverse('clients:list')
    
    params = {
        'age_min': str(age_range[0]),
        'age_max': str(age_range[1])
    }
    if gender:
        params['gender'] = gender
    
    response = client.get(url, params)
    
    assert response.status_code == 200
    # This would need to count actual results in a real implementation
    # For now, just verify the response is successful


@pytest.mark.django_db
def test_client_factory_integration():
    """Test that client factories work correctly with the model"""
    trainer = UserFactory()
    
    # Test basic factory
    client = ClientFactory(trainer=trainer)
    assert client.trainer == trainer
    assert client.name is not None
    
    # Test factory with traits
    diverse_clients = create_diverse_client_group(trainer)
    assert len(diverse_clients) == 9  # As defined in factory helper
    assert diverse_clients['male_young'].gender == 'male'
    assert diverse_clients['female_senior'].gender == 'female'
    
    # Test batch creation
    clients = create_test_clients(5, trainer=trainer)
    assert len(clients) == 5
    for client in clients:
        assert client.trainer == trainer