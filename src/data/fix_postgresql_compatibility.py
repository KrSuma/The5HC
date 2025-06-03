"""
Fix PostgreSQL compatibility issues for Heroku deployment
"""
import logging
import os
from datetime import datetime
from src.data.database_config import get_db_connection, IS_PRODUCTION, execute_query

logger = logging.getLogger(__name__)


def fix_rate_limiting_columns():
    """Ensure rate limiting columns exist and have proper defaults"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if columns exist
            if IS_PRODUCTION:
                # PostgreSQL column check
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'trainers'
                """)
                columns = [row['column_name'] if isinstance(row, dict) else row[0] for row in cursor.fetchall()]
            else:
                # SQLite column check
                cursor.execute("PRAGMA table_info(trainers)")
                columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns if needed
            if 'failed_login_attempts' not in columns:
                logger.info("Adding failed_login_attempts column")
                cursor.execute("""
                    ALTER TABLE trainers 
                    ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
                """)
                conn.commit()
            
            if 'locked_until' not in columns:
                logger.info("Adding locked_until column")
                if IS_PRODUCTION:
                    cursor.execute("""
                        ALTER TABLE trainers 
                        ADD COLUMN locked_until TIMESTAMP
                    """)
                else:
                    cursor.execute("""
                        ALTER TABLE trainers 
                        ADD COLUMN locked_until DATETIME
                    """)
                conn.commit()
            
            # Set default values for NULL columns
            cursor.execute("""
                UPDATE trainers 
                SET failed_login_attempts = 0 
                WHERE failed_login_attempts IS NULL
            """)
            conn.commit()
            
            logger.info("Rate limiting columns fixed successfully")
            
    except Exception as e:
        logger.error(f"Failed to fix rate limiting columns: {e}")
        raise


def verify_password_hashes():
    """Verify that all password hashes are properly formatted"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all trainers with their password hashes
            cursor.execute("SELECT id, username, password_hash FROM trainers")
            trainers = cursor.fetchall()
            
            invalid_count = 0
            for trainer in trainers:
                if isinstance(trainer, dict):
                    trainer_id = trainer['id']
                    username = trainer['username']
                    password_hash = trainer['password_hash']
                else:
                    trainer_id = trainer[0]
                    username = trainer[1]
                    password_hash = trainer[2]
                
                # Check if password hash is valid bcrypt format
                if not password_hash or not password_hash.startswith('$2b$'):
                    invalid_count += 1
                    logger.warning(f"Invalid password hash for trainer {username} (ID: {trainer_id})")
                    
                    # You might want to reset these passwords or handle them differently
                    # For now, we'll just log the issue
            
            if invalid_count > 0:
                logger.warning(f"Found {invalid_count} trainers with invalid password hashes")
                logger.warning("These trainers will need to reset their passwords")
            else:
                logger.info("All password hashes are valid")
                
    except Exception as e:
        logger.error(f"Failed to verify password hashes: {e}")
        raise


def test_authentication():
    """Test authentication queries with proper result handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Test query
            if IS_PRODUCTION:
                cursor.execute("""
                    SELECT id, username, password_hash, failed_login_attempts, locked_until 
                    FROM trainers 
                    LIMIT 1
                """)
            else:
                cursor.execute("""
                    SELECT id, username, password_hash, failed_login_attempts, locked_until 
                    FROM trainers 
                    LIMIT 1
                """)
            
            result = cursor.fetchone()
            if result:
                if isinstance(result, dict):
                    logger.info("PostgreSQL RealDictCursor working correctly")
                    logger.info(f"Sample trainer: {result.get('username')}")
                else:
                    logger.info("SQLite Row object working correctly")
                    logger.info(f"Sample trainer: {result[1] if len(result) > 1 else 'N/A'}")
            else:
                logger.warning("No trainers found in database")
                
    except Exception as e:
        logger.error(f"Authentication test failed: {e}")
        raise


def main():
    """Run all compatibility fixes"""
    logger.info(f"Running PostgreSQL compatibility fixes (IS_PRODUCTION={IS_PRODUCTION})")
    
    try:
        # Fix rate limiting columns
        fix_rate_limiting_columns()
        
        # Verify password hashes
        verify_password_hashes()
        
        # Test authentication queries
        test_authentication()
        
        logger.info("All compatibility fixes completed successfully")
        
    except Exception as e:
        logger.error(f"Compatibility fix failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()