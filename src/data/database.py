"""
Secure database utilities with improved password hashing and connection management
"""
import bcrypt
import secrets
import logging
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, timedelta
import re

# Import database configuration
from src.data.database_config import get_db_connection, DatabaseError, execute_query, adapt_query_for_db, IS_PRODUCTION


def execute_db_query(cursor, query: str, params: tuple = None):
    """Execute query with proper placeholder conversion for PostgreSQL"""
    if IS_PRODUCTION and params:
        # Convert SQLite ? placeholders to PostgreSQL %s
        query = query.replace('?', '%s')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fitness_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize the database with all necessary tables and indexes"""
    try:
        # For now, always run create_tables since it uses CREATE TABLE IF NOT EXISTS
        # This is safer and handles all edge cases
        from src.data.migrate_database import create_tables
        
        if create_tables():
            logger.info("Database initialized successfully")
        else:
            raise DatabaseError("Failed to create tables")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


# Password hashing and verification with bcrypt
def hash_password(password: str) -> str:
    """Hash password using bcrypt with automatic salt generation"""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)  # Adaptive cost factor
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    return hashed.decode('utf-8')


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify password using bcrypt"""
    try:
        if not stored_hash or not provided_password:
            return False
            
        # Ensure stored_hash is properly formatted
        if isinstance(stored_hash, str) and stored_hash.startswith('$2b$'):
            return bcrypt.checkpw(
                provided_password.encode('utf-8'), 
                stored_hash.encode('utf-8')
            )
        else:
            logger.error(f"Invalid password hash format: {stored_hash[:10] if stored_hash else 'None'}...")
            return False
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        logger.error(f"Hash format check: starts with $2b$: {stored_hash.startswith('$2b$') if stored_hash else 'N/A'}")
        return False


# Input validation and sanitization
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(value: Any, max_length: int = 255) -> str:
    """Sanitize user input"""
    if value is None:
        return ""
    
    # Convert to string and strip whitespace
    sanitized = str(value).strip()
    
    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    
    # Limit length
    return sanitized[:max_length]


# Rate limiting for authentication
class AuthRateLimiter:
    def __init__(self, max_attempts: int = 5, window_minutes: int = 5):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
    
    def check_rate_limit(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """Check if user has exceeded rate limit"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                execute_db_query(c, """
                    SELECT failed_login_attempts, locked_until 
                    FROM trainers 
                    WHERE username = ?
                """, (username,))
                
                result = c.fetchone()
                if not result:
                    return True, None
                
                # Handle both dict (PostgreSQL) and tuple/Row (SQLite) results
                if isinstance(result, dict):
                    attempts = result.get('failed_login_attempts', 0)
                    locked_until = result.get('locked_until')
                else:
                    attempts = result['failed_login_attempts'] if hasattr(result, '__getitem__') else result[0]
                    locked_until = result['locked_until'] if hasattr(result, '__getitem__') else result[1]
                
                # Check if account is locked
                if locked_until:
                    locked_time = datetime.fromisoformat(locked_until)
                    if datetime.now() < locked_time:
                        return False, locked_time
                    else:
                        # Reset lock
                        execute_db_query(c, """
                            UPDATE trainers 
                            SET failed_login_attempts = 0, locked_until = NULL 
                            WHERE username = ?
                        """, (username,))
                        conn.commit()
                
                return attempts < self.max_attempts, None
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, None
    
    def record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                # Increment failed attempts
                execute_db_query(c, """
                    UPDATE trainers 
                    SET failed_login_attempts = failed_login_attempts + 1 
                    WHERE username = ?
                """, (username,))
                
                # Check if we need to lock the account
                execute_db_query(c, """
                    SELECT failed_login_attempts 
                    FROM trainers 
                    WHERE username = ?
                """, (username,))
                
                result = c.fetchone()
                if result:
                    # Handle both dict (PostgreSQL) and tuple/Row (SQLite) results
                    if isinstance(result, dict):
                        attempts = result.get('failed_login_attempts', 0)
                    else:
                        attempts = result['failed_login_attempts'] if hasattr(result, '__getitem__') else result[0]
                    
                    if attempts >= self.max_attempts:
                        lock_until = datetime.now() + timedelta(minutes=self.window_minutes)
                        execute_db_query(c, """
                            UPDATE trainers 
                            SET locked_until = ? 
                            WHERE username = ?
                        """, (lock_until.isoformat(), username))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")
    
    def reset_attempts(self, username: str):
        """Reset failed login attempts on successful login"""
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                execute_db_query(c, """
                    UPDATE trainers 
                    SET failed_login_attempts = 0, 
                        locked_until = NULL,
                        last_login = CURRENT_TIMESTAMP
                    WHERE username = ?
                """, (username,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to reset attempts: {e}")


# Trainer management functions
rate_limiter = AuthRateLimiter()


def register_trainer(username: str, password: str, name: str, email: str) -> bool:
    """Register a new trainer with secure password hashing"""
    try:
        # Validate inputs
        username = sanitize_input(username, 50)
        name = sanitize_input(name, 100)
        email = sanitize_input(email, 100)
        
        if not username or not name:
            raise ValueError("Username and name are required")
        
        if not validate_email(email):
            raise ValueError("Invalid email format")
        
        # Hash password
        password_hash = hash_password(password)
        
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, """
                INSERT INTO trainers (username, password_hash, name, email) 
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, name, email))
            conn.commit()
            
        logger.info(f"Trainer registered successfully: {username}")
        return True
        
    except Exception as e:
        if "duplicate key value" in str(e).lower() or "unique constraint" in str(e).lower():
            logger.warning(f"Registration failed - username already exists: {username}")
            return False
        else:
            logger.error(f"Registration failed: {e}")
            return False


