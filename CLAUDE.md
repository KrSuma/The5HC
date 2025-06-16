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

# Run Django with WeasyPrint support (macOS)
./run_with_weasyprint.sh

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

# Create new trainer account
python manage.py create_trainer <username> <email> [--role owner|senior|trainer]

# List all trainers and organizations
python manage.py list_trainers [--organization SLUG] [--role ROLE] [--active-only]
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

#### 2025-06-16 (Session 7)
- ✅ Trainer Account Management System
  - Created Django management commands (create_trainer, list_trainers)
  - Implemented CLI-based trainer account creation with role assignment
  - Created comprehensive trainer account creation documentation
  - Successfully deployed test account for client (the5hc.dev@gmail.com)
- ✅ Assessment Score Validation Fix
  - Fixed "Enter a whole number" error for farmer carry scores
  - Modified AJAX endpoints to return integers instead of decimals
  - Deployed fix to production
- ✅ Assessment Form UI Improvement
  - Removed non-functioning score summary section from assessment form
  - Cleaned up Chart.js dependency and related JavaScript
  - Simplified assessment workflow - scores now viewed after saving

#### 2025-06-16 (Session 6)
- ✅ Critical Django Fixes
  - Fixed trainer instance assignment errors (request.user → request.trainer)
  - Fixed assessment form not showing input fields (Django form rendering)
  - Fixed assessment score visualization (proper 0-100% scale display)
  - Fixed trainer invite duplicate role options
  - Fixed client edit HTMX response error
  - Improved assessment list filter UI alignment
  - Created comprehensive trainer role permissions documentation

#### 2025-06-15 (Session 5)
- ✅ Trainer Invite Template Fix
  - Created missing trainer invite templates (trainer_invite.html, trainer_invite_content.html)
  - Fixed 500 error on production when accessing trainer invite page
  - Implemented full Korean translation for invite interface
- ✅ Organization Trainer Limits
  - Updated trainer limits from 10 to 50 for both organizations
  - Fixed "maximum trainers reached" error preventing invitations
  - Created test_trainer user with owner role for testing
- ✅ Production Migration Updates
  - Applied 4 pending migrations to Heroku successfully
  - All trainer foreign key migrations now active in production

#### 2025-06-15 (Session 4)
- ✅ Korean Language Implementation
  - Replaced Django i18n system with direct Korean text for reliability
  - Changed LANGUAGE_CODE to 'ko' and disabled USE_I18N
  - Translated all navigation, trainer, and organization pages to Korean
  - Footer copyright year updated to 2025
  - Ensured Korean displays consistently on Heroku deployment

#### 2025-06-15 (Session 3)
- ✅ Client Form Bug Fixes
  - Fixed ValueError when creating/editing clients (User vs Trainer instance)
  - Forms now properly assign trainer relationships
- ✅ WeasyPrint Local Development Support
  - Created `run_with_weasyprint.sh` script for macOS
  - Sets proper DYLD_LIBRARY_PATH for system libraries
  - PDF generation now works in local development
- ✅ PDF Report System Improvements
  - Fixed AttributeError for assessment_date field
  - Fixed PDF alignment and cut-off issues with proper A4 margins
  - Removed summary report type - now only detailed reports
  - Simplified to one-click PDF generation (no selection page)
  - Created migration for report type changes

#### 2025-06-15 (Sessions 1-2)
- ✅ Organization Dashboard Bug Fixes
  - Fixed FieldError for non-existent 'is_active' field in Client model
  - Fixed incorrect foreign key references (session_package → package)
  - Dashboard now loads without errors
- ✅ HTMX Navigation Fixes  
  - Fixed blank page issue caused by notification badge polling
  - Added proper hx-target specifications to prevent content replacement
  - Temporarily disabled HTMX navigation in navbar to stabilize the application
  - Fixed double header/footer on assessment registration page
- ✅ Directory Maintenance
  - Archived old migration JSON reports
  - Organized logs into proper directories
  - Updated documentation

