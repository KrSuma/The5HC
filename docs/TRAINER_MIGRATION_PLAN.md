# Trainer Migration Plan

## Overview

This document outlines the migration plan for converting the existing single-trainer system to a multi-trainer system with proper organization support.

## Current State

- The system currently uses `AUTH_USER_MODEL` (User) as the trainer reference in all models
- Models affected: Client, Assessment, SessionPackage, Session, Payment, FeeAuditLog
- Trainer models (Organization, Trainer, TrainerInvitation) have been created and migrated

## Migration Strategy

### Phase 1: Create Trainer Infrastructure ✅ COMPLETE
1. Created Organization model
2. Created Trainer model with OneToOne relationship to User
3. Created TrainerInvitation model
4. Created default organization and trainer profiles for existing users

### Phase 2: Foreign Key Migration (IN PROGRESS)
Due to Django's limitations with changing foreign key types, we need a custom approach:

#### Option 1: Clean Migration (Recommended for Development)
1. Export all existing data
2. Update all models to use `trainer = models.ForeignKey('trainers.Trainer'...)`
3. Drop and recreate the database
4. Run fresh migrations
5. Import data with updated foreign key references

#### Option 2: Gradual Migration (For Production)
1. Add temporary fields (trainer_profile) to all affected models
2. Create data migration to populate temporary fields
3. Remove old trainer fields
4. Rename temporary fields to 'trainer'
5. Add indexes

### Phase 3: Add Indexes ✅ COMPLETE
- Added indexes for Trainer model fields
- Added indexes for Organization slug
- Added indexes for TrainerInvitation lookup fields

### Phase 4: Update Application Code
1. Update views to use Trainer instead of User
2. Update forms to handle trainer selection
3. Update templates to display trainer information
4. Update API serializers and views

## Implementation Notes

### For Development Environment
```bash
# 1. Export existing data (if needed)
python manage.py dumpdata --exclude contenttypes --exclude auth.permission > backup.json

# 2. Update models (already done)

# 3. Create fresh migrations
python manage.py makemigrations

# 4. Apply migrations
python manage.py migrate

# 5. Create superuser and test
python manage.py createsuperuser
```

### For Production Environment
A more careful migration approach is needed:
1. Create comprehensive data migration scripts
2. Test on staging environment
3. Schedule downtime for migration
4. Run migrations with backup strategy

## Model Changes Summary

### Client Model
```python
# Old
trainer = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New  
trainer = models.ForeignKey('trainers.Trainer'...)
```

### Assessment Model
```python
# Old
trainer = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New
trainer = models.ForeignKey('trainers.Trainer'...)
```

### SessionPackage Model
```python
# Old
trainer = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New
trainer = models.ForeignKey('trainers.Trainer'...)
```

### Session Model
```python
# Old
trainer = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New
trainer = models.ForeignKey('trainers.Trainer'...)
```

### Payment Model
```python
# Old
trainer = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New
trainer = models.ForeignKey('trainers.Trainer'...)
```

### FeeAuditLog Model
```python
# Old
created_by = models.ForeignKey(settings.AUTH_USER_MODEL...)

# New
created_by = models.ForeignKey('trainers.Trainer'...)
```

## Next Steps

1. Decision needed on migration approach (clean vs gradual)
2. Create data migration scripts if using gradual approach
3. Update all views and forms to use Trainer model
4. Test thoroughly before production deployment