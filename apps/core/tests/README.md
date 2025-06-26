# Core Services Test Suite

This directory contains comprehensive tests for all service classes in the core app.

## Test Coverage

### 1. BaseService Tests (`test_base_service.py`)
- **Total Tests**: 40+
- **Coverage Areas**:
  - Service initialization with/without user
  - Organization property handling
  - Queryset filtering by organization
  - Object retrieval with permissions
  - Permission checking (view, edit, delete)
  - Error handling and management
  - Audit logging integration
  - Batch processing functionality
  - Edge cases and error scenarios

### 2. ClientService Tests (`test_client_service.py`)
- **Total Tests**: 35+
- **Coverage Areas**:
  - Annotated queryset with BMI, scores, activity status
  - Comprehensive search and filtering
  - Client statistics calculation
  - Timeline generation
  - Client creation and updates
  - Data export functionality
  - Dashboard metrics
  - Organization data isolation
  - Edge cases

### 3. PaymentService Tests (`test_payment_service.py`)
- **Total Tests**: 40+
- **Coverage Areas**:
  - Fee calculation (VAT, card fees)
  - Session package creation
  - Payment recording and validation
  - Session usage and cancellation
  - Package statistics
  - Financial summaries
  - Expiring package detection
  - Payment due tracking
  - Permission checks
  - Edge cases

### 4. ReportService Tests (`test_report_service.py`)
- **Total Tests**: 30+
- **Coverage Areas**:
  - Report generation with permissions
  - Report reuse logic
  - Bulk report generation
  - Client report history
  - Old report cleanup
  - Report statistics
  - Report regeneration
  - Export filtering
  - Report archiving
  - Edge cases

## Running Tests

### Run All Service Tests
```bash
# From project root
pytest apps/core/tests/

# Or use the test runner
python apps/core/tests/run_service_tests.py
```

### Run Specific Test File
```bash
# Test only BaseService
pytest apps/core/tests/test_base_service.py

# Test only ClientService
pytest apps/core/tests/test_client_service.py
```

### Run with Coverage
```bash
# Generate coverage report
python apps/core/tests/run_service_tests.py --coverage

# Or manually with pytest
pytest apps/core/tests/ --cov=apps.core.services --cov-report=html
```

### Run Specific Test Method
```bash
# Run a specific test class
pytest apps/core/tests/test_client_service.py::TestClientService

# Run a specific test method
pytest apps/core/tests/test_client_service.py::TestClientService::test_search_and_filter_text_search
```

### Verbose Output
```bash
python apps/core/tests/run_service_tests.py -v
```

## Test Organization

### Fixtures (in `conftest.py`)
- `test_organization`: Standard test organization
- `test_trainer_user`: User with trainer profile
- `test_superuser`: Superuser for permission tests
- `test_client`: Standard test client
- `another_organization`: For cross-org tests
- `another_trainer_user`: Trainer from different org

### Test Patterns
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: `test_<method>_<scenario>`
3. **Isolated Tests**: Each test is independent
4. **Comprehensive Coverage**: Success, failure, and edge cases
5. **Mocking**: External dependencies are mocked

### Common Test Scenarios
- Success cases with valid data
- Permission denied scenarios
- Missing/invalid data handling
- Cross-organization isolation
- Edge cases (empty data, None values)
- Exception handling
- Pagination and filtering
- Complex business logic

## Writing New Tests

### Test Template
```python
@pytest.mark.django_db
class TestNewService:
    """Test cases for NewService functionality."""
    
    @pytest.fixture
    def service(self, test_trainer_user):
        """Create service instance."""
        return NewService(user=test_trainer_user)
    
    def test_method_success(self, service):
        """Test successful case."""
        # Arrange
        data = {'key': 'value'}
        
        # Act
        result = service.method(data)
        
        # Assert
        assert result is not None
        assert not service.has_errors
    
    def test_method_permission_denied(self, service, another_trainer_user):
        """Test permission denied."""
        # Test cross-org access
        ...
    
    def test_method_invalid_data(self, service):
        """Test with invalid data."""
        # Test validation
        ...
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Core Service Tests
  run: |
    pytest apps/core/tests/ -v --tb=short
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
pytest apps/core/tests/ --tb=short -q
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the project root
   - Check PYTHONPATH includes project root

2. **Database Access**
   - Tests use `@pytest.mark.django_db` decorator
   - `conftest.py` auto-enables DB access

3. **Factory Errors**
   - Ensure all app factories are properly imported
   - Check factory definitions match models

4. **Permission Tests**
   - Remember superusers bypass most checks
   - Test with regular users for real scenarios

### Debug Tips
```bash
# Run with full traceback
pytest apps/core/tests/ --tb=long

# Run with pdb on failure
pytest apps/core/tests/ --pdb

# Show print statements
pytest apps/core/tests/ -s

# Run only failed tests
pytest apps/core/tests/ --lf
```

## Coverage Goals

Target coverage for service layer: **90%+**

Current coverage can be checked with:
```bash
pytest apps/core/tests/ --cov=apps.core.services --cov-report=term-missing
```

## Contributing

When adding new service methods:
1. Write tests FIRST (TDD approach)
2. Cover success, failure, and edge cases
3. Test permissions and organization filtering
4. Ensure tests are isolated and repeatable
5. Update this README with new test counts