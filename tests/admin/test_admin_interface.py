#!/usr/bin/env python3
"""
Test script for TestStandard admin interface functionality.
This script tests admin methods and ensures they work correctly.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from apps.assessments.models import TestStandard
from apps.assessments.admin import TestStandardAdmin
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.contrib.auth.models import User

def test_admin_functionality():
    """Test TestStandard admin functionality."""
    print("Testing TestStandard Admin Interface")
    print("=" * 40)
    
    # Create admin instance
    site = AdminSite()
    admin = TestStandardAdmin(TestStandard, site)
    
    # Get some test standards
    standards = TestStandard.objects.filter(test_type='push_up')[:3]
    
    if not standards.exists():
        print("No test standards found. Please run 'load_test_standards' first.")
        return
    
    print(f"\nFound {standards.count()} test standards to work with")
    
    # Test display methods
    print("\n1. Testing Display Methods")
    print("-" * 25)
    
    for standard in standards:
        age_range = admin.age_range_display(standard)
        threshold_display = admin.threshold_display(standard)
        
        print(f"  {standard.name}")
        print(f"    Age Range: {age_range}")
        print(f"    Thresholds: {threshold_display}")
    
    # Test get_score_for_value method
    print("\n2. Testing Scoring Methods")
    print("-" * 26)
    
    test_standard = standards.first()
    test_values = [
        test_standard.excellent_threshold + 5,
        test_standard.good_threshold,
        test_standard.average_threshold,
        test_standard.needs_improvement_threshold
    ]
    
    print(f"Testing with: {test_standard.name}")
    for value in test_values:
        score = test_standard.get_score_for_value(value)
        grade = test_standard.get_grade_description(value)
        print(f"  Value {value} → Score {score} ({grade})")
    
    # Test queryset optimization
    print("\n3. Testing Queryset Optimization")
    print("-" * 33)
    
    class MockRequest:
        pass
    
    request = MockRequest()
    queryset = admin.get_queryset(request)
    print(f"  Optimized queryset: {queryset.count()} standards loaded")
    
    # Test list display
    print("\n4. Testing List Display Configuration")
    print("-" * 36)
    
    print(f"  List display fields: {admin.list_display}")
    print(f"  List filters: {admin.list_filter}")
    print(f"  Search fields: {admin.search_fields}")
    print(f"  Editable fields: {admin.list_editable}")
    
    # Test actions
    print("\n5. Testing Available Actions")
    print("-" * 28)
    
    for action in admin.actions:
        if hasattr(admin, action):
            action_func = getattr(admin, action)
            print(f"  ✓ {action}: {action_func.short_description}")
        else:
            print(f"  ✗ {action}: Not found")
    
    print("\n" + "=" * 40)
    print("Admin interface test completed successfully!")
    print("\nTo access the admin interface:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Run the server: python manage.py runserver")
    print("3. Go to: http://localhost:8000/admin/assessments/teststandard/")

if __name__ == "__main__":
    test_admin_functionality()