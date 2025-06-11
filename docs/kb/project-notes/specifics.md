# Project-Specific Notes

## Database Architecture

- **Dual Database Support**: Automatic switching between SQLite (dev) and PostgreSQL (prod)
- **Migration System**: Automatic table creation via `migrate_database.py`
- **Connection Management**: Uses context managers for proper cleanup
- **Query Adaptation**: `adapt_query_for_db()` handles SQL dialect differences

## Authentication & Security

- BCrypt password hashing with 12 rounds
- Session management with 24-hour timeout
- Rate limiting for login attempts (5 attempts, 30-minute lockout)
- Activity tracking for audit trails
- CSRF protection disabled for Streamlit compatibility

## Service Layer Architecture

```
UI Layer (Streamlit Pages)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (SQLite/PostgreSQL)
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

## Key Files Reference

- `main.py` - Application entry point
- `src/services/service_layer.py` - Core business logic
- `src/data/database.py` - Database operations
- `src/data/database_config.py` - Database configuration
- `config/settings.py` - Application settings
- `src/utils/fee_calculator.py` - VAT/fee calculations
- `src/services/session_service.py` - Session management

## Dependencies (requirements.txt)

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

## Additional Resources

### Project Structure

- See `docs/PROJECT_STRUCTURE.md` for detailed file organization
- See `deployment/DEPLOYMENT_GUIDE.md` for deployment guide
- See `docs/HEROKU_DATABASE_SETUP.md` for database setup
- See `docs/NOTION_INTEGRATION_GUIDE.md` for external integrations