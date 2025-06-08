# The5HC Fitness Assessment System - Claude Code Knowledge Base

## Project Overview
The5HC is a comprehensive fitness assessment system built with Streamlit, designed for Korean fitness trainers to manage clients, conduct assessments, and track sessions. The application supports both SQLite (development) and PostgreSQL (production) databases with automatic environment detection.

## Build Commands

### Development
```bash
# Run locally with SQLite
python -m streamlit run main.py --server.port 8501 --server.address localhost

# Alternative: Use the provided shell script (macOS specific)
./run_app.sh
```

### Testing
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_deployment.py
pytest tests/test_session_management.py

# Test database deployment readiness
python tests/test_deployment.py
```

### Database Operations
```bash
# Run database migration (creates all tables)
python src/data/migrate_database.py

# Run PostgreSQL compatibility fixes
python src/data/fix_postgresql_compatibility.py

# Export data to JSON
python scripts/export_to_json.py

# Import data from JSON
python scripts/import_from_json.py
```

### Production Deployment (Heroku)
```bash
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# Third-party imports
import streamlit as st
import pandas as pd
import numpy as np
from pydantic import BaseModel

# Local application imports
from src.data.database import get_db_connection
from src.services.service_layer import AuthService
from src.utils.app_logging import app_logger, error_logger
from config.settings import config
```

### Function/Method Style
```python
def function_name(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief description of function purpose.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter description
        
    Returns:
        Description of return value
    """
    try:
        # Implementation
        result = process_data(param1)
        return {"status": "success", "data": result}
    except Exception as e:
        error_logger.log_error(e, context={"param1": param1})
        raise
```

### Error Handling Pattern
```python
# Service layer pattern
try:
    # Database operation
    with get_db_connection() as conn:
        result = execute_query(query, params)
        return True, result
except Exception as e:
    error_logger.log_error(e, context=context)
    return False, f"오류가 발생했습니다: {str(e)}"

# UI layer pattern
try:
    success, result = ServiceClass.method()
    if success:
        st.success("작업이 완료되었습니다.")
    else:
        st.error(result)
except Exception as e:
    st.error(f"예상치 못한 오류가 발생했습니다: {str(e)}")
```

### Streamlit UI Conventions
```python
# Page setup
st.set_page_config(
    page_title="Page Title",
    page_icon="🏋️",
    layout="wide"
)

# Use columns for layout
col1, col2 = st.columns([2, 1])
with col1:
    st.header("섹션 제목")
    
# Form submission pattern
with st.form("form_key"):
    input_value = st.text_input("라벨")
    submitted = st.form_submit_button("제출")
    
    if submitted:
        if not input_value:
            st.error("필수 입력값입니다.")
        else:
            # Process form
            pass
```

## Testing Practices

### Unit Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """Test suite for feature functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        
    def test_success_case(self):
        """Test successful operation"""
        # Arrange
        expected = {"status": "success"}
        
        # Act
        result = function_under_test()
        
        # Assert
        assert result == expected
        
    def test_error_case(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            function_under_test(invalid_param)
```

### Integration Testing
- Test database connections for both SQLite and PostgreSQL
- Verify table creation and migration scripts
- Test authentication flows end-to-end
- Validate session management across pages

## Workflow Conventions

### Git Commit Messages
Based on recent commits, follow this pattern:
```
# Feature additions
Add 세션 관리 button in 회원 관리 page for quick access

# Bug fixes
Fix datetime object subscriptable error in session package display
Fix session service PostgreSQL compatibility issues

# Refactoring
Optimize database initialization to run only once

# Configuration changes
Fix PostgreSQL authentication issues in Heroku deployment
```

### Branch Strategy
- Main branch: `main`
- Feature branches: Not specified in codebase, likely feature/branch-name
- Direct commits to main appear common for fixes

### Code Review Points
1. Database compatibility (SQLite vs PostgreSQL)
2. Korean language UI consistency
3. Error handling and user feedback
4. Session management and security
5. Performance optimization for database queries

## Environment Configuration

### Required Environment Variables
```bash
# Production (Heroku)
DATABASE_URL=postgres://...  # Automatically set by Heroku
SECRET_KEY=your-secret-key
DEBUG=False
LOG_LEVEL=INFO

# Development
# No environment variables required - uses SQLite by default
```

### Configuration Files
- `config/settings.py` - Main configuration with defaults
- `config/config_production.py` - Production-specific settings
- `src/data/database_config.py` - Database connection management
- `.streamlit/config.toml` - Streamlit UI configuration

### Dependencies (requirements.txt)
```
streamlit==1.41.0
pandas==2.2.3
numpy==2.2.0
matplotlib==3.10.0
weasyprint==63.1
seaborn==0.13.2
pillow==11.1.0
psycopg2-binary==2.9.10
bcrypt==4.2.1
pydantic==2.10.4
pytest==8.3.4
```

## Project-Specific Notes

### Database Architecture
- **Dual Database Support**: Automatic switching between SQLite (dev) and PostgreSQL (prod)
- **Migration System**: Automatic table creation via `migrate_database.py`
- **Connection Management**: Uses context managers for proper cleanup
- **Query Adaptation**: `adapt_query_for_db()` handles SQL dialect differences

### Authentication & Security
- BCrypt password hashing with 12 rounds
- Session management with 24-hour timeout
- Rate limiting for login attempts (5 attempts, 30-minute lockout)
- Activity tracking for audit trails
- CSRF protection disabled for Streamlit compatibility

### Service Layer Architecture
```
UI Layer (Streamlit Pages)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (SQLite/PostgreSQL)
```

### Korean Language Considerations
- All UI text in Korean
- NanumGothic font for PDF generation
- UTF-8 encoding throughout
- Currency formatting for Korean Won (₩)

## Common Operations

### Adding a New Feature
1. Create service method in appropriate service class
2. Add repository method if database access needed
3. Create/update UI page in `src/ui/pages/`
4. Add navigation in `main.py`
5. Update tests
6. Handle both SQLite and PostgreSQL compatibility

### Database Schema Changes
1. Update migration script in `src/data/migrate_database.py`
2. Add compatibility fixes if needed
3. Test on both SQLite and PostgreSQL
4. Update model classes if applicable
5. Run migration locally before deployment

### Adding a New Page
```python
# 1. Create page function in src/ui/pages/
def new_page():
    st.header("페이지 제목")
    # Page implementation

# 2. Import in main.py
from src.ui.pages.new_module import new_page

# 3. Add navigation button
if st.button("새 페이지", use_container_width=True):
    st.session_state.current_page = "new_page"

# 4. Add page routing
elif st.session_state.current_page == "new_page":
    new_page()
```

### Error Handling Best Practices
1. Use service layer for business logic errors
2. Return tuple (success: bool, result/error_message: Any)
3. Log errors with context using error_logger
4. Show user-friendly Korean error messages
5. Preserve form data on errors when possible

## Troubleshooting

### Common Issues

#### Database Connection Errors
```python
# Check environment
IS_PRODUCTION = bool(os.environ.get('DATABASE_URL'))

# Verify connection
with get_db_connection() as conn:
    print("Connection successful")
```

#### PostgreSQL Compatibility
- Use `%s` placeholders instead of `?` for PostgreSQL
- Use `RETURNING` clause for PostgreSQL inserts
- Handle `RealDictCursor` for PostgreSQL result sets
- Check column existence before access

#### Session Management Issues
- Sessions stored in database, not Streamlit session state
- Check `trainer_sessions` table for active sessions
- Verify session validation in `session_manager`
- Clear browser cookies if persistent issues

#### PDF Generation Errors
- Ensure WeasyPrint dependencies installed
- Check font paths for NanumGothic
- Verify image paths are absolute
- Test with simple HTML first

#### Heroku Deployment Issues
1. Check `heroku logs --tail` for errors
2. Verify DATABASE_URL is set
3. Ensure migration ran via release command
4. Check Procfile syntax
5. Verify all dependencies in requirements.txt

### Debug Mode
```python
# Enable debug logging
os.environ['DEBUG'] = 'True'
os.environ['LOG_LEVEL'] = 'DEBUG'

# Add debug prints in service layer
app_logger.debug(f"Processing: {data}")
```

## Recent Feature Implementations

### VAT and Fee Calculation (Fee Calculator)
- Location: `src/utils/fee_calculator.py`
- Fixed rates: 10% VAT, 3.5% card processing fee
- Inclusive calculation method (fees included in gross amount)
- Audit logging for all calculations
- Currency formatting for Korean Won

### Enhanced Session Management
- Session packages with expiry dates
- Payment tracking with fee calculations
- Attendance tracking
- Package usage analytics
- PostgreSQL compatible queries

### Database Migration Patterns
1. Dual query support (SQLite/PostgreSQL)
2. Automatic table creation
3. Column addition migrations
4. Data type compatibility handling
5. Transaction management

## Performance Considerations

### Database Optimization
- Connection pooling for PostgreSQL
- Indexed columns for common queries
- Batch operations where possible
- Caching for frequently accessed data
- Query optimization for large datasets

### UI Performance
- Lazy loading for large lists
- Pagination for data tables
- Efficient chart rendering
- Minimal state updates
- Strategic use of `st.cache_data`

### Production Monitoring
- Structured logging with context
- Error tracking and alerting
- Performance metrics logging
- User activity tracking
- Database query performance logs

## Security Considerations

1. **Authentication**: BCrypt hashing, rate limiting, account lockout
2. **Authorization**: Trainer-specific data access only
3. **Input Validation**: Sanitization, length limits, type checking
4. **SQL Injection**: Parameterized queries, no string concatenation
5. **XSS Prevention**: HTML escaping in reports
6. **CSRF**: Disabled for Streamlit (uses WebSocket)
7. **Secrets Management**: Environment variables for sensitive data
8. **Audit Trail**: Activity logging for compliance

## Maintenance Tasks

### Regular Tasks
1. Monitor error logs for patterns
2. Check database performance metrics
3. Review and clean old session data
4. Update dependencies for security patches
5. Backup database regularly

### Deployment Checklist
1. Run tests locally
2. Check PostgreSQL compatibility
3. Update migration scripts if needed
4. Test on staging environment
5. Deploy during low-traffic hours
6. Monitor logs post-deployment
7. Verify all features working

## Additional Resources

### Project Structure
- See `docs/PROJECT_STRUCTURE.md` for detailed file organization
- See `deployment/DEPLOYMENT.md` for deployment guide
- See `docs/HEROKU_DATABASE_SETUP.md` for database setup
- See `docs/NOTION_INTEGRATION_GUIDE.md` for external integrations

### Key Files Reference
- `main.py` - Application entry point
- `src/services/service_layer.py` - Core business logic
- `src/data/database.py` - Database operations
- `src/data/database_config.py` - Database configuration
- `config/settings.py` - Application settings
- `src/utils/fee_calculator.py` - VAT/fee calculations
- `src/services/session_service.py` - Session management