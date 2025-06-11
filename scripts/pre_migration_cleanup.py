#!/usr/bin/env python
"""
Pre-Migration Cleanup Script
Prepares the Streamlit database for Django migration by:
1. Merging duplicate tables (sessions/training_sessions, payments/payment_records)
2. Fixing missing foreign key relationships
3. Ensuring data integrity
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class PreMigrationCleanup:
    """Performs pre-migration cleanup tasks on Streamlit database"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cleanup_log = {
            'timestamp': datetime.now().isoformat(),
            'tasks': [],
            'errors': [],
            'warnings': []
        }
    
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            self.cleanup_log['errors'].append(str(e))
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def backup_database(self):
        """Create a backup of the database before cleanup"""
        try:
            backup_path = Path(self.db_path).parent / f"fitness_assessment_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # Use SQLite backup API
            backup_conn = sqlite3.connect(str(backup_path))
            with backup_conn:
                self.conn.backup(backup_conn)
            backup_conn.close()
            
            print(f"✅ Database backed up to: {backup_path}")
            self.cleanup_log['tasks'].append({
                'task': 'backup_database',
                'status': 'success',
                'backup_path': str(backup_path)
            })
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            self.cleanup_log['errors'].append(f"Backup failed: {e}")
            return False
    
    def merge_session_tables(self):
        """Merge sessions and training_sessions tables"""
        print("\n📋 Merging session tables...")
        cursor = self.conn.cursor()
        
        try:
            # Check both tables
            cursor.execute("SELECT COUNT(*) FROM sessions")
            sessions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM training_sessions")
            training_sessions_count = cursor.fetchone()[0]
            
            print(f"  - sessions: {sessions_count} rows")
            print(f"  - training_sessions: {training_sessions_count} rows")
            
            if training_sessions_count == 0:
                print("  ✅ No training_sessions to merge")
                return True
            
            # Get column mapping
            cursor.execute("PRAGMA table_info(sessions)")
            sessions_cols = {col['name'] for col in cursor.fetchall()}
            
            cursor.execute("PRAGMA table_info(training_sessions)")
            training_cols = {col['name'] for col in cursor.fetchall()}
            
            # Common columns (excluding id)
            common_cols = (sessions_cols & training_cols) - {'id'}
            common_cols_str = ', '.join(sorted(common_cols))
            
            # Check for duplicates before merging
            cursor.execute(f"""
                SELECT COUNT(*) FROM training_sessions ts
                WHERE EXISTS (
                    SELECT 1 FROM sessions s
                    WHERE s.client_id = ts.client_id
                    AND s.package_id = ts.package_id
                    AND s.session_date = ts.session_date
                )
            """)
            duplicates = cursor.fetchone()[0]
            
            if duplicates > 0:
                print(f"  ⚠️  Found {duplicates} potential duplicate sessions")
                self.cleanup_log['warnings'].append(f"{duplicates} potential duplicate sessions found")
            
            # Copy non-duplicate training_sessions to sessions
            cursor.execute(f"""
                INSERT INTO sessions ({common_cols_str})
                SELECT {common_cols_str}
                FROM training_sessions ts
                WHERE NOT EXISTS (
                    SELECT 1 FROM sessions s
                    WHERE s.client_id = ts.client_id
                    AND s.package_id = ts.package_id
                    AND s.session_date = ts.session_date
                )
            """)
            
            rows_copied = cursor.rowcount
            print(f"  ✅ Copied {rows_copied} unique rows from training_sessions")
            
            # Drop training_sessions table
            cursor.execute("DROP TABLE training_sessions")
            print("  ✅ Dropped training_sessions table")
            
            self.conn.commit()
            
            self.cleanup_log['tasks'].append({
                'task': 'merge_session_tables',
                'status': 'success',
                'rows_merged': rows_copied,
                'duplicates_skipped': duplicates
            })
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error merging session tables: {e}")
            self.cleanup_log['errors'].append(f"Session merge failed: {e}")
            self.conn.rollback()
            return False
    
    def merge_payment_tables(self):
        """Merge payments and payment_records tables"""
        print("\n📋 Merging payment tables...")
        cursor = self.conn.cursor()
        
        try:
            # Check both tables
            cursor.execute("SELECT COUNT(*) FROM payments")
            payments_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM payment_records")
            payment_records_count = cursor.fetchone()[0]
            
            print(f"  - payments: {payments_count} rows")
            print(f"  - payment_records: {payment_records_count} rows")
            
            if payment_records_count == 0:
                print("  ✅ No payment_records to merge")
                return True
            
            # Get column mapping
            cursor.execute("PRAGMA table_info(payments)")
            payments_cols = {col['name'] for col in cursor.fetchall()}
            
            cursor.execute("PRAGMA table_info(payment_records)")
            records_cols = {col['name'] for col in cursor.fetchall()}
            
            # Map payment_records columns to payments columns
            column_mapping = {
                'id': 'id',
                'client_id': 'client_id',
                'trainer_id': 'trainer_id',
                'package_id': 'package_id',
                'amount': 'amount',
                'payment_method': 'payment_method',
                'payment_date': 'payment_date',
                'description': 'description',
                'created_at': 'created_at'
            }
            
            # Build insert query with proper column mapping
            source_cols = []
            target_cols = []
            
            for rec_col, pay_col in column_mapping.items():
                if rec_col in records_cols and pay_col in payments_cols and rec_col != 'id':
                    source_cols.append(rec_col)
                    target_cols.append(pay_col)
            
            # Check for duplicates
            cursor.execute(f"""
                SELECT COUNT(*) FROM payment_records pr
                WHERE EXISTS (
                    SELECT 1 FROM payments p
                    WHERE p.client_id = pr.client_id
                    AND p.amount = pr.amount
                    AND p.payment_date = pr.payment_date
                )
            """)
            duplicates = cursor.fetchone()[0]
            
            if duplicates > 0:
                print(f"  ⚠️  Found {duplicates} potential duplicate payments")
                self.cleanup_log['warnings'].append(f"{duplicates} potential duplicate payments found")
            
            # Copy non-duplicate payment_records to payments
            source_cols_str = ', '.join(source_cols)
            target_cols_str = ', '.join(target_cols)
            
            cursor.execute(f"""
                INSERT INTO payments ({target_cols_str})
                SELECT {source_cols_str}
                FROM payment_records pr
                WHERE NOT EXISTS (
                    SELECT 1 FROM payments p
                    WHERE p.client_id = pr.client_id
                    AND p.amount = pr.amount
                    AND p.payment_date = pr.payment_date
                )
            """)
            
            rows_copied = cursor.rowcount
            print(f"  ✅ Copied {rows_copied} unique rows from payment_records")
            
            # Drop payment_records table
            cursor.execute("DROP TABLE payment_records")
            print("  ✅ Dropped payment_records table")
            
            self.conn.commit()
            
            self.cleanup_log['tasks'].append({
                'task': 'merge_payment_tables',
                'status': 'success',
                'rows_merged': rows_copied,
                'duplicates_skipped': duplicates
            })
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error merging payment tables: {e}")
            self.cleanup_log['errors'].append(f"Payment merge failed: {e}")
            self.conn.rollback()
            return False
    
    def fix_missing_trainer_ids(self):
        """Fix missing trainer_id values in related tables"""
        print("\n📋 Fixing missing trainer_id values...")
        cursor = self.conn.cursor()
        
        tables_to_fix = ['sessions', 'payments']
        total_fixed = 0
        
        try:
            for table in tables_to_fix:
                # Check if table exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    continue
                
                # Count missing trainer_ids
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE trainer_id IS NULL")
                missing_count = cursor.fetchone()[0]
                
                if missing_count > 0:
                    print(f"  - {table}: {missing_count} missing trainer_id values")
                    
                    # Update based on client's trainer
                    cursor.execute(f"""
                        UPDATE {table}
                        SET trainer_id = (
                            SELECT trainer_id 
                            FROM clients 
                            WHERE clients.id = {table}.client_id
                        )
                        WHERE trainer_id IS NULL
                    """)
                    
                    fixed = cursor.rowcount
                    total_fixed += fixed
                    print(f"    ✅ Fixed {fixed} records")
                else:
                    print(f"  - {table}: ✅ No missing trainer_id values")
            
            self.conn.commit()
            
            self.cleanup_log['tasks'].append({
                'task': 'fix_missing_trainer_ids',
                'status': 'success',
                'records_fixed': total_fixed
            })
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error fixing trainer_ids: {e}")
            self.cleanup_log['errors'].append(f"Fix trainer_ids failed: {e}")
            self.conn.rollback()
            return False
    
    def verify_data_integrity(self):
        """Verify data integrity after cleanup"""
        print("\n🔍 Verifying data integrity...")
        cursor = self.conn.cursor()
        
        issues = []
        
        # Check for orphaned records
        checks = [
            ("Orphaned clients", """
                SELECT COUNT(*) FROM clients c 
                LEFT JOIN trainers t ON c.trainer_id = t.id 
                WHERE t.id IS NULL
            """),
            ("Orphaned assessments", """
                SELECT COUNT(*) FROM assessments a 
                LEFT JOIN clients c ON a.client_id = c.id 
                WHERE c.id IS NULL
            """),
            ("Orphaned sessions", """
                SELECT COUNT(*) FROM sessions s 
                LEFT JOIN session_packages p ON s.package_id = p.id 
                WHERE p.id IS NULL
            """),
            ("Orphaned payments", """
                SELECT COUNT(*) FROM payments p 
                LEFT JOIN clients c ON p.client_id = c.id 
                WHERE c.id IS NULL
            """)
        ]
        
        for check_name, query in checks:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count > 0:
                issues.append(f"{check_name}: {count}")
                print(f"  ❌ {check_name}: {count}")
            else:
                print(f"  ✅ {check_name}: 0")
        
        # Check duplicate emails
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT email FROM trainers 
                GROUP BY email 
                HAVING COUNT(*) > 1
            )
        """)
        dup_emails = cursor.fetchone()[0]
        if dup_emails > 0:
            issues.append(f"Duplicate emails: {dup_emails}")
            print(f"  ❌ Duplicate emails: {dup_emails}")
        else:
            print(f"  ✅ No duplicate emails")
        
        if issues:
            self.cleanup_log['warnings'].extend(issues)
        
        return len(issues) == 0
    
    def save_cleanup_log(self):
        """Save cleanup log to file"""
        log_path = Path(__file__).parent / 'pre_migration_cleanup_log.json'
        
        with open(log_path, 'w') as f:
            json.dump(self.cleanup_log, f, indent=2)
        
        print(f"\n💾 Cleanup log saved to: {log_path}")
    
    def run(self):
        """Run all pre-migration cleanup tasks"""
        print("\n🚀 Starting Pre-Migration Cleanup")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Backup database first
            if not self.backup_database():
                print("\n❌ Backup failed - aborting cleanup")
                return False
            
            # Run cleanup tasks
            tasks = [
                ("Merge session tables", self.merge_session_tables),
                ("Merge payment tables", self.merge_payment_tables),
                ("Fix missing trainer IDs", self.fix_missing_trainer_ids),
                ("Verify data integrity", self.verify_data_integrity)
            ]
            
            all_success = True
            for task_name, task_func in tasks:
                if not task_func():
                    all_success = False
                    print(f"\n⚠️  {task_name} had issues")
            
            # Save log
            self.save_cleanup_log()
            
            # Summary
            print("\n📊 Cleanup Summary:")
            print(f"  - Tasks completed: {len([t for t in self.cleanup_log['tasks'] if t['status'] == 'success'])}")
            print(f"  - Errors: {len(self.cleanup_log['errors'])}")
            print(f"  - Warnings: {len(self.cleanup_log['warnings'])}")
            
            if all_success:
                print("\n✅ Pre-migration cleanup completed successfully!")
            else:
                print("\n⚠️  Cleanup completed with some issues - review log for details")
            
            return all_success
            
        except Exception as e:
            print(f"\n❌ Cleanup failed: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup_log['errors'].append(f"Fatal error: {e}")
            self.save_cleanup_log()
            return False
        finally:
            self.disconnect()


def main():
    """Main function"""
    # Find database path
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / 'data' / 'fitness_assessment.db'
    
    if not db_path.exists():
        db_path = project_root / 'fitness_assessment.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return 1
    
    # Confirm before running
    print(f"Database: {db_path}")
    print("\nThis script will:")
    print("1. Create a backup of the database")
    print("2. Merge duplicate tables (sessions/training_sessions, payments/payment_records)")
    print("3. Fix missing foreign key relationships")
    print("4. Verify data integrity")
    print("\n⚠️  This will modify the database structure!")
    
    response = input("\nProceed with cleanup? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cleanup cancelled")
        return 1
    
    # Run cleanup
    cleanup = PreMigrationCleanup(str(db_path))
    success = cleanup.run()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())