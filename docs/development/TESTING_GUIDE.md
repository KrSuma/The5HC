# The5HC Django Testing Guide

## Overview

This guide covers the testing infrastructure, best practices, and patterns for The5HC Django project. We use **pytest** as our testing framework, following modern Django testing practices.

## Table of Contents
1. [Testing Stack](#testing-stack)
2. [Quick Start](#quick-start)
3. [Project Testing Structure](#project-testing-structure)
4. [Writing Tests](#writing-tests)
5. [Factory Pattern](#factory-pattern)
6. [Common Testing Patterns](#common-testing-patterns)
7. [Running Tests](#running-tests)
8. [Debugging Tests](#debugging-tests)
9. [CI/CD Integration](#cicd-integration)
10. [Best Practices](#best-practices)

## Testing Stack

- **pytest** (8.3.4) - Modern Python testing framework
- **pytest-django** (4.10.0) - Django integration for pytest
- **pytest-mock** (3.15.0) - Mocking support
- **factory_boy** (3.3.1) - Test data generation
- **faker** - Realistic test data (included with factory_boy)

## Quick Start

### Running All Tests
```bash
cd django_migration
source venv/bin/activate
pytest
```

### Running Tests for Specific App
```bash
pytest apps/accounts/
pytest apps/clients/
pytest apps/assessments/
```

### Running Specific Test File
```bash
pytest apps/accounts/test_authentication.py
```

### Running Specific Test Method
```bash
pytest apps/accounts/test_authentication.py::TestAuthenticationViews::test_login_successful_with_username
```

### Running Tests with Coverage
```bash
pytest --cov=apps --cov-report=html
# View coverage report at htmlcov/index.html
```

## Project Testing Structure

```
django_migration/
├── pytest.ini                      # pytest configuration
├── conftest.py                     # Global fixtures and configuration
├── the5hc/settings/test.py        # Test-specific Django settings
├── apps/
│   ├── accounts/
│   │   ├── factories.py           # User and auth factories
│   │   ├── test_models.py         # User model tests
│   │   ├── test_forms_simple.py   # Form validation tests
│   │   ├── test_authentication.py # Auth views and workflow tests
│   │   └── test_views.py          # View tests
│   ├── clients/
│   │   ├── factories.py           # Client factories
│   │   └── test_clients.py        # Client model and view tests
│   ├── assessments/
│   │   ├── factories.py           # Assessment factories
│   │   └── test_assessments.py    # Assessment tests
│   └── sessions/
│       ├── factories.py           # Session package factories
│       └── test_sessions.py       # Session management tests
```

## Writing Tests

### Basic Test Structure

```python
"""
Pytest-style tests for [module] functionality.
Following django-test.md guidelines for modern Django testing.
"""
import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from .factories import UserFactory, ClientFactory


class TestClientViews:
    """Test suite for client views"""
    
    pytestmark = pytest.mark.django_db  # Enable database access
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user = UserFactory()
        self.client_url = reverse('clients:list')
    
    def test_client_list_requires_authentication(self, client):
        """Test that client list requires login"""
        response = client.get(self.client_url)
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_client_list_shows_user_clients(self, client):
        """Test that authenticated users see their clients"""
        # Create test data
        client1 = ClientFactory(trainer=self.user)
        client2 = ClientFactory(trainer=self.user)
        other_client = ClientFactory()  # Different trainer
        
        # Login and access
        client.force_login(self.user)
        response = client.get(self.client_url)
        
        # Assertions
        assert response.status_code == 200
        assertContains(response, client1.name)
        assertContains(response, client2.name)
        assert other_client.name not in response.content.decode()
```

### Model Tests

```python
class TestClientModel:
    """Test Client model functionality"""
    
    pytestmark = pytest.mark.django_db
    
    def test_bmi_calculation(self):
        """Test BMI property calculation"""
        client = ClientFactory(height=170, weight=70)
        
        expected_bmi = 70 / (1.70 ** 2)
        assert abs(client.BMI - expected_bmi) < 0.01
    
    def test_str_representation(self):
        """Test string representation"""
        client = ClientFactory(name="홍길동")
        
        assert str(client) == "홍길동"
    
    @pytest.mark.parametrize('height,weight,expected_bmi', [
        (170, 70, 24.22),
        (180, 80, 24.69),
        (160, 55, 21.48),
    ])
    def test_bmi_various_inputs(self, height, weight, expected_bmi):
        """Test BMI calculation with various inputs"""
        client = ClientFactory(height=height, weight=weight)
        
        assert abs(client.BMI - expected_bmi) < 0.01
```

### Form Tests

```python
class TestClientForm:
    """Test client form validation"""
    
    def test_valid_form_data(self):
        """Test form with valid data"""
        form_data = {
            'name': '김철수',
            'email': 'kim@example.com',
            'phone_number': '010-1234-5678',
            'birth_date': '1990-01-01',
            'height': 175,
            'weight': 70,
        }
        form = ClientForm(data=form_data)
        
        assert form.is_valid()
    
    def test_invalid_email(self):
        """Test form with invalid email"""
        form_data = {
            'name': '김철수',
            'email': 'invalid-email',
            # ... other fields
        }
        form = ClientForm(data=form_data)
        
        assert not form.is_valid()
        assert 'email' in form.errors
```

### View Tests with HTMX

```python
class TestHTMXViews:
    """Test HTMX-enabled views"""
    
    pytestmark = pytest.mark.django_db
    
    def test_htmx_client_search(self, client, rf):
        """Test HTMX search functionality"""
        user = UserFactory()
        client1 = ClientFactory(trainer=user, name="김철수")
        client2 = ClientFactory(trainer=user, name="이영희")
        
        client.force_login(user)
        
        # Make HTMX request
        response = client.get(
            reverse('clients:search'),
            {'q': '김'},
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assertContains(response, "김철수")
        assert "이영희" not in response.content.decode()
        
    def test_htmx_form_submission(self, client):
        """Test HTMX form submission"""
        user = UserFactory()
        client.force_login(user)
        
        response = client.post(
            reverse('clients:create'),
            {'name': '새 고객', 'email': 'new@example.com'},
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'HX-Redirect' in response.headers
```

## Factory Pattern

### Basic Factory Usage

```python
# apps/accounts/factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances with Korean data"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f'trainer{n}')
    email = factory.Faker('email', locale='ko_KR')
    name = factory.Faker('name', locale='ko_KR')
    is_active = True
    is_staff = False
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')
        obj.save()


class AdminUserFactory(UserFactory):
    """Factory for admin users"""
    is_staff = True
    is_superuser = True


class ClientFactory(DjangoModelFactory):
    """Factory for creating Client instances"""
    
    class Meta:
        model = 'clients.Client'
    
    trainer = factory.SubFactory(UserFactory)
    name = factory.Faker('name', locale='ko_KR')
    email = factory.Faker('email', locale='ko_KR')
    phone_number = factory.Faker('phone_number', locale='ko_KR')
    birth_date = factory.Faker('date_of_birth', minimum_age=20, maximum_age=60)
    height = factory.Faker('random_int', min=150, max=190)
    weight = factory.Faker('random_int', min=45, max=100)
```

### Advanced Factory Patterns

```python
class AssessmentFactory(DjangoModelFactory):
    """Factory with calculated fields"""
    
    class Meta:
        model = 'assessments.Assessment'
    
    client = factory.SubFactory(ClientFactory)
    date = factory.Faker('date_this_year')
    
    # Fitness test scores (0-100 range)
    test1 = factory.Faker('random_int', min=40, max=90)
    test2 = factory.Faker('random_int', min=40, max=90)
    # ... more test fields
    
    @factory.lazy_attribute
    def overall_score(self):
        """Calculate overall score from test scores"""
        scores = [self.test1, self.test2]  # Add all test scores
        return sum(scores) / len(scores)


class SessionPackageFactory(DjangoModelFactory):
    """Factory with related objects"""
    
    class Meta:
        model = 'sessions.SessionPackage'
    
    trainer = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory, trainer=factory.SelfAttribute('..trainer'))
    package_name = factory.Faker('random_element', elements=['10회', '20회', '30회'])
    
    @factory.post_generation
    def sessions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for session in extracted:
                self.sessions.add(session)
```

## Common Testing Patterns

### Authentication Testing

```python
def test_view_requires_authentication(client):
    """Test that view redirects anonymous users"""
    response = client.get(reverse('protected:view'))
    
    assert response.status_code == 302
    assert '/accounts/login/' in response.url


def test_authenticated_access(client):
    """Test authenticated user can access view"""
    user = UserFactory()
    client.force_login(user)
    
    response = client.get(reverse('protected:view'))
    
    assert response.status_code == 200
```

### Form Testing with Validation

```python
def test_form_validation_errors():
    """Test form shows appropriate validation errors"""
    form = ClientForm(data={
        'name': '',  # Required field
        'email': 'invalid',  # Invalid format
    })
    
    assert not form.is_valid()
    assert 'name' in form.errors
    assert 'email' in form.errors
    assert '필수 항목입니다' in str(form.errors['name'])
```

### Testing Database Queries

```python
@pytest.mark.django_db
def test_optimized_queries(django_assert_num_queries):
    """Test view uses optimized queries"""
    user = UserFactory()
    ClientFactory.create_batch(10, trainer=user)
    
    with django_assert_num_queries(2):  # Expect exactly 2 queries
        list(Client.objects.filter(trainer=user).select_related('trainer'))
```

### Mocking External Services

```python
def test_email_sending(mocker):
    """Test email is sent on user registration"""
    mock_send_mail = mocker.patch('django.core.mail.send_mail')
    
    # Create user which triggers email
    user = UserFactory()
    
    # Verify email was called
    mock_send_mail.assert_called_once()
    assert user.email in mock_send_mail.call_args[1]['recipient_list']
```

### Testing File Uploads

```python
def test_pdf_report_generation(client, tmp_path):
    """Test PDF report is generated correctly"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    user = UserFactory()
    assessment = AssessmentFactory()
    client.force_login(user)
    
    response = client.post(
        reverse('reports:generate'),
        {'assessment_id': assessment.id}
    )
    
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s

# Run specific test pattern
pytest -k "test_login"

# Run failed tests from last run
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Performance Options

```bash
# Reuse test database (faster for multiple runs)
pytest --reuse-db

# Create new test database
pytest --create-db

# Skip migrations (fastest, but may miss migration issues)
pytest --no-migrations
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=apps --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=apps --cov-report=html

# Fail if coverage is below threshold
pytest --cov=apps --cov-fail-under=80
```

## Debugging Tests

### Using pdb

```python
def test_complex_logic():
    """Test with debugging"""
    import pdb; pdb.set_trace()  # Breakpoint
    
    result = complex_function()
    assert result == expected
```

### Print Debugging

```bash
# Run tests with print output
pytest -s

# In test code
def test_debug_output(capfd):
    """Test with captured output"""
    print("Debug info:", some_value)
    
    # Test continues...
    
    # Check printed output
    captured = capfd.readouterr()
    assert "Debug info:" in captured.out
```

### Detailed Failure Information

```bash
# Show full diff for assertion failures
pytest -vv

# Show local variables in tracebacks
pytest --showlocals

# Stop on first failure
pytest -x

# Enter pdb on failures
pytest --pdb
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost/test_db
      run: |
        cd django_migration
        pytest --cov=apps --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: bash -c 'cd django_migration && pytest'
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### 1. Test Organization
- One test file per module (test_models.py, test_views.py, test_forms.py)
- Group related tests in classes
- Use descriptive test names that explain what is being tested

### 2. Test Data
- Always use factories instead of creating objects manually
- Use realistic Korean data with proper locale
- Create minimal data needed for each test
- Clean up is automatic with pytest transactions

### 3. Assertions
- Use simple, clear assertions
- One logical assertion per test method
- Use pytest's detailed assertion introspection
- Avoid complex assertion logic

### 4. Performance
- Use pytest-django's fixtures for database access
- Mock external services and API calls
- Use --reuse-db for faster local development
- Profile slow tests and optimize

### 5. Maintainability
- Keep tests simple and focused
- Don't test Django's built-in functionality
- Update tests when changing code
- Remove obsolete tests

### 6. Documentation
- Add docstrings to complex test methods
- Document test fixtures and utilities
- Keep this guide updated with new patterns

## Common Issues and Solutions

### Issue: Tests fail with "No such table"
**Solution**: Run migrations or use --create-db flag
```bash
pytest --create-db
```

### Issue: Locale errors with Korean data
**Solution**: Install Korean locale
```bash
# On Ubuntu/Debian
sudo locale-gen ko_KR.UTF-8
sudo update-locale
```

### Issue: Tests are slow
**Solution**: Use test optimizations
```bash
# Use faster password hasher (in test settings)
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Reuse database
pytest --reuse-db

# Run in parallel
pytest -n auto
```

### Issue: Import errors
**Solution**: Ensure proper Python path
```bash
# From django_migration directory
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [factory_boy documentation](https://factoryboy.readthedocs.io/)
- [Django testing documentation](https://docs.djangoproject.com/en/5.0/topics/testing/)

## Next Steps

1. Run the test suite regularly during development
2. Add tests for new features before implementing
3. Maintain test coverage above 80%
4. Set up CI/CD to run tests automatically
5. Review and refactor tests periodically