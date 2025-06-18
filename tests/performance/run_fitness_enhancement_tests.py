#!/usr/bin/env python3
"""
Comprehensive test runner for Fitness Assessment Enhancement features.
This script tests all the new functionality added in Phases 1-5.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.test')
django.setup()

from apps.assessments.models import Assessment, TestStandard, NormativeData
from apps.assessments.scoring import (
    calculate_overhead_squat_score,
    calculate_pushup_score, 
    calculate_single_leg_balance_score,
    calculate_farmers_carry_score,
    get_test_standard,
    get_score_from_standard_or_fallback
)
from apps.assessments.risk_calculator import calculate_injury_risk
from django.core.management import call_command

def test_phase_1_movement_quality():
    """Test Phase 1: FMS Scoring Enhancement"""
    print("\n=== Phase 1: FMS Scoring Enhancement ===")
    
    # Test overhead squat scoring with movement quality
    perfect_score = calculate_overhead_squat_score(
        knee_valgus=False,
        forward_lean=False, 
        heel_lift=False,
        pain=False
    )
    assert perfect_score == 3, f"Expected 3, got {perfect_score}"
    print("✓ Perfect overhead squat scoring works")
    
    # Test with one compensation
    one_compensation = calculate_overhead_squat_score(
        knee_valgus=True,
        forward_lean=False,
        heel_lift=False,
        pain=False
    )
    assert one_compensation == 2, f"Expected 2, got {one_compensation}"
    print("✓ One compensation scoring works")
    
    # Test with pain (should be 0)
    pain_score = calculate_overhead_squat_score(
        knee_valgus=False,
        forward_lean=False,
        heel_lift=False,
        pain=True
    )
    assert pain_score == 0, f"Expected 0, got {pain_score}"
    print("✓ Pain detection works")


def test_phase_2_risk_scoring():
    """Test Phase 2: Risk Scoring System"""
    print("\n=== Phase 2: Risk Scoring System ===")
    
    # Test risk calculation with sample data
    test_data = {
        'strength_score': 85,
        'mobility_score': 70,
        'balance_score': 90,
        'cardio_score': 75,
        'overall_score': 80,
        'overhead_squat_score': 2,
        'push_up_score': 3,
        'toe_touch_score': 2,
        'shoulder_mobility_score': 3,
        'overhead_squat_knee_valgus': False,
        'overhead_squat_forward_lean': True,
        'overhead_squat_heel_lift': False,
        'shoulder_mobility_pain': False,
        'shoulder_mobility_asymmetry': 2.0,
        'single_leg_balance_right_eyes_open': 45,
        'single_leg_balance_left_eyes_open': 40,
        'single_leg_balance_right_eyes_closed': 25,
        'single_leg_balance_left_eyes_closed': 20,
    }
    
    risk_score, risk_factors = calculate_injury_risk(test_data)
    
    assert 0 <= risk_score <= 100, f"Risk score should be 0-100, got {risk_score}"
    assert isinstance(risk_factors, dict), "Risk factors should be a dictionary"
    print(f"✓ Risk calculation works: {risk_score:.1f}/100")


def test_phase_3_analytics():
    """Test Phase 3: Analytics Enhancement"""
    print("\n=== Phase 3: Analytics Enhancement ===")
    
    # Check if normative data exists
    norm_count = NormativeData.objects.count()
    print(f"✓ Normative data loaded: {norm_count} entries")
    
    if norm_count > 0:
        # Test percentile calculation
        sample_norm = NormativeData.objects.first()
        percentile = sample_norm.get_percentile(sample_norm.percentile_50)
        assert 45 <= percentile <= 55, f"50th percentile should be ~50, got {percentile}"
        print("✓ Percentile calculation works")


def test_phase_4_test_variations():
    """Test Phase 4: Test Variations Support"""
    print("\n=== Phase 4: Test Variations Support ===")
    
    # Test push-up variations
    standard_score = calculate_pushup_score('Male', 25, 30, 'standard')
    modified_score = calculate_pushup_score('Male', 25, 30, 'modified')
    wall_score = calculate_pushup_score('Male', 25, 30, 'wall')
    
    assert modified_score < standard_score, "Modified should score less than standard"
    assert wall_score < modified_score, "Wall should score less than modified"
    print("✓ Push-up variations work correctly")
    
    # Test farmer's carry with body weight percentage
    standard_carry = calculate_farmers_carry_score('Male', 80, 25, 60, 100)
    light_carry = calculate_farmers_carry_score('Male', 80, 25, 60, 50)
    
    assert light_carry <= standard_carry, "Light weight should score less or equal"
    print("✓ Farmer's carry variations work correctly")


def test_phase_5_standards_configuration():
    """Test Phase 5: Standards Configuration"""
    print("\n=== Phase 5: Standards Configuration ===")
    
    # Check if test standards exist
    standard_count = TestStandard.objects.count()
    print(f"✓ Test standards loaded: {standard_count} entries")
    
    if standard_count > 0:
        # Test getting a standard
        standard = get_test_standard('push_up', 'M', 25, 'standard')
        if standard:
            print(f"✓ Database standard found: {standard.name}")
            
            # Test scoring with database standard
            score = get_score_from_standard_or_fallback('push_up', 30, 'M', 25, 'standard')
            assert 1 <= score <= 4, f"Score should be 1-4, got {score}"
            print("✓ Database-backed scoring works")
        else:
            print("⚠ No push-up standard found, using fallback")
    
    # Test fallback still works
    fallback_score = calculate_pushup_score('Male', 25, 30, 'standard')
    assert 1 <= fallback_score <= 4, f"Fallback score should be 1-4, got {fallback_score}"
    print("✓ Fallback scoring works")


def test_integration():
    """Test integration between all phases"""
    print("\n=== Integration Testing ===")
    
    # Test that all components work together
    try:
        # This would normally be done in Assessment.calculate_scores()
        # but we'll test the individual components
        
        # Movement quality
        squat_score = calculate_overhead_squat_score(
            knee_valgus=True, forward_lean=False, heel_lift=False
        )
        
        # Variations
        pushup_score = calculate_pushup_score('Female', 35, 15, 'modified')
        
        # Balance
        balance_score = calculate_single_leg_balance_score(30, 35, 20, 25)
        
        # Risk assessment (minimal data)
        risk_data = {
            'strength_score': 70,
            'mobility_score': 60,
            'balance_score': 80,
            'cardio_score': 75,
            'overall_score': 70,
            'overhead_squat_score': squat_score,
            'push_up_score': pushup_score,
        }
        risk_score, _ = calculate_injury_risk(risk_data)
        
        print(f"✓ Integration test complete:")
        print(f"  - Squat score: {squat_score}")
        print(f"  - Push-up score: {pushup_score}")
        print(f"  - Balance score: {balance_score:.1f}")
        print(f"  - Risk score: {risk_score:.1f}")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True


def main():
    """Run all fitness enhancement tests"""
    print("Fitness Assessment Enhancement - Comprehensive Test Suite")
    print("=" * 60)
    
    try:
        test_phase_1_movement_quality()
        test_phase_2_risk_scoring()
        test_phase_3_analytics()
        test_phase_4_test_variations()
        test_phase_5_standards_configuration()
        
        if test_integration():
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED - Fitness Enhancement is working correctly!")
            print("\nFeatures successfully implemented:")
            print("• Movement quality tracking (Phase 1)")
            print("• Injury risk assessment (Phase 2)")
            print("• Percentile rankings (Phase 3)")
            print("• Test variations support (Phase 4)")
            print("• Configurable standards (Phase 5)")
            return True
        else:
            print("\n❌ Integration test failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)