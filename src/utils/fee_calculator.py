"""
Fee calculation utilities for VAT and card processing fees
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Union
import json
import logging

logger = logging.getLogger(__name__)


class FeeCalculator:
    """Handles all fee calculations with fixed Korean tax rates"""
    
    def __init__(self):
        self.vat_rate = Decimal('0.10')  # Fixed 10% VAT
        self.card_fee_rate = Decimal('0.035')  # Fixed 3.5% card fee
    
    def calculate_fee_breakdown(self, gross_amount: Union[int, Decimal]) -> Dict:
        """
        Calculate VAT and card fees from gross amount
        
        Formula (inclusive method):
        - VAT Amount = Gross Amount × (VAT Rate ÷ (1 + VAT Rate))
        - Card Fee = Gross Amount × Card Fee Rate
        - Net Amount = Gross Amount - VAT Amount - Card Fee
        
        Args:
            gross_amount: Total amount charged (including all fees)
            
        Returns:
            Dictionary with all calculated amounts as integers (KRW)
        """
        try:
            gross = Decimal(str(gross_amount))
            
            if gross <= 0:
                raise ValueError("Amount must be positive")
            
            # Calculate VAT (부가세) - inclusive method
            vat_amount = gross * (self.vat_rate / (Decimal('1') + self.vat_rate))
            vat_amount = vat_amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            
            # Calculate card fee (카드 수수료)
            card_fee = gross * self.card_fee_rate
            card_fee = card_fee.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            
            # Calculate net amount
            net_amount = gross - vat_amount - card_fee
            
            result = {
                'gross_amount': int(gross),
                'vat_amount': int(vat_amount),
                'card_fee_amount': int(card_fee),
                'net_amount': int(net_amount),
                'vat_rate': float(self.vat_rate),
                'card_fee_rate': float(self.card_fee_rate),
                'calculation_details': {
                    'method': 'inclusive',
                    'vat_formula': f'{gross} × ({self.vat_rate} ÷ (1 + {self.vat_rate}))',
                    'fee_formula': f'{gross} × {self.card_fee_rate}',
                    'precision': 'ROUND_HALF_UP'
                }
            }
            
            # Validate calculation
            if not self.validate_calculation(result):
                logger.warning(f"Calculation validation failed for amount {gross_amount}")
                # Adjust for rounding errors
                result = self._adjust_for_rounding(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating fees for amount {gross_amount}: {e}")
            raise
    
    def validate_calculation(self, fee_breakdown: Dict) -> bool:
        """Validate that calculations are correct"""
        total = (fee_breakdown['net_amount'] + 
                fee_breakdown['vat_amount'] + 
                fee_breakdown['card_fee_amount'])
        return total == fee_breakdown['gross_amount']
    
    def _adjust_for_rounding(self, fee_breakdown: Dict) -> Dict:
        """Adjust net amount to ensure totals match due to rounding"""
        total = (fee_breakdown['vat_amount'] + 
                fee_breakdown['card_fee_amount'])
        adjusted_net = fee_breakdown['gross_amount'] - total
        
        fee_breakdown['net_amount'] = adjusted_net
        fee_breakdown['calculation_details']['adjusted'] = True
        
        return fee_breakdown
    
    def reverse_calculate_gross(self, net_amount: Union[int, Decimal]) -> Dict:
        """
        Calculate gross amount from desired net amount
        Useful when you want to charge exactly X amount after fees
        
        Args:
            net_amount: Desired amount after all fees
            
        Returns:
            Dictionary with calculated gross amount and breakdown
        """
        try:
            net = Decimal(str(net_amount))
            
            if net <= 0:
                raise ValueError("Net amount must be positive")
            
            # Reverse calculation
            # Gross = Net / (1 - VAT_rate/(1+VAT_rate) - Card_fee_rate)
            vat_factor = self.vat_rate / (Decimal('1') + self.vat_rate)
            total_fee_rate = vat_factor + self.card_fee_rate
            
            gross = net / (Decimal('1') - total_fee_rate)
            gross = gross.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            
            # Now calculate forward to get exact breakdown
            return self.calculate_fee_breakdown(gross)
            
        except Exception as e:
            logger.error(f"Error reverse calculating for net amount {net_amount}: {e}")
            raise


class CurrencyFormatter:
    """Handle Korean Won currency formatting"""
    
    @staticmethod
    def format(amount: int) -> str:
        """Format amount as Korean Won"""
        return f"₩{amount:,}"
    
    @staticmethod
    def format_short(amount: int) -> str:
        """Format large amounts in shortened form"""
        if amount >= 100000000:  # 1억 이상
            return f"₩{amount / 100000000:.1f}억"
        elif amount >= 10000:  # 1만 이상
            return f"₩{amount / 10000:.0f}만"
        return f"₩{amount:,}"
    
    @staticmethod
    def parse_amount(amount_str: str) -> int:
        """Parse formatted amount string back to integer"""
        # Remove currency symbol and commas
        cleaned = amount_str.replace('₩', '').replace(',', '').strip()
        
        # Handle shortened forms
        if '억' in cleaned:
            number = float(cleaned.replace('억', '').strip())
            return int(number * 100000000)
        elif '만' in cleaned:
            number = float(cleaned.replace('만', '').strip())
            return int(number * 10000)
        
        return int(cleaned)


class FeeAuditLogger:
    """Handle audit logging for fee calculations"""
    
    @staticmethod
    def create_audit_log(db, package_id: int, payment_id: int, 
                        calculation_type: str, fee_breakdown: Dict,
                        trainer_id: int) -> bool:
        """Create audit log entry for fee calculation"""
        try:
            from src.data.database_config import adapt_query_for_db, IS_PRODUCTION
            
            # Convert calculation details to JSON
            details_json = json.dumps(fee_breakdown.get('calculation_details', {}))
            
            query = adapt_query_for_db(
                sqlite_query="""
                INSERT INTO fee_audit_log 
                (package_id, payment_id, calculation_type, gross_amount, 
                 vat_amount, card_fee_amount, net_amount, vat_rate, 
                 card_fee_rate, calculation_details, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                postgresql_query="""
                INSERT INTO fee_audit_log 
                (package_id, payment_id, calculation_type, gross_amount, 
                 vat_amount, card_fee_amount, net_amount, vat_rate, 
                 card_fee_rate, calculation_details, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            )
            
            params = (
                package_id,
                payment_id,
                calculation_type,
                fee_breakdown['gross_amount'],
                fee_breakdown['vat_amount'],
                fee_breakdown['card_fee_amount'],
                fee_breakdown['net_amount'],
                fee_breakdown['vat_rate'],
                fee_breakdown['card_fee_rate'],
                details_json,
                trainer_id
            )
            
            db.execute_query(query, params, fetch_all=False)
            return True
            
        except Exception as e:
            logger.error(f"Error creating fee audit log: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    calculator = FeeCalculator()
    formatter = CurrencyFormatter()
    
    # Test case from requirements
    test_amount = 1980000
    breakdown = calculator.calculate_fee_breakdown(test_amount)
    
    print(f"Test amount: {formatter.format(test_amount)}")
    print(f"VAT (10%): {formatter.format(breakdown['vat_amount'])}")
    print(f"Card fee (3.5%): {formatter.format(breakdown['card_fee_amount'])}")
    print(f"Net amount: {formatter.format(breakdown['net_amount'])}")
    print(f"Validation: {'✓' if calculator.validate_calculation(breakdown) else '✗'}")
    
    # Test reverse calculation
    desired_net = 1000000
    reverse_result = calculator.reverse_calculate_gross(desired_net)
    print(f"\nReverse calculation for net {formatter.format(desired_net)}:")
    print(f"Required gross: {formatter.format(reverse_result['gross_amount'])}")