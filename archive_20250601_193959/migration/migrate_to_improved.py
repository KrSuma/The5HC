"""
Migration script to transition from old system to improved system
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import logging

from secure_db_utils import hash_password, init_db as init_secure_db
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handle database migration to new secure system"""
    
    def __init__(self, old_db_path: str = "fitness_assessment.db", 
                 new_db_path: str = "fitness_assessment_improved.db"):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        
    def backup_database(self):
        """Create backup of existing database"""
        backup_path = f"{self.old_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(self.old_db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def migrate_schema(self):
        """Migrate database schema to support new features"""
        with sqlite3.connect(self.new_db_path) as conn:
            cursor = conn.cursor()
            
            # Add new columns to trainers table
            migrations = [
                # Add columns for enhanced security
                "ALTER TABLE trainers ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE trainers ADD COLUMN last_login TIMESTAMP",
                "ALTER TABLE trainers ADD COLUMN failed_login_attempts INTEGER DEFAULT 0",
                "ALTER TABLE trainers ADD COLUMN locked_until TIMESTAMP",
                
                # Add columns for better tracking
                "ALTER TABLE clients ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE clients ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                
                "ALTER TABLE assessments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ]
            
            for migration in migrations:
                try:
                    cursor.execute(migration)
                    logger.info(f"Applied migration: {migration[:50]}...")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        logger.info(f"Column already exists, skipping: {migration[:50]}...")
                    else:
                        raise
            
            conn.commit()
    
    def migrate_passwords(self):
        """Migrate passwords from HMAC-SHA256 to bcrypt"""
        logger.warning("""
        ⚠️  IMPORTANT: Password Migration Required
        
        The old system used HMAC-SHA256 for password hashing, while the new system uses bcrypt.
        Since we cannot convert hashed passwords, all users will need to reset their passwords.
        
        Options:
        1. Force password reset on next login
        2. Send password reset emails to all users
        3. Manually set temporary passwords
        """)
        
        with sqlite3.connect(self.new_db_path) as conn:
            cursor = conn.cursor()
            
            # Add a flag to indicate password needs reset
            try:
                cursor.execute("ALTER TABLE trainers ADD COLUMN password_reset_required BOOLEAN DEFAULT 1")
            except sqlite3.OperationalError:
                pass  # Column might already exist
            
            # Mark all existing users as needing password reset
            cursor.execute("UPDATE trainers SET password_reset_required = 1")
            conn.commit()
            
        logger.info("All users marked for password reset on next login")
    
    def migrate_data(self):
        """Copy data from old database to new"""
        # Copy the old database to new location
        shutil.copy2(self.old_db_path, self.new_db_path)
        logger.info(f"Database copied to: {self.new_db_path}")
        
        # Apply schema migrations
        self.migrate_schema()
        
        # Handle password migration
        self.migrate_passwords()
        
        # Create indexes for performance
        self.create_indexes()
    
    def create_indexes(self):
        """Create performance indexes"""
        with sqlite3.connect(self.new_db_path) as conn:
            cursor = conn.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_clients_trainer ON clients(trainer_id)",
                "CREATE INDEX IF NOT EXISTS idx_assessments_trainer ON assessments(trainer_id)",
                "CREATE INDEX IF NOT EXISTS idx_assessments_client ON assessments(client_id)",
                "CREATE INDEX IF NOT EXISTS idx_assessments_date ON assessments(date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_trainers_username ON trainers(username)",
            ]
            
            for index in indexes:
                cursor.execute(index)
                logger.info(f"Created index: {index}")
            
            conn.commit()
    
    def verify_migration(self):
        """Verify migration was successful"""
        with sqlite3.connect(self.new_db_path) as conn:
            cursor = conn.cursor()
            
            # Check row counts
            tables = ['trainers', 'clients', 'assessments']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"{table}: {count} rows")
            
            # Check new columns exist
            cursor.execute("PRAGMA table_info(trainers)")
            columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = ['created_at', 'last_login', 'failed_login_attempts', 'locked_until']
            for col in required_columns:
                if col in columns:
                    logger.info(f"✓ Column {col} exists in trainers table")
                else:
                    logger.error(f"✗ Column {col} missing from trainers table")
                    return False
        
        return True
    
    def run_migration(self):
        """Run complete migration process"""
        logger.info("Starting database migration...")
        
        try:
            # 1. Backup existing database
            backup_path = self.backup_database()
            
            # 2. Migrate data and schema
            self.migrate_data()
            
            # 3. Verify migration
            if self.verify_migration():
                logger.info("✅ Migration completed successfully!")
                logger.info(f"New database: {self.new_db_path}")
                logger.info(f"Backup saved: {backup_path}")
                
                # Update config to use new database
                config.database.path = self.new_db_path
                
                return True
            else:
                logger.error("❌ Migration verification failed!")
                return False
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False


