# Troubleshooting Guide

## Common Issues and Solutions

### Database Connection Errors

#### Checking Environment

```python
# Check environment
IS_PRODUCTION = bool(os.environ.get('DATABASE_URL'))

# Verify connection
with get_db_connection() as conn:
    print("Connection successful")
```

### PostgreSQL Compatibility

Common issues and fixes:

- Use `%s` placeholders instead of `?` for PostgreSQL
- Use `RETURNING` clause for PostgreSQL inserts
- Handle `RealDictCursor` for PostgreSQL result sets
- Check column existence before access

### Session Management Issues

Common problems:

- Sessions stored in database, not Streamlit session state
- Check `trainer_sessions` table for active sessions
- Verify session validation in `session_manager`
- Clear browser cookies if persistent issues

### PDF Generation Errors

Troubleshooting steps:

1. Ensure WeasyPrint dependencies installed
2. Check font paths for NanumGothic
3. Verify image paths are absolute
4. Test with simple HTML first

### Heroku Deployment Issues

Debugging checklist:

1. Check `heroku logs --tail` for errors
2. Verify DATABASE_URL is set
3. Ensure migration ran via release command
4. Check Procfile syntax
5. Verify all dependencies in requirements.txt

## Debug Mode

Enable detailed logging:

```python
# Enable debug logging
os.environ['DEBUG'] = 'True'
os.environ['LOG_LEVEL'] = 'DEBUG'

# Add debug prints in service layer
app_logger.debug(f"Processing: {data}")
```

## Performance Debugging

Use the performance debugging script:

```bash
python debug_performance.py
```

## Database Issues

### SQLite to PostgreSQL Migration

Common conversion issues:

1. **Date/Time Handling**: PostgreSQL is stricter with datetime formats
2. **Boolean Fields**: SQLite uses 0/1, PostgreSQL uses true/false
3. **Auto-increment**: SQLite uses AUTOINCREMENT, PostgreSQL uses SERIAL
4. **String Concatenation**: SQLite uses ||, PostgreSQL uses CONCAT

### Query Adaptation

The system includes `adapt_query_for_db()` function to handle SQL dialect differences automatically.

## Authentication Issues

### Login Problems

1. Check rate limiting (5 attempts, 30-minute lockout)
2. Verify password hashing (BCrypt with 12 rounds)
3. Check session timeout (24 hours)
4. Clear browser cookies and cache

### Session Persistence

- Sessions are stored in `trainer_sessions` table
- Check for expired sessions
- Verify session validation middleware

## UI/Frontend Issues

### Streamlit Specific

1. **State Management**: Use `st.session_state` correctly
2. **Form Rerun**: Handle form submissions properly
3. **Widget Keys**: Ensure unique keys for widgets
4. **Container Width**: Use `use_container_width=True` for responsive design

### HTMX/Alpine.js (Django)

1. **HTMX Headers**: Check for `HX-Request` header
2. **Alpine Data**: Verify x-data initialization
3. **CSRF Tokens**: Include in HTMX requests
4. **Loading States**: Check hx-indicator setup

## Testing Issues

### pytest Failures

Common causes:

1. **Database Access**: Missing `@pytest.mark.django_db` decorator
2. **Fixtures**: Incorrect fixture scope or dependencies
3. **Factory Issues**: Missing or incorrect factory definitions
4. **Async Tests**: Missing `@pytest.mark.asyncio` decorator

### Test Database

```bash
# Reset test database
pytest --create-db

# Reuse existing test database
pytest --reuse-db
```

## API Issues (Django)

### JWT Authentication

1. Check token expiration (60 minutes)
2. Verify token format in Authorization header
3. Check CORS settings for frontend apps
4. Verify user permissions

### Serializer Errors

1. Check field mappings match model
2. Verify required vs optional fields
3. Check nested serializer relationships
4. Validate custom validation methods

## Dependency Issues

### Python Dependencies

```bash
# Check for conflicts
pip check

# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### System Dependencies (macOS)

For PDF generation:

```bash
# Install WeasyPrint dependencies
brew install cairo pango gdk-pixbuf libffi glib

# Set library path if needed
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

## Logging and Monitoring

### Log Locations

- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Django logs: `django_migration/logs/django.log`
- Heroku logs: `heroku logs --tail`

### Log Levels

```python
# Set appropriate log level
os.environ['LOG_LEVEL'] = 'DEBUG'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Emergency Procedures

### Database Corruption

1. Stop the application
2. Backup current database
3. Restore from latest backup
4. Run integrity checks
5. Apply missing migrations

### Production Hotfix

1. Create hotfix branch
2. Apply minimal fix
3. Test thoroughly
4. Deploy with monitoring
5. Create proper fix later

### Rollback Procedure

```bash
# Heroku rollback
heroku releases
heroku rollback v[previous-version]
```