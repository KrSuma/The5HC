#!/usr/bin/env python
"""
Fix Duplicate Emails Script
Resolves duplicate email addresses in the trainers table
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class DuplicateEmailFixer:
    """Fixes duplicate email addresses in trainers table"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.changes = []
    
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def find_duplicate_emails(self):
        """Find all duplicate emails in trainers table"""
        cursor = self.conn.cursor()
        
        # Find duplicate emails
        cursor.execute("""
            SELECT email, GROUP_CONCAT(username) as usernames, 
                   GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM trainers
            GROUP BY email
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("✅ No duplicate emails found!")
            return []
        
        duplicate_list = []
        for dup in duplicates:
            duplicate_list.append({
                'email': dup['email'],
                'usernames': dup['usernames'].split(','),
                'ids': [int(id) for id in dup['ids'].split(',')],
                'count': dup['count']
            })
        
        return duplicate_list
    
    def display_duplicates(self, duplicates):
        """Display duplicate emails found"""
        print("\n📋 Duplicate emails found:")
        for i, dup in enumerate(duplicates, 1):
            print(f"\n{i}. Email: {dup['email']}")
            print(f"   Used by {dup['count']} trainers:")
            for j, username in enumerate(dup['usernames']):
                print(f"   - {username} (ID: {dup['ids'][j]})")
    
    def suggest_fixes(self, duplicates):
        """Suggest email fixes for duplicates"""
        suggestions = []
        
        for dup in duplicates:
            email_base = dup['email'].split('@')[0]
            email_domain = dup['email'].split('@')[1]
            
            # Keep the first trainer's email unchanged
            # Modify others by appending numbers
            for i, (username, trainer_id) in enumerate(zip(dup['usernames'], dup['ids'])):
                if i == 0:
                    # Keep first one unchanged
                    continue
                else:
                    # Suggest modified email
                    new_email = f"{email_base}{i}@{email_domain}"
                    suggestions.append({
                        'trainer_id': trainer_id,
                        'username': username,
                        'old_email': dup['email'],
                        'new_email': new_email
                    })
        
        return suggestions
    
    def apply_fixes(self, suggestions, dry_run=True):
        """Apply email fixes to the database"""
        cursor = self.conn.cursor()
        
        print(f"\n{'🔍 DRY RUN - No changes will be made' if dry_run else '⚡ APPLYING FIXES'}")
        print("-" * 60)
        
        for fix in suggestions:
            # Check if new email already exists
            cursor.execute("SELECT COUNT(*) FROM trainers WHERE email = ?", (fix['new_email'],))
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"⚠️  Cannot use {fix['new_email']} - already exists!")
                # Try with timestamp
                timestamp = datetime.now().strftime('%Y%m%d')
                fix['new_email'] = fix['new_email'].replace('@', f'_{timestamp}@')
            
            print(f"Trainer: {fix['username']} (ID: {fix['trainer_id']})")
            print(f"  Old email: {fix['old_email']}")
            print(f"  New email: {fix['new_email']}")
            
            if not dry_run:
                cursor.execute(
                    "UPDATE trainers SET email = ? WHERE id = ?",
                    (fix['new_email'], fix['trainer_id'])
                )
                self.changes.append(fix)
                print("  ✅ Updated!")
            else:
                print("  📝 Would update")
            
            print()
        
        if not dry_run:
            self.conn.commit()
            print(f"✅ Applied {len(self.changes)} email fixes")
    
    def verify_fixes(self):
        """Verify no duplicate emails remain"""
        duplicates = self.find_duplicate_emails()
        
        if not duplicates:
            print("\n✅ Verification passed - no duplicate emails remain!")
            return True
        else:
            print("\n❌ Verification failed - duplicate emails still exist!")
            self.display_duplicates(duplicates)
            return False
    
    def save_changelog(self):
        """Save a log of changes made"""
        if not self.changes:
            return
        
        log_path = Path(__file__).parent / 'email_fixes_changelog.json'
        
        import json
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'database': self.db_path,
            'changes': self.changes,
            'total_fixes': len(self.changes)
        }
        
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n💾 Changelog saved to: {log_path}")
    
    def run(self, dry_run=True):
        """Run the duplicate email fix process"""
        print("\n🚀 Starting Duplicate Email Fix Process")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Find duplicates
            duplicates = self.find_duplicate_emails()
            
            if not duplicates:
                return True
            
            # Display duplicates
            self.display_duplicates(duplicates)
            
            # Generate suggestions
            suggestions = self.suggest_fixes(duplicates)
            
            print("\n💡 Suggested fixes:")
            for sug in suggestions:
                print(f"  - {sug['username']}: {sug['old_email']} → {sug['new_email']}")
            
            # Apply fixes
            if dry_run:
                print("\n" + "=" * 60)
                response = input("\nDo you want to apply these fixes? (yes/no): ")
                if response.lower() in ['yes', 'y']:
                    self.apply_fixes(suggestions, dry_run=False)
                    self.verify_fixes()
                    self.save_changelog()
                else:
                    print("❌ Fixes cancelled")
                    return False
            else:
                self.apply_fixes(suggestions, dry_run=False)
                self.verify_fixes()
                self.save_changelog()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix duplicate emails in trainers table')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--auto', action='store_true', help='Apply fixes automatically without prompting')
    args = parser.parse_args()
    
    # Find database path
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / 'data' / 'fitness_assessment.db'
    
    if not db_path.exists():
        db_path = project_root / 'fitness_assessment.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return 1
    
    # Run fixer
    fixer = DuplicateEmailFixer(str(db_path))
    
    if args.auto:
        success = fixer.run(dry_run=False)
    else:
        success = fixer.run(dry_run=True)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())