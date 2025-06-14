#!/usr/bin/env python
"""
Streamlit Database Analysis Script
Analyzes the existing Streamlit SQLite database to prepare for Django migration
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class StreamlitDatabaseAnalyzer:
    """Analyzes Streamlit database structure and data for migration planning"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.analysis_results = {
            'tables': {},
            'data_integrity': {},
            'migration_plan': {},
            'warnings': [],
            'summary': {}
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
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def analyze_table_structure(self):
        """Analyze the structure of all tables"""
        cursor = self.conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        print("\n📊 Analyzing table structures...")
        
        for table in tables:
            table_name = table['name']
            print(f"\n  Table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Store table structure
            self.analysis_results['tables'][table_name] = {
                'columns': [],
                'foreign_keys': [],
                'row_count': row_count,
                'indexes': []
            }
            
            # Process columns
            for col in columns:
                column_info = {
                    'name': col['name'],
                    'type': col['type'],
                    'not_null': bool(col['notnull']),
                    'default': col['dflt_value'],
                    'primary_key': bool(col['pk'])
                }
                self.analysis_results['tables'][table_name]['columns'].append(column_info)
                print(f"    - {col['name']} ({col['type']}) {'NOT NULL' if col['notnull'] else 'NULL'} {'PK' if col['pk'] else ''}")
            
            # Process foreign keys
            for fk in foreign_keys:
                fk_info = {
                    'column': fk['from'],
                    'references_table': fk['table'],
                    'references_column': fk['to']
                }
                self.analysis_results['tables'][table_name]['foreign_keys'].append(fk_info)
                print(f"    - FK: {fk['from']} -> {fk['table']}.{fk['to']}")
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            for idx in indexes:
                self.analysis_results['tables'][table_name]['indexes'].append({
                    'name': idx['name'],
                    'unique': bool(idx['unique'])
                })
            
            print(f"    - Rows: {row_count}")
    
    def analyze_data_integrity(self):
        """Check data integrity and identify potential issues"""
        cursor = self.conn.cursor()
        print("\n🔍 Checking data integrity...")
        
        # Check trainers table
        if 'trainers' in self.analysis_results['tables']:
            print("\n  Trainers table:")
            
            # Check for duplicate usernames
            cursor.execute("""
                SELECT username, COUNT(*) as count 
                FROM trainers 
                GROUP BY username 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                self.analysis_results['warnings'].append(f"Duplicate usernames found: {duplicates}")
                print(f"    ⚠️  Duplicate usernames: {len(duplicates)}")
            else:
                print("    ✅ No duplicate usernames")
            
            # Check for duplicate emails
            cursor.execute("""
                SELECT email, COUNT(*) as count 
                FROM trainers 
                GROUP BY email 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                self.analysis_results['warnings'].append(f"Duplicate emails found: {duplicates}")
                print(f"    ⚠️  Duplicate emails: {len(duplicates)}")
            else:
                print("    ✅ No duplicate emails")
        
        # Check clients table
        if 'clients' in self.analysis_results['tables']:
            print("\n  Clients table:")
            
            # Check for orphaned clients
            cursor.execute("""
                SELECT COUNT(*) 
                FROM clients c 
                LEFT JOIN trainers t ON c.trainer_id = t.id 
                WHERE t.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                self.analysis_results['warnings'].append(f"{orphaned} orphaned clients without trainers")
                print(f"    ⚠️  Orphaned clients: {orphaned}")
            else:
                print("    ✅ No orphaned clients")
        
        # Check assessments table
        if 'assessments' in self.analysis_results['tables']:
            print("\n  Assessments table:")
            
            # Check for orphaned assessments
            cursor.execute("""
                SELECT COUNT(*) 
                FROM assessments a 
                LEFT JOIN clients c ON a.client_id = c.id 
                WHERE c.id IS NULL
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                self.analysis_results['warnings'].append(f"{orphaned} orphaned assessments without clients")
                print(f"    ⚠️  Orphaned assessments: {orphaned}")
            else:
                print("    ✅ No orphaned assessments")
            
            # Check for missing trainer_id
            cursor.execute("SELECT COUNT(*) FROM assessments WHERE trainer_id IS NULL")
            missing_trainer = cursor.fetchone()[0]
            if missing_trainer > 0:
                self.analysis_results['warnings'].append(f"{missing_trainer} assessments without trainer_id")
                print(f"    ⚠️  Assessments without trainer_id: {missing_trainer}")
        
        # Check session_packages table
        if 'session_packages' in self.analysis_results['tables']:
            print("\n  Session packages table:")
            
            # Check for packages with invalid remaining sessions
            cursor.execute("""
                SELECT COUNT(*) 
                FROM session_packages 
                WHERE remaining_sessions > total_sessions
            """)
            invalid = cursor.fetchone()[0]
            if invalid > 0:
                self.analysis_results['warnings'].append(f"{invalid} packages with remaining > total sessions")
                print(f"    ⚠️  Invalid remaining sessions: {invalid}")
            else:
                print("    ✅ Session counts valid")
        
        # Check for fee columns
        if 'session_packages' in self.analysis_results['tables']:
            columns = [col['name'] for col in self.analysis_results['tables']['session_packages']['columns']]
            fee_columns = ['gross_amount', 'vat_amount', 'card_fee_amount', 'net_amount']
            missing_fee_columns = [col for col in fee_columns if col not in columns]
            
            if missing_fee_columns:
                print(f"    ⚠️  Missing fee columns: {missing_fee_columns}")
                self.analysis_results['warnings'].append(f"Missing fee columns in session_packages: {missing_fee_columns}")
            else:
                print("    ✅ All fee columns present")
    
    def analyze_relationships(self):
        """Analyze table relationships and dependencies"""
        print("\n🔗 Analyzing relationships...")
        
        relationships = {
            'trainers': {
                'has_many': ['clients', 'assessments', 'session_packages', 'sessions', 'payments']
            },
            'clients': {
                'belongs_to': 'trainers',
                'has_many': ['assessments', 'session_packages', 'sessions', 'payments']
            },
            'assessments': {
                'belongs_to': ['clients', 'trainers']
            },
            'session_packages': {
                'belongs_to': ['clients', 'trainers'],
                'has_many': ['sessions', 'payments']
            },
            'sessions': {
                'belongs_to': ['clients', 'session_packages', 'trainers']
            },
            'payments': {
                'belongs_to': ['clients', 'session_packages', 'trainers']
            }
        }
        
        self.analysis_results['migration_plan']['relationships'] = relationships
        
        for table, rels in relationships.items():
            if table in self.analysis_results['tables']:
                print(f"\n  {table}:")
                if 'belongs_to' in rels:
                    if isinstance(rels['belongs_to'], list):
                        for parent in rels['belongs_to']:
                            print(f"    - belongs to {parent}")
                    else:
                        print(f"    - belongs to {rels['belongs_to']}")
                if 'has_many' in rels:
                    for child in rels['has_many']:
                        print(f"    - has many {child}")
    
    def generate_migration_plan(self):
        """Generate a migration plan for Django"""
        print("\n📋 Generating migration plan...")
        
        # Define table to model mapping
        model_mapping = {
            'trainers': 'accounts.User',
            'clients': 'clients.Client',
            'assessments': 'assessments.Assessment',
            'session_packages': 'sessions.SessionPackage',
            'sessions': 'sessions.Session',
            'payments': 'sessions.Payment',
            'fee_audit_log': 'sessions.FeeAuditLog'
        }
        
        # Define field type mappings
        type_mapping = {
            'INTEGER': 'IntegerField',
            'TEXT': 'CharField/TextField',
            'REAL': 'FloatField',
            'DATETIME': 'DateTimeField',
            'DATE': 'DateField',
            'TIME': 'TimeField',
            'BOOLEAN': 'BooleanField',
            'DECIMAL': 'DecimalField'
        }
        
        migration_order = [
            'trainers',      # No dependencies
            'clients',       # Depends on trainers
            'assessments',   # Depends on clients and trainers
            'session_packages',  # Depends on clients and trainers
            'sessions',      # Depends on clients, packages, trainers
            'payments',      # Depends on clients, packages, trainers
            'fee_audit_log'  # Depends on packages, payments, trainers
        ]
        
        self.analysis_results['migration_plan']['model_mapping'] = model_mapping
        self.analysis_results['migration_plan']['type_mapping'] = type_mapping
        self.analysis_results['migration_plan']['migration_order'] = migration_order
        
        print("\n  Migration order:")
        for i, table in enumerate(migration_order, 1):
            if table in self.analysis_results['tables']:
                row_count = self.analysis_results['tables'][table]['row_count']
                model = model_mapping.get(table, 'Unknown')
                print(f"    {i}. {table} -> {model} ({row_count} rows)")
    
    def generate_summary(self):
        """Generate analysis summary"""
        total_tables = len(self.analysis_results['tables'])
        total_rows = sum(table['row_count'] for table in self.analysis_results['tables'].values())
        
        self.analysis_results['summary'] = {
            'total_tables': total_tables,
            'total_rows': total_rows,
            'warnings_count': len(self.analysis_results['warnings']),
            'database_size': os.path.getsize(self.db_path) / (1024 * 1024),  # MB
            'analysis_date': datetime.now().isoformat()
        }
        
        print("\n📈 Summary:")
        print(f"  - Total tables: {total_tables}")
        print(f"  - Total rows: {total_rows:,}")
        print(f"  - Database size: {self.analysis_results['summary']['database_size']:.2f} MB")
        print(f"  - Warnings: {len(self.analysis_results['warnings'])}")
    
    def save_analysis(self, output_path: str):
        """Save analysis results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Analysis saved to: {output_path}")
    
    def run_analysis(self):
        """Run complete analysis"""
        print("\n🚀 Starting Streamlit Database Analysis")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            self.analyze_table_structure()
            self.analyze_data_integrity()
            self.analyze_relationships()
            self.generate_migration_plan()
            self.generate_summary()
            
            # Save results
            output_path = Path(__file__).parent / 'streamlit_db_analysis.json'
            self.save_analysis(str(output_path))
            
            # Print warnings
            if self.analysis_results['warnings']:
                print("\n⚠️  Warnings:")
                for warning in self.analysis_results['warnings']:
                    print(f"  - {warning}")
            
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
        # Try alternate location
        db_path = project_root / 'fitness_assessment.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return 1
    
    # Run analysis
    analyzer = StreamlitDatabaseAnalyzer(str(db_path))
    success = analyzer.run_analysis()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())