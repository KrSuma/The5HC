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
- ✅ Manual score override feature (5 phases complete, deployed to production)
- ✅ Delete button HTMX attributes display fix

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

## CRITICAL: HTMX Dual Template Pattern

**⚠️ IMPORTANT**: This project uses a dual-template pattern for HTMX navigation. When adding ANY new feature to templates, you MUST update BOTH templates:

1. **Full Page Template** (e.g., `assessment_form.html`) - Used for direct URL navigation
2. **Content Template** (e.g., `assessment_form_content.html`) - Used for HTMX navigation

### Why This Matters
- Direct URL navigation (typing `/assessments/add/` in browser) uses the full page template
- HTMX navigation (clicking links with `hx-get`) uses the content template
- Missing features in either template causes confusing bugs where features work in one navigation method but not the other

### Required Actions When Modifying Templates
1. **ALWAYS check if a template has a corresponding `_content.html` version**
2. **Apply ALL changes to BOTH templates**
3. **Test features using BOTH navigation methods**:
   - Direct URL access (refresh the page)
   - HTMX navigation (click through the app)

### Common Template Pairs
- `assessment_form.html` ↔ `assessment_form_content.html`
- `assessment_list.html` ↔ `assessment_list_content.html`
- `client_form.html` ↔ `client_form_content.html`
- `client_list.html` ↔ `client_list_content.html`

### Example Issue
Timer components were added only to `assessment_form_content.html` but not to `assessment_form.html`, causing timers to be invisible when navigating directly to `/assessments/add/`. This took significant time to debug.

## JavaScript Integration Guidelines

### Alpine.js Component Requirements
When working with Alpine.js components in templates:

1. **Variable Synchronization**: Ensure all `x-model` bindings in form fields have corresponding variables in the Alpine component
2. **Method Definitions**: All `@change`, `@input`, or `@click` handlers must have corresponding methods defined
3. **Form Field Bindings**: Check these files when adding form fields with Alpine.js:
   - `apps/assessments/forms/assessment_forms.py` - Form field definitions with x-model attributes
   - `templates/assessments/assessment_form.html` - Main Alpine.js component definition
   - `templates/assessments/assessment_form_content.html` - If using separate content templates

### Common Alpine.js Variables for Assessment Forms
```javascript
// Movement quality variables
pushUpType: 'standard',
overheadSquatQuality: '',
toeTouchFlexibility: '',
shoulderMobilityCategory: '',

// Overhead squat compensations
overheadSquatKneeValgus: false,
overheadSquatForwardLean: false,
overheadSquatHeelLift: false,
overheadSquatArmDrop: false,
```

### CDN Best Practices
1. **Chart.js**: Use specific version to avoid source map errors
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
   ```

2. **Tailwind CSS**: Production warning is expected with CDN. For production deployment:
   - Current: `<script src="https://cdn.tailwindcss.com"></script>` (development only)
   - Production: Should use PostCSS or Tailwind CLI build process

### Debugging JavaScript Errors
1. Check browser console for Alpine.js expression errors
2. Verify all x-model variables exist in the Alpine component
3. Ensure all event handler methods are defined
4. Check for missing form field initializations in `initializeScoresFromForm()`