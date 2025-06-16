# The5HC - Comprehensive Code Overview and Summary

**Generated**: 2025-06-16

## Project Overview

The5HC is a comprehensive fitness assessment system built with Django 5.0.1, designed for Korean fitness trainers to manage clients, conduct assessments, and track sessions. The application features a modern web stack with HTMX and Alpine.js for dynamic UI, a complete RESTful API, and supports both SQLite (development) and PostgreSQL (production) databases.

**Production URL**: https://the5hc.herokuapp.com/

## Technology Stack

### Backend
- **Framework**: Django 5.0.1
- **API**: Django REST Framework with JWT authentication
- **Database**: PostgreSQL (production) / SQLite (development)
- **PDF Generation**: WeasyPrint
- **Testing**: pytest with Factory Boy

### Frontend
- **UI Framework**: HTMX 1.9.10 + Alpine.js 3.x
- **CSS**: Tailwind CSS
- **Charts**: Chart.js
- **Language**: Korean (direct text, not Django i18n)

### Deployment
- **Platform**: Heroku
- **Server**: Gunicorn
- **Static Files**: WhiteNoise
- **Python Version**: 3.12

## Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  HTMX + Alpine.js + Tailwind CSS + Chart.js                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Django Views                             │
│  Class-based views with HTMX support                        │
│  Permission decorators for role-based access                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  Models with business methods                                │
│  Form validation and processing                              │
│  Service classes for complex operations                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│  Django ORM with optimized queries                          │
│  Database migrations                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Database                               │
│  PostgreSQL (production) / SQLite (development)             │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema and Relationships

### Core Models and Relationships

```
Organization (1) ──────┬──── (*) Trainer
                       │
                       └──── (*) TrainerInvitation

User (1) ────────────────── (1) Trainer

Trainer (1) ──────┬──── (*) Client
                  │
                  ├──── (*) Assessment
                  │
                  ├──── (*) SessionPackage
                  │
                  ├──── (*) Session
                  │
                  ├──── (*) Payment
                  │
                  ├──── (*) FeeAuditLog
                  │
                  └──── (*) Notification

Client (1) ───────┬──── (*) Assessment
                  │
                  ├──── (*) SessionPackage
                  │
                  └──── (*) Session

SessionPackage (1) ──── (*) Session
                  │
                  └──── (*) Payment

AuditLog ─────────────── Generic FK to any model
```

### Detailed Model Structure

#### 1. **User Model** (Django Custom User)
```python
- email (unique)
- username (unique) 
- is_active
- is_staff
- is_superuser
- date_joined
```

#### 2. **Organization Model**
```python
- name
- description
- max_trainers (default: 50)
- business_hours (JSON)
- timezone
- contact_email
- contact_phone
- address
- created_at
- updated_at
```

#### 3. **Trainer Model**
```python
- user (OneToOne → User)
- organization (FK → Organization)
- role (choices: owner, senior, trainer, assistant)
- phone
- bio
- certifications
- specialties (JSON)
- is_active
- created_at
- updated_at
- notification_preferences (JSON)
- theme_preference
- language_preference
- session_price
- available_hours (JSON)
- profile_photo
```

#### 4. **Client Model**
```python
- trainer (FK → Trainer)
- name
- gender (choices: male, female)
- birth_date
- height (cm)
- weight (kg)
- phone
- email
- memo
- is_active
- created_at
- updated_at
```

#### 5. **Assessment Model**
```python
- client (FK → Client)
- trainer (FK → Trainer)
- push_up_reps
- balance_left_seconds
- balance_right_seconds
- farmer_carry_left_seconds
- farmer_carry_right_seconds
- farmer_carry_time
- toe_touch_distance
- harvard_step_test_hr1
- harvard_step_test_hr2
- harvard_step_test_hr3
- push_up_score
- balance_score
- strength_score
- mobility_score
- cardio_score
- overall_score
- created_at
- updated_at
```

#### 6. **SessionPackage Model**
```python
- client (FK → Client)
- trainer (FK → Trainer)
- total_sessions
- used_sessions
- start_date
- end_date
- gross_amount
- vat_amount
- card_fee_amount
- net_amount
- vat_rate (default: 0.10)
- card_fee_rate (default: 0.035)
- fee_calculation_method
- is_active
- created_at
- updated_at
```

#### 7. **Session Model**
```python
- client (FK → Client)
- trainer (FK → Trainer)
- package (FK → SessionPackage, nullable)
- date
- status (choices: scheduled, completed, cancelled)
- memo
- created_at
- updated_at
```

#### 8. **Payment Model**
```python
- package (FK → SessionPackage)
- trainer (FK → Trainer)
- payment_date
- gross_amount
- vat_amount
- card_fee_amount
- net_amount
- vat_rate
- card_fee_rate
- payment_method
- created_at
```

#### 9. **FeeAuditLog Model**
```python
- trainer (FK → Trainer)
- session_package (FK → SessionPackage, nullable)
- payment (FK → Payment, nullable)
- calculation_type
- gross_amount
- vat_amount
- card_fee_amount
- net_amount
- vat_rate
- card_fee_rate
- calculation_method
- calculation_details (JSON)
- created_at
```

#### 10. **TrainerInvitation Model**
```python
- organization (FK → Organization)
- inviter (FK → Trainer)
- email
- role
- status (choices: pending, accepted, declined, expired)
- token (unique)
- expires_at
- created_at
- accepted_at
```