#### 2025-06-15 (Earlier)
- ✅ Trainers App Implementation - Phase 1-5 (COMPLETE)
  - Phase 1: Database Schema and Migrations
    - Created Organization, Trainer, and TrainerInvitation models
    - Updated foreign key references in Client, Assessment, SessionPackage, Session, Payment, and FeeAuditLog models
    - Created database migrations with initial data setup
    - Added database indexes for performance optimization
    - Configured comprehensive Django admin interfaces
    - Created migration strategy documentation
  - Phase 2: Trainer Profile Management
    - Implemented comprehensive forms (TrainerProfileForm, OrganizationForm, TrainerInvitationForm)
    - Created 8 views with role-based permissions and HTMX support
    - Built complete template set following HTMX navigation pattern
    - Added trainer profile editing with photo upload
    - Implemented trainer invitation system
    - Added organization management for owners
  - Phase 3: Permission System and Data Isolation
    - Implemented TrainerContextMiddleware for request-level context
    - Created comprehensive permission decorators (role-based, organization-based)
    - Updated all views for organization-level data isolation
    - Added foundation for organization switching
    - Implemented audit logging system with AuditLog model
    - Integrated audit logging for authentication and client operations
  - Phase 4: UI/UX Implementation for Trainer Features
    - Added organization context to navbar with role badges
    - Created comprehensive organization dashboard for owners
    - Implemented trainer analytics with Chart.js visualizations
    - Added in-app notification system with real-time updates
    - Enhanced navigation with trainer/organization specific links
  - Phase 5: Testing and Documentation (COMPLETE)
    - ✅ 5.1: Created comprehensive unit tests for all trainer models (20 tests, 100% pass rate)
    - ✅ 5.2: Implemented view and permission tests (80+ tests across 4 files)
    - ✅ 5.3: Tested organization data isolation (verified core isolation works)
    - ✅ 5.4: Documented multi-tenant architecture
    - ✅ 5.5: Created trainer app user guide in Korean
  - ✅ All migrations applied and tested
  - ✅ Complete multi-tenant system with data isolation
  - ✅ Comprehensive test coverage (models, views, permissions, integration)

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
- **Trainer Foreign Key Migration**: Successfully migrated all models to use Trainer foreign keys. All data isolation tests passing.
- **Integration Test Failures**: 11 of 12 integration tests still fail due to incomplete features (organization switching, audit log signatures). Core data isolation verified working.
- **Organization Dashboard**: ✅ FIXED - Field reference errors resolved.
- **HTMX Navigation**: Temporarily disabled in navbar due to content replacement issues. Standard navigation working.
- **WeasyPrint on macOS**: ✅ FIXED - Use `./run_with_weasyprint.sh` to set library paths.
- **Client Form Errors**: ✅ FIXED - Trainer assignment now uses correct instance type.
- **PDF Report Issues**: ✅ FIXED - Proper A4 layout, removed summary type, one-click generation.
- **Trainer Invite Templates**: ✅ FIXED - Created missing templates with Korean translation.
- **Organization Trainer Limits**: ✅ FIXED - Increased limits from 10 to 50 trainers.

### Important Notes

- **Python Version**: Heroku now uses `.python-version` file instead of `runtime.txt`. The project uses Python 3.12.

### Important Files

- `manage.py` - Django management command
- `the5hc/settings/` - Django settings (base, development, production, test)
- `apps/` - Django applications (7 apps, including configured trainers app)
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment configuration
- `.python-version` - Python version specification (3.12) - Heroku now uses this instead of runtime.txt
- `Aptfile` - System dependencies for WeasyPrint on Heroku
- `.env.example` - Environment variable template

### Key Documentation

- `docs/HTMX_NAVIGATION_PATTERN.md` - HTMX navigation implementation guide
- `docs/TRAINER_MIGRATION_PLAN.md` - Multi-trainer migration strategy
- `docs/ASSESSMENT_SCORING_ALGORITHMS.md` - Fitness assessment scoring logic
- `logs/FEATURE_CHANGELOG.md` - Detailed feature implementation history
- `logs/PROJECT_STATUS_SUMMARY.md` - Current project status overview
- `docs/MULTI_TENANT_ARCHITECTURE.md` - Multi-tenant architecture documentation
- `docs/TRAINER_APP_USER_GUIDE.md` - Trainer app user guide (Korean)
- `logs/feature/TRAINERS_APP_IMPLEMENTATION_COMPLETE_LOG.md` - Complete trainers app implementation details
- `logs/maintenance/CLEANUP_LOG_2025_06_15_SESSION3.md` - Latest maintenance session log
- `logs/maintenance/PDF_REPORT_IMPROVEMENTS_LOG.md` - PDF generation improvements
- `logs/maintenance/REMOVE_SUMMARY_REPORT_LOG.md` - Report simplification details
- `logs/maintenance/KOREAN_TRANSLATION_COMPLETE_LOG.md` - Korean language implementation
- `logs/maintenance/SESSION_5_SUMMARY_2025_06_15.md` - Trainer invite fix and limit updates
- `logs/maintenance/SESSION_6_FIXES_2025_06_16.md` - Critical Django fixes and UI improvements
- `logs/maintenance/SESSION_7_COMPLETE_LOG.md` - Trainer account creation system and score fix
- `docs/TRAINER_ROLE_PERMISSIONS.md` - Comprehensive trainer role and permissions guide
- `docs/TRAINER_ACCOUNT_CREATION_GUIDE.md` - Guide for creating trainer accounts
- `summary.md` - Comprehensive project overview with database schema

## Complete Project File Structure

**Updated**: 2025-06-16 (Session 7 - Added trainer account creation management commands)

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
│   └── trainers/                  # Trainer management (models, admin, views, forms, templates, middleware, decorators, audit, notifications, management commands)
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
│   ├── maintenance/               # Maintenance logs
│   └── archive/                   # Archived logs and old documentation
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
├── the5hc_dev                     # SQLite database
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── .gitignore                     # Git configuration
├── Procfile                       # Heroku deployment
├── .python-version                # Python version (Heroku now uses this)
├── Aptfile                        # Heroku system dependencies
├── README.md                      # Project documentation
└── CLAUDE.md                      # This knowledge base

Total Project Structure:
- Django Application: 150+ files across 7 apps (trainers app fully implemented with tests)
- Templates: 75+ HTML files with HTMX/Alpine.js (including trainers templates)
- Tests: 80+ test files with pytest (including comprehensive trainer tests)
- Documentation: 45+ markdown files (organized)
- Logs: 49 active log files (consolidated and organized with archive)
- Task Management: PRDs and task lists for feature implementation
- API Endpoints: 8+ RESTful endpoints with JWT auth
```