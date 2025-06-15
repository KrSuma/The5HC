# Trainer Migration Notes

## Important: Data Migration Required

When migrating from the old system to the new trainer-based system, the following steps need to be taken:

1. **Create Trainer Profiles**: For each existing User in the system, create a corresponding Trainer profile
2. **Update Foreign Keys**: All existing relationships pointing to User need to be updated to point to the new Trainer model

## Manual Migration Steps

Before running migrations in production:

1. Create a default Organization
2. Create Trainer profiles for all existing Users
3. Update all foreign keys in the following tables:
   - clients.trainer -> points to Trainer instead of User
   - assessments.trainer -> points to Trainer instead of User  
   - session_packages.trainer -> points to Trainer instead of User
   - sessions.trainer -> points to Trainer instead of User
   - payments.trainer -> points to Trainer instead of User
   - fee_audit_log.created_by -> points to Trainer instead of User

## Development Note

For development purposes, you may need to:
1. Export existing data
2. Drop and recreate the database
3. Run migrations
4. Import data with updated foreign keys

Or create a custom data migration script to handle the conversion.