class CodeMigration:
    """Guide for migrating code to use new modules"""
    
    @staticmethod
    def generate_migration_guide():
        """Generate migration guide for developers"""
        guide = """
# Code Migration Guide

## 1. Update Imports

Replace old imports with new secure modules:

```python
# Old
import improved_db_utils as db_utils
import service_layer

# New
from secure_db_utils import init_db, get_db_connection
from improved_service_layer import (
    AuthService, ClientService, AssessmentService,
    DashboardService, AnalyticsService
)
from session_manager import session_manager, login_required
from config import config
```

## 2. Update Authentication

```python
# Old
success = service_layer.AuthService.login(username, password)

# New
success, message = AuthService.login(username, password)
if success:
    st.success(message)
else:
    st.error(message)
```

## 3. Add Session Management

```python
# Add to main.py
from session_manager import auto_logout_check, show_session_timeout_warning

# In your main app
auto_logout_check()
show_session_timeout_warning()
```

## 4. Update Database Calls

```python
# Old
clients = db_utils.get_clients(trainer_id)

# New (with caching)
clients = ClientService.get_trainer_clients(trainer_id)
```

## 5. Use Configuration

```python
# Old
DB_PATH = "fitness_assessment.db"
FONT_PATH = "NanumGothic.ttf"

# New
from config import config
db_path = config.database.path
font_path = config.get_font_path()
```

## 6. Add Logging

```python
# Add to services
from logging_config import app_logger, error_logger

try:
    # Your code
    app_logger.info("Operation successful")
except Exception as e:
    error_logger.log_error(e, context={'operation': 'name'})
```

## 7. Protected Routes

```python
# Add to pages that require login
from session_manager import login_required

@login_required
def protected_page():
    # Your page code
```
"""
        return guide
    
    @staticmethod
    def create_migration_checklist():
        """Create checklist for migration"""
        checklist = """
# Migration Checklist

## Pre-Migration
- [ ] Backup all data
- [ ] Review current customizations
- [ ] Test in development environment
- [ ] Notify users of planned downtime

## Database Migration
- [ ] Run migration script
- [ ] Verify data integrity
- [ ] Test database connections
- [ ] Update connection strings

## Code Updates
- [ ] Update imports in all files
- [ ] Add session management
- [ ] Implement new security features
- [ ] Update service layer calls
- [ ] Add error handling and logging

## Configuration
- [ ] Create .env file for sensitive data
- [ ] Update configuration values
- [ ] Set appropriate security settings
- [ ] Configure logging levels

## Testing
- [ ] Test authentication flow
- [ ] Test all CRUD operations
- [ ] Verify caching works
- [ ] Check session timeouts
- [ ] Test rate limiting

## Deployment
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Monitor logs for errors
- [ ] Deploy to production
- [ ] Monitor performance

## Post-Migration
- [ ] Force password resets
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Document any issues
"""
        return checklist


def main():
    """Run migration process"""
    print("""
    🚀 Fitness Assessment System Migration Tool
    
    This tool will help you migrate from the old system to the new improved system.
    
    Features of the new system:
    - Bcrypt password hashing
    - Session management with timeouts
    - Comprehensive logging
    - Database abstraction layer
    - Caching for better performance
    - Centralized configuration
    
    """)
    
    # Ask for confirmation
    response = input("Do you want to proceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    # Run database migration
    migration = DatabaseMigration()
    if migration.run_migration():
        print("\n✅ Database migration completed!")
        
        # Generate migration guide
        guide = CodeMigration.generate_migration_guide()
        with open("MIGRATION_GUIDE.md", "w") as f:
            f.write(guide)
        print("📄 Migration guide saved to MIGRATION_GUIDE.md")
        
        # Generate checklist
        checklist = CodeMigration.create_migration_checklist()
        with open("MIGRATION_CHECKLIST.md", "w") as f:
            f.write(checklist)
        print("📋 Migration checklist saved to MIGRATION_CHECKLIST.md")
        
        print("\n⚠️  Important Next Steps:")
        print("1. All users must reset their passwords")
        print("2. Update your code to use new imports")
        print("3. Test thoroughly before deploying")
        print("4. Monitor logs for any issues")
        
    else:
        print("\n❌ Migration failed! Check logs for details.")


if __name__ == "__main__":
    main()