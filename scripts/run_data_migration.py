#!/usr/bin/env python
"""
Script to run the data migration from Streamlit to Django
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the data migration script"""
    # Change to Django project directory
    django_dir = Path(__file__).resolve().parent.parent
    os.chdir(django_dir)
    
    print("=" * 60)
    print("STREAMLIT TO DJANGO DATA MIGRATION")
    print("=" * 60)
    
    # Run the migration script
    cmd = [sys.executable, "scripts/migrate_data_from_streamlit.py"]
    
    # Add --auto flag if provided
    if "--auto" in sys.argv:
        cmd.append("--auto")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nMigration completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nMigration failed with error code: {e.returncode}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())