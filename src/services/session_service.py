"""
Session Management Service for tracking training sessions, credits, and payments
"""
import sqlite3
import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, date
from contextlib import contextmanager
from dataclasses import dataclass

# Import database connection utilities
from src.data.database import get_db_connection, DatabaseError
from src.data.database_config import IS_PRODUCTION

logger = logging.getLogger(__name__)


@dataclass
class SessionPackage:
    """Data class for session packages"""
    id: Optional[int]
    client_id: int
    trainer_id: int
    total_amount: int
    session_price: int
    total_sessions: int
    remaining_credits: int
    remaining_sessions: int
    package_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True


@dataclass
class TrainingSession:
    """Data class for training sessions"""
    id: Optional[int]
    client_id: int
    trainer_id: int
    package_id: int
    session_date: str
    session_time: Optional[str]
    session_duration: int
    session_cost: int
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class PaymentRecord:
    """Data class for payment records"""
    id: Optional[int]
    client_id: int
    trainer_id: int
    package_id: Optional[int]
    amount: int
    payment_method: Optional[str]
    payment_date: str
    description: Optional[str] = None
    created_at: Optional[str] = None


class SessionService:
    """Service for managing training sessions, credits, and payments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_session_package(self, client_id: int, trainer_id: int, 
                              total_amount: int, session_price: int,
                              package_name: Optional[str] = None,
                              notes: Optional[str] = None) -> int:
        """
        Create a new session package for a client
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            total_amount: Total amount paid (in KRW)
            session_price: Price per session (in KRW)
            package_name: Optional name for the package
            notes: Optional notes
            
        Returns:
            ID of the created package
        """
        try:
            total_sessions = total_amount // session_price
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    cursor.execute('''
                        INSERT INTO session_packages 
                        (client_id, trainer_id, total_amount, session_price, 
                         total_sessions, remaining_credits, remaining_sessions,
                         package_name, notes, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    ''', (client_id, trainer_id, total_amount, session_price,
                          total_sessions, total_amount, total_sessions,
                          package_name, notes))
                    result = cursor.fetchone()
                    package_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    cursor.execute('''
                        INSERT INTO session_packages 
                        (client_id, trainer_id, total_amount, session_price, 
                         total_sessions, remaining_credits, remaining_sessions,
                         package_name, notes, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (client_id, trainer_id, total_amount, session_price,
                          total_sessions, total_amount, total_sessions,
                          package_name, notes))
                    package_id = cursor.lastrowid
                
                # Record the payment
                self._record_payment(cursor, client_id, trainer_id, package_id,
                                   total_amount, "Package Purchase", 
                                   datetime.now().strftime("%Y-%m-%d"))
                
                conn.commit()
                self.logger.info(f"Created session package {package_id} for client {client_id}")
                return package_id
                
        except Exception as e:
            self.logger.error(f"Failed to create session package: {e}")
            raise DatabaseError(f"Failed to create session package: {e}")
    
    def get_client_packages(self, client_id: int, trainer_id: int, 
                           active_only: bool = True) -> List[SessionPackage]:
        """
        Get all session packages for a client
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            active_only: Whether to return only active packages
            
        Returns:
            List of SessionPackage objects
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, client_id, trainer_id, total_amount, session_price,
                           total_sessions, remaining_credits, remaining_sessions,
                           package_name, notes, created_at, updated_at, is_active
                    FROM session_packages 
                    WHERE client_id = ? AND trainer_id = ?
                '''
                params = [client_id, trainer_id]
                
                if active_only:
                    query += ' AND is_active = 1'
                
                query += ' ORDER BY created_at DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                packages = []
                for row in rows:
                    packages.append(SessionPackage(
                        id=row[0], client_id=row[1], trainer_id=row[2],
                        total_amount=row[3], session_price=row[4],
                        total_sessions=row[5], remaining_credits=row[6],
                        remaining_sessions=row[7], package_name=row[8],
                        notes=row[9], created_at=row[10], updated_at=row[11],
                        is_active=bool(row[12])
                    ))
                
                return packages
                
        except Exception as e:
            self.logger.error(f"Failed to get client packages: {e}")
            raise DatabaseError(f"Failed to get client packages: {e}")
    
    def schedule_session(self, client_id: int, trainer_id: int, package_id: int,
                        session_date: str, session_time: Optional[str] = None,
                        session_duration: int = 60, notes: Optional[str] = None) -> int:
        """
        Schedule a new training session
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            package_id: ID of the session package
            session_date: Date of the session (YYYY-MM-DD format)
            session_time: Time of the session (HH:MM format)
            session_duration: Duration in minutes
            notes: Optional notes
            
        Returns:
            ID of the created session
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get package info
                cursor.execute('''
                    SELECT session_price, remaining_sessions, remaining_credits
                    FROM session_packages 
                    WHERE id = ? AND client_id = ? AND trainer_id = ? AND is_active = 1
                ''', (package_id, client_id, trainer_id))
                
                package_info = cursor.fetchone()
                if not package_info:
                    raise ValueError("Invalid package or package not active")
                
                session_price, remaining_sessions, remaining_credits = package_info
                
                if remaining_sessions <= 0 or remaining_credits < session_price:
                    raise ValueError("Not enough sessions or credits remaining")
                
                # Create the session
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    cursor.execute('''
                        INSERT INTO training_sessions 
                        (client_id, trainer_id, package_id, session_date, session_time,
                         session_duration, session_cost, status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled', %s)
                        RETURNING id
                    ''', (client_id, trainer_id, package_id, session_date, session_time,
                          session_duration, session_price, notes))
                    result = cursor.fetchone()
                    session_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    cursor.execute('''
                        INSERT INTO training_sessions 
                        (client_id, trainer_id, package_id, session_date, session_time,
                         session_duration, session_cost, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
                    ''', (client_id, trainer_id, package_id, session_date, session_time,
                          session_duration, session_price, notes))
                    session_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Scheduled session {session_id} for client {client_id}")
                return session_id
                
        except Exception as e:
            self.logger.error(f"Failed to schedule session: {e}")
            raise DatabaseError(f"Failed to schedule session: {e}")
    
    def complete_session(self, session_id: int, trainer_id: int, 
                        notes: Optional[str] = None) -> bool:
        """
        Mark a session as completed and deduct credits
        
        Args:
            session_id: ID of the session
            trainer_id: ID of the trainer (for security)
            notes: Optional completion notes
            
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get session info
                cursor.execute('''
                    SELECT package_id, session_cost, status, client_id
                    FROM training_sessions 
                    WHERE id = ? AND trainer_id = ?
                ''', (session_id, trainer_id))
                
                session_info = cursor.fetchone()
                if not session_info:
                    raise ValueError("Session not found or access denied")
                
                package_id, session_cost, status, client_id = session_info
                
                if status == 'completed':
                    raise ValueError("Session already completed")
                
                # Update session status
                cursor.execute('''
                    UPDATE training_sessions 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, notes = ?
                    WHERE id = ?
                ''', (notes, session_id))
                
                # Update package credits and sessions
                cursor.execute('''
                    UPDATE session_packages 
                    SET remaining_credits = remaining_credits - ?,
                        remaining_sessions = remaining_sessions - 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (session_cost, package_id))
                
                conn.commit()
                
                self.logger.info(f"Completed session {session_id}, deducted {session_cost} credits")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to complete session: {e}")
            raise DatabaseError(f"Failed to complete session: {e}")
    
    def cancel_session(self, session_id: int, trainer_id: int, 
                      reason: Optional[str] = None) -> bool:
        """
        Cancel a scheduled session
        
        Args:
            session_id: ID of the session
            trainer_id: ID of the trainer (for security)
            reason: Optional cancellation reason
            
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Update session status
                cursor.execute('''
                    UPDATE training_sessions 
                    SET status = 'cancelled', notes = ?
                    WHERE id = ? AND trainer_id = ? AND status = 'scheduled'
                ''', (reason, session_id, trainer_id))
                
                if cursor.rowcount == 0:
                    raise ValueError("Session not found, access denied, or already processed")
                
                conn.commit()
                
                self.logger.info(f"Cancelled session {session_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to cancel session: {e}")
            raise DatabaseError(f"Failed to cancel session: {e}")
    
    def get_client_sessions(self, client_id: int, trainer_id: int, 
                           status: Optional[str] = None) -> List[TrainingSession]:
        """
        Get all sessions for a client
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            status: Optional status filter ('scheduled', 'completed', 'cancelled')
            
        Returns:
            List of TrainingSession objects
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, client_id, trainer_id, package_id, session_date,
                           session_time, session_duration, session_cost, status,
                           notes, created_at, completed_at
                    FROM training_sessions 
                    WHERE client_id = ? AND trainer_id = ?
                '''
                params = [client_id, trainer_id]
                
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                
                query += ' ORDER BY session_date DESC, session_time DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append(TrainingSession(
                        id=row[0], client_id=row[1], trainer_id=row[2],
                        package_id=row[3], session_date=row[4], session_time=row[5],
                        session_duration=row[6], session_cost=row[7], status=row[8],
                        notes=row[9], created_at=row[10], completed_at=row[11]
                    ))
                
                return sessions
                
        except Exception as e:
            self.logger.error(f"Failed to get client sessions: {e}")
            raise DatabaseError(f"Failed to get client sessions: {e}")
    
    def get_package_summary(self, package_id: int, trainer_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary of a session package
        
        Args:
            package_id: ID of the package
            trainer_id: ID of the trainer (for security)
            
        Returns:
            Dictionary with package details and session history
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get package details
                cursor.execute('''
                    SELECT sp.*, c.name as client_name
                    FROM session_packages sp
                    JOIN clients c ON sp.client_id = c.id
                    WHERE sp.id = ? AND sp.trainer_id = ?
                ''', (package_id, trainer_id))
                
                package_row = cursor.fetchone()
                if not package_row:
                    raise ValueError("Package not found or access denied")
                
                # Get session history
                cursor.execute('''
                    SELECT id, session_date, session_time, session_cost, status, notes
                    FROM training_sessions 
                    WHERE package_id = ? AND trainer_id = ?
                    ORDER BY session_date DESC
                ''', (package_id, trainer_id))
                
                sessions = cursor.fetchall()
                
                # Calculate statistics
                completed_sessions = len([s for s in sessions if s[4] == 'completed'])
                scheduled_sessions = len([s for s in sessions if s[4] == 'scheduled'])
                total_spent = sum(s[3] for s in sessions if s[4] == 'completed')
                
                return {
                    'package': {
                        'id': package_row[0],
                        'client_name': package_row[-1],
                        'total_amount': package_row[3],
                        'session_price': package_row[4],
                        'total_sessions': package_row[5],
                        'remaining_credits': package_row[6],
                        'remaining_sessions': package_row[7],
                        'package_name': package_row[8],
                        'created_at': package_row[10],
                        'is_active': bool(package_row[12])
                    },
                    'sessions': [
                        {
                            'id': s[0], 'date': s[1], 'time': s[2],
                            'cost': s[3], 'status': s[4], 'notes': s[5]
                        } for s in sessions
                    ],
                    'statistics': {
                        'completed_sessions': completed_sessions,
                        'scheduled_sessions': scheduled_sessions,
                        'total_spent': total_spent,
                        'utilization_rate': (completed_sessions / package_row[5] * 100) if package_row[5] > 0 else 0
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get package summary: {e}")
            raise DatabaseError(f"Failed to get package summary: {e}")
    
    def add_credits(self, client_id: int, trainer_id: int, amount: int,
                   payment_method: Optional[str] = None, 
                   description: Optional[str] = None) -> bool:
        """
        Add credits to the most recent active package
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            amount: Amount to add (in KRW)
            payment_method: Payment method used
            description: Description of the payment
            
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get the most recent active package
                cursor.execute('''
                    SELECT id, session_price
                    FROM session_packages 
                    WHERE client_id = ? AND trainer_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (client_id, trainer_id))
                
                package_info = cursor.fetchone()
                if not package_info:
                    raise ValueError("No active package found for client")
                
                package_id, session_price = package_info
                additional_sessions = amount // session_price
                
                # Update package credits
                cursor.execute('''
                    UPDATE session_packages 
                    SET remaining_credits = remaining_credits + ?,
                        remaining_sessions = remaining_sessions + ?,
                        total_amount = total_amount + ?,
                        total_sessions = total_sessions + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (amount, additional_sessions, amount, additional_sessions, package_id))
                
                # Record the payment
                self._record_payment(cursor, client_id, trainer_id, package_id,
                                   amount, payment_method or "Credit Top-up",
                                   datetime.now().strftime("%Y-%m-%d"), description)
                
                conn.commit()
                
                self.logger.info(f"Added {amount} credits ({additional_sessions} sessions) to package {package_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add credits: {e}")
            raise DatabaseError(f"Failed to add credits: {e}")
    
    def _record_payment(self, cursor, client_id: int, trainer_id: int,
                       package_id: Optional[int], amount: int,
                       payment_method: str, payment_date: str,
                       description: Optional[str] = None):
        """Helper method to record payment"""
        if IS_PRODUCTION:
            cursor.execute('''
                INSERT INTO payment_records 
                (client_id, trainer_id, package_id, amount, payment_method, 
                 payment_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (client_id, trainer_id, package_id, amount, payment_method,
                  payment_date, description))
        else:
            cursor.execute('''
                INSERT INTO payment_records 
                (client_id, trainer_id, package_id, amount, payment_method, 
                 payment_date, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (client_id, trainer_id, package_id, amount, payment_method,
                  payment_date, description))
    
    def get_payment_history(self, client_id: int, trainer_id: int) -> List[PaymentRecord]:
        """
        Get payment history for a client
        
        Args:
            client_id: ID of the client
            trainer_id: ID of the trainer
            
        Returns:
            List of PaymentRecord objects
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, client_id, trainer_id, package_id, amount,
                           payment_method, payment_date, description, created_at
                    FROM payment_records 
                    WHERE client_id = ? AND trainer_id = ?
                    ORDER BY payment_date DESC
                ''', (client_id, trainer_id))
                
                rows = cursor.fetchall()
                
                payments = []
                for row in rows:
                    payments.append(PaymentRecord(
                        id=row[0], client_id=row[1], trainer_id=row[2],
                        package_id=row[3], amount=row[4], payment_method=row[5],
                        payment_date=row[6], description=row[7], created_at=row[8]
                    ))
                
                return payments
                
        except Exception as e:
            self.logger.error(f"Failed to get payment history: {e}")
            raise DatabaseError(f"Failed to get payment history: {e}")