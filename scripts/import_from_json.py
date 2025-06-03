#!/usr/bin/env python3
"""
Import JSON data into Heroku PostgreSQL database
Run this on Heroku: heroku run python scripts/import_from_json.py
"""
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database_config import get_db_connection, execute_query

def import_data():
    """Import data from JSON files to PostgreSQL"""
    import_dir = os.path.join(os.path.dirname(__file__), 'data_export')
    
    if not os.path.exists(import_dir):
        print(f"Import directory not found at {import_dir}")
        print("Please upload your exported JSON files first")
        return
    
    # Tables in order of dependencies
    tables = ['trainers', 'clients', 'assessments', 'session_packages', 'sessions', 'payments']
    
    print("Starting data import to PostgreSQL...")
    
    for table in tables:
        filename = os.path.join(import_dir, f"{table}.json")
        
        if not os.path.exists(filename):
            print(f"⚠ Skipping {table} - file not found")
            continue
        
        try:
            # Load JSON data
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                print(f"⚠ No data found in {table}.json")
                continue
            
            # Get column names from first record
            columns = list(data[0].keys())
            
            # Import each record
            imported = 0
            for record in data:
                # Prepare values
                values = []
                for col in columns:
                    value = record.get(col)
                    # Convert ISO datetime strings back to datetime
                    if isinstance(value, str) and 'T' in value:
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
                    values.append(value)
                
                # Build INSERT query
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                
                query = f"""
                    INSERT INTO {table} ({column_names})
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])}
                """
                
                try:
                    execute_query(query, values)
                    imported += 1
                except Exception as e:
                    print(f"  Error importing record: {e}")
            
            print(f"✓ Imported {imported}/{len(data)} records into {table}")
            
        except Exception as e:
            print(f"✗ Error importing {table}: {e}")
    
    print("\nImport complete!")
    
    # Verify import
    print("\nVerifying data...")
    for table in tables:
        try:
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch_one=True)
            print(f"  {table}: {result['count']} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")

if __name__ == "__main__":
    import_data()