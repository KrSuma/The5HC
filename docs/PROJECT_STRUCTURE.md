# The5HC Complete Project Structure

**Updated**: 2025-06-25 (Session 18)

## Directory Overview

```
The5HC/
├── apps/                          # Django applications (7 apps)
│   ├── __init__.py
│   ├── accounts/                  # User authentication & management
│   ├── analytics/                 # Dashboard and analytics  
│   ├── api/                       # RESTful API with DRF
│   ├── assessments/               # Fitness assessment system
│   ├── clients/                   # Client management
│   ├── reports/                   # PDF report generation
│   ├── sessions/                  # Session & payment tracking
│   └── trainers/                  # Trainer & organization management
├── the5hc/                        # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings/                  # Modular settings
│   │   ├── __init__.py
│   │   ├── base.py               # Base settings
│   │   ├── development.py        # Development settings
│   │   ├── production.py         # Production settings
│   │   └── test.py               # Test settings
│   ├── urls.py                    # URL configuration
│   └── wsgi.py                    # WSGI config
├── static/                        # Static assets
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript files
│   └── fonts/                     # Korean fonts
├── media/                         # User uploads
├── templates/                     # Django templates
│   ├── base.html                  # Base template with HTMX/Alpine
│   ├── accounts/                  # Auth templates
│   ├── assessments/               # Assessment templates
│   ├── clients/                   # Client templates
│   ├── components/                # Reusable components
│   ├── dashboard/                 # Dashboard templates
│   ├── registration/              # Registration templates
│   ├── reports/                   # Report templates
│   ├── sessions/                  # Session templates
│   └── trainers/                  # Trainer templates
├── locale/                        # Translations
│   └── ko/LC_MESSAGES/            # Korean translations
├── scripts/                       # Utility scripts
│   ├── analyze_data_issues.py
│   ├── migrate_data_from_streamlit.py
│   └── reports/                   # Script reports
├── tests/                         # Test files
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures
│   ├── manual/                    # Manual test scripts
│   ├── performance/               # Performance tests
│   └── admin/                     # Admin interface tests
├── docs/                          # All documentation
│   ├── api/                       # API documentation
│   ├── deployment/                # Deployment guides
│   ├── development/               # Development guides
│   ├── kb/                        # Knowledge base (modular)
│   │   ├── build/                # Build commands
│   │   ├── code-style/           # Style guidelines
│   │   ├── django/               # Django details
│   │   ├── project-notes/        # Project specifics
│   │   ├── troubleshooting/      # Troubleshooting
│   │   └── workflow/             # Workflows
│   ├── project/                   # Project guidelines
│   │   ├── claude-task-rules.md
│   │   ├── claude-mindset.md
│   │   └── django-test.md
│   ├── migration/                 # Migration docs
│   ├── ACTIVE_ISSUES.md          # Current issues tracker
│   ├── CURRENT_SPRINT.md         # Recent sessions
│   ├── FEATURE_HISTORY.md        # Complete feature history
│   ├── PROJECT_STRUCTURE.md      # This file
│   └── [Various guides].md        # Other documentation
├── logs/                          # All logs (consolidated)
│   ├── migration/                 # Migration phase logs
│   ├── feature/                   # Feature implementation logs
│   ├── maintenance/               # Maintenance logs
│   └── archive/                   # Archived logs
├── tasks/                         # Task management
│   ├── prd-*.md                   # Product Requirements Documents
│   └── tasks-*.md                 # Task lists from PRDs
├── assets/                        # Project assets
│   └── fonts/                     # Font files for PDF
├── venv/                          # Virtual environment
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
├── pytest.ini                     # pytest configuration
├── conftest.py                    # pytest fixtures
├── run_api_tests.py               # API test runner
├── run_with_weasyprint.sh         # macOS WeasyPrint runner
├── the5hc_dev                     # SQLite database
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── .gitignore                     # Git configuration
├── Procfile                       # Heroku deployment
├── .python-version                # Python version (3.12)
├── Aptfile                        # Heroku system dependencies
├── README.md                      # Project documentation
└── CLAUDE.md                      # Claude Code knowledge base
```

## Django App Structure Details

### Each app typically contains:
```
app_name/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── forms.py              # Django forms
├── models.py             # Database models
├── views.py              # View functions/classes
├── urls.py               # URL patterns
├── serializers.py        # DRF serializers (API apps)
├── services.py           # Business logic
├── utils.py              # Helper functions
├── decorators.py         # Custom decorators
├── middleware.py         # Custom middleware
├── signals.py            # Django signals
├── managers.py           # Custom model managers
├── migrations/           # Database migrations
├── tests/                # App-specific tests
├── templates/app_name/   # App templates
├── static/app_name/      # App static files
└── management/           # Management commands
    └── commands/
```

## Key Statistics

- **Django Applications**: 7 fully implemented apps
- **Templates**: 75+ HTML files with HTMX/Alpine.js
- **Tests**: 80+ test files with pytest
- **Documentation**: 50+ markdown files
- **Logs**: 60+ log files tracking development
- **Management Commands**: 15+ custom commands
- **API Endpoints**: 8+ RESTful endpoints with JWT auth
- **Models**: 20+ Django models
- **Forms**: 15+ Django forms
- **Views**: 50+ view functions/classes

## Important Files

### Configuration
- `the5hc/settings/base.py` - Core Django settings
- `the5hc/settings/production.py` - Production overrides
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment config

### Entry Points
- `manage.py` - Django management command
- `the5hc/urls.py` - Main URL configuration
- `the5hc/wsgi.py` - WSGI application

### Testing
- `pytest.ini` - pytest configuration
- `conftest.py` - Global pytest fixtures
- `run_api_tests.py` - API test runner

### Documentation
- `README.md` - Project overview
- `CLAUDE.md` - Claude Code knowledge base
- `docs/` - All documentation files

### Utilities
- `run_with_weasyprint.sh` - PDF generation helper
- `scripts/migrate_data_from_streamlit.py` - Data migration

## Technology Stack

- **Backend**: Django 5.0.1, Django REST Framework
- **Frontend**: HTMX 1.9.10, Alpine.js 3.x, Tailwind CSS
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: Django auth with JWT for API
- **PDF Generation**: WeasyPrint
- **Testing**: pytest with Factory Boy
- **Deployment**: Heroku, Gunicorn, WhiteNoise

## Notes

- All Django apps follow standard Django conventions
- Templates use HTMX for dynamic updates
- Alpine.js handles client-side interactivity
- Korean localization throughout
- Comprehensive test coverage with pytest
- Production-ready with Heroku deployment