"""
Database configuration for both development (SQLite) and production (PostgreSQL)
"""
import os
import sqlite3
import logging
from typing import Optional, Any
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_PRODUCTION = bool(DATABASE_URL)

# Log configuration for debugging
logger.info(f"Database config: DATABASE_URL exists={bool(DATABASE_URL)}, IS_PRODUCTION={IS_PRODUCTION}")

if IS_PRODUCTION:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import urllib.parse
        logger.info("PostgreSQL driver imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import psycopg2: {e}")
        raise

    # Heroku DATABASE_URL starts with postgres:// but psycopg2 needs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Parse Heroku database URL
    parsed_url = urllib.parse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed_url.hostname,
        'port': parsed_url.port or 5432,
        'database': parsed_url.path[1:],  # Remove leading slash
        'user': parsed_url.username,
        'password': parsed_url.password,
        'sslmode': 'require'
    }
    logger.info(f"PostgreSQL config parsed: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
else:
    # Development SQLite configuration
    DB_CONFIG = {
        'db_path': 'data/fitness_assessment.db',
        'timeout': 30.0
    }


class DatabaseError(Exception):
    """Custom database exception"""
    pass


@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    conn = None
    try:
        if IS_PRODUCTION:
            # PostgreSQL connection
            logger.info(f"Connecting to PostgreSQL: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                sslmode=DB_CONFIG['sslmode'],
                cursor_factory=RealDictCursor
            )
            conn.autocommit = False
        else:
            # SQLite connection
            conn = sqlite3.connect(
                DB_CONFIG['db_path'],
                timeout=DB_CONFIG['timeout'],
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
        
        yield conn
        
        if IS_PRODUCTION:
            conn.commit()
        else:
            conn.commit()
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {type(e).__name__}: {str(e)}")
        logger.error(f"Database config: IS_PRODUCTION={IS_PRODUCTION}, DB_URL exists={bool(DATABASE_URL)}")
        if IS_PRODUCTION:
            logger.error(f"PostgreSQL config: host={DB_CONFIG.get('host')}, db={DB_CONFIG.get('database')}")
        raise DatabaseError(f"Database operation failed: {type(e).__name__}: {str(e)}")
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = True) -> Any:
    """
    Execute a database query with proper error handling
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: Return single row
        fetch_all: Return all rows
        
    Returns:
        Query results or None
    """
    try:
        # Convert SQLite-style placeholders to PostgreSQL-style if needed
        if IS_PRODUCTION and params:
            # Replace ? with %s for PostgreSQL
            query = query.replace('?', '%s')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all and cursor.description:
                return cursor.fetchall()
            else:
                return cursor.rowcount
                
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise DatabaseError(f"Query failed: {e}")


def get_sql_type():
    """Get SQL dialect type for query construction"""
    return "postgresql" if IS_PRODUCTION else "sqlite"


def adapt_query_for_db(sqlite_query: str, postgresql_query: str = None) -> str:
    """
    Adapt SQL query for current database type
    
    Args:
        sqlite_query: SQLite compatible query
        postgresql_query: PostgreSQL specific query (optional)
        
    Returns:
        Appropriate query for current database
    """
    if IS_PRODUCTION:
        if postgresql_query:
            return postgresql_query
        else:
            # Basic SQLite to PostgreSQL conversions
            query = sqlite_query
            # Handle AUTOINCREMENT properly - must replace the entire phrase
            query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            query = query.replace("DATETIME", "TIMESTAMP")
            query = query.replace("REAL", "FLOAT")
            query = query.replace("TEXT", "VARCHAR(255)")
            query = query.replace("BOOLEAN", "BOOLEAN")
            # Ensure no standalone AUTOINCREMENT remains
            query = query.replace("AUTOINCREMENT", "")
            return query
    else:
        return sqlite_query