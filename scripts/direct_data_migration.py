#!/usr/bin/env python
"""
Direct data migration script that works without full Django initialization
This is a workaround for the WeasyPrint dependency issue
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database paths
STREAMLIT_DB = Path(__file__).resolve().parent.parent.parent / 'data' / 'fitness_assessment.db'
DJANGO_DB = Path(__file__).resolve().parent.parent / 'the5hc_dev'


class DirectMigrator:
    def __init__(self):
        self.streamlit_conn = None
        self.django_conn = None
        self.stats = {
            'trainers': {'processed': 0, 'created': 0, 'errors': 0},
            'clients': {'processed': 0, 'created': 0, 'errors': 0},
            'assessments': {'processed': 0, 'created': 0, 'errors': 0},
            'session_packages': {'processed': 0, 'created': 0, 'errors': 0},
            'sessions': {'processed': 0, 'created': 0, 'errors': 0},
            'payments': {'processed': 0, 'created': 0, 'errors': 0}
        }
        
    def connect(self):
        """Connect to both databases"""
        try:
            self.streamlit_conn = sqlite3.connect(STREAMLIT_DB)
            self.streamlit_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to Streamlit DB: {STREAMLIT_DB}")
            
            self.django_conn = sqlite3.connect(DJANGO_DB)
            self.django_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to Django DB: {DJANGO_DB}")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
            
    def close(self):
        """Close database connections"""
        if self.streamlit_conn:
            self.streamlit_conn.close()
        if self.django_conn:
            self.django_conn.close()
            
    def check_django_tables(self):
        """Check if Django tables exist"""
        cursor = self.django_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            'accounts_user',
            'clients_client', 
            'assessments_assessment',
            'sessions_sessionpackage',
            'sessions_session',
            'sessions_payment'
        ]
        
        missing = [t for t in required_tables if t not in tables]
        if missing:
            logger.error(f"Missing Django tables: {missing}")
            logger.error("Please run 'python manage.py migrate' first")
            return False
        
        logger.info("All required Django tables exist")
        return True
        
    def migrate_all(self):
        """Run migration"""
        try:
            self.connect()
            
            if not self.check_django_tables():
                return False
                
            logger.info("Starting direct data migration...")
            
            # For now, just report on what we would migrate
            self.analyze_streamlit_data()
            
            logger.info("Migration analysis complete!")
            self.print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        finally:
            self.close()
            
    def analyze_streamlit_data(self):
        """Analyze Streamlit database contents"""
        cursor = self.streamlit_conn.cursor()
        
        tables = ['trainers', 'clients', 'assessments', 'session_packages', 'sessions', 'payments']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            self.stats[table]['processed'] = count
            logger.info(f"{table}: {count} records found")
            
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "="*50)
        print("MIGRATION ANALYSIS")
        print("="*50)
        for table, stats in self.stats.items():
            print(f"{table.upper()}: {stats['processed']} records")
        print("="*50)


def main():
    """Main entry point"""
    print("Direct Data Migration Tool")
    print("=" * 50)
    
    if not STREAMLIT_DB.exists():
        logger.error(f"Streamlit database not found: {STREAMLIT_DB}")
        return 1
        
    if not DJANGO_DB.exists():
        logger.error(f"Django database not found: {DJANGO_DB}")
        logger.error("Please run Django migrations first")
        return 1
    
    migrator = DirectMigrator()
    success = migrator.migrate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())