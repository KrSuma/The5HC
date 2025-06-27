# Phase 4 - Data Migration Plan

**Date**: 2025-01-09
**Author**: Claude
**Phase**: Phase 4 - Data Migration

## Executive Summary

This document outlines the comprehensive plan for migrating data from the Streamlit SQLite database to the Django PostgreSQL database. The analysis has identified 42 rows across 9 tables, with several data quality issues that need to be addressed before migration.

## Database Analysis Results

### Table Summary
- **Total Tables**: 9 (with 2 sets of duplicate tables)
- **Total Rows**: 42
- **Database Size**: 0.11 MB
- **Critical Issues**: 3 (duplicate emails, duplicate tables)

### Table Inventory

| Streamlit Table | Django Model | Row Count | Status |
|----------------|--------------|-----------|---------|
| trainers | accounts.User | 7 | ⚠️ Duplicate emails |
| clients | clients.Client | 10 | ✅ Ready |
| assessments | assessments.Assessment | 7 | ✅ Ready |
| session_packages | sessions.SessionPackage | 5 | ✅ Ready |
| sessions | sessions.Session | 4 | ⚠️ Duplicate with training_sessions |
| training_sessions | sessions.Session | 3 | ⚠️ Duplicate with sessions |
| payments | sessions.Payment | 4 | ⚠️ Duplicate with payment_records |
| payment_records | sessions.Payment | 2 | ⚠️ Duplicate with payments |
| fee_audit_log | sessions.FeeAuditLog | 0 | ✅ Empty |

## Critical Issues to Resolve

### 1. Duplicate Email (Priority: HIGH)
- **Issue**: Email 'jaesun9090@gmail.com' is used by usernames: 'criminal' and 'jaesun9090'
- **Impact**: Django User model requires unique emails
- **Resolution**: Update one of the duplicate emails before migration

### 2. Duplicate Tables (Priority: HIGH)
- **Sessions Tables**: 
  - `sessions` (4 rows) and `training_sessions` (3 rows)
  - Need to merge into single dataset
- **Payment Tables**:
  - `payments` (4 rows) and `payment_records` (2 rows)
  - Need to merge into single dataset

### 3. Data Type Consistency (Priority: MEDIUM)
- All date fields appear to be in consistent ISO format (YYYY-MM-DD)
- No immediate action required

### 4. Missing Relationships (Priority: LOW)
- Some sessions and payments might be missing trainer_id
- Can be inferred from client relationships during migration

## Migration Strategy

### Pre-Migration Tasks

1. **Fix Duplicate Emails**
   ```sql
   -- Update duplicate email for user 'criminal'
   UPDATE trainers 
   SET email = 'criminal@example.com' 
   WHERE username = 'criminal';
   ```

2. **Merge Duplicate Tables**
   - Combine sessions + training_sessions
   - Combine payments + payment_records
   - Ensure no duplicate records

3. **Run Fee Migration** (if not already done)
   ```bash
   python run_fee_migration.py
   ```

### Migration Order

1. **trainers** → accounts.User (7 rows)
   - Map fields to Django User model
   - Preserve password hashes
   - Handle authentication fields

2. **clients** → clients.Client (10 rows)
   - Direct field mapping
   - Maintain trainer relationships

3. **assessments** → assessments.Assessment (7 rows)
   - Map all 27 test fields
   - Preserve scores and notes

4. **session_packages** → sessions.SessionPackage (5 rows)
   - Include fee calculation fields
   - Maintain active status

5. **sessions** (merged) → sessions.Session (7 rows total)
   - Merge data from both tables
   - Ensure unique records

6. **payments** (merged) → sessions.Payment (6 rows total)
   - Merge data from both tables
   - Include fee breakdowns

7. **fee_audit_log** → sessions.FeeAuditLog (0 rows)
   - Table structure only

## Field Mapping Details

### Trainers → User
```python
{
    'id': 'id',
    'username': 'username',
    'password_hash': 'password',  # Already hashed
    'name': 'first_name + last_name',  # Split name
    'email': 'email',
    'created_at': 'date_joined',
    'last_login': 'last_login',
    'failed_login_attempts': 'custom field',
    'locked_until': 'custom field'
}
```

### Key Considerations

1. **User Model**: Django's User model expects first_name and last_name separately
2. **Password**: Already bcrypt hashed, compatible with Django
3. **Timestamps**: Convert to timezone-aware datetime
4. **Foreign Keys**: Maintain referential integrity

## Data Validation Checklist

- [ ] All trainers have unique emails
- [ ] All clients have valid trainer references
- [ ] All assessments have valid client and trainer references
- [ ] All session packages have valid client references
- [ ] All sessions have valid package references
- [ ] All payments have valid client references
- [ ] Date formats are consistent
- [ ] Numeric fields are within valid ranges

## Migration Scripts

### 1. Pre-Migration Cleanup Script
- Fix duplicate emails
- Merge duplicate tables
- Validate data integrity

### 2. Main Migration Script
- Read from Streamlit SQLite
- Transform data to Django models
- Write to Django database
- Maintain relationships

### 3. Post-Migration Validation Script
- Verify row counts
- Check relationships
- Validate data integrity
- Generate migration report

## Risk Mitigation

1. **Backup Strategy**
   - Backup Streamlit database before migration
   - Backup Django database before migration
   - Keep transaction logs

2. **Rollback Plan**
   - Django migrations can be reversed
   - Keep original Streamlit database intact
   - Document all transformations

3. **Testing Strategy**
   - Test with sample data first
   - Validate each table after migration
   - Run Django tests post-migration

## Success Criteria

1. All 42 rows successfully migrated
2. No data loss or corruption
3. All relationships maintained
4. Django application functional with migrated data
5. All tests passing

## Next Steps

1. Create and run pre-migration cleanup script
2. Implement main migration script
3. Test migration with sample data
4. Execute full migration
5. Run post-migration validation
6. Update documentation

## Estimated Timeline

- Pre-migration cleanup: 1 hour
- Migration script development: 2-3 hours
- Testing: 1 hour
- Full migration execution: 30 minutes
- Validation: 30 minutes

**Total: 5-6 hours**