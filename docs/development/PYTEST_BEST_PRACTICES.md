# Pytest Best Practices for The5HC Team

## Introduction

This document outlines pytest-specific best practices for The5HC development team. Follow these guidelines to write consistent, maintainable, and efficient tests.

## 🎯 Core Principles

### 1. **Tests Should Be Independent**
Each test must run successfully on its own and not depend on other tests.

```python
# ❌ BAD - Tests depend on each other
class TestUserWorkflow:
    def test_create_user(self):
        self.user = User.objects.create(username='test')
    
    def test_login_user(self):
        # This fails if test_create_user didn't run first!
        response = self.client.login(username='test', password='pass')

# ✅ GOOD - Each test is independent
class TestUserWorkflow:
    def test_create_user(self):
        user = UserFactory()
        assert user.id is not None
    
    def test_login_user(self):
        user = UserFactory(password='testpass')
        response = self.client.login(username=user.username, password='testpass')
```

### 2. **Use Fixtures for Setup, Not Methods**

```python
# ❌ BAD - Using setUp method (unittest style)
class TestClient:
    def setUp(self):
        self.user = User.objects.create_user(...)
        self.client = Client.objects.create(...)

# ✅ GOOD - Using pytest fixtures
@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def client_obj(user):
    return ClientFactory(trainer=user)

class TestClient:
    def test_client_detail(self, client, user, client_obj):
        client.force_login(user)
        response = client.get(f'/clients/{client_obj.id}/')
        assert response.status_code == 200
```

### 3. **Always Use Factory Pattern**

```python
# ❌ BAD - Manual object creation
def test_client_creation():
    user = User.objects.create(
        username='trainer1',
        email='trainer@example.com',
        password='password123'
    )
    client = Client.objects.create(
        trainer=user,
        name='홍길동',
        email='hong@example.com',
        phone_number='010-1234-5678'
    )

# ✅ GOOD - Using factories
def test_client_creation():
    client = ClientFactory()
    assert client.trainer is not None
    assert client.name  # Auto-generated Korean name
```

## 📝 Naming Conventions

### Test Files
- Start with `test_` prefix: `test_models.py`, `test_views.py`
- Mirror the module being tested: `models.py` → `test_models.py`

### Test Classes
- Use `Test` prefix with descriptive name
- Group related tests logically

```python
class TestUserAuthentication:
    """Tests for user authentication functionality"""

class TestUserPermissions:
    """Tests for user permission checks"""
```

### Test Methods
- Start with `test_`
- Be descriptive about what is being tested
- Include the expected behavior

```python
# ❌ BAD - Vague test names
def test_user():
    pass

def test_login():
    pass

# ✅ GOOD - Clear, descriptive names
def test_user_creation_with_valid_data_succeeds():
    pass

def test_login_with_invalid_credentials_returns_error():
    pass

def test_locked_account_prevents_login_until_timeout():
    pass
```

## 🏗️ Test Structure

### Arrange-Act-Assert Pattern

```python
def test_client_bmi_calculation():
    # Arrange - Set up test data
    client = ClientFactory(height=170, weight=70)
    
    # Act - Perform the action
    bmi = client.calculate_bmi()
    
    # Assert - Check the result
    assert bmi == pytest.approx(24.22, rel=0.01)
```

### Given-When-Then for Complex Tests

```python
def test_session_package_expiration():
    """
    Given a session package with 10 sessions valid for 30 days
    When 8 sessions are used and 31 days have passed
    Then the package should be marked as expired
    """
    # Given
    package = SessionPackageFactory(
        total_sessions=10,
        valid_days=30,
        created_at=timezone.now() - timedelta(days=31)
    )
    SessionFactory.create_batch(8, package=package, status='completed')
    
    # When
    package.refresh_from_db()
    is_expired = package.is_expired()
    
    # Then
    assert is_expired is True
    assert package.remaining_sessions == 2
```

## 🎨 Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize('email,is_valid', [
    ('user@example.com', True),
    ('user.name@example.co.kr', True),
    ('invalid.email', False),
    ('@example.com', False),
    ('user@', False),
    ('', False),
])
def test_email_validation(email, is_valid):
    """Test email validation with various inputs"""
    form = ClientForm(data={'email': email, 'name': 'Test'})
    
    if is_valid:
        assert 'email' not in form.errors
    else:
        assert 'email' in form.errors


@pytest.mark.parametrize('height,weight,expected_bmi,bmi_category', [
    (170, 50, 17.30, '저체중'),
    (170, 65, 22.49, '정상'),
    (170, 75, 25.95, '과체중'),
    (170, 90, 31.14, '비만'),
])
def test_bmi_calculation_and_category(height, weight, expected_bmi, bmi_category):
    """Test BMI calculation returns correct value and category"""
    client = ClientFactory(height=height, weight=weight)
    
    assert client.bmi == pytest.approx(expected_bmi, rel=0.01)
    assert client.bmi_category == bmi_category
```

## 🔧 Fixtures Best Practices

### Scope Management

```python
# Module-level fixture (created once per module)
@pytest.fixture(scope='module')
def expensive_resource():
    """Use for expensive operations like loading large datasets"""
    return load_reference_data()

# Function-level fixture (default - created for each test)
@pytest.fixture
def client_with_assessment():
    """Fresh data for each test"""
    client = ClientFactory()
    AssessmentFactory(client=client)
    return client

# Class-level fixture (shared within test class)
@pytest.fixture(scope='class')
def api_client():
    """Reused within a test class"""
    return APIClient()
