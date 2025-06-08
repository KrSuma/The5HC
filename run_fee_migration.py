#!/usr/bin/env python
"""
Script to run the VAT and fee columns migration
"""
import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.add_fee_columns_migration import run_fee_migration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("Starting VAT and fee columns migration...")
    print("=" * 50)
    
    try:
        success = run_fee_migration()
        
        if success:
            print("\n" + "=" * 50)
            print("Migration completed successfully!")
            print("All existing packages and payments have been updated with fee calculations.")
            print("\nNext steps:")
            print("1. Test the enhanced session management page")
            print("2. Verify fee calculations are correct")
            print("3. Check that existing data was migrated properly")
        else:
            print("\n" + "=" * 50)
            print("Migration failed! Check the logs for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nMigration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)