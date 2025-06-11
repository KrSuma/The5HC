# API Test Guide for The5HC Django Project

## Overview

This guide provides comprehensive documentation for testing the RESTful API implemented in Phase 5 of The5HC Django migration project.

## Test Coverage

### 1. Authentication Tests (`test_auth.py`)
- ✅ Login with username
- ✅ Login with email
- ✅ Invalid credentials handling
- ✅ Token refresh functionality
- ✅ Protected endpoint access
- ✅ Missing field validation

### 2. Client API Tests (`test_clients.py`)
- ✅ List clients (trainer-specific)
- ✅ Retrieve single client
- ✅ Create new client
- ✅ Update client (full and partial)
- ✅ Delete client
- ✅ Search functionality
- ✅ Ordering/sorting
- ✅ Client assessments endpoint
- ✅ Client packages endpoint
- ✅ Client statistics endpoint

### 3. Assessment API Tests (`test_assessments.py`)
- ✅ List assessments
- ✅ Retrieve single assessment
- ✅ Create assessment
- ✅ Update assessment
- ✅ Delete assessment
- ✅ Search by client name
- ✅ Order by date/score
- ✅ Assessment comparison endpoint
- ✅ Pagination

### 4. Session-Related API Tests (`test_sessions.py`)
#### SessionPackage Tests
- ✅ List packages
- ✅ Filter by active status
- ✅ Create package
- ✅ Package sessions endpoint
- ✅ Package payments endpoint
- ✅ Complete session endpoint

#### Session Tests
- ✅ List sessions
- ✅ Filter by date range
- ✅ Filter by attendance status
- ✅ Calendar view endpoint

#### Payment Tests
- ✅ List payments
- ✅ Filter by payment method
- ✅ Create payment
- ✅ Payment summary endpoint

### 5. User API Tests (`test_users.py`)
- ✅ List users (current user only)
- ✅ Retrieve user profile
- ✅ Me endpoint
- ✅ Change password
- ✅ Dashboard statistics
- ✅ Read-only enforcement

### 6. Permission Tests (`test_permissions.py`)
- ✅ Trainer data isolation
- ✅ Cross-trainer access prevention
- ✅ Authentication requirements
- ✅ Token validation
- ✅ Data modification restrictions

### 7. Documentation Tests (`test_documentation.py`)
- ✅ OpenAPI schema endpoint
- ✅ Swagger UI accessibility
- ✅ ReDoc accessibility
- ✅ Error response formats
- ✅ Pagination format validation

## Running the Tests

### Quick Start
```bash
cd django_migration
source venv/bin/activate
pytest apps/api/ -v
```

### Using the Test Runner Script
```bash
cd django_migration
python run_api_tests.py
```

### Individual Test Modules
```bash
# Authentication tests
pytest apps/api/test_auth.py -v

# Client API tests
pytest apps/api/test_clients.py -v

# Assessment API tests
pytest apps/api/test_assessments.py -v

# Session-related tests
pytest apps/api/test_sessions.py -v

# User API tests
pytest apps/api/test_users.py -v

# Permission tests
pytest apps/api/test_permissions.py -v

# Documentation tests
pytest apps/api/test_documentation.py -v
```

### With Coverage Report
```bash
pytest apps/api/ --cov=apps.api --cov-report=html
```

## Test Structure

### Fixtures and Setup
Each test class uses pytest fixtures for:
- APIClient setup
- User authentication
- Test data creation using Factory Boy
- JWT token generation

### Test Organization
```python
@pytest.mark.django_db
class TestClientAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        # ... setup code
    
    def test_list_clients_success(self):
        """Test listing clients"""
        # ... test implementation
```

### Common Test Patterns

#### 1. Authentication Setup
```python
refresh = RefreshToken.for_user(self.user)
self.token = str(refresh.access_token)
self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
```

#### 2. Permission Testing
```python
# Test accessing another trainer's data
response = self.client.get(f'/api/v1/clients/{other_trainer_client.id}/')
assert response.status_code == status.HTTP_404_NOT_FOUND
```

#### 3. Data Validation
```python
response = self.client.post('/api/v1/clients/', invalid_data)
assert response.status_code == status.HTTP_400_BAD_REQUEST
assert 'field_name' in response.data
```

## API Endpoints Reference

### Authentication
- `POST /api/v1/auth/login/` - Login (email or username)
- `POST /api/v1/auth/refresh/` - Refresh JWT token

### Resources
- `/api/v1/clients/` - Client management
- `/api/v1/assessments/` - Fitness assessments
- `/api/v1/packages/` - Session packages
- `/api/v1/sessions/` - Training sessions
- `/api/v1/payments/` - Payment records
- `/api/v1/users/` - User profiles

### Custom Actions
- `GET /api/v1/clients/{id}/assessments/`
- `GET /api/v1/clients/{id}/packages/`
- `GET /api/v1/clients/{id}/statistics/`
- `GET /api/v1/assessments/{id}/comparison/`
- `POST /api/v1/packages/{id}/complete_session/`
- `GET /api/v1/sessions/calendar/`
- `GET /api/v1/payments/summary/`
- `GET /api/v1/users/me/`
- `POST /api/v1/users/change_password/`
- `GET /api/v1/users/dashboard_stats/`

## Test Data Management

### Using Factory Boy
All test data is created using Factory Boy factories:
```python
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory

# Create test data
client = ClientFactory(trainer=self.user)
assessment = AssessmentFactory(client=client)
```

### Factory Examples
- `UserFactory` - Creates trainer users
- `ClientFactory` - Creates client records
- `AssessmentFactory` - Creates fitness assessments
- `SessionPackageFactory` - Creates session packages
- `SessionFactory` - Creates training sessions
- `PaymentFactory` - Creates payment records

## Debugging Failed Tests

### Verbose Output
```bash
pytest apps/api/test_clients.py::TestClientAPI::test_create_client_success -vv
```

### Print Response Data
```python
print(f"Status: {response.status_code}")
print(f"Data: {response.data}")
```

### Check Database State
```python
from apps.clients.models import Client
print(f"Client count: {Client.objects.count()}")
```

## Expected Test Results

When all tests pass, you should see:
```
==================== test session starts ====================
collected 70 tests

apps/api/test_auth.py::TestAuthenticationAPI::test_login_with_username_success PASSED
apps/api/test_auth.py::TestAuthenticationAPI::test_login_with_email_success PASSED
...
==================== 70 passed in 12.34s ====================
```

## Common Issues and Solutions

### 1. Import Errors
Ensure you're in the Django project directory and virtual environment is activated.

### 2. Database Access Errors
Make sure tests use `@pytest.mark.django_db` decorator.

### 3. Authentication Failures
Check that JWT tokens are properly generated and included in headers.

### 4. Factory Errors
Ensure all required factories are properly defined with necessary fields.

## Next Steps

1. **Run all API tests** to ensure everything works
2. **Add more edge case tests** as needed
3. **Monitor test coverage** and aim for >90%
4. **Update tests** when API changes
5. **Integrate with CI/CD** pipeline

## Maintenance

- Keep tests updated with API changes
- Add tests for new endpoints
- Refactor tests when patterns emerge
- Document any special test requirements