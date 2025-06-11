# Pre-Phase 4 Cleanup Plan

**Date**: 2025-01-09
**Author**: Claude
**Purpose**: Clean and organize directory structure before continuing Phase 4 implementation

## Cleanup Tasks

### 1. Log File Consolidation
- [ ] Move `fitness_app.log` to `/logs/` directory
- [ ] Review and consolidate Django phase logs if appropriate
- [ ] Ensure all active logs are in proper directories

### 2. Test File Organization
- [ ] Move `test_fee_calculations.py` from root to `/tests/`
- [ ] Verify all test files are properly organized

### 3. Script Organization
- [ ] Create `/scripts/migrations/` subdirectory
- [ ] Move `run_fee_migration.py` to `/scripts/migrations/`
- [ ] Move `run_migration.py` to `/scripts/migrations/`
- [ ] Move `debug_performance.py` to `/scripts/` or remove if obsolete

### 4. Database File Review
- [ ] Check if `/data/fitness_assessment.db` is duplicate
- [ ] Remove or archive `database.py.backup` if not needed

### 5. Documentation Consolidation
- [ ] Consider consolidating deployment documents
- [ ] Update main README with Streamlit retention decision

### 6. Django Project Cleanup
- [ ] Remove `requirements-minimal.txt` if not used
- [ ] Verify need for `runtime.txt`
- [ ] Document purpose of empty template directories

### 7. Create Required Directories
- [ ] Ensure `/tasks/` directory exists for PRD workflow
- [ ] Add `.gitkeep` to maintain empty directories

## Benefits
- Cleaner root directory
- Better organization following CLAUDE.md guidelines
- Easier navigation for Phase 4 implementation
- Consistent with project standards

## Next Steps
After cleanup:
1. Update CLAUDE.md if directory structure changes
2. Create cleanup log documenting changes
3. Continue with Phase 4 PDF implementation