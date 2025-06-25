Load @docs/project/claude-task-rules.md
Load @docs/project/claude-mindset.md
Load @docs/project/django-test.md

# The5HC Fitness Assessment System - Claude Code Knowledge Base

## Project Overview

The5HC is a comprehensive fitness assessment system built with Django 5.0.1, designed for Korean fitness trainers to manage clients, conduct assessments, and track sessions. Features modern web stack with HTMX/Alpine.js, RESTful API, and dual database support.

**Production URL**: https://the5hc.herokuapp.com/  
**Status**: Phase 6 Complete - In Production (2025-01-11)

## Quick Start

### Essential Commands

```bash
# Development
python manage.py runserver
./run_with_weasyprint.sh        # macOS with PDF support
pytest                          # Run tests

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Common Management
python manage.py create_trainer <username> <email> [--role]
python manage.py recalculate_scores [--assessment-id ID]
python manage.py load_test_standards
python manage.py load_mcq_questions [--file FILE]
```

### Technology Stack
- **Backend**: Django 5.0.1, Django REST Framework, JWT Auth
- **Frontend**: HTMX 1.9.10, Alpine.js 3.x, Tailwind CSS  
- **Database**: PostgreSQL (production), SQLite (development)
- **Testing**: pytest, Factory Boy, faker
- **PDF**: WeasyPrint
- **Deployment**: Heroku, Gunicorn, WhiteNoise

## Documentation Hub

### Core Documentation
- **Build & Deploy**: Load @docs/kb/build/commands.md
- **Code Style**: Load @docs/kb/code-style/guidelines.md
- **Django Details**: Load @docs/kb/django/migration-details.md
- **Troubleshooting**: Load @docs/kb/troubleshooting/guide.md
- **Workflow**: Load @docs/kb/workflow/conventions.md
- **Project Notes**: Load @docs/kb/project-notes/specifics.md

### Feature Documentation
- **Feature History**: Load @docs/FEATURE_HISTORY.md (all completed features)
- **Current Sprint**: Load @docs/CURRENT_SPRINT.md (recent sessions)
- **Active Issues**: Load @docs/ACTIVE_ISSUES.md
- **Project Structure**: Load @docs/PROJECT_STRUCTURE.md

### Key Guides
- `docs/HTMX_NAVIGATION_PATTERN.md` - HTMX implementation
- `docs/TRAINER_ROLE_PERMISSIONS.md` - Role system
- `docs/ASSESSMENT_SCORING_ALGORITHMS.md` - Scoring logic
- `docs/MULTI_TENANT_ARCHITECTURE.md` - Multi-tenant design
- `docs/MCQ_IMPLEMENTATION_STATUS.md` - MCQ system status

## Current Focus (Session 18 - 2025-06-25)

### Completed Today
- ✅ Movement quality fields visibility investigation (browser cache issue)
- ✅ Dashboard score display fix (floatformat:2 for decimal precision)
- ✅ Physical assessment category reorganization
- ✅ Manual score field fixes (all 7 phases complete with visual feedback)

### Active Work
- MCQ System: 8/10 phases complete (Phase 9: PDF reports pending)
- See @docs/CURRENT_SPRINT.md for detailed session logs

## Project Status Summary

### Completed Phases
- ✅ Phase 1-6: Django migration complete, deployed to production
- ✅ Trainers App: Multi-tenant system with organizations
- ✅ Fitness Assessment Enhancement: 6/6 phases complete
- ✅ MCQ System: 8/10 phases complete (database, scoring, UI, API, admin, commands, testing)

### Active Issues
- MCQ PDF report integration pending (Phase 9)
- 11/12 integration tests fail (organization switching not implemented)
- See @docs/ACTIVE_ISSUES.md for complete list

## Key Directories

```
The5HC/
├── apps/           # Django applications (7 apps)
├── the5hc/         # Django settings
├── templates/      # HTMX/Alpine templates  
├── static/         # CSS/JS assets
├── locale/         # Korean translations
├── docs/           # All documentation
├── logs/           # Development logs
├── tasks/          # PRDs and task lists
└── tests/          # Test suites
```

See @docs/PROJECT_STRUCTURE.md for complete file structure

## Environment

- Python 3.12 (`.python-version`)
- Django 5.0.1
- Working directory: `/Users/jslee/PycharmProjects/The5HC`
- Platform: darwin (macOS)
- Git branch: main

## Notes

- **HTMX Navigation**: See `docs/HTMX_NAVIGATION_PATTERN.md` for content-only templates
- **WeasyPrint on macOS**: Use `./run_with_weasyprint.sh` for PDF generation
- **Testing**: Use pytest with `@pytest.mark.django_db` for database access
- **Korean UI**: All user-facing text in Korean with proper formatting