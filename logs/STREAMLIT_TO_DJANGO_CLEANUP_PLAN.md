# Streamlit to Django Migration - Comprehensive Cleanup Plan

**Date**: 2025-01-11
**Author**: Claude
**Purpose**: Complete cleanup plan for removing Streamlit and consolidating the project after Django migration

## Executive Summary

The5HC has successfully migrated from Streamlit to Django with Phases 1-5 complete. This cleanup plan categorizes all files for deletion, retention, or modification to create a clean Django-only codebase.

## Migration Status Confirmation

- ✅ Phase 1-5: COMPLETED (Django setup, models, UI, PDF, API, testing)
- ✅ Data Migration: 42 records successfully migrated
- ✅ Feature Parity: Django has full functionality including PDF generation
- 🔲 Phase 6: Production deployment (not started)

## Cleanup Categories

### 1. DELETE - Streamlit-Specific Files and Directories

#### Root Level Files
```
DELETE: main.py                    # Streamlit entry point
DELETE: run_app.sh                 # Streamlit run script
DELETE: debug_performance.py       # Streamlit performance debugging
DELETE: run_migration.py           # Old database migration script
DELETE: run_fee_migration.py       # Old fee migration script
DELETE: Procfile                   # Heroku config for Streamlit
```

#### Entire Directories to Remove
```
DELETE: src/                       # Entire Streamlit source code
DELETE: config/                    # Streamlit configuration
DELETE: scripts/                   # Streamlit data scripts
DELETE: tests/                     # Streamlit tests (Django has its own)
DELETE: tasks/                     # PRD workflow directory (empty)
DELETE: .streamlit/                # Streamlit configuration (if exists)
```

#### Data Files
```
DELETE: data/fitness_assessment.db                    # Original SQLite (data migrated)
DELETE: data/fitness_assessment_backup_*.db          # Backup databases
```

### 2. KEEP - Still Needed for Django

#### Root Level Files
```
KEEP: README.md                    # Update to remove Streamlit references
KEEP: requirements.txt             # Update to Django-only dependencies
KEEP: .gitignore                   # Update to remove Streamlit patterns
```

#### Directories
```
KEEP: django_migration/            # This IS the main project now
KEEP: assets/fonts/                # Needed for PDF generation in Django
KEEP: docs/                        # Documentation (needs cleanup)
KEEP: logs/                        # Historical logs (consolidate)
KEEP: deployment/                  # Deployment guides (update for Django)
```

### 3. EDIT - Files Needing Updates

#### README.md
- Remove all Streamlit references
- Update to describe Django-only project
- Update installation instructions
- Update deployment instructions

#### requirements.txt
- Remove all Streamlit dependencies
- Keep only Django deployment dependencies if needed for root
- Or DELETE if using django_migration/requirements.txt

#### CLAUDE.md
- Update project overview (remove Streamlit mention)
- Update file structure
- Update command references
- Mark Django as primary application

#### .gitignore
- Remove Streamlit-specific patterns
- Add Django-specific patterns if missing

## Detailed File Analysis

### src/ Directory Breakdown (ALL TO BE DELETED)
```
src/
├── __init__.py                    # DELETE
├── config/                        # DELETE - Streamlit config
│   ├── __init__.py
│   └── settings.py
├── core/                          # DELETE - Business logic moved to Django
│   ├── __init__.py
│   ├── constants.py              # Already ported to Django
│   ├── models.py                 # Django has its own models
│   ├── recommendations.py        # Already ported to Django
│   └── scoring.py                # Already ported to Django
├── data/                         # DELETE - Database layer
│   ├── __init__.py
│   ├── add_fee_columns_migration.py
│   ├── archive/
│   ├── cache.py
│   ├── database.py
│   ├── database_config.py
│   ├── fix_postgresql_compatibility.py
│   ├── migrate_database.py
│   └── repositories.py
├── services/                     # DELETE - Service layer
│   ├── __init__.py
│   ├── add_client.py
│   ├── assessment_service.py
│   ├── auth.py
│   ├── auth_service.py
│   ├── client_service.py
│   ├── enhanced_session_service.py
│   ├── report_service.py
│   ├── service_layer.py
│   └── session_service.py
├── ui/                          # DELETE - Streamlit UI
│   ├── __init__.py
│   ├── components/
│   └── pages/
└── utils/                       # DELETE - Utilities
    ├── __init__.py
    ├── app_logging.py
    ├── cache.py
    ├── fee_calculator.py        # Already ported to Django
    ├── helpers.py
    ├── html_report_generator.py
    ├── logging.py
    ├── pdf_generator.py         # Django has WeasyPrint integration
    ├── pdf_utils.py
    ├── validators.py
    └── weasyprint_pdf_generator.py
```

### Log Files Consolidation

#### Keep These Logs (Move to django_migration/logs/)
```
logs/FEATURE_CHANGELOG.md          # Important feature history
logs/PROJECT_STATUS_SUMMARY.md     # Latest project status
logs/STREAMLIT_REMOVAL_ANALYSIS.md # This cleanup reference
```

