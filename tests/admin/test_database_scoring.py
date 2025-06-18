#!/usr/bin/env python3
"""
Test script for database-backed scoring functions.
This script tests that the updated scoring functions work with and without database standards.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from apps.assessments.scoring import (
    calculate_pushup_score, 
    calculate_single_leg_balance_score,
    calculate_farmers_carry_score,
    get_test_standard
)

def test_scoring_functions():
    """Test all updated scoring functions."""
    print("Testing Database-Backed Scoring Functions")
    print("=" * 50)
    
    # Test push-up scoring
    print("\n1. Testing Push-up Scoring")
    print("-" * 30)
    
    # Test with different scenarios
    test_cases = [
        ("Male", 25, 30, "standard"),
        ("Female", 35, 20, "standard"),
        ("Male", 45, 15, "modified"),
        ("Female", 55, 10, "wall"),
    ]
    
    for gender, age, reps, push_type in test_cases:
        score = calculate_pushup_score(gender, age, reps, push_type)
        print(f"  {gender}, {age}y, {reps} reps, {push_type}: Score = {score}")
    
    # Test single leg balance scoring
    print("\n2. Testing Single Leg Balance Scoring")
    print("-" * 40)
    
    balance_cases = [
        (45, 50, 25, 30),  # Good balance
        (20, 25, 10, 15),  # Poor balance
        (60, 55, 35, 40),  # Excellent balance
    ]
    
    for right_open, left_open, right_closed, left_closed in balance_cases:
        score = calculate_single_leg_balance_score(right_open, left_open, right_closed, left_closed)
        print(f"  Balance times: {right_open}/{left_open} (open), {right_closed}/{left_closed} (closed): Score = {score:.2f}")
    
    # Test farmer's carry scoring
    print("\n3. Testing Farmer's Carry Scoring")
    print("-" * 35)
    
    carry_cases = [
        ("Male", 80, 25, 60, 100),    # Standard load
        ("Female", 60, 20, 45, 80),   # Reduced load
        ("Male", 90, 30, 70, 120),    # Heavy load
    ]
    
    for gender, weight, distance, time, body_weight_pct in carry_cases:
        score = calculate_farmers_carry_score(gender, weight, distance, time, body_weight_pct)
        print(f"  {gender}, {weight}kg, {distance}m, {time}s, {body_weight_pct}% BW: Score = {score:.2f}")
    
    # Test database standard retrieval
    print("\n4. Testing Database Standard Retrieval")
    print("-" * 42)
    
    # Try to get a standard (will be None if not loaded)
    standard = get_test_standard('push_up', 'M', 25, 'standard')
    if standard:
        print(f"  Found standard: {standard.name}")
        print(f"  Thresholds: {standard.excellent_threshold}/{standard.good_threshold}/{standard.average_threshold}")
    else:
        print("  No database standards found - using fallback values")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")

if __name__ == "__main__":
    test_scoring_functions()