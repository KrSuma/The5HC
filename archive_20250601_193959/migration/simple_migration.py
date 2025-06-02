"""
Simple migration to prepare database for improvements
"""
import shutil
from datetime import datetime
import sqlite3

# Backup existing database
backup_path = f"fitness_assessment.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2("fitness_assessment.db", backup_path)
print(f"✅ Database backed up to: {backup_path}")

# Add new columns if they don't exist
try:
    conn = sqlite3.connect("fitness_assessment.db")
    cursor = conn.cursor()
    
    # Try to add new columns (will fail silently if they already exist)
    migrations = [
        "ALTER TABLE trainers ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE trainers ADD COLUMN last_login TIMESTAMP", 
        "ALTER TABLE trainers ADD COLUMN failed_login_attempts INTEGER DEFAULT 0",
        "ALTER TABLE trainers ADD COLUMN locked_until TIMESTAMP",
    ]
    
    for migration in migrations:
        try:
            cursor.execute(migration)
            print(f"✅ Applied: {migration}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⏭️  Column already exists, skipping")
            else:
                print(f"❌ Error: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Database preparation complete!")
    
except Exception as e:
    print(f"❌ Error during migration: {e}")

print("\n⚠️  Note: All users will need to reset their passwords when using the new secure system.")