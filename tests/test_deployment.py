"""
Test script to verify deployment readiness
"""
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database_config import get_db_connection, IS_PRODUCTION, execute_query

logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        print(f"Testing database connection...")
        print(f"Production mode: {IS_PRODUCTION}")
        
        # Test connection
        with get_db_connection() as conn:
            print("✓ Database connection successful")
        
        # Test table existence
        tables_to_check = ['trainers', 'clients', 'assessments', 'session_packages', 'sessions', 'payments']
        
        for table in tables_to_check:
            try:
                if IS_PRODUCTION:
                    query = f"SELECT COUNT(*) FROM {table}"
                else:
                    query = f"SELECT COUNT(*) FROM {table}"
                    
                result = execute_query(query, fetch_one=True)
                print(f"✓ Table '{table}' exists and accessible")
            except Exception as e:
                print(f"✗ Table '{table}' error: {e}")
                return False
        
        print("✓ All database tables verified")
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    required_modules = [
        'streamlit',
        'pandas',
        'numpy',
        'matplotlib',
        'bcrypt',
        'weasyprint'
    ]
    
    if IS_PRODUCTION:
        required_modules.append('psycopg2')
    
    print("Testing module imports...")
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {module}: {e}")
            return False
    
    print("✓ All required modules available")
    return True

def main():
    """Run all deployment tests"""
    print("=" * 50)
    print("DEPLOYMENT READINESS TEST")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Database Connection", test_database_connection),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        if test_func():
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        print("You can now deploy to Heroku using:")
        print("  git add .")
        print("  git commit -m 'Deploy to Heroku'")
        print("  git push heroku main")
    else:
        print("❌ SOME TESTS FAILED - Fix issues before deploying")
        sys.exit(1)
    
    print("=" * 50)

if __name__ == "__main__":
    main()