#!/usr/bin/env python
"""
Data Issues Analysis Script
Identifies and reports specific data issues that need to be resolved before migration
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class DataIssuesAnalyzer:
    """Analyzes specific data issues in the Streamlit database"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.issues = {
            'duplicate_tables': [],
            'duplicate_data': [],
            'missing_data': [],
            'data_inconsistencies': [],
            'migration_conflicts': [],
            'recommendations': []
        }
    
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def analyze_duplicate_tables(self):
        """Identify duplicate table structures"""
        print("\n🔍 Analyzing duplicate tables...")
        cursor = self.conn.cursor()
        
        # Check sessions vs training_sessions
        cursor.execute("SELECT COUNT(*) FROM sessions")
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM training_sessions")
        training_sessions_count = cursor.fetchone()[0]
        
        print(f"  - sessions table: {sessions_count} rows")
        print(f"  - training_sessions table: {training_sessions_count} rows")
        
        # Compare schemas
        cursor.execute("PRAGMA table_info(sessions)")
        sessions_schema = {col['name']: col['type'] for col in cursor.fetchall()}
        
        cursor.execute("PRAGMA table_info(training_sessions)")
        training_sessions_schema = {col['name']: col['type'] for col in cursor.fetchall()}
        
        if sessions_count > 0 and training_sessions_count > 0:
            self.issues['duplicate_tables'].append({
                'tables': ['sessions', 'training_sessions'],
                'issue': 'Both tables contain data',
                'recommendation': 'Merge data from both tables during migration'
            })
        
        # Check payments vs payment_records
        cursor.execute("SELECT COUNT(*) FROM payments")
        payments_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payment_records")
        payment_records_count = cursor.fetchone()[0]
        
        print(f"  - payments table: {payments_count} rows")
        print(f"  - payment_records table: {payment_records_count} rows")
        
        if payments_count > 0 and payment_records_count > 0:
            self.issues['duplicate_tables'].append({
                'tables': ['payments', 'payment_records'],
                'issue': 'Both tables contain data',
                'recommendation': 'Merge data from both tables during migration'
            })
    
    def analyze_duplicate_emails(self):
        """Find duplicate emails in trainers table"""
        print("\n🔍 Checking for duplicate emails...")
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT email, GROUP_CONCAT(username) as usernames, COUNT(*) as count
            FROM trainers
            GROUP BY email
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        for dup in duplicates:
            print(f"  - Email '{dup['email']}' used by: {dup['usernames']}")
            self.issues['duplicate_data'].append({
                'table': 'trainers',
                'field': 'email',
                'value': dup['email'],
                'usernames': dup['usernames'],
                'recommendation': 'Update duplicate emails to be unique before migration'
            })
    
    def analyze_missing_relationships(self):
        """Check for missing foreign key relationships"""
        print("\n🔍 Checking for missing relationships...")
        cursor = self.conn.cursor()
        
        # Check sessions without trainer_id
        cursor.execute("""
            SELECT COUNT(*) FROM sessions WHERE trainer_id IS NULL
        """)
        sessions_missing_trainer = cursor.fetchone()[0]
        
        if sessions_missing_trainer > 0:
            print(f"  - {sessions_missing_trainer} sessions without trainer_id")
            self.issues['missing_data'].append({
                'table': 'sessions',
                'field': 'trainer_id',
                'count': sessions_missing_trainer,
                'recommendation': 'Infer trainer_id from client relationship'
            })
        
        # Check payments without trainer_id
        cursor.execute("""
            SELECT COUNT(*) FROM payments WHERE trainer_id IS NULL
        """)
        payments_missing_trainer = cursor.fetchone()[0]
        
        if payments_missing_trainer > 0:
            print(f"  - {payments_missing_trainer} payments without trainer_id")
            self.issues['missing_data'].append({
                'table': 'payments',
                'field': 'trainer_id',
                'count': payments_missing_trainer,
                'recommendation': 'Infer trainer_id from client relationship'
            })
    
    def analyze_data_types(self):
        """Check for data type inconsistencies"""
        print("\n🔍 Checking data type consistency...")
        cursor = self.conn.cursor()
        
        # Check date formats
        tables_with_dates = {
            'assessments': ['date'],
            'sessions': ['session_date'],
            'training_sessions': ['session_date'],
            'payments': ['payment_date'],
            'payment_records': ['payment_date']
        }
        
        for table, date_fields in tables_with_dates.items():
            for field in date_fields:
                try:
                    cursor.execute(f"""
                        SELECT {field}, COUNT(*) as count
                        FROM {table}
                        WHERE {field} IS NOT NULL
                        GROUP BY date({field})
                        HAVING count > 0
                        LIMIT 1
                    """)
                    sample = cursor.fetchone()
                    if sample:
                        print(f"  - {table}.{field} sample: {sample[field]}")
                except Exception as e:
                    print(f"  - ⚠️  {table}.{field} has inconsistent date format")
                    self.issues['data_inconsistencies'].append({
                        'table': table,
                        'field': field,
                        'issue': 'Inconsistent date format',
                        'recommendation': 'Standardize date format during migration'
                    })
    
    def analyze_fee_data(self):
        """Analyze fee calculation data"""
        print("\n🔍 Analyzing fee data...")
        cursor = self.conn.cursor()
        
        # Check session_packages with missing fee data
        cursor.execute("""
            SELECT COUNT(*) 
            FROM session_packages 
            WHERE gross_amount IS NULL 
            AND total_amount IS NOT NULL
        """)
        missing_fee_data = cursor.fetchone()[0]
        
        if missing_fee_data > 0:
            print(f"  - {missing_fee_data} packages without fee breakdown")
            self.issues['missing_data'].append({
                'table': 'session_packages',
                'field': 'fee_columns',
                'count': missing_fee_data,
                'recommendation': 'Run fee migration script before Django migration'
            })
        
        # Check for inconsistent amounts
        cursor.execute("""
            SELECT COUNT(*)
            FROM session_packages
            WHERE gross_amount IS NOT NULL
            AND total_amount != gross_amount
        """)
        inconsistent_amounts = cursor.fetchone()[0]
        
        if inconsistent_amounts > 0:
            print(f"  - {inconsistent_amounts} packages with inconsistent amounts")
            self.issues['data_inconsistencies'].append({
                'table': 'session_packages',
                'field': 'amount_fields',
                'count': inconsistent_amounts,
                'recommendation': 'Review and reconcile amount discrepancies'
            })
    
    def generate_recommendations(self):
        """Generate specific recommendations for data cleanup"""
        print("\n📋 Generating recommendations...")
        
        # Priority 1: Fix duplicate emails
        if any(issue['field'] == 'email' for issue in self.issues['duplicate_data']):
            self.issues['recommendations'].append({
                'priority': 1,
                'action': 'Fix duplicate emails in trainers table',
                'script': 'fix_duplicate_emails.py',
                'description': 'Update duplicate emails to be unique (e.g., append numbers)'
            })
        
        # Priority 2: Merge duplicate tables
        if self.issues['duplicate_tables']:
            self.issues['recommendations'].append({
                'priority': 2,
                'action': 'Merge duplicate table data',
                'script': 'merge_duplicate_tables.py',
                'description': 'Combine data from sessions/training_sessions and payments/payment_records'
            })
        
        # Priority 3: Fix missing relationships
        if self.issues['missing_data']:
            self.issues['recommendations'].append({
                'priority': 3,
                'action': 'Fix missing foreign keys',
                'script': 'fix_missing_relationships.py',
                'description': 'Populate missing trainer_id values based on client relationships'
            })
        
        # Priority 4: Run fee migration
        if any(issue['field'] == 'fee_columns' for issue in self.issues['missing_data']):
            self.issues['recommendations'].append({
                'priority': 4,
                'action': 'Run fee migration',
                'script': 'run_fee_migration.py',
                'description': 'Calculate and populate fee breakdown columns'
            })
    
    def save_report(self, output_path: str):
        """Save issues report to JSON file"""
        report = {
            'analysis_date': datetime.now().isoformat(),
            'database': self.db_path,
            'issues': self.issues,
            'summary': {
                'total_issues': sum(len(v) for v in self.issues.values() if isinstance(v, list)),
                'critical_issues': len(self.issues['duplicate_data']) + len(self.issues['duplicate_tables']),
                'recommendations_count': len(self.issues['recommendations'])
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved to: {output_path}")
    
    def run_analysis(self):
        """Run complete data issues analysis"""
        print("\n🚀 Starting Data Issues Analysis")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            self.analyze_duplicate_tables()
            self.analyze_duplicate_emails()
            self.analyze_missing_relationships()
            self.analyze_data_types()
            self.analyze_fee_data()
            self.generate_recommendations()
            
            # Save report
            output_path = Path(__file__).parent / 'data_issues_report.json'
            self.save_report(str(output_path))
            
            # Print summary
            print("\n📊 Summary:")
            print(f"  - Total issues found: {sum(len(v) for v in self.issues.values() if isinstance(v, list))}")
            print(f"  - Critical issues: {len(self.issues['duplicate_data']) + len(self.issues['duplicate_tables'])}")
            print(f"  - Recommendations: {len(self.issues['recommendations'])}")
            
            # Print recommendations
            if self.issues['recommendations']:
                print("\n🎯 Recommended Actions (in order):")
                for rec in sorted(self.issues['recommendations'], key=lambda x: x['priority']):
                    print(f"  {rec['priority']}. {rec['action']}")
                    print(f"     → {rec['description']}")
            
            print("\n✅ Analysis complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
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
    
    # Run analysis
    analyzer = DataIssuesAnalyzer(str(db_path))
    success = analyzer.run_analysis()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())