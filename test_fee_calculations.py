#!/usr/bin/env python
"""
Test script for VAT and fee calculations
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.fee_calculator import FeeCalculator, CurrencyFormatter
from decimal import Decimal


def test_basic_calculations():
    """Test basic fee calculations"""
    print("Testing Basic Fee Calculations")
    print("=" * 50)
    
    calculator = FeeCalculator()
    formatter = CurrencyFormatter()
    
    # Test case from requirements
    test_amounts = [1980000, 660000, 100000, 1000000, 5000000]
    
    for amount in test_amounts:
        print(f"\nTest amount: {formatter.format(amount)}")
        breakdown = calculator.calculate_fee_breakdown(amount)
        
        print(f"  VAT (10%): {formatter.format(breakdown['vat_amount'])}")
        print(f"  Card fee (3.5%): {formatter.format(breakdown['card_fee_amount'])}")
        print(f"  Net amount: {formatter.format(breakdown['net_amount'])}")
        
        # Validate calculation
        is_valid = calculator.validate_calculation(breakdown)
        print(f"  Validation: {'✓ Passed' if is_valid else '✗ Failed'}")
        
        # Calculate sessions based on gross amount
        session_price = 60000
        total_sessions = amount // session_price  # Use gross amount, not net
        print(f"  Sessions (₩60,000 each): {total_sessions}회 (based on gross amount)")


def test_edge_cases():
    """Test edge cases and rounding"""
    print("\n\nTesting Edge Cases")
    print("=" * 50)
    
    calculator = FeeCalculator()
    formatter = CurrencyFormatter()
    
    # Test amounts that might cause rounding issues
    edge_cases = [1, 999, 12345, 99999, 123456789]
    
    for amount in edge_cases:
        breakdown = calculator.calculate_fee_breakdown(amount)
        is_valid = calculator.validate_calculation(breakdown)
        
        print(f"\nAmount: {formatter.format(amount)}")
        print(f"  Total components: {breakdown['vat_amount'] + breakdown['card_fee_amount'] + breakdown['net_amount']}")
        print(f"  Validation: {'✓' if is_valid else '✗'}")


def test_reverse_calculation():
    """Test reverse calculation from net to gross"""
    print("\n\nTesting Reverse Calculations")
    print("=" * 50)
    
    calculator = FeeCalculator()
    formatter = CurrencyFormatter()
    
    # Test: What gross amount is needed to get specific net amounts?
    desired_nets = [1000000, 500000, 300000]
    
    for net in desired_nets:
        result = calculator.reverse_calculate_gross(net)
        
        print(f"\nDesired net: {formatter.format(net)}")
        print(f"  Required gross: {formatter.format(result['gross_amount'])}")
        print(f"  Actual net: {formatter.format(result['net_amount'])}")
        print(f"  Difference: {formatter.format(abs(net - result['net_amount']))}")


def test_currency_formatting():
    """Test currency formatting"""
    print("\n\nTesting Currency Formatting")
    print("=" * 50)
    
    formatter = CurrencyFormatter()
    
    test_values = [
        (1000, "Standard"),
        (10000, "Ten thousand"),
        (100000, "Hundred thousand"),
        (1000000, "Million"),
        (100000000, "Hundred million"),
        (1234567890, "Large number")
    ]
    
    for value, desc in test_values:
        print(f"{desc}: {formatter.format(value)} / {formatter.format_short(value)}")


def test_scenario_from_requirements():
    """Test the exact scenario from requirements"""
    print("\n\nTesting Requirements Scenario")
    print("=" * 50)
    
    calculator = FeeCalculator()
    formatter = CurrencyFormatter()
    
    # Initial top-up
    initial_amount = 1980000
    breakdown = calculator.calculate_fee_breakdown(initial_amount)
    
    print(f"총 충전액: {formatter.format(breakdown['gross_amount'])}")
    print(f"부가세 (10%): {formatter.format(breakdown['vat_amount'])}")
    print(f"카드 수수료 (3.5%): {formatter.format(breakdown['card_fee_amount'])}")
    print(f"순 잔여 크래딧: {formatter.format(breakdown['net_amount'])}")
    
    # Expected values from requirements
    expected_vat = 180000
    expected_fee = 69300
    expected_net = 1730700
    
    print(f"\nExpected vs Actual:")
    print(f"  VAT: {expected_vat} vs {breakdown['vat_amount']} ({'✓' if expected_vat == breakdown['vat_amount'] else '✗'})")
    print(f"  Fee: {expected_fee} vs {breakdown['card_fee_amount']} ({'✓' if expected_fee == breakdown['card_fee_amount'] else '✗'})")
    print(f"  Net: {expected_net} vs {breakdown['net_amount']} ({'✓' if expected_net == breakdown['net_amount'] else '✗'})")
    
    # Show session calculation difference
    session_price = 60000
    sessions_on_gross = initial_amount // session_price
    sessions_on_net = breakdown['net_amount'] // session_price
    
    print(f"\nSession Calculation:")
    print(f"  Based on gross amount: {sessions_on_gross}회 (₩{initial_amount:,} ÷ ₩{session_price:,})")
    print(f"  Based on net amount: {sessions_on_net}회 (₩{breakdown['net_amount']:,} ÷ ₩{session_price:,})")
    print(f"  → We use gross amount, so: {sessions_on_gross}회")
    
    # After 3 sessions
    session_cost = 60000
    sessions_used = 3
    used_credits = session_cost * sessions_used
    remaining_credits = breakdown['net_amount'] - used_credits
    
    print(f"\nAfter {sessions_used} sessions:")
    print(f"사용 크래딧: {formatter.format(used_credits)}")
    print(f"남은 크래딧: {formatter.format(remaining_credits)}")


if __name__ == "__main__":
    test_basic_calculations()
    test_edge_cases()
    test_reverse_calculation()
    test_currency_formatting()
    test_scenario_from_requirements()
    
    print("\n\nAll tests completed!")