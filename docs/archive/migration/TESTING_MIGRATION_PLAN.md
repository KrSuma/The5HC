# Testing Infrastructure Migration Plan

**Date**: 2025-01-09
**Purpose**: Migrate from Django TestCase to pytest following django-test.md guidelines
**Estimated Timeline**: 2-3 weeks

## Overview

This plan outlines the step-by-step process to migrate our testing infrastructure from Django's built-in `TestCase` to modern pytest-based testing following the established guidelines.

## Phase 1: Setup and Configuration (Day 1-2)

### Step 1: Install Required Packages
```bash
pip install pytest==8.0.0
pip install pytest-django==4.7.0
pip install pytest-cov==4.1.0
pip install factory-boy==3.3.0
pip install pytest-mock==3.12.0
pip install pytest-asyncio==0.23.0
pip install faker==22.0.0

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 2: Create pytest Configuration
Create `pytest.ini` in project root:
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = the5hc.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = apps tests
addopts = 
    --reuse-db 
    --nomigrations
    --cov=apps
    --cov-report=html
    --cov-report=term-missing:skip-covered
    -v
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Step 3: Create Test Settings Module
Create `the5hc/settings/test.py`:
```python
from .base import *

# Test-specific settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable caching in tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable debug toolbar
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,
}
```

### Step 4: Create conftest.py
Create `conftest.py` in project root:
```python
import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

@pytest.fixture
def api_client():
    """Django test client instance"""
    return Client()

@pytest.fixture
def authenticated_client(db):
    """Authenticated client with test user"""
    from apps.accounts.factories import UserFactory
    user = UserFactory()
    client = Client()
    client.force_login(user)
    return client

