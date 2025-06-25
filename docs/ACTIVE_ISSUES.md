# Active Issues & Known Problems

This document tracks currently unresolved issues. For resolved issues, see the fix logs in `logs/maintenance/`.

## High Priority Issues

### 1. MCQ PDF Report Integration
- **Status**: Phase 9 of MCQ implementation pending
- **Impact**: MCQ scores not included in PDF reports
- **Next Steps**: Implement MCQ section in PDF template
- **Related**: `tasks/mcq-implementation-plan.md`

### 2. Integration Test Failures
- **Status**: 11 of 12 integration tests failing
- **Root Cause**: Features not fully implemented
  - Organization switching
  - Audit log signatures
  - Multi-tenant data isolation edge cases
- **Impact**: Cannot verify complete multi-tenant isolation
- **Workaround**: Core data isolation verified working through unit tests

## Medium Priority Issues

### 3. HTMX Navigation in Navbar
- **Status**: Temporarily disabled
- **Issue**: Content replacement causing blank pages
- **Workaround**: Standard navigation working
- **Fix Required**: Proper hx-target specifications

### 4. pytest-asyncio Incompatibility
- **Status**: Removed from requirements.txt
- **Issue**: AttributeError with Package objects
- **Impact**: Cannot test async views
- **Workaround**: Tests run successfully without it

## Low Priority Issues

### 5. Notification Badge Polling
- **Status**: Disabled
- **Issue**: Interferes with HTMX navigation
- **Impact**: No real-time notification updates
- **Future**: Implement WebSocket solution

### 6. Organization Switching
- **Status**: Foundation implemented, UI pending
- **Impact**: Users cannot switch between organizations
- **Workaround**: Single organization per user

### 7. Trainer App Placeholders
- **Status**: Analytics and some views incomplete
- **Components**:
  - Trainer analytics dashboard
  - Advanced permission management
  - Audit log viewer
- **Impact**: Limited trainer management features

## Environment-Specific Issues

### 8. WeasyPrint on macOS Development
- **Status**: Requires manual setup
- **Solution**: Use `./run_with_weasyprint.sh`
- **Permanent Fix**: Update development setup docs

### 9. Korean Translations in Test Environment
- **Status**: Falls back to English in tests
- **Issue**: Locale not compiled in test environment
- **Impact**: Tests show English instead of Korean
- **Workaround**: Tests still pass with fallback

## Technical Debt

### 10. Incomplete Features from Migration
- Session calendar view (basic implementation only)
- Advanced analytics dashboards
- Email notifications
- Trainer invitation workflow UI
- Comprehensive audit logging

### 11. API Documentation
- **Status**: Basic Swagger/ReDoc available
- **Missing**: Detailed endpoint descriptions
- **Impact**: API harder to use without docs

## Monitoring Required

### 12. Performance at Scale
- No performance testing completed
- Database indexes may need optimization
- Query optimization for large datasets pending

## Notes

- Most issues have workarounds in place
- Core functionality is stable and in production
- Focus on completing MCQ implementation first
- Integration test fixes can wait until features complete

For issue resolution history, check:
- `logs/maintenance/` - Bug fixes
- `logs/feature/` - Feature implementations
- `docs/FEATURE_HISTORY.md` - Complete history