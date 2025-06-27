# Markdown Files Cleanup Plan

**Date**: 2025-06-27
**Total Files Analyzed**: 226 .md files
**Files to Clean**: ~45 files

## Cleanup Actions

### 1. Root Directory (8 files)
**Delete (2):**
- `fitness-assessment-scoring-report.md` - Duplicate of docs version
- `summary.md` - Outdated project summary

**Archive (6):**
- `CLEANUP_COMPLETE.md` → `logs/archive/refactoring/`
- `CLEANUP_FINAL_STATUS.md` → `logs/archive/refactoring/`
- `CLEANUP_SUMMARY.md` → `logs/archive/refactoring/`
- `FORM_DEPLOYMENT_SUMMARY.md` → `logs/archive/refactoring/`
- `additional-questions.md` → `docs/archive/planning/mcq-additional-questions.md`
- `timer.md` → `docs/archive/planning/timer-requirements.md`

### 2. Docs Directory (13 files)
**Archive Migration Docs (8):**
- `docs/migration/PHASE5_PREPARATION.md`
- `docs/migration/PHASE6_DEPLOYMENT_PLAN.md`
- `docs/migration/POSTGRESQL_FIXES.md`
- `docs/migration/IMPORT_FIXES_SUMMARY.md`
- `docs/migration/ORGANIZATION_SUMMARY.md`
- `docs/development/PHASE4_DATA_MIGRATION_PLAN.md`
- `docs/development/TESTING_MIGRATION_PLAN.md`
- `docs/DJANGO_MIGRATION_GUIDE.md`

**Archive Planning Docs (4):**
- `docs/TRAINER_MIGRATION_PLAN.md`
- `docs/VAT_FEES_IMPLEMENTATION_PLAN.md`
- `docs/MCQ_PHASE4_PLANNING.md`
- `docs/MCQ_PHASE5_PLANNING.md`

**Archive Other (2):**
- `docs/SYSTEM_ARCHITECTURE.md` - Outdated (Streamlit)
- `docs/PYTEST_FIX_LOG.md` - One-time fix log

### 3. Logs Directory (~25 files)
**Archive Duplicate/Incremental Logs:**
- Session summaries (when complete logs exist)
- Individual phase logs (when consolidated logs exist)
- Incremental work logs (SESSION2, SESSION3, etc.)
- Old cleanup logs from June 15-19

### 4. Files Kept
- All files in `docs/archive/` - Already properly archived
- All feature implementation logs - Contain unique technical details
- Recent session logs (last 3-4 sessions)
- Core documentation (CLAUDE.md, README.md, etc.)
- Active guides and current documentation

## Manual Actions Required After Cleanup

1. **Consolidate Testing Documentation**
   - Merge 3 testing guides into one comprehensive guide
   
2. **Update MCQ Status**
   - Update `MCQ_IMPLEMENTATION_STATUS.md` to reflect Phase 9 completion
   
3. **Review KB Files**
   - Check `docs/kb/` files for Streamlit references
   - Update to reflect Django architecture

## Benefits of Cleanup

- **Root directory**: Reduced from 15+ to ~7 .md files
- **Better organization**: All archives properly categorized
- **No duplicates**: Removed redundant documentation
- **Current docs only**: Archived all completed/outdated plans
- **Cleaner logs**: Kept only essential logs in active directory

## Script Location
`cleanup_markdown_files.sh` - Ready to execute