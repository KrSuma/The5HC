# Workflow Conventions

## Change Logging Requirements

**IMPORTANT**: All significant changes to the codebase must be logged.

### 1. Create Change Log Files

When making major changes or completing migration phases, create detailed log files:

- Phase completion logs (e.g., `PHASE1_COMPLETION_LOG.md`)
- Feature implementation logs
- Migration logs
- Major refactoring logs

### 2. Log Format

```markdown
# [Change Type] - [Brief Description]

**Date**: [Date]
**Author**: Claude
**Phase/Feature**: [Name]

## Summary
[Brief overview of changes]

## Detailed Changes
- [File/Module]: [What was changed and why]
- [File/Module]: [What was changed and why]

## New Files Created
- [Path]: [Purpose]

## Modified Files
- [Path]: [Nature of modifications]

## Testing
- [What was tested]
- [Test results]

## Next Steps
- [What comes next]
```

### 3. When to Log

- Completing a migration phase
- Adding new features
- Major refactoring
- Database schema changes
- Configuration changes
- Bug fixes that affect multiple files

## Directory and File Cleanup Guidelines

**IMPORTANT**: Keep the project directory clean and organized.

### 1. Consolidate Documentation

When multiple similar documents exist (e.g., multiple phase completion logs), consolidate them into a single comprehensive document.

### 2. Use Log Directory

Place all log files in appropriate `logs/` directories:

- Main project logs: `/logs/`
- Django migration logs: `/django_migration/logs/`
- Keep only the most current/comprehensive version

### 3. Clean Up After Phases

- Remove redundant documentation files
- Archive old versions if needed
- Keep only essential files in root directories
- **Note**: Do NOT delete `__pycache__` directories - keep them in the project

### 4. File Organization

```
Good:
logs/
├── PHASE1_COMPLETE_LOG.md
└── feature_implementation_log.md

Avoid:
PHASE1_COMPLETE.md
PHASE1_COMPLETION_LOG.md
PHASE1_FINAL_SUMMARY.md
(Multiple similar files in root)
```

### 5. When to Clean

- After completing a major phase
- When consolidating documentation
- Before starting a new major feature
- When files become redundant
- **Exception**: Keep `__pycache__` directories for faster Python execution

## Git Commit Messages

Based on recent commits, follow this pattern:

```
# Feature additions
Add 세션 관리 button in 회원 관리 page for quick access

# Bug fixes
Fix datetime object subscriptable error in session package display
Fix session service PostgreSQL compatibility issues

# Refactoring
Optimize database initialization to run only once

# Configuration changes
Fix PostgreSQL authentication issues in Heroku deployment

# Migration phases
Complete Phase 1: Django project setup with HTMX/Alpine.js
```

## Branch Strategy

- Main branch: `main`
- Feature branches: Not specified in codebase, likely feature/branch-name
- Direct commits to main appear common for fixes

## Maintenance Tasks

### Regular Tasks

1. Monitor error logs for patterns
2. Check database performance metrics
3. Review and clean old session data
4. Update dependencies for security patches
5. Backup database regularly

### Routine Directory Cleanup and Documentation Updates

**IMPORTANT**: Perform these maintenance tasks regularly to keep the project organized.

#### 1. Directory Cleanup Checklist

```bash
# Check for files in wrong locations
ls django_migration/*.log  # Log files should be in logs/
ls django_migration/*.md   # Check if docs belong in docs/ or logs/

# Common cleanup patterns:
# - Move *.log files to logs/
# - Move phase logs (PHASE*_LOG.md) to logs/
# - Move documentation (guides, plans) to docs/
# - Keep only README.md in root directories
```

#### 2. CLAUDE.md Update Process

When significant changes occur:

1. **Review Current Status**: Check migration phases, completed features
2. **Update Progress Sections**: Mark completed tasks, add new ones
3. **Update File Structure**: Reflect new files and directories
4. **Update Command Lists**: Add new commands, remove obsolete ones
5. **Update Key Documents**: Add references to new logs and guides

#### 3. Log Creation Guidelines

After major work sessions:

1. **Create Activity Logs**: Document what was changed and why
2. **Use Consistent Naming**: 
   - Phase logs: `PHASE[N]_[DESCRIPTION]_LOG.md`
   - Feature logs: `[FEATURE]_IMPLEMENTATION_LOG.md`
   - Cleanup logs: `[TYPE]_CLEANUP_LOG.md`
3. **Include Key Information**:
   - Date and author
   - Summary of changes
   - Files affected
   - Next steps

#### 4. When to Perform Cleanup

- After completing a development phase
- Before starting major new features
- When multiple similar files accumulate
- After significant API or structure changes
- As part of regular maintenance routine