```

### Fixture Composition

```python
@pytest.fixture
def trainer():
    """Base trainer fixture"""
    return UserFactory(is_staff=True)

@pytest.fixture
def trainer_with_clients(trainer):
    """Trainer with associated clients"""
    ClientFactory.create_batch(5, trainer=trainer)
    return trainer

@pytest.fixture
def full_test_setup(trainer_with_clients):
    """Complete test environment"""
    for client in trainer_with_clients.clients.all():
        AssessmentFactory(client=client)
        SessionPackageFactory(client=client, trainer=trainer_with_clients)
    return trainer_with_clients
```

### Auto-use Fixtures

```python
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This is useful when all tests in a module need DB access.
    """
    pass

@pytest.fixture(autouse=True)
def set_test_environment(settings):
    """Automatically configure test environment"""
    settings.DEBUG = False
    settings.TESTING = True
```

## 🚀 Performance Tips

### 1. **Use --reuse-db for Local Development**
```bash
# First run creates test database
pytest --reuse-db

# Subsequent runs reuse the database (much faster)
pytest --reuse-db
```

### 2. **Optimize Database Queries**
```python
def test_efficient_client_list(django_assert_num_queries):
    """Ensure view uses optimal queries"""
    trainer = UserFactory()
    ClientFactory.create_batch(10, trainer=trainer)
    
    # This should use exactly 2 queries
    with django_assert_num_queries(2):
        clients = Client.objects.filter(trainer=trainer).select_related('trainer')
        list(clients)  # Force evaluation
```

### 3. **Mock External Services**
```python
@pytest.fixture
def mock_email_service(mocker):
    """Mock email sending to avoid actual emails in tests"""
    return mocker.patch('django.core.mail.send_mail')

def test_registration_sends_email(mock_email_service):
    """Test email is sent without actually sending"""
    UserFactory()
    mock_email_service.assert_called_once()
```

## 🐛 Debugging Tests

### 1. **Use -s Flag for Print Debugging**
```python
def test_complex_calculation():
    result = complex_function()
    print(f"Result: {result}")  # This will show with pytest -s
    assert result == expected
```

### 2. **Use --pdb for Interactive Debugging**
```bash
# Drop into debugger on failure
pytest --pdb

# In your test
def test_debug_me():
    import pdb; pdb.set_trace()  # Manual breakpoint
    result = function_to_debug()
```

### 3. **Capture Logs**
```python
def test_error_logging(caplog):
    """Test that errors are logged correctly"""
    with caplog.at_level(logging.ERROR):
        trigger_error_condition()
    
    assert 'Expected error message' in caplog.text
```

## ⚠️ Common Pitfalls and Solutions

### 1. **Forgetting @pytest.mark.django_db**
```python
# ❌ This will fail with "Database access not allowed"
def test_user_creation():
    user = UserFactory()

# ✅ Correct way
@pytest.mark.django_db
def test_user_creation():
    user = UserFactory()
```

### 2. **Modifying Fixtures**
```python
# ❌ BAD - Modifying shared fixture
@pytest.fixture(scope='module')
def user():
    return UserFactory()

def test_modify_user(user):
    user.name = 'Modified'
    user.save()  # This affects other tests!

# ✅ GOOD - Create new instance or use function scope
@pytest.fixture
def user():
    return UserFactory()
```

### 3. **Testing Django Internals**
```python
# ❌ BAD - Testing Django's functionality
def test_django_orm_save():
    user = UserFactory()
    assert user.pk is not None  # Django guarantees this

# ✅ GOOD - Test your business logic
def test_user_activation_sends_notification():
    user = UserFactory(is_active=False)
    user.activate()
    assert user.is_active
    assert user.activation_email_sent
```

## 📊 Coverage Guidelines

### Running Coverage
```bash
# Generate coverage report
pytest --cov=apps --cov-report=html

# View missing lines
pytest --cov=apps --cov-report=term-missing
```

### What to Test
- ✅ Business logic
- ✅ Custom model methods
- ✅ Form validation
- ✅ View permissions and responses
- ✅ API endpoints
- ✅ Error handling

### What NOT to Test
- ❌ Django admin (unless customized)
- ❌ Third-party library internals
- ❌ Django ORM basic operations
- ❌ Simple property methods
- ❌ Database migrations

## 🔄 Continuous Integration

### Pre-commit Testing
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: django-tests
        name: Django Tests
        entry: bash -c 'cd django_migration && pytest apps/'
        language: system
        pass_filenames: false
        types: [python]
```

### GitHub Actions
```yaml
- name: Run Tests
  run: |
    cd django_migration
    pytest --cov=apps --cov-report=xml -v
    
- name: Check Coverage
  run: |
    coverage report --fail-under=80
```

## 📚 Additional Resources

### Useful Pytest Plugins
- `pytest-timeout` - Prevent hanging tests
- `pytest-randomly` - Run tests in random order
- `pytest-benchmark` - Performance testing
- `pytest-asyncio` - Async test support

### Commands Cheat Sheet
```bash
# Run last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "login or auth"

# Show local variables on failure
pytest -l

# Stop after first failure
pytest -x

# Run tests in parallel
pytest -n 4

# Show slowest tests
pytest --durations=10
```

## 🎉 Summary

Remember these key points:
1. Write independent tests using factories
2. Use descriptive names and clear structure
3. Leverage pytest features (fixtures, parametrize, marks)
4. Mock external dependencies
5. Keep tests simple and focused
6. Run tests frequently during development

Happy testing! 🚀