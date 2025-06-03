#!/usr/bin/env python3
"""
Script to run database migrations
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.migrate_database import run_migration

if __name__ == "__main__":
    print("Running database migration...")
    if run_migration():
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)