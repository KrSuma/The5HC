# Documentation Update Plan - Post-Streamlit Cleanup

**Date**: 2025-01-11
**Purpose**: Update all documentation to reflect Django-only architecture after Streamlit removal

## Files Requiring Updates

### 1. README.md (Root)

**Current State**: Mixed Streamlit/Django documentation
**Required Changes**:
- Remove all Streamlit references and commands
- Update project description to Django-only
- Update installation instructions for Django
- Update deployment instructions
- Add Django-specific badges/shields
- Update technology stack section
- Remove Streamlit screenshots (if any)

**New Structure**:
```markdown
# The5HC Fitness Assessment System

A comprehensive fitness assessment system built with Django for Korean fitness trainers.

## Features
- Client management
- Fitness assessments with 27 metrics
- Session tracking and package management
- PDF report generation
- RESTful API
- Korean language support

## Technology Stack
- Django 5.0.1
- HTMX + Alpine.js
- Tailwind CSS
- PostgreSQL/SQLite
- Django REST Framework

## Installation
1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r django_migration/requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Create superuser: `python manage.py createsuperuser`
6. Run server: `python manage.py runserver`

## Deployment
[Heroku deployment instructions for Django]
```

### 2. CLAUDE.md

**Required Changes**:
- Update project overview (remove "built with Streamlit")
- Update file structure to reflect post-cleanup state
- Remove Streamlit commands from Quick Reference
- Update Important Files section
- Remove src/ directory references
- Update migration status to show completion

### 3. requirements.txt (Root)

**Options**:
1. **DELETE**: Use only django_migration/requirements.txt
2. **UPDATE**: Keep minimal deployment requirements
3. **REDIRECT**: Create simple file pointing to Django requirements

**Recommendation**: Option 3 - Create redirect
```
# See django_migration/requirements.txt for all dependencies
```

### 4. .gitignore

**Add Django-specific patterns**:
```
# Django
*.pyc
__pycache__/
db.sqlite3
media/
staticfiles/
.env
*.log

# Remove Streamlit patterns
# DELETE: .streamlit/secrets.toml
# DELETE: streamlit-specific entries
```

### 5. django_migration/README.md

**Update to reflect**:
- Remove "migration" terminology
- This is now the main application
- Update status to show Phase 5 complete
- Add production deployment instructions

### 6. docs/DJANGO_MIGRATION_GUIDE.md

**Options**:
1. **ARCHIVE**: Move to docs/migration/COMPLETED_MIGRATION.md
2. **UPDATE**: Change to "Django Development Guide"
3. **DELETE**: No longer needed after migration

**Recommendation**: Option 1 - Archive for historical reference

### 7. docs/PROJECT_STRUCTURE.md

**Complete Rewrite Needed**:
- Remove all Streamlit directories
- Update to Django-only structure
- Add new directory tree
- Update descriptions

### 8. docs/SYSTEM_ARCHITECTURE.md

**Update Architecture**:
- Remove Streamlit service layer
- Update to Django MVT architecture
- Update data flow diagrams
- Update deployment architecture

### 9. deployment/DEPLOYMENT_GUIDE.md

**Update for Django**:
- Remove Streamlit deployment steps
- Add Django deployment steps
- Update Procfile content for Django
- Update environment variables
- Add static file collection steps

## Documentation Cleanup Actions

### Move to Archive
```
mkdir -p docs/archive/streamlit-migration/
mv docs/PHASE5_PREPARATION.md docs/archive/streamlit-migration/
mv docs/migration/*.md docs/archive/streamlit-migration/
```

### Delete Outdated
```
rm docs/NOTION_INTEGRATION_GUIDE.md  # If not used
```

### Create New
1. `docs/DJANGO_DEPLOYMENT_GUIDE.md` - Production deployment
2. `docs/API_DOCUMENTATION.md` - API endpoints reference
3. `docs/DEVELOPMENT_SETUP.md` - Local development guide

## Update Priority

1. **HIGH**: README.md, CLAUDE.md (main entry points)
2. **MEDIUM**: .gitignore, requirements.txt (functional impact)
3. **LOW**: Other documentation (reference material)

## Sample Updates

### README.md Header Update
```markdown
# The5HC Fitness Assessment System

[![Django](https://img.shields.io/badge/Django-5.0.1-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![HTMX](https://img.shields.io/badge/HTMX-1.9.10-purple.svg)](https://htmx.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern fitness assessment system for Korean personal trainers, built with Django and HTMX.
```

### CLAUDE.md Project Overview Update
```markdown
## Project Overview

The5HC is a comprehensive fitness assessment system built with Django, designed for Korean fitness trainers to manage clients, conduct assessments, and track sessions. The application uses HTMX and Alpine.js for dynamic interactions and supports both SQLite (development) and PostgreSQL (production) databases.
```

## Verification Checklist

After documentation updates:
- [ ] No Streamlit references remain
- [ ] All commands work with Django
- [ ] File paths are accurate
- [ ] Installation instructions tested
- [ ] Deployment guide validated
- [ ] API documentation complete
- [ ] Architecture diagrams updated

## Timeline

1. **Immediate**: Update README.md and CLAUDE.md
2. **Before Cleanup**: Update .gitignore
3. **After Cleanup**: Update PROJECT_STRUCTURE.md
4. **Final**: Archive migration docs, create new guides