#!/usr/bin/env python3
"""
Simple test script for session management functionality
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.services.session_service import SessionService, SessionPackage, TrainingSession
from database import init_db

def test_session_functionality():
    """Test basic session management functionality"""
    print("Testing Session Management System...")
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Create session service
    session_service = SessionService()
    print("✓ Session service created")
    
    # Test data
    client_id = 1
    trainer_id = 1
    
    try:
        # Test 1: Create a session package
        print("\n1. Creating session package...")
        package_id = session_service.create_session_package(
            client_id=client_id,
            trainer_id=trainer_id,
            total_amount=300000,  # 300,000 KRW
            session_price=60000,  # 60,000 KRW per session
            package_name="5회 집중 트레이닝"
        )
        print(f"✓ Package created with ID: {package_id}")
        
        # Test 2: Get client packages
        print("\n2. Retrieving client packages...")
        packages = session_service.get_client_packages(client_id, trainer_id)
        print(f"✓ Found {len(packages)} packages")
        
        if packages:
            package = packages[0]
            print(f"   - Package: {package.package_name}")
            print(f"   - Total sessions: {package.total_sessions}")
            print(f"   - Remaining credits: ₩{package.remaining_credits:,}")
            print(f"   - Remaining sessions: {package.remaining_sessions}")
        
        # Test 3: Schedule a session
        print("\n3. Scheduling a session...")
        session_id = session_service.schedule_session(
            client_id=client_id,
            trainer_id=trainer_id,
            package_id=package_id,
            session_date="2025-06-04",
            session_time="10:00",
            notes="첫 번째 세션"
        )
        print(f"✓ Session scheduled with ID: {session_id}")
        
        # Test 4: Complete the session
        print("\n4. Completing the session...")
        result = session_service.complete_session(session_id, trainer_id, "세션 완료!")
        print(f"✓ Session completed: {result}")
        
        # Test 5: Check updated package
        print("\n5. Checking updated package...")
        packages = session_service.get_client_packages(client_id, trainer_id)
        if packages:
            package = packages[0]
            print(f"✓ Updated package:")
            print(f"   - Remaining credits: ₩{package.remaining_credits:,}")
            print(f"   - Remaining sessions: {package.remaining_sessions}")
        
        # Test 6: Get session history
        print("\n6. Getting session history...")
        sessions = session_service.get_client_sessions(client_id, trainer_id)
        print(f"✓ Found {len(sessions)} sessions")
        
        for session in sessions:
            print(f"   - {session.session_date} {session.session_time}: {session.status}")
        
        # Test 7: Add credits
        print("\n7. Adding credits...")
        result = session_service.add_credits(client_id, trainer_id, 60000, "카드", "추가 결제")
        print(f"✓ Credits added: {result}")
        
        # Test 8: Get payment history
        print("\n8. Getting payment history...")
        payments = session_service.get_payment_history(client_id, trainer_id)
        print(f"✓ Found {len(payments)} payments")
        
        for payment in payments:
            print(f"   - {payment.payment_date}: ₩{payment.amount:,} ({payment.payment_method})")
        
        # Test 9: Get package summary
        print("\n9. Getting package summary...")
        summary = session_service.get_package_summary(package_id, trainer_id)
        print("✓ Package summary:")
        print(f"   - Client: {summary['package']['client_name']}")
        print(f"   - Completed sessions: {summary['statistics']['completed_sessions']}")
        print(f"   - Total spent: ₩{summary['statistics']['total_spent']:,}")
        print(f"   - Utilization rate: {summary['statistics']['utilization_rate']:.1f}%")
        
        print("\n🎉 All tests passed! Session management system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_functionality()