#!/usr/bin/env python3
"""
Simple test suite for core fitness enhancement functionality.
Tests functionality without database dependencies.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from apps.assessments.scoring import (
    calculate_overhead_squat_score,
    calculate_pushup_score, 
    calculate_single_leg_balance_score,
    calculate_farmers_carry_score
)
from apps.assessments.risk_calculator import calculate_injury_risk

def test_core_functionality():
    """Test core functionality without database dependencies"""
    print("Simple Test Suite - Core Functionality")
    print("=" * 45)
    
    print("\n1. Movement Quality Scoring")
    print("-" * 25)
    
    # Test overhead squat
    perfect = calculate_overhead_squat_score(
        knee_valgus=False, forward_lean=False, heel_lift=False, pain=False
    )
    one_comp = calculate_overhead_squat_score(
        knee_valgus=True, forward_lean=False, heel_lift=False, pain=False
    )
    with_pain = calculate_overhead_squat_score(
        knee_valgus=False, forward_lean=False, heel_lift=False, pain=True
    )
    
    print(f"  Perfect form: {perfect} (expected: 3)")
    print(f"  One compensation: {one_comp} (expected: 2)")
    print(f"  With pain: {with_pain} (expected: 0)")
    
    assert perfect == 3 and one_comp == 2 and with_pain == 0
    print("  ✓ Movement quality scoring works")
    
    print("\n2. Test Variations")
    print("-" * 15)
    
    # Test push-up variations
    standard = calculate_pushup_score('Male', 25, 30, 'standard')
    modified = calculate_pushup_score('Male', 25, 30, 'modified')
    wall = calculate_pushup_score('Male', 25, 30, 'wall')
    
    print(f"  Standard push-up: {standard}")
    print(f"  Modified push-up: {modified}")
    print(f"  Wall push-up: {wall}")
    
    # Test that all scores are valid (1-4 range)
    assert 1 <= standard <= 4 and 1 <= modified <= 4 and 1 <= wall <= 4
    print("  ✓ Push-up scoring returns valid scores")
    
    # Test farmer's carry
    carry_standard = calculate_farmers_carry_score('Male', 80, 25, 60, 100)
    carry_light = calculate_farmers_carry_score('Male', 80, 25, 60, 50)
    
    print(f"  Standard carry: {carry_standard:.1f}")
    print(f"  Light carry: {carry_light:.1f}")
    
    # Test that scores are valid
    assert 1 <= carry_standard <= 4 and 1 <= carry_light <= 4
    print("  ✓ Farmer's carry scoring returns valid scores")
    
    print("\n3. Balance Scoring")
    print("-" * 14)
    
    balance_good = calculate_single_leg_balance_score(45, 50, 30, 35)
    balance_poor = calculate_single_leg_balance_score(15, 20, 5, 10)
    
    print(f"  Good balance: {balance_good:.1f}")
    print(f"  Poor balance: {balance_poor:.1f}")
    
    assert balance_good > balance_poor
    print("  ✓ Balance scoring works")
    
    print("\n4. Risk Assessment")
    print("-" * 15)
    
    # Test low risk
    low_risk_data = {
        'strength_score': 90,
        'mobility_score': 85,
        'balance_score': 95,
        'cardio_score': 88,
        'overall_score': 90,
        'overhead_squat_score': 3,
        'push_up_score': 4,
        'toe_touch_score': 3,
        'shoulder_mobility_score': 3,
        'overhead_squat_knee_valgus': False,
        'overhead_squat_forward_lean': False,
        'overhead_squat_heel_lift': False,
        'shoulder_mobility_pain': False,
        'shoulder_mobility_asymmetry': 1.0,
        'single_leg_balance_right_eyes_open': 60,
        'single_leg_balance_left_eyes_open': 55,
        'single_leg_balance_right_eyes_closed': 35,
        'single_leg_balance_left_eyes_closed': 30,
    }
    
    low_risk, low_factors = calculate_injury_risk(low_risk_data)
    
    # Test high risk
    high_risk_data = {
        'strength_score': 40,
        'mobility_score': 35,
        'balance_score': 30,
        'cardio_score': 45,
        'overall_score': 35,
        'overhead_squat_score': 1,
        'push_up_score': 1,
        'toe_touch_score': 1,
        'shoulder_mobility_score': 1,
        'overhead_squat_knee_valgus': True,
        'overhead_squat_forward_lean': True,
        'overhead_squat_heel_lift': True,
        'shoulder_mobility_pain': True,
        'shoulder_mobility_asymmetry': 8.0,
        'single_leg_balance_right_eyes_open': 10,
        'single_leg_balance_left_eyes_open': 8,
        'single_leg_balance_right_eyes_closed': 3,
        'single_leg_balance_left_eyes_closed': 2,
    }
    
    high_risk, high_factors = calculate_injury_risk(high_risk_data)
    
    print(f"  Low risk scenario: {low_risk:.1f}/100")
    print(f"  High risk scenario: {high_risk:.1f}/100")
    
    assert 0 <= low_risk <= 100 and 0 <= high_risk <= 100
    assert high_risk > low_risk
    print("  ✓ Risk assessment works")
    
    print("\n" + "=" * 45)
    print("✅ ALL CORE TESTS PASSED!")
    print("\nFunctionality verified:")
    print("• Movement quality scoring")
    print("• Test variations (push-up, farmer's carry)")
    print("• Balance assessment")
    print("• Injury risk calculation")
    
    return True

if __name__ == "__main__":
    try:
        success = test_core_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)