@pytest.fixture
def test_user(db):
    """Create a test user"""
    from apps.accounts.factories import UserFactory
    return UserFactory()

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database by default.
    Tests that don't need DB access can use @pytest.mark.django_db(transaction=False)
    """
    pass
```

## Phase 2: Create Factory Classes (Day 3-4)

### Step 5: Create Base Factory Configuration
Create `apps/factories.py`:
```python
import factory
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker('ko_KR')  # Korean locale for realistic data

class BaseFactory(DjangoModelFactory):
    """Base factory with common configuration"""
    class Meta:
        abstract = True
```

### Step 6: Create Model Factories

#### accounts/factories.py
```python
import factory
from django.contrib.auth import get_user_model
from apps.factories import BaseFactory, fake

User = get_user_model()

class UserFactory(BaseFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'trainer{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')
```

#### clients/factories.py
```python
import factory
from apps.factories import BaseFactory, fake
from apps.accounts.factories import UserFactory
from .models import Client

class ClientFactory(BaseFactory):
    class Meta:
        model = Client
    
    trainer = factory.SubFactory(UserFactory)
    name = factory.LazyFunction(lambda: fake.name())
    email = factory.Faker('email')
    phone = factory.LazyFunction(lambda: fake.phone_number())
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=65)
    gender = factory.Iterator(['male', 'female'])
    height = factory.Faker('pydecimal', left_digits=3, right_digits=1, min_value=150, max_value=200)
    weight = factory.Faker('pydecimal', left_digits=2, right_digits=1, min_value=45, max_value=120)
    notes = factory.Faker('text', max_nb_chars=200)
    is_active = True
```

#### assessments/factories.py
```python
import factory
from apps.factories import BaseFactory, fake
from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from .models import Assessment

class AssessmentFactory(BaseFactory):
    class Meta:
        model = Assessment
    
    trainer = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)
    assessment_date = factory.Faker('date_this_year')
    
    # Body composition
    body_fat_percentage = factory.Faker('pydecimal', left_digits=2, right_digits=1, min_value=5, max_value=35)
    muscle_mass = factory.Faker('pydecimal', left_digits=2, right_digits=1, min_value=20, max_value=50)
    
    # Test scores (will be customized per test)
    @factory.lazy_attribute
    def test_scores(self):
        return {
            'push_ups': fake.random_int(min=10, max=50),
            'sit_ups': fake.random_int(min=20, max=60),
            'flexibility': fake.pydecimal(left_digits=2, right_digits=1, min_value=-10, max_value=20),
            # Add more test fields as needed
        }
```

#### sessions/factories.py
```python
import factory
from decimal import Decimal
from apps.factories import BaseFactory, fake
from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from .models import SessionPackage, Session, Payment

class SessionPackageFactory(BaseFactory):
    class Meta:
        model = SessionPackage
    
    trainer = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)
    package_name = factory.LazyAttribute(lambda obj: f'{obj.client.name} 패키지')
    total_sessions = factory.Iterator([10, 20, 30, 50])
    session_cost = factory.Iterator([50000, 60000, 70000, 80000])
    gross_amount = factory.LazyAttribute(lambda obj: obj.total_sessions * obj.session_cost)
    remaining_sessions = factory.LazyAttribute(lambda obj: obj.total_sessions)
    is_active = True

class SessionFactory(BaseFactory):
    class Meta:
        model = Session
    
    package = factory.SubFactory(SessionPackageFactory)
    session_date = factory.Faker('date_between', start_date='today', end_date='+30d')
    session_duration = 60
    session_cost = factory.LazyAttribute(lambda obj: obj.package.session_cost)
    status = 'scheduled'
    notes = factory.Faker('text', max_nb_chars=100)

class PaymentFactory(BaseFactory):
    class Meta:
        model = Payment
    
    package = factory.SubFactory(SessionPackageFactory)
    amount = factory.LazyAttribute(lambda obj: obj.package.gross_amount)
    payment_date = factory.Faker('date_this_month')
    payment_method = factory.Iterator(['card', 'cash', 'transfer'])
```

## Phase 3: Convert Existing Tests (Day 5-10)

### Step 7: Create Conversion Script
Create a script to help identify patterns and plan conversion:
```python
# scripts/analyze_tests.py
import os
import ast

def analyze_test_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    # Count TestCase classes
    testcase_count = 0
    test_methods = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if any(base.id == 'TestCase' for base in node.bases if hasattr(base, 'id')):
                testcase_count += 1
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        test_methods.append(item.name)
    
    return {
        'file': filepath,
        'testcase_count': testcase_count,
        'test_methods': test_methods,
        'total_tests': len(test_methods)
    }

# Run analysis
for app in ['accounts', 'clients', 'assessments', 'sessions']:
    test_file = f'apps/{app}/tests.py'
    if os.path.exists(test_file):
        print(analyze_test_file(test_file))
```

### Step 8: Convert Tests by App

#### Conversion Template
For each app, follow this pattern:

1. **Rename existing file**: `tests.py` → `tests_old.py`
2. **Create new test structure**:
   ```
   apps/accounts/tests/
   ├── __init__.py
   ├── test_models.py
   ├── test_views.py
   ├── test_forms.py
   └── test_integration.py
   ```

#### Example Conversion (accounts/tests/test_views.py)
```python
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed, assertRedirects

from apps.accounts.factories import UserFactory

@pytest.mark.django_db
class TestLoginView:
    """Test cases for login functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.login_url = reverse('accounts:login')
        self.dashboard_url = reverse('accounts:dashboard')
    
    def test_login_page_renders(self, client):
        """Test login page GET request"""
        response = client.get(self.login_url)
        
        assert response.status_code == 200
        assertTemplateUsed(response, 'registration/login.html')
    
    def test_login_with_username_success(self, client):
        """Test successful login with username"""
        user = UserFactory(username='test_trainer', password='testpass123')
        
        response = client.post(self.login_url, {
            'email_or_username': 'test_trainer',
            'password': 'testpass123'
        })
        
        assert response.status_code == 302
        assertRedirects(response, self.dashboard_url)
    
    @pytest.mark.parametrize('credentials,expected_error', [
        ({'email_or_username': 'wrong', 'password': 'testpass123'}, '잘못된 이메일'),
        ({'email_or_username': 'test_trainer', 'password': 'wrong'}, '잘못된 비밀번호'),
        ({'email_or_username': '', 'password': ''}, '필수 항목입니다'),
    ])
    def test_login_failures(self, client, credentials, expected_error):
        """Test various login failure scenarios"""
        UserFactory(username='test_trainer', password='testpass123')
        
        response = client.post(self.login_url, credentials)
        
        assert response.status_code == 200
        assert expected_error in response.content.decode('utf-8')
    
    def test_htmx_login_request(self, client):
        """Test HTMX login returns correct headers"""
        user = UserFactory(password='testpass123')
        
        response = client.post(
            self.login_url,
            {'email_or_username': user.username, 'password': 'testpass123'},
            HTTP_HX_REQUEST='true'
        )
        
        assert response.status_code == 200
        assert 'HX-Redirect' in response.headers
```

### Step 9: Create Test Migration Checklist

Create a tracking document for conversion progress:
```markdown
# Test Migration Checklist

## accounts app
- [ ] Create factories.py
- [ ] Convert test_models.py
- [ ] Convert test_views.py
- [ ] Convert test_forms.py
- [ ] Remove old tests.py
- [ ] Verify all tests pass

## clients app
- [ ] Create factories.py
- [ ] Convert test_models.py
- [ ] Convert test_views.py
- [ ] Convert test_forms.py
- [ ] Remove old tests.py
- [ ] Verify all tests pass

## assessments app
- [ ] Create factories.py
- [ ] Convert test_models.py
- [ ] Convert test_views.py
- [ ] Convert test_forms.py
- [ ] Remove old tests.py
- [ ] Verify all tests pass

