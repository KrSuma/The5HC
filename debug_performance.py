#!/usr/bin/env python
"""
Debug performance issues with package creation
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.fee_calculator import FeeCalculator
from src.data.database import get_db_connection
from src.services.enhanced_session_service import EnhancedSessionService

def test_fee_calculation_speed():
    """Test fee calculation performance"""
    print("Testing fee calculation speed...")
    calculator = FeeCalculator()
    
    start = time.time()
    for i in range(100):
        breakdown = calculator.calculate_fee_breakdown(1980000)
    end = time.time()
    
    print(f"100 fee calculations took: {end - start:.3f} seconds")
    print(f"Average per calculation: {(end - start) / 100 * 1000:.1f} ms")

def test_database_operations():
    """Test database operation speed"""
    print("\nTesting database operations...")
    
    # Test connection
    start = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session_packages")
        count = cursor.fetchone()[0]
    end = time.time()
    
    print(f"Database connection and count query took: {(end - start) * 1000:.1f} ms")
    print(f"Found {count} packages in database")
    
    # Test insert without fees
    start = time.time()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO session_packages 
            (client_id, trainer_id, total_amount, session_price, 
             total_sessions, remaining_credits, remaining_sessions,
             package_name, notes, updated_at)
            VALUES (1, 1, 1980000, 60000, 33, 1980000, 33, 'Test Package', 'Test', CURRENT_TIMESTAMP)
        """)
        package_id = cursor.lastrowid
        conn.rollback()  # Don't actually save
    end = time.time()
    
    print(f"Package insert (without fees) took: {(end - start) * 1000:.1f} ms")

def test_audit_log_performance():
    """Test audit log table performance"""
    print("\nTesting audit log performance...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if audit log table has any indexes
        cursor.execute("PRAGMA table_info(fee_audit_log);")
        columns = cursor.fetchall()
        print(f"Audit log has {len(columns)} columns")
        
        # Check for indexes
        cursor.execute("PRAGMA index_list(fee_audit_log);")
        indexes = cursor.fetchall()
        print(f"Audit log has {len(indexes)} indexes")

def test_cache_operations():
    """Test cache operations"""
    print("\nTesting cache operations...")
    from src.utils.cache import cache_manager
    
    client_cache = cache_manager.get_cache('clients')
    
    # Test cache set/get
    start = time.time()
    for i in range(100):
        client_cache.set(f"test_key_{i}", {"data": i})
    end = time.time()
    print(f"100 cache sets took: {(end - start) * 1000:.1f} ms")
    
    start = time.time()
    for i in range(100):
        data = client_cache.get(f"test_key_{i}")
    end = time.time()
    print(f"100 cache gets took: {(end - start) * 1000:.1f} ms")
    
    start = time.time()
    client_cache.invalidate()
    end = time.time()
    print(f"Cache invalidation took: {(end - start) * 1000:.1f} ms")

if __name__ == "__main__":
    test_fee_calculation_speed()
    test_database_operations()
    test_audit_log_performance()
    test_cache_operations()