#### Delete These Logs (Outdated/Redundant)
```
logs/CLAUDE_MD_UPDATE_LOG.md
logs/DOCUMENTATION_CONSOLIDATION_LOG.md
logs/PHASE4_PDF_UPDATES_LOG.md
logs/PRE_PHASE4_CLEANUP_LOG.md
logs/PRE_PHASE4_CLEANUP_PLAN.md
logs/REQUIREMENTS_UPDATE_LOG.md
logs/STRUCTURE_REORGANIZATION_LOG.md
logs/*.log                         # All .log files (runtime logs)
```

### Documentation Cleanup

#### docs/ Directory Actions
```
KEEP & UPDATE:
docs/DJANGO_MIGRATION_GUIDE.md    # Update to reflect completion
docs/HEROKU_DATABASE_SETUP.md     # Update for Django deployment
docs/PHASE5_PREPARATION.md         # Archive or delete (Phase 5 complete)
docs/PROJECT_STRUCTURE.md          # Update with Django-only structure
docs/SYSTEM_ARCHITECTURE.md        # Update to Django architecture
docs/VAT_FEES_IMPLEMENTATION_PLAN.md # Keep for reference

KEEP AS-IS:
docs/kb/                          # Knowledge base (already reorganized)
docs/migration/                   # Migration history
docs/project/                     # Project management docs
docs/samples/                     # Sample files

DELETE:
docs/NOTION_INTEGRATION_GUIDE.md  # If not used by Django
```

## New Project Structure (After Cleanup)

```
The5HC/
├── django_migration/             # Main Django project
│   ├── apps/                    # Django applications
│   ├── locale/                  # Translations
│   ├── logs/                    # All logs (consolidated)
│   ├── media/                   # User uploads
│   ├── scripts/                 # Django utilities
│   ├── static/                  # Static assets
│   ├── templates/               # Django templates
│   ├── the5hc/                  # Django settings
│   ├── manage.py                # Django management
│   ├── requirements.txt         # Dependencies
│   └── README.md                # Django documentation
├── assets/                      # Shared assets
│   └── fonts/                   # PDF generation fonts
├── docs/                        # Project documentation
│   ├── kb/                      # Knowledge base
│   ├── migration/               # Migration history
│   └── *.md                     # Various guides
├── deployment/                  # Deployment configurations
├── README.md                    # Main project README
├── CLAUDE.md                    # AI assistant knowledge base
└── .gitignore                   # Git ignore rules
```

## Cleanup Execution Plan

### Phase 1: Immediate Deletions (Safe)
```bash
# Delete Streamlit application files
rm -rf src/
rm main.py
rm run_app.sh
rm debug_performance.py
rm run_migration.py
rm run_fee_migration.py
rm Procfile

# Delete old data files (already migrated)
rm data/fitness_assessment.db
rm data/fitness_assessment_backup_*.db

# Delete Streamlit config
rm -rf config/

# Delete Streamlit scripts
rm -rf scripts/

# Delete Streamlit tests
rm -rf tests/

# Delete empty tasks directory
rm -rf tasks/
```

### Phase 2: Log Consolidation
```bash
# Move important logs to Django
mv logs/FEATURE_CHANGELOG.md django_migration/logs/
mv logs/PROJECT_STATUS_SUMMARY.md django_migration/logs/
mv logs/STREAMLIT_REMOVAL_ANALYSIS.md django_migration/logs/

# Delete old logs
rm logs/*.log
rm logs/*_LOG.md
```

### Phase 3: Documentation Updates
1. Update README.md to describe Django-only project
2. Update CLAUDE.md to reflect new structure
3. Update or delete requirements.txt (root level)
4. Update .gitignore

### Phase 4: Final Restructure (Optional)
Consider moving django_migration/ contents to root:
```bash
# Move Django to root (optional, after backup)
mv django_migration/* .
mv django_migration/.* . 2>/dev/null
rmdir django_migration/
```

## Verification Checklist

After cleanup, verify:
- [ ] Django application still runs: `python manage.py runserver`
- [ ] Tests still pass: `pytest`
- [ ] PDF generation works with fonts from assets/
- [ ] No broken imports or references
- [ ] Documentation is accurate
- [ ] Git repository is clean

## Important Notes

1. **BACKUP FIRST**: Create a full backup before executing cleanup
2. **Data Migration Verified**: Ensure Django database has all data
3. **Feature Parity Confirmed**: Test all features work in Django
4. **Keep Historical Logs**: Preserve migration history in django_migration/logs/
5. **Update Documentation**: All docs should reflect Django-only status

## Next Steps After Cleanup

1. Update deployment configuration for Django-only
2. Set up CI/CD for Django project
3. Plan Phase 6: Production deployment
4. Consider repository rename (remove 'migration' references)
5. Archive Streamlit version if needed for reference