#### 11. **Notification Model**
```python
- trainer (FK → Trainer)
- type (choices: info, success, warning, error)
- title
- message
- data (JSON)
- is_read
- created_at
- updated_at
```

#### 12. **AuditLog Model**
```python
- user (FK → User)
- action
- model_name
- object_id
- object_repr
- changes (JSON)
- ip_address
- user_agent
- extra_data (JSON)
- created_at
```

## Key Features and Implementation

### 1. Multi-Tenant Architecture
- Organization-based data isolation
- Role-based permissions (owner > senior > trainer > assistant)
- Middleware for automatic trainer context
- Decorators for view-level access control

### 2. Authentication & Security
- JWT authentication for API (60-minute tokens)
- Session-based authentication for web
- Rate limiting on login attempts
- BCrypt password hashing
- CSRF protection for forms

### 3. Client Management
- Full CRUD operations
- Advanced search and filtering
- BMI calculation
- CSV export functionality
- Activity tracking

### 4. Fitness Assessment System
- 7 standardized fitness tests
- Automatic score calculation (0-100 scale)
- Category scores (strength, mobility, balance, cardio)
- Multi-step form with Alpine.js
- Visual score representation

### 5. Session Management
- Package-based credit system
- VAT (10%) and card fee (3.5%) calculations
- Session scheduling and tracking
- Payment recording
- Calendar visualization

### 6. Financial Management
- Automatic fee calculation
- Fee audit logging
- Payment tracking
- Net/gross amount handling
- Financial transparency

### 7. PDF Report Generation
- WeasyPrint integration
- Korean language support
- Assessment reports with scores
- Professional formatting

### 8. Analytics Dashboard
- Real-time metrics
- Revenue tracking
- Session statistics
- Client growth metrics
- Chart.js visualizations

### 9. RESTful API
- Complete CRUD operations
- JWT authentication
- OpenAPI/Swagger documentation
- Custom business logic endpoints
- Pagination and filtering

### 10. Notification System
- In-app notifications
- Real-time badge updates
- Multiple notification types
- Mark as read functionality

## Code Organization

### Django Apps Structure

1. **accounts** - User authentication and management
2. **analytics** - Dashboard and analytics views
3. **api** - RESTful API with Django REST Framework
4. **assessments** - Fitness assessment management
5. **clients** - Client CRUD operations
6. **reports** - PDF report generation
7. **sessions** - Session and payment tracking
8. **trainers** - Multi-trainer support and permissions

### Key Design Patterns

1. **HTMX Navigation Pattern**
   - Separate content templates for partial updates
   - Detection of HX-Request headers
   - Prevents duplicate headers/footers

2. **Permission System**
   - Role-based decorators
   - Organization-level data filtering
   - Middleware for trainer context

3. **Form Handling**
   - Django forms with Alpine.js integration
   - Real-time validation
   - Multi-step workflows

4. **API Design**
   - ViewSets for standard CRUD
   - Custom actions for business logic
   - Consistent serializer patterns

## Testing Strategy

- **Framework**: pytest with pytest-django
- **Fixtures**: Factory Boy for test data
- **Coverage**: 72%+ test coverage
- **Test Types**: Unit, integration, API tests
- **Test Organization**: Per-app test modules

## Deployment Configuration

### Production Settings
- PostgreSQL database
- Gunicorn WSGI server
- WhiteNoise for static files
- Heroku buildpacks for dependencies
- Environment-based configuration

### Key Environment Variables
- `DATABASE_URL` - PostgreSQL connection
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode flag
- `ALLOWED_HOSTS` - Production domains

## Recent Development Focus

### Completed Features (2025-06-16)
- Fixed trainer instance assignment errors
- Fixed assessment form rendering
- Fixed score visualization (0-100% scale)
- Improved UI/UX with Korean labels
- Created comprehensive documentation

### Known Issues
- Integration tests need completion
- HTMX navigation in navbar temporarily disabled
- Some features pending implementation

## Performance Considerations

1. **Database Optimization**
   - Indexed foreign keys
   - Optimized queries with select_related
   - Pagination for large datasets

2. **Frontend Performance**
   - HTMX for partial page updates
   - Alpine.js for reactive UI
   - Lazy loading for charts

3. **Caching Strategy**
   - Static file caching with WhiteNoise
   - Database query optimization
   - Session-based caching

## Security Measures

1. **Authentication**
   - JWT tokens for API
   - Session-based for web
   - Rate limiting

2. **Authorization**
   - Role-based permissions
   - Organization data isolation
   - View-level decorators

3. **Data Protection**
   - HTTPS in production
   - CSRF protection
   - SQL injection prevention
   - XSS protection

## Maintenance and Monitoring

1. **Logging**
   - Structured logging
   - Error tracking
   - Audit trails

2. **Monitoring**
   - Heroku metrics
   - Application logs
   - Database performance

3. **Backup Strategy**
   - Database backups
   - Code repository
   - Documentation

## Future Roadmap

1. **Short-term**
   - Complete integration tests
   - Fix HTMX navigation issues
   - Performance optimization

2. **Medium-term**
   - Mobile app API
   - Advanced analytics
   - Email notifications

3. **Long-term**
   - Multi-language support
   - Advanced reporting
   - AI-powered recommendations

## Conclusion

The5HC represents a modern, well-architected Django application with a focus on user experience, security, and maintainability. The codebase follows Django best practices while incorporating modern frontend technologies for a responsive, dynamic user interface. The multi-tenant architecture with role-based permissions provides a solid foundation for scaling to support multiple fitness organizations.