def authenticate(username: str, password: str) -> Optional[int]:
    """Authenticate trainer with rate limiting"""
    try:
        # Check rate limit
        allowed, locked_until = rate_limiter.check_rate_limit(username)
        if not allowed:
            logger.warning(f"Login attempt blocked due to rate limit: {username}")
            return None
        
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, """
                SELECT id, password_hash 
                FROM trainers 
                WHERE username = ?
            """, (username,))
            
            result = c.fetchone()
            if result:
                # Handle both dict (PostgreSQL) and tuple/Row (SQLite) results
                if isinstance(result, dict):
                    trainer_id = result.get('id')
                    stored_hash = result.get('password_hash')
                else:
                    trainer_id = result['id'] if hasattr(result, '__getitem__') else result[0]
                    stored_hash = result['password_hash'] if hasattr(result, '__getitem__') else result[1]
                
                if stored_hash and verify_password(stored_hash, password):
                    rate_limiter.reset_attempts(username)
                    logger.info(f"Successful login: {username}")
                    return trainer_id
            
            # Record failed attempt
            rate_limiter.record_failed_attempt(username)
            logger.warning(f"Failed login attempt: {username}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


# Client management functions
def add_client(trainer_id: int, name: str, age: int, gender: str, 
               height: float, weight: float, email: str = "", phone: str = "") -> Optional[int]:
    """Add a new client with input validation"""
    try:
        # Validate and sanitize inputs
        name = sanitize_input(name, 100)
        email = sanitize_input(email, 100)
        phone = sanitize_input(phone, 20)
        
        if not name:
            raise ValueError("Name is required")
        
        if email and not validate_email(email):
            raise ValueError("Invalid email format")
        
        if age < 5 or age > 120:
            raise ValueError("Age must be between 5 and 120")
        
        if height < 50 or height > 300:
            raise ValueError("Height must be between 50 and 300 cm")
        
        if weight < 10 or weight > 500:
            raise ValueError("Weight must be between 10 and 500 kg")
        
        if gender not in ['남성', '여성', '기타', 'Male', 'Female', 'Other']:
            raise ValueError("Invalid gender value")
        
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, """
                INSERT INTO clients 
                (trainer_id, name, age, gender, height, weight, email, phone) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (trainer_id, name, age, gender, height, weight, email, phone))
            conn.commit()
            
            client_id = c.lastrowid
            logger.info(f"Client added successfully: {client_id}")
            return client_id
            
    except Exception as e:
        logger.error(f"Failed to add client: {e}")
        raise


def get_clients(trainer_id: int) -> List[Tuple[int, str]]:
    """Get all clients for a trainer"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, """
                SELECT id, name 
                FROM clients 
                WHERE trainer_id = ? 
                ORDER BY name
            """, (trainer_id,))
            
            rows = c.fetchall()
            if rows:
                # Handle both dict (PostgreSQL) and Row (SQLite) results
                if isinstance(rows[0], dict):
                    return [(row['id'], row['name']) for row in rows]
                else:
                    return [(row[0], row[1]) for row in rows]
            return []
            
    except Exception as e:
        logger.error(f"Failed to get clients: {e}")
        return []


def get_client_details(client_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed client information"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, "SELECT * FROM clients WHERE id = ?", (client_id,))
            row = c.fetchone()
            
            if row:
                # Handle both dict (PostgreSQL) and Row (SQLite) results
                if isinstance(row, dict):
                    return row
                else:
                    return dict(row)
            return None
            
    except Exception as e:
        logger.error(f"Failed to get client details: {e}")
        return None


# Assessment management functions
def save_assessment(assessment_data: Dict[str, Any]) -> Optional[int]:
    """Save assessment with validation"""
    try:
        # Validate required fields
        required_fields = ['client_id', 'trainer_id', 'date']
        for field in required_fields:
            if field not in assessment_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare columns and values
        columns = list(assessment_data.keys())
        placeholders = ['?' for _ in columns]
        values = [assessment_data[col] for col in columns]
        
        with get_db_connection() as conn:
            c = conn.cursor()
            query = f"""
                INSERT INTO assessments ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)})
            """
            execute_db_query(c, query, values)
            conn.commit()
            
            assessment_id = c.lastrowid
            logger.info(f"Assessment saved successfully: {assessment_id}")
            return assessment_id
            
    except Exception as e:
        logger.error(f"Failed to save assessment: {e}")
        raise


def get_assessments(client_id: int) -> List[Dict[str, Any]]:
    """Get all assessments for a client"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, """
                SELECT id, date, overall_score 
                FROM assessments 
                WHERE client_id = ? 
                ORDER BY date DESC
            """, (client_id,))
            
            rows = c.fetchall()
            if rows:
                # Handle both dict (PostgreSQL) and Row (SQLite) results
                if isinstance(rows[0], dict):
                    return rows
                else:
                    return [dict(row) for row in rows]
            return []
            
    except Exception as e:
        logger.error(f"Failed to get assessments: {e}")
        return []


def get_assessment_details(assessment_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed assessment information"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            execute_db_query(c, "SELECT * FROM assessments WHERE id = ?", (assessment_id,))
            row = c.fetchone()
            
            if row:
                # Handle both dict (PostgreSQL) and Row (SQLite) results
                if isinstance(row, dict):
                    return row
                else:
                    return dict(row)
            return None
            
    except Exception as e:
        logger.error(f"Failed to get assessment details: {e}")
        return None


# Trainer statistics
def get_trainer_stats(trainer_id: int) -> Dict[str, Any]:
    """Get trainer statistics with optimized query"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Single query with CTEs for better performance
            execute_db_query(c, """
                WITH stats AS (
                    SELECT 
                        COUNT(DISTINCT c.id) as total_clients,
                        COUNT(DISTINCT a.id) as total_assessments,
                        AVG(a.overall_score) as avg_score,
                        MAX(a.date) as last_assessment_date
                    FROM trainers t
                    LEFT JOIN clients c ON t.id = c.trainer_id
                    LEFT JOIN assessments a ON t.id = a.trainer_id
                    WHERE t.id = ?
                )
                SELECT * FROM stats
            """, (trainer_id,))
            
            result = c.fetchone()
            if result:
                # Handle both dict (PostgreSQL) and Row (SQLite) results
                if isinstance(result, dict):
                    stats = result
                else:
                    stats = dict(result)
                # Handle NULL values
                stats['total_clients'] = stats['total_clients'] or 0
                stats['total_assessments'] = stats['total_assessments'] or 0
                stats['avg_score'] = round(stats['avg_score'], 1) if stats['avg_score'] else 0
                return stats
            
            return {
                'total_clients': 0,
                'total_assessments': 0,
                'avg_score': 0,
                'last_assessment_date': None
            }
            
    except Exception as e:
        logger.error(f"Failed to get trainer stats: {e}")
        return {
            'total_clients': 0,
            'total_assessments': 0,
            'avg_score': 0,
            'last_assessment_date': None
        }


# Migration function for existing database
def migrate_to_bcrypt():
    """Migrate existing passwords to bcrypt (one-time migration)"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if we have the old schema
            execute_db_query(c, "PRAGMA table_info(trainers)")
            columns = [col[1] for col in c.fetchall()]
            
            if 'password_hash' not in columns:
                # Add new column
                execute_db_query(c, "ALTER TABLE trainers ADD COLUMN password_hash TEXT")
                
                # Note: Existing passwords would need to be reset since we can't 
                # convert from HMAC-SHA256 to bcrypt without the original password
                logger.warning("Password migration required - users will need to reset passwords")
                
            conn.commit()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    # Initialize database when module is run directly
    init_db()