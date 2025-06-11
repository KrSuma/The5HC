# Test Templates and Examples for The5HC

This document provides ready-to-use test templates for common scenarios in The5HC project.

## 📋 Table of Contents
1. [Model Test Template](#model-test-template)
2. [View Test Template](#view-test-template)
3. [Form Test Template](#form-test-template)
4. [API Test Template](#api-test-template)
5. [HTMX Test Template](#htmx-test-template)
6. [Complete Feature Test Example](#complete-feature-test-example)

## Model Test Template

```python
"""
Tests for [App Name] models.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.[app_name].models import [ModelName]
from apps.[app_name].factories import [ModelName]Factory


class Test[ModelName]Model:
    """Test suite for [ModelName] model"""
    
    pytestmark = pytest.mark.django_db
    
    # Basic Creation and Field Tests
    def test_create_with_required_fields(self):
        """Test creating [model] with required fields only"""
        obj = [ModelName]Factory()
        
        assert obj.pk is not None
        assert obj.created_at is not None
        # Add assertions for required fields
    
    def test_create_with_all_fields(self):
        """Test creating [model] with all fields populated"""
        obj = [ModelName]Factory(
            # Specify all fields explicitly
            field1='value1',
            field2='value2',
        )
        
        assert obj.field1 == 'value1'
        assert obj.field2 == 'value2'
    
    # String Representation
    def test_str_representation(self):
        """Test string representation of [model]"""
        obj = [ModelName]Factory(name='Test Name')
        
        assert str(obj) == 'Test Name'
    
    # Custom Properties/Methods
    def test_custom_property(self):
        """Test [property_name] property calculation"""
        obj = [ModelName]Factory(
            # Set up data for property
        )
        
        expected = # Calculate expected value
        assert obj.property_name == expected
    
    # Validation Tests
    def test_field_validation(self):
        """Test field validation rules"""
        with pytest.raises(ValidationError):
            obj = [ModelName]Factory(invalid_field='invalid_value')
            obj.full_clean()
    
    # Relationship Tests
    def test_related_objects(self):
        """Test relationships with other models"""
        obj = [ModelName]Factory()
        related = RelatedFactory(parent=obj)
        
        assert obj.related_set.count() == 1
        assert related in obj.related_set.all()
    
    # Business Logic Tests
    def test_business_method(self):
        """Test [method_name] business logic"""
        obj = [ModelName]Factory()
        
        result = obj.business_method()
        
        assert result == expected_result
    
    # Edge Cases
    @pytest.mark.parametrize('field_value,expected', [
        (None, 'default'),
        ('', 'default'),
        ('value', 'value'),
    ])
    def test_edge_cases(self, field_value, expected):
        """Test edge cases for [field_name]"""
        obj = [ModelName]Factory(field_name=field_value)
        
        assert obj.get_field_display() == expected


# Example: Client Model Test
class TestClientModel:
    """Test suite for Client model"""
    
    pytestmark = pytest.mark.django_db
    
    def test_bmi_calculation_normal_values(self):
        """Test BMI calculation with normal values"""
        client = ClientFactory(height=170, weight=70)
        
        expected_bmi = 70 / (1.70 ** 2)
        assert abs(client.BMI - expected_bmi) < 0.01
    
    def test_bmi_category_classification(self):
        """Test BMI category classification"""
        test_cases = [
            (170, 50, '저체중'),
            (170, 65, '정상'),
            (170, 75, '과체중'),
            (170, 90, '비만'),
        ]
        
        for height, weight, expected_category in test_cases:
            client = ClientFactory(height=height, weight=weight)
            assert client.bmi_category == expected_category
    
    def test_age_calculation(self):
        """Test age calculation from birth date"""
        birth_date = date.today() - timedelta(days=365 * 30 + 7)  # 30 years
        client = ClientFactory(birth_date=birth_date)
        
        assert client.age == 30
```

## View Test Template

```python
"""
Tests for [App Name] views.
"""
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from pytest_django.asserts import (
    assertContains, assertNotContains, 
    assertRedirects, assertTemplateUsed
)

from apps.accounts.factories import UserFactory
from apps.[app_name].factories import [Model]Factory
from apps.[app_name].models import [Model]


class Test[Model]ListView:
    """Test suite for [Model] list view"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
        self.url = reverse('[app_name]:[model]_list')
    
    def test_anonymous_user_redirected(self, client):
        """Test anonymous users are redirected to login"""
        response = client.get(self.url)
        
        assertRedirects(response, f'/accounts/login/?next={self.url}')
    
    def test_authenticated_user_can_access(self, client):
        """Test authenticated users can access the view"""
        client.force_login(self.user)
        response = client.get(self.url)
        
        assert response.status_code == 200
        assertTemplateUsed(response, '[app_name]/[model]_list.html')
    
    def test_user_sees_only_own_objects(self, client):
        """Test users only see their own objects"""
        # Create objects for different users
        obj1 = [Model]Factory(user=self.user)
        obj2 = [Model]Factory(user=self.user)
        other_obj = [Model]Factory()  # Different user
        
        client.force_login(self.user)
        response = client.get(self.url)
        
        assertContains(response, obj1.name)
        assertContains(response, obj2.name)
        assertNotContains(response, other_obj.name)
    
    def test_search_functionality(self, client):
        """Test search filters results correctly"""
        obj1 = [Model]Factory(user=self.user, name='Apple')
        obj2 = [Model]Factory(user=self.user, name='Banana')
        
        client.force_login(self.user)
        response = client.get(self.url, {'q': 'Apple'})
        
        assertContains(response, 'Apple')
        assertNotContains(response, 'Banana')
    
    def test_pagination(self, client):
        """Test pagination works correctly"""
        # Create 25 objects (assuming 20 per page)
        [Model]Factory.create_batch(25, user=self.user)
        
        client.force_login(self.user)
        response = client.get(self.url)
        
        assertContains(response, 'Page 1 of 2')
        assert len(response.context['object_list']) == 20


class Test[Model]CreateView:
    """Test suite for [Model] create view"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
        self.url = reverse('[app_name]:[model]_create')
    
    def test_get_create_form(self, client):
        """Test GET request shows create form"""
        client.force_login(self.user)
        response = client.get(self.url)
        
        assert response.status_code == 200
        assertContains(response, '<form')
        assert 'form' in response.context
    
    def test_create_with_valid_data(self, client):
        """Test creating object with valid data"""
        client.force_login(self.user)
        
        form_data = {
            'name': '테스트 객체',
            'description': '설명',
            # Add all required fields
        }
        
        response = client.post(self.url, form_data)
        
        # Check redirect
        assert response.status_code == 302
        
        # Check object created
        assert [Model].objects.filter(name='테스트 객체').exists()
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '성공적으로 생성되었습니다' in str(messages[0])
    
    def test_create_with_invalid_data(self, client):
        """Test form errors are displayed"""
        client.force_login(self.user)
        
        form_data = {
            'name': '',  # Required field
        }
        
        response = client.post(self.url, form_data)
        
        assert response.status_code == 200
        assert response.context['form'].errors
        assertContains(response, '필수 항목입니다')


class Test[Model]UpdateView:
    """Test suite for [Model] update view"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
        self.obj = [Model]Factory(user=self.user)
        self.url = reverse('[app_name]:[model]_update', args=[self.obj.pk])
    
    def test_owner_can_update(self, client):
        """Test owner can update their object"""
        client.force_login(self.user)
        
        form_data = {
            'name': '수정된 이름',
            # Include all required fields
        }
        
        response = client.post(self.url, form_data)
        
        assert response.status_code == 302
        
        self.obj.refresh_from_db()
        assert self.obj.name == '수정된 이름'
    
    def test_non_owner_cannot_update(self, client):
        """Test non-owner cannot update object"""
        other_user = UserFactory()
        client.force_login(other_user)
        
        response = client.get(self.url)
        
        assert response.status_code == 404


class Test[Model]DeleteView:
    """Test suite for [Model] delete view"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
        self.obj = [Model]Factory(user=self.user)
        self.url = reverse('[app_name]:[model]_delete', args=[self.obj.pk])
    
    def test_delete_confirmation_page(self, client):
        """Test delete confirmation page is shown"""
        client.force_login(self.user)
        response = client.get(self.url)
        
        assert response.status_code == 200
        assertContains(response, '정말 삭제하시겠습니까?')
    
    def test_successful_deletion(self, client):
        """Test successful deletion"""
        client.force_login(self.user)
        response = client.post(self.url)
        
        assert response.status_code == 302
        assert not [Model].objects.filter(pk=self.obj.pk).exists()
```

## Form Test Template

```python
"""
Tests for [App Name] forms.
"""
import pytest
from datetime import date

from apps.[app_name].forms import [Form]Name
from apps.accounts.factories import UserFactory


class Test[Form]Name:
    """Test suite for [Form]Name"""
    
    def test_form_fields(self):
        """Test form has correct fields"""
        form = [Form]Name()
        
        expected_fields = ['field1', 'field2', 'field3']
        for field in expected_fields:
            assert field in form.fields
    
    def test_required_fields(self):
        """Test required field validation"""
        form = [Form]Name(data={})
        
        assert not form.is_valid()
        
        required_fields = ['field1', 'field2']
        for field in required_fields:
            assert field in form.errors
    
    def test_field_validation(self):
        """Test specific field validation rules"""
        # Test email validation
        form_data = {
            'email': 'invalid-email',
            'name': 'Test Name',
        }
        form = [Form]Name(data=form_data)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_custom_validation(self):
        """Test custom clean methods"""
        form_data = {
            'start_date': date(2024, 1, 1),
            'end_date': date(2023, 12, 31),  # Before start
        }
        form = [Form]Name(data=form_data)
        
        assert not form.is_valid()
        assert '종료일은 시작일 이후여야 합니다' in str(form.errors)
    
    def test_form_save(self):
        """Test form save method creates object"""
        user = UserFactory()
        form_data = {
            'name': '테스트',
            'description': '설명',
        }
        form = [Form]Name(data=form_data)
        
        assert form.is_valid()
        
        obj = form.save(commit=False)
        obj.user = user
        obj.save()
        
        assert obj.name == '테스트'
        assert obj.user == user
    
    @pytest.mark.parametrize('phone,is_valid', [
        ('010-1234-5678', True),
        ('01012345678', True),
        ('02-123-4567', True),
        ('invalid', False),
        ('123-456', False),
    ])
    def test_phone_number_validation(self, phone, is_valid):
        """Test phone number validation patterns"""
        form_data = {
            'name': 'Test',
            'phone_number': phone,
        }
        form = [Form]Name(data=form_data)
        
        if is_valid:
            assert 'phone_number' not in form.errors
        else:
            assert 'phone_number' in form.errors
```

## API Test Template

```python
"""
Tests for [App Name] API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.[app_name].factories import [Model]Factory


class Test[Model]API:
    """Test suite for [Model] API endpoints"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_list_endpoint(self):
        """Test listing objects via API"""
        # Create test data
        obj1 = [Model]Factory(user=self.user)
        obj2 = [Model]Factory(user=self.user)
        other_obj = [Model]Factory()  # Different user
        
        url = reverse('api:[model]-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Check data structure
        obj_data = response.data['results'][0]
        assert 'id' in obj_data
        assert 'name' in obj_data
    
    def test_create_endpoint(self):
        """Test creating object via API"""
        url = reverse('api:[model]-list')
        data = {
            'name': '새 객체',
            'description': '설명',
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '새 객체'
        
        # Verify object created
        assert [Model].objects.filter(name='새 객체').exists()
    
    def test_update_endpoint(self):
        """Test updating object via API"""
        obj = [Model]Factory(user=self.user)
        url = reverse('api:[model]-detail', args=[obj.pk])
        
        data = {
            'name': '수정된 이름',
        }
        
        response = self.client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        obj.refresh_from_db()
        assert obj.name == '수정된 이름'
    
    def test_delete_endpoint(self):
        """Test deleting object via API"""
        obj = [Model]Factory(user=self.user)
        url = reverse('api:[model]-detail', args=[obj.pk])
        
        response = self.client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not [Model].objects.filter(pk=obj.pk).exists()
    
    def test_authentication_required(self):
        """Test API requires authentication"""
        self.client.force_authenticate(user=None)  # Logout
        
        url = reverse('api:[model]-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_filtering(self):
        """Test API filtering capabilities"""
        [Model]Factory.create_batch(3, user=self.user, status='active')
        [Model]Factory.create_batch(2, user=self.user, status='inactive')
        
        url = reverse('api:[model]-list')
        response = self.client.get(url, {'status': 'active'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
```

## HTMX Test Template

```python
"""
Tests for HTMX-enabled views.
"""
import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains

from apps.accounts.factories import UserFactory
from apps.[app_name].factories import [Model]Factory


class TestHTMXViews:
    """Test suite for HTMX functionality"""
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.user = UserFactory()
    
    def test_htmx_search(self, client):
        """Test HTMX search returns partial template"""
        client.force_login(self.user)
        
        # Create test data
        obj1 = [Model]Factory(user=self.user, name='Apple')
        obj2 = [Model]Factory(user=self.user, name='Banana')
        
        url = reverse('[app_name]:search')
        response = client.get(
            url,
            {'q': 'Apple'},
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assertContains(response, 'Apple')
        assert 'Banana' not in response.content.decode()
        
        # Should return partial template, not full page
        assert '<!DOCTYPE html>' not in response.content.decode()
    
    def test_htmx_form_validation(self, client):
        """Test HTMX form shows inline validation errors"""
        client.force_login(self.user)
        
        url = reverse('[app_name]:create')
        response = client.post(
            url,
            {'name': ''},  # Invalid - empty required field
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assertContains(response, '필수 항목입니다')
        
        # Should return just the form, not full page
        assert '<form' in response.content.decode()
        assert '<!DOCTYPE html>' not in response.content.decode()
    
    def test_htmx_delete_confirmation(self, client):
        """Test HTMX delete shows confirmation modal"""
        client.force_login(self.user)
        obj = [Model]Factory(user=self.user)
        
        url = reverse('[app_name]:delete', args=[obj.pk])
        response = client.get(
            url,
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assertContains(response, '정말 삭제하시겠습니까?')
        assertContains(response, f'hx-delete="{url}"')
    
    def test_htmx_infinite_scroll(self, client):
        """Test HTMX infinite scroll pagination"""
        client.force_login(self.user)
        
        # Create many objects
        [Model]Factory.create_batch(25, user=self.user)
        
        url = reverse('[app_name]:list')
        response = client.get(
            url,
            {'page': 2},
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        
        # Should have next page trigger
        if response.context['page_obj'].has_next():
            assertContains(response, 'hx-trigger="revealed"')
    
    def test_htmx_live_validation(self, client):
        """Test HTMX live field validation"""
        client.force_login(self.user)
        
        url = reverse('[app_name]:validate_field')
        response = client.post(
            url,
            {
                'field': 'email',
                'value': 'invalid-email'
            },
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assertContains(response, '올바른 이메일 주소를 입력하세요')
```

## Complete Feature Test Example

```python
"""
Complete test example for Session Package feature.
This demonstrates testing a complex feature with multiple components.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory
from apps.sessions.models import SessionPackage, Session, Payment


class TestSessionPackageFeature:
    """
    Complete test suite for session package management feature.
    Tests models, forms, views, and business logic.
    """
    
    pytestmark = pytest.mark.django_db
    
    def setup_method(self):
        """Set up test fixtures"""
        self.trainer = UserFactory()
        self.client_obj = ClientFactory(trainer=self.trainer)
    
    # Model Tests
    def test_package_creation(self):
        """Test creating a session package with fee calculations"""
        package = SessionPackageFactory(
            client=self.client_obj,
            trainer=self.trainer,
            package_type='10회',
            base_price=500000
        )
        
        # Check fee calculations
        assert package.vat_amount == Decimal('50000')  # 10% VAT
        assert package.card_fee == Decimal('17500')    # 3.5% card fee
        assert package.total_amount == Decimal('567500')
    
    def test_package_expiration(self):
        """Test package expiration logic"""
        # Create package that expires in 30 days
        package = SessionPackageFactory(
            valid_days=30,
            start_date=date.today() - timedelta(days=31)
        )
        
        assert package.is_expired is True
        assert package.days_remaining == -1
    
    def test_session_deduction(self):
        """Test session deduction from package"""
        package = SessionPackageFactory(
            total_sessions=10,
            used_sessions=0
        )
        
        # Use a session
        session = SessionFactory(
            package=package,
            status='completed'
        )
        
        package.refresh_from_db()
        assert package.used_sessions == 1
        assert package.remaining_sessions == 9
    
    # View Tests
    def test_package_list_view(self, client):
        """Test package list shows user's packages"""
        # Create packages
        package1 = SessionPackageFactory(trainer=self.trainer)
        package2 = SessionPackageFactory(trainer=self.trainer)
        other_package = SessionPackageFactory()  # Different trainer
        
        client.force_login(self.trainer)
        response = client.get(reverse('sessions:package_list'))
        
        assert response.status_code == 200
        assertContains(response, package1.client.name)
        assertContains(response, package2.client.name)
        assert other_package.client.name not in response.content.decode()
    
    def test_package_create_flow(self, client):
        """Test complete package creation flow"""
        client.force_login(self.trainer)
        
        # Step 1: Access create form
        url = reverse('sessions:package_create')
        response = client.get(url)
        assert response.status_code == 200
        
        # Step 2: Submit package data
        form_data = {
            'client': self.client_obj.id,
            'package_type': '10회',
            'base_price': '500000',
            'start_date': date.today().isoformat(),
            'valid_days': '30',
        }
        
        response = client.post(url, form_data)
        assertRedirects(response, reverse('sessions:package_list'))
        
        # Step 3: Verify package created
        package = SessionPackage.objects.get(client=self.client_obj)
        assert package.total_sessions == 10
        assert package.total_amount == Decimal('567500')
    
    def test_htmx_session_scheduling(self, client):
        """Test HTMX-based session scheduling"""
        package = SessionPackageFactory(
            trainer=self.trainer,
            total_sessions=10,
            used_sessions=0
        )
        
        client.force_login(self.trainer)
        
        # Schedule a session via HTMX
        url = reverse('sessions:schedule_session')
        response = client.post(
            url,
            {
                'package': package.id,
                'date': date.today().isoformat(),
                'time': '10:00',
            },
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'HX-Trigger' in response.headers
        
        # Verify session created
        session = Session.objects.get(package=package)
        assert session.status == 'scheduled'
    
    # Integration Tests
    def test_complete_package_lifecycle(self, client):
        """Test complete lifecycle: create, use, expire"""
        client.force_login(self.trainer)
        
        # 1. Create package
        package = SessionPackageFactory(
            trainer=self.trainer,
            total_sessions=3,
            valid_days=7
        )
        
        # 2. Schedule and complete sessions
        for i in range(2):
            session = SessionFactory(
                package=package,
                status='scheduled'
            )
            
            # Complete the session
            url = reverse('sessions:complete_session', args=[session.id])
            response = client.post(url)
            assert response.status_code == 302
        
        # 3. Check package status
        package.refresh_from_db()
        assert package.used_sessions == 2
        assert package.remaining_sessions == 1
        assert package.completion_rate == 67  # 2/3 = 67%
        
        # 4. Try to use expired package
        package.start_date = date.today() - timedelta(days=8)
        package.save()
        
        with pytest.raises(ValidationError):
            SessionFactory(package=package)
    
    # Edge Cases
    def test_refund_handling(self):
        """Test refund affects package status"""
        package = SessionPackageFactory(
            total_amount=Decimal('500000'),
            status='active'
        )
        
        # Process refund
        package.process_refund(amount=Decimal('500000'))
        
        assert package.status == 'refunded'
        assert package.is_active is False
    
    @pytest.mark.parametrize('sessions,amount,expected_per_session', [
        (10, '500000', '50000'),
        (20, '900000', '45000'), 
        (30, '1200000', '40000'),
    ])
    def test_per_session_pricing(self, sessions, amount, expected_per_session):
        """Test per-session price calculation"""
        package = SessionPackageFactory(
            total_sessions=sessions,
            base_price=Decimal(amount)
        )
        
        assert package.price_per_session == Decimal(expected_per_session)
```

## Usage Instructions

1. **Choose the appropriate template** based on what you're testing
2. **Copy the template** to your test file
3. **Replace placeholders** ([Model], [app_name], etc.) with actual names
4. **Remove unnecessary test methods** that don't apply
5. **Add specific test cases** for your feature's requirements
6. **Run the tests** to ensure they work correctly

## Tips for Using Templates

- Start with basic tests (creation, str representation)
- Add validation tests for all form fields
- Test both success and failure paths
- Include edge cases and error conditions
- Use parametrize for testing multiple scenarios
- Mock external dependencies
- Keep tests focused and independent

Remember: These are templates to get you started. Adapt them to your specific needs!