## sessions app
- [ ] Create factories.py
- [ ] Convert test_models.py
- [ ] Convert test_views.py
- [ ] Convert test_forms.py
- [ ] Remove old tests.py
- [ ] Verify all tests pass
```

## Phase 4: Advanced Testing Features (Day 11-12)

### Step 10: Add Advanced pytest Features

#### Create fixtures for common scenarios
```python
# conftest.py additions
@pytest.fixture
def mock_email_backend(settings):
    """Mock email backend for testing"""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

@pytest.fixture
def api_request_factory():
    """Request factory for API testing"""
    from django.test import RequestFactory
    return RequestFactory()

@pytest.fixture
def captured_queries(django_capture_on_commit_callbacks):
    """Fixture to capture database queries"""
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    with CaptureQueriesContext(connection) as context:
        yield context
```

#### Add performance testing
```python
# apps/clients/tests/test_performance.py
import pytest
from django.test.utils import override_settings

from apps.clients.factories import ClientFactory

@pytest.mark.django_db
class TestClientPerformance:
    """Performance tests for client operations"""
    
    @pytest.mark.slow
    def test_client_list_query_count(self, django_assert_num_queries, authenticated_client):
        """Ensure client list view doesn't have N+1 queries"""
        # Create test data
        ClientFactory.create_batch(10)
        
        # Test query count
        with django_assert_num_queries(2):  # 1 for auth, 1 for clients
            response = authenticated_client.get('/clients/')
            assert response.status_code == 200
```

### Step 11: Add Integration Tests
```python
# tests/test_integration.py
import pytest
from django.urls import reverse

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory

@pytest.mark.django_db
@pytest.mark.integration
class TestAssessmentWorkflow:
    """Integration tests for complete assessment workflow"""
    
    def test_complete_assessment_flow(self, client):
        """Test creating client and performing assessment"""
        # Create trainer
        trainer = UserFactory(password='testpass123')
        
        # Login
        client.post(reverse('accounts:login'), {
            'email_or_username': trainer.username,
            'password': 'testpass123'
        })
        
        # Create client
        response = client.post(reverse('clients:create'), {
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '010-1234-5678',
            'date_of_birth': '1990-01-01',
            'gender': 'male',
            'height': 175,
            'weight': 70
        })
        assert response.status_code == 302
        
        # Verify client created
        from apps.clients.models import Client
        test_client = Client.objects.get(email='test@example.com')
        assert test_client.trainer == trainer
        
        # Create assessment
        response = client.post(reverse('assessments:create'), {
            'client_id': test_client.id,
            'assessment_date': '2024-01-01',
            'body_fat_percentage': 15.5,
            # ... other fields
        })
        assert response.status_code == 302
```

## Phase 5: CI/CD Integration (Day 13-14)

### Step 12: Create GitHub Actions Workflow
Create `.github/workflows/test.yml`:
```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

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
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      run: |
        pytest --cov --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Step 13: Add Pre-commit Hooks
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ['-x', '--tb=short']
```

## Phase 6: Documentation and Training (Day 14)

### Step 14: Create Testing Documentation
Create `docs/TESTING_GUIDE.md`:
```markdown
# Testing Guide

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific app tests
```bash
pytest apps/accounts/
```

### Run with coverage
```bash
pytest --cov=apps --cov-report=html
```

### Run specific test markers
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests
```

## Writing Tests

### Basic Test Structure
```python
import pytest
from apps.accounts.factories import UserFactory

@pytest.mark.django_db
def test_user_creation():
    user = UserFactory()
    assert user.is_active
```

### Using Factories
```python
# Create single instance
user = UserFactory()

# Create multiple instances
users = UserFactory.create_batch(5)

# Create with specific attributes
admin = UserFactory(is_staff=True, is_superuser=True)
```

### Testing Views
```python
def test_view_requires_login(client):
    response = client.get('/protected/')
    assert response.status_code == 302
```
```

### Step 15: Team Training
1. Conduct workshop on pytest basics
2. Review factory_boy patterns
3. Practice converting existing tests together
4. Establish testing best practices

## Success Criteria

- [ ] All tests converted to pytest
- [ ] 90%+ code coverage maintained
- [ ] CI/CD pipeline running all tests
- [ ] Team trained on new testing approach
- [ ] Documentation complete
- [ ] All tests passing in < 2 minutes

## Rollback Plan

If issues arise:
1. Keep `tests_old.py` files until fully migrated
2. Can run both pytest and Django tests during transition
3. Gradual migration app by app
4. Revert to Django TestCase if critical issues

## Timeline Summary

- **Week 1**: Setup, configuration, and factory creation
- **Week 2**: Test conversion and advanced features
- **Week 3**: CI/CD integration, documentation, and training

Total estimated time: 2-3 weeks depending on team size and existing test complexity.