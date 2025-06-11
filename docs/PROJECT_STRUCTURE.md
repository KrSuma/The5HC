# Project Structure

## Overview
The 5HC Fitness Assessment System is a Django-based web application with a clean, modular structure designed for easy maintenance and deployment.

```
The5HC/
├── README.md                 # Main project documentation
├── CLAUDE.md                 # Knowledge base for Claude Code
├── Procfile                  # Heroku deployment configuration
├── runtime.txt              # Python version (3.10.14)
├── requirements.txt         # Points to Django requirements
├── .gitignore              # Git ignore rules
│
├── django_migration/        # Main Django project
│   ├── manage.py           # Django management command
│   ├── requirements.txt    # Python dependencies
│   ├── pytest.ini          # pytest configuration
│   ├── conftest.py         # pytest fixtures
│   ├── the5hc_dev         # SQLite development database
│   │
│   ├── apps/              # Django applications
│   │   ├── accounts/      # User authentication & management
│   │   ├── analytics/     # Dashboard and analytics
│   │   ├── api/           # RESTful API (DRF)
│   │   ├── assessments/   # Fitness assessment system
│   │   ├── clients/       # Client management
│   │   ├── reports/       # PDF report generation
│   │   ├── sessions/      # Session & payment tracking
│   │   └── trainers/      # Trainer management (placeholder)
│   │
│   ├── the5hc/           # Django project settings
│   │   ├── settings/     # Modular settings
│   │   │   ├── base.py   # Base settings
│   │   │   ├── development.py # Dev settings
│   │   │   ├── production.py  # Prod settings
│   │   │   └── test.py   # Test settings
│   │   ├── urls.py       # Main URL configuration
│   │   ├── wsgi.py       # WSGI configuration
│   │   └── asgi.py       # ASGI configuration
│   │
│   ├── templates/        # Django templates
│   │   ├── base.html     # Base template with HTMX/Alpine
│   │   ├── accounts/     # Authentication templates
│   │   ├── assessments/  # Assessment templates
│   │   ├── clients/      # Client management templates
│   │   ├── dashboard/    # Dashboard templates
│   │   ├── reports/      # Report templates
│   │   ├── sessions/     # Session templates
│   │   └── components/   # Reusable components
│   │
│   ├── static/          # Static assets
│   │   ├── css/         # Stylesheets
│   │   ├── js/          # JavaScript files
│   │   └── fonts/       # Korean fonts (NanumGothic)
│   │
│   ├── locale/          # Internationalization
│   │   └── ko/          # Korean translations
│   │       └── LC_MESSAGES/
│   │           ├── django.po  # Translation file
│   │           └── django.mo  # Compiled translations
│   │
│   ├── media/           # User uploads (gitignored)
│   │
│   ├── scripts/         # Utility scripts
│   │   ├── migrate_data_from_streamlit.py
│   │   ├── analyze_streamlit_database.py
│   │   └── reports/     # Migration reports
│   │
│   ├── tests/           # Manual test scripts
│   └── logs/            # Development logs
│
├── docs/               # Documentation
│   ├── kb/             # Knowledge base
│   ├── project/        # Project guidelines
│   └── migration/      # Migration documentation
│
├── logs/               # Project logs
└── tasks/              # PRD workflow directory
```

## Key Design Decisions

### 1. **Django Architecture**
- **Apps**: Modular Django apps for separation of concerns
- **Settings**: Environment-specific settings modules
- **Templates**: Server-side rendering with HTMX for dynamic updates
- **API**: RESTful API with Django REST Framework for external integrations

### 2. **Technology Stack**
- **Backend**: Django 5.0.1
- **Frontend**: HTMX 1.9.10 + Alpine.js 3.x + Tailwind CSS
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: Django auth with JWT for API
- **PDF Generation**: WeasyPrint
- **Testing**: pytest with Factory Boy

### 3. **Security Features**
- Rate limiting on login (5 attempts = 30-minute lockout)
- JWT authentication for API access
- CSRF protection
- Secure password hashing
- Permission-based access control

### 4. **Internationalization**
- Full Korean language support
- 135+ translation entries
- Korean number formatting
- Culturally appropriate UI

## Django App Structure

### accounts/
- Custom User model
- Authentication views (login/logout)
- Rate limiting middleware
- User profile management

### api/
- RESTful endpoints
- JWT authentication
- Serializers for all models
- OpenAPI/Swagger documentation

### assessments/
- 7 fitness test models
- Multi-step assessment workflow
- Real-time score calculations
- Compensation pattern tracking

### clients/
- Client CRUD operations
- Search and filtering
- CSV export functionality
- BMI calculations

### reports/
- PDF report generation
- WeasyPrint integration
- Chart generation
- Korean font support

### sessions/
- Session package management
- Payment tracking
- VAT/fee calculations (10% VAT, 3.5% card fee)
- Calendar view

## Development Workflow

1. **Setup**: Create virtual environment and install dependencies
2. **Database**: Run migrations for initial setup
3. **Translations**: Compile message files for Korean support
4. **Testing**: Run pytest for unit and integration tests
5. **Development**: Use Django development server
6. **API Testing**: Use interactive API test runner

## Deployment

### Heroku Deployment
- Uses Procfile for web and release processes
- PostgreSQL database via Heroku addon
- Static files served by WhiteNoise
- Environment variables for configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Set to False in production
- `DATABASE_URL`: PostgreSQL connection (auto-set by Heroku)
- `ALLOWED_HOSTS`: Your domain name

## Testing Infrastructure

- **Framework**: pytest with Django plugin
- **Coverage**: 72%+ test coverage
- **Factories**: Factory Boy for test data
- **API Tests**: Comprehensive endpoint testing
- **Test Database**: Reusable test database for speed

## Next Steps

1. Complete production deployment (Phase 6)
2. Add real-time features with WebSockets
3. Implement advanced analytics
4. Mobile app development using API
5. Integration with fitness wearables