Load @docs/project/claude-task-rules.md
Load @docs/project/claude-mindset.md
Load @docs/project/django-test.md

# The5HC Fitness Assessment System - Claude Code Knowledge Base

## Project Overview

The5HC is a comprehensive fitness assessment system built with Django 5.0.1, designed for Korean fitness trainers to manage clients, conduct assessments, and track sessions. The application features a modern web stack with HTMX and Alpine.js for dynamic UI, a complete RESTful API, and supports both SQLite (development) and PostgreSQL (production) databases.

**Production URL**: https://the5hc.herokuapp.com/

## Documentation Structure

This knowledge base is organized into focused sections:

- **Build & Deployment**: Load @docs/kb/build/commands.md
- **Code Style Guidelines**: Load @docs/kb/code-style/guidelines.md
- **Django Migration Details**: Load @docs/kb/django/migration-details.md
- **Troubleshooting Guide**: Load @docs/kb/troubleshooting/guide.md
- **Workflow Conventions**: Load @docs/kb/workflow/conventions.md
- **Project-Specific Notes**: Load @docs/kb/project-notes/specifics.md

## Quick Reference

### Essential Commands

```bash
# Run Django development server
python manage.py runserver

# Run tests
pytest

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Compile translations
python manage.py compilemessages

# Create superuser
python manage.py createsuperuser

# Run API tests
python run_api_tests.py

# Recalculate assessment scores
python manage.py recalculate_scores [--dry-run] [--assessment-id ID]
```

### Key Technologies

- **Backend**: Django 5.0.1, Django REST Framework
- **Frontend**: HTMX 1.9.10, Alpine.js 3.x, Tailwind CSS
- **Database**: PostgreSQL (production), SQLite (development)
- **Testing**: pytest, Factory Boy, faker
- **PDF Generation**: WeasyPrint
- **Deployment**: Heroku, Gunicorn, WhiteNoise
- **API**: JWT authentication, OpenAPI/Swagger docs

### Project Status

- ✅ Phase 1: Project setup and infrastructure - COMPLETE
- ✅ Phase 2: Database models and migration - COMPLETE
- ✅ Phase 3: Forms and UI implementation - COMPLETE
- ✅ Phase 4: PDF generation and data migration - COMPLETE
- ✅ Phase 5: API development and testing - COMPLETE
- ✅ Phase 6: Production deployment - COMPLETE (2025-01-11)

### Recent Completed Features

#### 2025-06-14
- ✅ PDF Report Generation Implementation (COMPLETE)
  - Fixed integration between assessments and reports apps
  - Removed conflicting URL patterns
  - Updated field mappings in report service
  - PDF generation now fully functional with Korean support
- ✅ HTMX Navigation Pattern Standardization (COMPLETE)
  - Fixed duplicate header/footer issues across multiple views
  - Created content-only templates for HTMX navigation
  - Implemented proper detection of navigation vs partial requests
  - Created comprehensive documentation at `docs/HTMX_NAVIGATION_PATTERN.md`
  - Fixed views: Assessment list, Client add/edit/detail

#### 2025-06-13
- ✅ Assessment Score Calculation Implementation (COMPLETE)
  - ✅ Phase 1: Model field updates for proper scoring
  - ✅ Phase 2: Implement calculate_scores() method
  - ✅ Phase 3: Form and UI updates for score display
  - ✅ Phase 4: Data migration for existing assessments (All 6 assessments updated)
  - ✅ Phase 5: Testing and validation (pytest configuration fixed)

### Known Issues & Fixes

- **pytest-asyncio incompatibility**: Removed from requirements.txt due to AttributeError with Package objects. Tests now run successfully without it.
- **HTMX Navigation Pattern**: Fixed duplicate header/footer issues by implementing content-only templates for HTMX navigation. See `docs/HTMX_NAVIGATION_PATTERN.md` for implementation guide.

### Important Files

- `manage.py` - Django management command
- `the5hc/settings/` - Django settings (base, development, production, test)
- `apps/` - Django applications (7 apps)
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration
- `runtime.txt` - Python version specification (python-3.12.1)
- `Aptfile` - System dependencies for WeasyPrint on Heroku
- `.env.example` - Environment variable template

## Complete Project File Structure

**Updated**: 2025-01-11 (Django at root directory after reorganization)

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
│   └── trainers/                  # Trainer management (placeholder)
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
│   └── sessions/                  # Session templates
├── locale/                        # Translations
│   └── ko/LC_MESSAGES/            # Korean translations
├── scripts/                       # Utility scripts
│   ├── analyze_data_issues.py
│   ├── migrate_data_from_streamlit.py
│   └── reports/                   # Script reports
├── tests/                         # Test files
│   └── manual/                    # Manual test scripts
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
│   ├── migration/                 # Migration docs
│   ├── HTMX_NAVIGATION_PATTERN.md # HTMX navigation guide
│   ├── ASSESSMENT_SCORING_ALGORITHMS.md # Scoring documentation
│   ├── PYTEST_FIX_LOG.md          # pytest troubleshooting
│   └── SCORING_VALIDATION_EXAMPLES.md # Score validation
├── logs/                          # All logs (consolidated)
│   ├── migration/                 # Migration phase logs
│   ├── feature/                   # Feature implementation logs
│   └── maintenance/               # Maintenance logs
├── assets/                        # Project assets
│   └── fonts/                     # Font files for PDF
├── venv/                          # Virtual environment
├── manage.py                      # Django management
├── requirements.txt               # Python dependencies
├── pytest.ini                     # pytest configuration
├── conftest.py                    # pytest fixtures
├── run_api_tests.py               # API test runner
├── the5hc_dev                     # SQLite database
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── .gitignore                     # Git configuration
├── Procfile                       # Heroku deployment
├── runtime.txt                    # Python version
├── Aptfile                        # Heroku system dependencies
├── README.md                      # Project documentation
└── CLAUDE.md                      # This knowledge base

Total Project Structure:
- Django Application: 100+ files across 7 apps
- Templates: 30+ HTML files with HTMX/Alpine.js  
- Tests: 70+ test files with pytest
- Documentation: 25+ markdown files (organized)
- Logs: 54 log files (organized in subdirectories)
- API Endpoints: 8+ RESTful endpoints with JWT auth
```