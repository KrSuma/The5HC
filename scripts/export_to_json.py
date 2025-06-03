#!/usr/bin/env python3
"""
Export local SQLite data to JSON for migration to Heroku PostgreSQL
"""
import json
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def export_data():
    """Export all data from SQLite to JSON files"""
    # Connect to SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fitness_assessment.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Tables to export
    tables = ['trainers', 'clients', 'assessments', 'session_packages', 'sessions', 'payments']
    
    export_dir = os.path.join(os.path.dirname(__file__), 'data_export')
    os.makedirs(export_dir, exist_ok=True)
    
    print(f"Exporting data to {export_dir}")
    
    for table in tables:
        try:
            # Get all data from table
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            data = []
            for row in rows:
                row_dict = dict(row)
                # Convert datetime objects to strings
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                data.append(row_dict)
            
            # Save to JSON
            filename = os.path.join(export_dir, f"{table}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Exported {len(data)} records from {table}")
            
        except Exception as e:
            print(f"✗ Error exporting {table}: {e}")
    
    conn.close()
    print(f"\nExport complete! Files saved in {export_dir}")
    print("Upload these files to Heroku and run import_from_json.py")

if __name__ == "__main__":
    export_data()