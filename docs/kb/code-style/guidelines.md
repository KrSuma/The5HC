# Code Style Guidelines

## Import Organization

Always organize imports in this specific order:

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

## Function/Method Style

### Docstring Format

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

## Error Handling Patterns

### Service Layer Pattern

```python
try:
    # Database operation
    with get_db_connection() as conn:
        result = execute_query(query, params)
        return True, result
except Exception as e:
    error_logger.log_error(e, context=context)
    return False, f"오류가 발생했습니다: {str(e)}"
```

### UI Layer Pattern

```python
try:
    success, result = ServiceClass.method()
    if success:
        st.success("작업이 완료되었습니다.")
    else:
        st.error(result)
except Exception as e:
    st.error(f"예상치 못한 오류가 발생했습니다: {str(e)}")
```

## Streamlit UI Conventions

### Page Setup

```python
st.set_page_config(
    page_title="Page Title",
    page_icon="🏋️",
    layout="wide"
)
```

### Layout with Columns

```python
# Use columns for layout
col1, col2 = st.columns([2, 1])
with col1:
    st.header("섹션 제목")
```

### Form Submission Pattern

```python
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

### Integration Testing Guidelines

- Test database connections for both SQLite and PostgreSQL
- Verify table creation and migration scripts
- Test authentication flows end-to-end
- Validate session management across pages

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

## Error Handling Best Practices

1. Use service layer for business logic errors
2. Return tuple (success: bool, result/error_message: Any)
3. Log errors with context using error_logger
4. Show user-friendly Korean error messages
5. Preserve form data on errors when possible

## Korean Language Considerations

- All UI text in Korean
- NanumGothic font for PDF generation
- UTF-8 encoding throughout
- Currency formatting for Korean Won (₩)

## Code Review Points

1. Database compatibility (SQLite vs PostgreSQL)
2. Korean language UI consistency
3. Error handling and user feedback
4. Session management and security
5. Performance optimization for database queries
6. Change logs are created for significant modifications