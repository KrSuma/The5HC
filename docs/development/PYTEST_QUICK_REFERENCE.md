# pytest Quick Reference Guide

## Django TestCase vs pytest Comparison

### Basic Test Structure

**Django TestCase (OLD)**
```python
from django.test import TestCase

class MyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(...)
    
    def test_something(self):
        self.assertEqual(1 + 1, 2)
```

**pytest (NEW)**
```python
import pytest

@pytest.mark.django_db
class TestMyFeature:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
    
    def test_something(self):
        assert 1 + 1 == 2
```

## Common Conversions

### Assertions

| Django TestCase | pytest |
|----------------|---------|
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertTrue(x)` | `assert x` |
| `self.assertFalse(x)` | `assert not x` |
| `self.assertIn(a, b)` | `assert a in b` |
| `self.assertIsNone(x)` | `assert x is None` |
| `self.assertRaises(Exception)` | `with pytest.raises(Exception):` |
| `self.assertContains(response, text)` | `assertContains(response, text)` * |
| `self.assertRedirects(response, url)` | `assertRedirects(response, url)` * |

\* Import from `pytest_django.asserts`

### Database Access

**Django TestCase**: Automatic
```python
class MyTest(TestCase):
    def test_db_access(self):
        User.objects.create(...)  # Works automatically
```

**pytest**: Explicit
```python
@pytest.mark.django_db
def test_db_access():
    User.objects.create(...)  # Requires decorator
```

### Client Usage

**Django TestCase**
```python
class MyTest(TestCase):
    def test_view(self):
        response = self.client.get('/url/')
```

**pytest**
```python
def test_view(client):  # client is a fixture
    response = client.get('/url/')
```

## Key pytest Features

### Fixtures

```python
@pytest.fixture
def sample_data():
    return {'key': 'value'}

def test_using_fixture(sample_data):
    assert sample_data['key'] == 'value'
```

### Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

### Marking Tests

```python
@pytest.mark.slow
def test_slow_operation():
    # Run with: pytest -m "not slow"
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass
```

## Factory Usage

### Creating Objects

```python
# Single object
user = UserFactory()

# With specific attributes
admin = UserFactory(is_staff=True, username='admin')

# Multiple objects
users = UserFactory.create_batch(5)

# Using build (not saved to DB)
user = UserFactory.build()
```

### Common Factory Patterns

```python
# SubFactory for relationships
class ClientFactory(factory.Factory):
    trainer = factory.SubFactory(UserFactory)

# Sequence for unique values
username = factory.Sequence(lambda n: f'user{n}')

# Faker for realistic data
email = factory.Faker('email')
name = factory.Faker('name', locale='ko_KR')

# LazyAttribute for computed values
email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
```

## pytest Commands

```bash
# Run all tests
pytest

# Run specific file
pytest apps/accounts/tests/test_views.py

# Run specific test
pytest apps/accounts/tests/test_views.py::TestLoginView::test_login_successful

# Run with coverage
pytest --cov=apps --cov-report=html

# Run in parallel
pytest -n 4

# Show print statements
pytest -s

# Verbose output
pytest -v

# Run only marked tests
pytest -m "not slow"
pytest -m integration
```

## Common Fixtures

| Fixture | Description |
|---------|-------------|
| `client` | Django test client |
| `admin_client` | Logged-in admin client |
| `rf` | RequestFactory |
| `db` | Database access |
| `settings` | Django settings |
| `mailoutbox` | Email testing |
| `django_user_model` | User model |
| `django_assert_num_queries` | Query counting |
| `mocker` | Mock objects (pytest-mock) |

## Testing Best Practices

1. **Use descriptive test names**
   ```python
   def test_user_can_login_with_valid_credentials():  # Good
   def test_login():  # Too vague
   ```

2. **One assertion per test (when practical)**
   ```python
   def test_user_creation_sets_correct_username():
       user = UserFactory(username='testuser')
       assert user.username == 'testuser'
   ```

3. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def authenticated_client(client):
       user = UserFactory()
       client.force_login(user)
       return client
   ```

4. **Group related tests in classes**
   ```python
   @pytest.mark.django_db
   class TestUserAuthentication:
       def test_login(self):
           pass
       def test_logout(self):
           pass
   ```

5. **Use parametrize for similar tests**
   ```python
   @pytest.mark.parametrize("role,expected_perm", [
       ('admin', True),
       ('user', False),
   ])
   def test_permissions(role, expected_perm):
       user = UserFactory(role=role)
       assert user.has_perm('can_edit') == expected_perm
   ```

## Migration Checklist

When converting a test file:

- [ ] Add `@pytest.mark.django_db` to tests that need database
- [ ] Replace `TestCase` with pytest style
- [ ] Convert `setUp()` to fixtures
- [ ] Replace Django assertions with pytest assertions
- [ ] Create factories for model creation
- [ ] Use parametrize for repetitive tests
- [ ] Remove `self` from test methods
- [ ] Update imports
- [ ] Run tests to ensure they pass