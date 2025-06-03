"""
Database migration script for Heroku deployment
Handles creation of tables in PostgreSQL and data migration from SQLite
"""
import os
import logging
from src.data.database_config import get_db_connection, IS_PRODUCTION, execute_query, adapt_query_for_db

logger = logging.getLogger(__name__)


def create_tables():
    """Create all necessary tables for the application"""
    
    # Trainers table
    trainers_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS trainers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS trainers (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(200) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Clients table
    clients_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainer_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            email TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainer_id) REFERENCES trainers (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            trainer_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            age INTEGER NOT NULL,
            gender VARCHAR(20) NOT NULL,
            height FLOAT NOT NULL,
            weight FLOAT NOT NULL,
            email VARCHAR(200),
            phone VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainer_id) REFERENCES trainers (id)
        )
        """
    )
    
    # Assessments table
    assessments_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            date DATETIME NOT NULL,
            overhead_squat_score INTEGER,
            overhead_squat_notes TEXT,
            push_up_reps INTEGER,
            push_up_score INTEGER,
            push_up_notes TEXT,
            single_leg_balance_right_eyes_open INTEGER,
            single_leg_balance_left_eyes_open INTEGER,
            single_leg_balance_right_eyes_closed INTEGER,
            single_leg_balance_left_eyes_closed INTEGER,
            single_leg_balance_notes TEXT,
            toe_touch_distance REAL,
            toe_touch_score INTEGER,
            toe_touch_notes TEXT,
            shoulder_mobility_right REAL,
            shoulder_mobility_left REAL,
            shoulder_mobility_score INTEGER,
            shoulder_mobility_notes TEXT,
            farmer_carry_weight REAL,
            farmer_carry_distance REAL,
            farmer_carry_notes TEXT,
            harvard_step_test_notes TEXT,
            overall_score REAL,
            strength_score REAL,
            mobility_score REAL,
            balance_score REAL,
            cardio_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS assessments (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            date TIMESTAMP NOT NULL,
            overhead_squat_score INTEGER,
            overhead_squat_notes TEXT,
            push_up_reps INTEGER,
            push_up_score INTEGER,
            push_up_notes TEXT,
            single_leg_balance_right_eyes_open INTEGER,
            single_leg_balance_left_eyes_open INTEGER,
            single_leg_balance_right_eyes_closed INTEGER,
            single_leg_balance_left_eyes_closed INTEGER,
            single_leg_balance_notes TEXT,
            toe_touch_distance FLOAT,
            toe_touch_score INTEGER,
            toe_touch_notes TEXT,
            shoulder_mobility_right FLOAT,
            shoulder_mobility_left FLOAT,
            shoulder_mobility_score INTEGER,
            shoulder_mobility_notes TEXT,
            farmer_carry_weight FLOAT,
            farmer_carry_distance FLOAT,
            farmer_carry_notes TEXT,
            harvard_step_test_notes TEXT,
            overall_score FLOAT,
            strength_score FLOAT,
            mobility_score FLOAT,
            balance_score FLOAT,
            cardio_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        """
    )
    
    # Session management tables
    packages_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS session_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            package_name TEXT,
            total_amount REAL NOT NULL,
            session_price REAL NOT NULL,
            total_sessions INTEGER NOT NULL,
            remaining_sessions INTEGER NOT NULL,
            remaining_credits REAL NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS session_packages (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            package_name VARCHAR(200),
            total_amount FLOAT NOT NULL,
            session_price FLOAT NOT NULL,
            total_sessions INTEGER NOT NULL,
            remaining_sessions INTEGER NOT NULL,
            remaining_credits FLOAT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        """
    )
    
    sessions_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            package_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            session_time TIME,
            session_duration INTEGER NOT NULL,
            session_cost REAL NOT NULL,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (package_id) REFERENCES session_packages (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            package_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            session_time TIME,
            session_duration INTEGER NOT NULL,
            session_cost FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (package_id) REFERENCES session_packages (id)
        )
        """
    )
    
    payments_query = adapt_query_for_db(
        sqlite_query="""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            package_id INTEGER,
            amount REAL NOT NULL,
            payment_method TEXT,
            description TEXT,
            payment_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (package_id) REFERENCES session_packages (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            package_id INTEGER,
            amount FLOAT NOT NULL,
            payment_method VARCHAR(50),
            description TEXT,
            payment_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (package_id) REFERENCES session_packages (id)
        )
        """
    )
    
    # Execute all table creation queries
    tables = [
        ("trainers", trainers_query),
        ("clients", clients_query),
        ("assessments", assessments_query),
        ("session_packages", packages_query),
        ("sessions", sessions_query),
        ("payments", payments_query)
    ]
    
    try:
        for table_name, query in tables:
            logger.debug(f"Ensuring table exists: {table_name}")
            logger.debug(f"Using {'PostgreSQL' if IS_PRODUCTION else 'SQLite'} mode")
            logger.debug(f"Query for {table_name}: {query[:100]}...")  # Log first 100 chars of query
            execute_query(query, fetch_all=False)
            logger.debug(f"Table ready: {table_name}")
            
        logger.info("All tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        logger.error(f"Failed query might be: {query[:200]}..." if 'query' in locals() else "Query not available")
        return False


def run_migration():
    """Run the complete database migration"""
    logger.info("Starting database migration...")
    
    if IS_PRODUCTION:
        logger.info("Running migration for PostgreSQL (Production)")
    else:
        logger.info("Running migration for SQLite (Development)")
    
    # Create tables
    if create_tables():
        logger.info("Database migration completed successfully!")
        return True
    else:
        logger.error("Database migration failed!")
        return False


if __name__ == "__main__":
    run_migration()