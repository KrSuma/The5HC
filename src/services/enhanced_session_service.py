"""
Enhanced Session Management Service with VAT and fee calculations
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from src.services.session_service import SessionService, SessionPackage, TrainingSession, PaymentRecord
from src.utils.fee_calculator import FeeCalculator, CurrencyFormatter, FeeAuditLogger
from src.data.database import get_db_connection, DatabaseError
from src.data.database_config import IS_PRODUCTION

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSessionPackage(SessionPackage):
    """Extended session package with fee information"""
    gross_amount: Optional[int] = None
    vat_amount: Optional[int] = None
    card_fee_amount: Optional[int] = None
    net_amount: Optional[int] = None
    vat_rate: Optional[float] = None
    card_fee_rate: Optional[float] = None


@dataclass
class EnhancedPaymentRecord(PaymentRecord):
    """Extended payment record with fee information"""
    gross_amount: Optional[int] = None
    vat_amount: Optional[int] = None
    card_fee_amount: Optional[int] = None
    net_amount: Optional[int] = None
    vat_rate: Optional[float] = None
    card_fee_rate: Optional[float] = None


class EnhancedSessionService(SessionService):
    """Enhanced session service with VAT and fee calculations"""
    
    def __init__(self):
        super().__init__()
        self.fee_calculator = FeeCalculator()
        self.currency_formatter = CurrencyFormatter()
    
    def get_client_packages(self, client_id: int, trainer_id: int, 
                           active_only: bool = True) -> List[EnhancedSessionPackage]:
        """
        Get all session packages for a client with fee information
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, client_id, trainer_id, total_amount, session_price,
                           total_sessions, remaining_credits, remaining_sessions,
                           package_name, notes, created_at, updated_at, is_active,
                           gross_amount, vat_amount, card_fee_amount, net_amount,
                           vat_rate, card_fee_rate
                    FROM session_packages 
                    WHERE client_id = ? AND trainer_id = ?
                '''
                params = [client_id, trainer_id]
                
                if active_only:
                    if IS_PRODUCTION:
                        query += ' AND is_active = true'
                    else:
                        query += ' AND is_active = 1'
                
                query += ' ORDER BY created_at DESC'
                
                if IS_PRODUCTION:
                    query = query.replace('?', '%s')
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                packages = []
                for row in rows:
                    if isinstance(row, dict):
                        packages.append(EnhancedSessionPackage(
                            id=row['id'], client_id=row['client_id'], trainer_id=row['trainer_id'],
                            total_amount=row['total_amount'], session_price=row['session_price'],
                            total_sessions=row['total_sessions'], remaining_credits=row['remaining_credits'],
                            remaining_sessions=row['remaining_sessions'], package_name=row['package_name'],
                            notes=row['notes'], created_at=row['created_at'], updated_at=row['updated_at'],
                            is_active=bool(row['is_active']),
                            gross_amount=row['gross_amount'], vat_amount=row['vat_amount'],
                            card_fee_amount=row['card_fee_amount'], net_amount=row['net_amount'],
                            vat_rate=row['vat_rate'], card_fee_rate=row['card_fee_rate']
                        ))
                    else:
                        packages.append(EnhancedSessionPackage(
                            id=row[0], client_id=row[1], trainer_id=row[2],
                            total_amount=row[3], session_price=row[4],
                            total_sessions=row[5], remaining_credits=row[6],
                            remaining_sessions=row[7], package_name=row[8],
                            notes=row[9], created_at=row[10], updated_at=row[11],
                            is_active=bool(row[12]),
                            gross_amount=row[13], vat_amount=row[14],
                            card_fee_amount=row[15], net_amount=row[16],
                            vat_rate=row[17], card_fee_rate=row[18]
                        ))
                
                return packages
                
        except Exception as e:
            self.logger.error(f"Failed to get client packages: {e}")
            raise DatabaseError(f"Failed to get client packages: {e}")
    
    def create_session_package_with_fees(self, client_id: int, trainer_id: int,
                                       gross_amount: int, session_price: int,
                                       package_name: Optional[str] = None,
                                       notes: Optional[str] = None) -> int:
        """
        Create a new session package with VAT and fee calculations
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            gross_amount: Total amount charged (including all fees)
            session_price: Price per session (after fees)
            package_name: Optional name for the package
            notes: Optional notes
            
        Returns:
            ID of the created package
        """
        try:
            # Calculate fee breakdown
            fee_breakdown = self.fee_calculator.calculate_fee_breakdown(gross_amount)
            
            # Calculate sessions based on gross amount (before deductions)
            total_sessions = gross_amount // session_price
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    cursor.execute('''
                        INSERT INTO session_packages 
                        (client_id, trainer_id, gross_amount, vat_amount, 
                         card_fee_amount, net_amount, vat_rate, card_fee_rate,
                         total_amount, session_price, total_sessions, 
                         remaining_credits, remaining_sessions, package_name, 
                         notes, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    ''', (client_id, trainer_id, 
                          fee_breakdown['gross_amount'], fee_breakdown['vat_amount'],
                          fee_breakdown['card_fee_amount'], fee_breakdown['net_amount'],
                          fee_breakdown['vat_rate'], fee_breakdown['card_fee_rate'],
                          gross_amount, session_price, total_sessions,
                          fee_breakdown['net_amount'], total_sessions,
                          package_name, notes))
                    result = cursor.fetchone()
                    package_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    cursor.execute('''
                        INSERT INTO session_packages 
                        (client_id, trainer_id, gross_amount, vat_amount, 
                         card_fee_amount, net_amount, vat_rate, card_fee_rate,
                         total_amount, session_price, total_sessions, 
                         remaining_credits, remaining_sessions, package_name, 
                         notes, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (client_id, trainer_id, 
                          fee_breakdown['gross_amount'], fee_breakdown['vat_amount'],
                          fee_breakdown['card_fee_amount'], fee_breakdown['net_amount'],
                          fee_breakdown['vat_rate'], fee_breakdown['card_fee_rate'],
                          gross_amount, session_price, total_sessions,
                          fee_breakdown['net_amount'], total_sessions,
                          package_name, notes))
                    package_id = cursor.lastrowid
                
                # Record the payment with fee breakdown
                payment_id = self._record_payment_with_fees(
                    cursor, client_id, trainer_id, package_id,
                    fee_breakdown, "card", f"패키지 구매: {package_name or '기본 패키지'}"
                )
                
                # Create audit log
                FeeAuditLogger.create_audit_log(
                    self, package_id, payment_id, 'package_creation',
                    fee_breakdown, trainer_id
                )
                
                conn.commit()
                
                self.logger.info(f"Created package {package_id} with fees: "
                               f"gross={gross_amount}, net={fee_breakdown['net_amount']}")
                return package_id
                
        except Exception as e:
            self.logger.error(f"Failed to create package with fees: {e}")
            raise DatabaseError(f"Failed to create package with fees: {e}")
    
    def add_credits_with_fees(self, client_id: int, trainer_id: int, 
                            gross_amount: int, payment_method: Optional[str] = None,
                            description: Optional[str] = None) -> bool:
        """
        Add credits to the most recent active package with fee calculations
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            gross_amount: Total amount to add (including fees)
            payment_method: Payment method used
            description: Description of the payment
            
        Returns:
            True if successful
        """
        try:
            # Calculate fee breakdown
            fee_breakdown = self.fee_calculator.calculate_fee_breakdown(gross_amount)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get the most recent active package
                if IS_PRODUCTION:
                    cursor.execute('''
                        SELECT id, session_price, gross_amount, vat_amount, 
                               card_fee_amount, net_amount
                        FROM session_packages 
                        WHERE client_id = %s AND trainer_id = %s AND is_active = true
                        ORDER BY created_at DESC
                        LIMIT 1
                    ''', (client_id, trainer_id))
                else:
                    cursor.execute('''
                        SELECT id, session_price, gross_amount, vat_amount, 
                               card_fee_amount, net_amount
                        FROM session_packages 
                        WHERE client_id = ? AND trainer_id = ? AND is_active = 1
                        ORDER BY created_at DESC
                        LIMIT 1
                    ''', (client_id, trainer_id))
                
                package_info = cursor.fetchone()
                if not package_info:
                    raise ValueError("No active package found for client")
                
                # Handle both dict and tuple results
                if isinstance(package_info, dict):
                    package_id = package_info['id']
                    session_price = package_info['session_price']
                    current_gross = package_info['gross_amount'] or 0
                    current_vat = package_info['vat_amount'] or 0
                    current_card_fee = package_info['card_fee_amount'] or 0
                    current_net = package_info['net_amount'] or 0
                else:
                    package_id = package_info[0]
                    session_price = package_info[1]
                    current_gross = package_info[2] or 0
                    current_vat = package_info[3] or 0
                    current_card_fee = package_info[4] or 0
                    current_net = package_info[5] or 0
                
                # Calculate additional sessions based on gross amount (before deductions)
                additional_sessions = gross_amount // session_price
                
                # Update package with accumulated amounts
                if IS_PRODUCTION:
                    cursor.execute('''
                        UPDATE session_packages 
                        SET remaining_credits = remaining_credits + %s,
                            remaining_sessions = remaining_sessions + %s,
                            total_amount = total_amount + %s,
                            total_sessions = total_sessions + %s,
                            gross_amount = %s,
                            vat_amount = %s,
                            card_fee_amount = %s,
                            net_amount = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (fee_breakdown['net_amount'], additional_sessions, 
                          gross_amount, additional_sessions,
                          current_gross + fee_breakdown['gross_amount'],
                          current_vat + fee_breakdown['vat_amount'],
                          current_card_fee + fee_breakdown['card_fee_amount'],
                          current_net + fee_breakdown['net_amount'],
                          package_id))
                else:
                    cursor.execute('''
                        UPDATE session_packages 
                        SET remaining_credits = remaining_credits + ?,
                            remaining_sessions = remaining_sessions + ?,
                            total_amount = total_amount + ?,
                            total_sessions = total_sessions + ?,
                            gross_amount = ?,
                            vat_amount = ?,
                            card_fee_amount = ?,
                            net_amount = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (fee_breakdown['net_amount'], additional_sessions, 
                          gross_amount, additional_sessions,
                          current_gross + fee_breakdown['gross_amount'],
                          current_vat + fee_breakdown['vat_amount'],
                          current_card_fee + fee_breakdown['card_fee_amount'],
                          current_net + fee_breakdown['net_amount'],
                          package_id))
                
                # Record the payment with fee breakdown
                payment_id = self._record_payment_with_fees(
                    cursor, client_id, trainer_id, package_id,
                    fee_breakdown, payment_method or "card",
                    description or "크래딧 충전"
                )
                
                # Create audit log
                FeeAuditLogger.create_audit_log(
                    self, package_id, payment_id, 'credit_addition',
                    fee_breakdown, trainer_id
                )
                
                conn.commit()
                
                self.logger.info(f"Added {gross_amount} gross ({fee_breakdown['net_amount']} net) "
                               f"to package {package_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add credits with fees: {e}")
            raise DatabaseError(f"Failed to add credits with fees: {e}")
    
    def _record_payment_with_fees(self, cursor, client_id: int, trainer_id: int,
                                 package_id: Optional[int], fee_breakdown: Dict,
                                 payment_method: str, description: str) -> int:
        """Helper method to record payment with fee breakdown"""
        payment_date = datetime.now().strftime("%Y-%m-%d")
        
        if IS_PRODUCTION:
            cursor.execute('''
                INSERT INTO payments 
                (client_id, trainer_id, package_id, amount, gross_amount,
                 vat_amount, card_fee_amount, net_amount, vat_rate, 
                 card_fee_rate, payment_method, payment_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (client_id, trainer_id, package_id, fee_breakdown['gross_amount'],
                  fee_breakdown['gross_amount'], fee_breakdown['vat_amount'],
                  fee_breakdown['card_fee_amount'], fee_breakdown['net_amount'],
                  fee_breakdown['vat_rate'], fee_breakdown['card_fee_rate'],
                  payment_method, payment_date, description))
            result = cursor.fetchone()
            return result['id'] if isinstance(result, dict) else result[0]
        else:
            cursor.execute('''
                INSERT INTO payments 
                (client_id, trainer_id, package_id, amount, gross_amount,
                 vat_amount, card_fee_amount, net_amount, vat_rate, 
                 card_fee_rate, payment_method, payment_date, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (client_id, trainer_id, package_id, fee_breakdown['gross_amount'],
                  fee_breakdown['gross_amount'], fee_breakdown['vat_amount'],
                  fee_breakdown['card_fee_amount'], fee_breakdown['net_amount'],
                  fee_breakdown['vat_rate'], fee_breakdown['card_fee_rate'],
                  payment_method, payment_date, description))
            return cursor.lastrowid
    
    def get_enhanced_package_summary(self, package_id: int, trainer_id: int) -> Dict[str, Any]:
        """
        Get comprehensive package summary with fee breakdown
        
        Args:
            package_id: ID of the package
            trainer_id: ID of the trainer
            
        Returns:
            Dictionary with enhanced package details including fees
        """
        try:
            # Get base summary
            base_summary = super().get_package_summary(package_id, trainer_id)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get fee information
                if IS_PRODUCTION:
                    cursor.execute('''
                        SELECT gross_amount, vat_amount, card_fee_amount, 
                               net_amount, vat_rate, card_fee_rate
                        FROM session_packages 
                        WHERE id = %s AND trainer_id = %s
                    ''', (package_id, trainer_id))
                else:
                    cursor.execute('''
                        SELECT gross_amount, vat_amount, card_fee_amount, 
                               net_amount, vat_rate, card_fee_rate
                        FROM session_packages 
                        WHERE id = ? AND trainer_id = ?
                    ''', (package_id, trainer_id))
                
                fee_info = cursor.fetchone()
                
                if fee_info:
                    if isinstance(fee_info, dict):
                        fee_data = {
                            'gross_amount': fee_info['gross_amount'] or base_summary['package']['total_amount'],
                            'vat_amount': fee_info['vat_amount'] or 0,
                            'card_fee_amount': fee_info['card_fee_amount'] or 0,
                            'net_amount': fee_info['net_amount'] or base_summary['package']['total_amount'],
                            'vat_rate': fee_info['vat_rate'] or 0.10,
                            'card_fee_rate': fee_info['card_fee_rate'] or 0.035
                        }
                    else:
                        fee_data = {
                            'gross_amount': fee_info[0] or base_summary['package']['total_amount'],
                            'vat_amount': fee_info[1] or 0,
                            'card_fee_amount': fee_info[2] or 0,
                            'net_amount': fee_info[3] or base_summary['package']['total_amount'],
                            'vat_rate': fee_info[4] or 0.10,
                            'card_fee_rate': fee_info[5] or 0.035
                        }
                    
                    # Add fee information to the summary
                    base_summary['fee_breakdown'] = fee_data
                    
                    # Calculate usage based on net amount
                    net_amount = fee_data['net_amount']
                    remaining_credits = base_summary['package']['remaining_credits']
                    used_credits = net_amount - remaining_credits if net_amount else 0
                    
                    base_summary['usage_summary'] = {
                        'used_credits': used_credits,
                        'remaining_credits': remaining_credits,
                        'utilization_percentage': (used_credits / net_amount * 100) if net_amount > 0 else 0
                    }
                
                return base_summary
                
        except Exception as e:
            self.logger.error(f"Failed to get enhanced package summary: {e}")
            raise DatabaseError(f"Failed to get enhanced package summary: {e}")
    
    def get_enhanced_payment_history(self, client_id: int, trainer_id: int) -> List[EnhancedPaymentRecord]:
        """
        Get payment history with fee breakdown
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            
        Returns:
            List of EnhancedPaymentRecord objects
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if IS_PRODUCTION:
                    cursor.execute('''
                        SELECT id, client_id, trainer_id, package_id, amount,
                               gross_amount, vat_amount, card_fee_amount, net_amount,
                               vat_rate, card_fee_rate, payment_method, payment_date, 
                               description, created_at
                        FROM payments 
                        WHERE client_id = %s AND trainer_id = %s
                        ORDER BY payment_date DESC
                    ''', (client_id, trainer_id))
                else:
                    cursor.execute('''
                        SELECT id, client_id, trainer_id, package_id, amount,
                               gross_amount, vat_amount, card_fee_amount, net_amount,
                               vat_rate, card_fee_rate, payment_method, payment_date, 
                               description, created_at
                        FROM payments 
                        WHERE client_id = ? AND trainer_id = ?
                        ORDER BY payment_date DESC
                    ''', (client_id, trainer_id))
                
                rows = cursor.fetchall()
                
                payments = []
                for row in rows:
                    if isinstance(row, dict):
                        payments.append(EnhancedPaymentRecord(
                            id=row['id'], client_id=row['client_id'], trainer_id=row['trainer_id'],
                            package_id=row['package_id'], amount=row['amount'],
                            gross_amount=row['gross_amount'] or row['amount'],
                            vat_amount=row['vat_amount'] or 0,
                            card_fee_amount=row['card_fee_amount'] or 0,
                            net_amount=row['net_amount'] or row['amount'],
                            vat_rate=row['vat_rate'], card_fee_rate=row['card_fee_rate'],
                            payment_method=row['payment_method'], payment_date=row['payment_date'],
                            description=row['description'], created_at=row['created_at']
                        ))
                    else:
                        payments.append(EnhancedPaymentRecord(
                            id=row[0], client_id=row[1], trainer_id=row[2],
                            package_id=row[3], amount=row[4],
                            gross_amount=row[5] or row[4],
                            vat_amount=row[6] or 0,
                            card_fee_amount=row[7] or 0,
                            net_amount=row[8] or row[4],
                            vat_rate=row[9], card_fee_rate=row[10],
                            payment_method=row[11], payment_date=row[12],
                            description=row[13], created_at=row[14]
                        ))
                
                return payments
                
        except Exception as e:
            self.logger.error(f"Failed to get enhanced payment history: {e}")
            raise DatabaseError(f"Failed to get enhanced payment history: {e}")
    
    def execute_query(self, query: str, params: tuple, fetch_all: bool = True):
        """Execute a database query (for audit logging)"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if IS_PRODUCTION and params:
                query = query.replace('?', '%s')
            cursor.execute(query, params)
            if fetch_all:
                return cursor.fetchall()
            conn.commit()
            return cursor.lastrowid