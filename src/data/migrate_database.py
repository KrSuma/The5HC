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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until DATETIME,
            last_login DATETIME
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS trainers (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(200) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            last_login TIMESTAMP
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
            trainer_id INTEGER NOT NULL,
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
            farmer_carry_score INTEGER,
            farmer_carry_notes TEXT,
            harvard_step_test_heart_rate INTEGER,
            harvard_step_test_duration REAL,
            harvard_step_test_notes TEXT,
            overall_score REAL,
            strength_score REAL,
            mobility_score REAL,
            balance_score REAL,
            cardio_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (trainer_id) REFERENCES trainers (id)
        )
        """,
        postgresql_query="""
        CREATE TABLE IF NOT EXISTS assessments (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
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
            farmer_carry_score INTEGER,
            farmer_carry_notes TEXT,
            harvard_step_test_heart_rate INTEGER,
            harvard_step_test_duration FLOAT,
            harvard_step_test_notes TEXT,
            overall_score FLOAT,
            strength_score FLOAT,
            mobility_score FLOAT,
            balance_score FLOAT,
            cardio_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (trainer_id) REFERENCES trainers (id)
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
        
        # Add rate limit columns if needed
        if add_rate_limit_columns():
            logger.info("Rate limit columns verified/added successfully")
        
        # Add trainer_id column to assessments if needed
        if add_trainer_id_to_assessments():
            logger.info("trainer_id column verified/added to assessments table")
        
        # Add missing assessment columns if needed
        if add_missing_assessment_columns():
            logger.info("Missing assessment columns verified/added successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        logger.error(f"Failed query might be: {query[:200]}..." if 'query' in locals() else "Query not available")
        return False


def add_rate_limit_columns():
    """Add rate limiting columns to trainers table if they don't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if columns already exist
            if IS_PRODUCTION:
                # PostgreSQL check
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'trainers' 
                    AND column_name IN ('failed_login_attempts', 'locked_until', 'last_login')
                """)
                rows = cursor.fetchall()
                # Handle RealDictCursor results
                if rows and isinstance(rows[0], dict):
                    existing_columns = [row['column_name'] for row in rows]
                else:
                    existing_columns = [row[0] for row in rows] if rows else []
            else:
                # SQLite check
                cursor.execute("PRAGMA table_info(trainers)")
                columns_info = cursor.fetchall()
                existing_columns = [col[1] for col in columns_info]
            
            # Add missing columns
            if 'failed_login_attempts' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE trainers ADD COLUMN failed_login_attempts INTEGER DEFAULT 0",
                    postgresql_query="ALTER TABLE trainers ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added failed_login_attempts column to trainers table")
            
            if 'locked_until' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE trainers ADD COLUMN locked_until DATETIME",
                    postgresql_query="ALTER TABLE trainers ADD COLUMN locked_until TIMESTAMP"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added locked_until column to trainers table")
            
            if 'last_login' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE trainers ADD COLUMN last_login DATETIME",
                    postgresql_query="ALTER TABLE trainers ADD COLUMN last_login TIMESTAMP"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added last_login column to trainers table")
                
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error adding rate limit columns: {e}")
        return False


def add_missing_assessment_columns():
    """Add missing score columns to assessments table if they don't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Define columns to check and add
            columns_to_add = [
                ('farmer_carry_score', 'INTEGER', 'INTEGER'),
                ('harvard_step_test_heart_rate', 'INTEGER', 'INTEGER'), 
                ('harvard_step_test_duration', 'REAL', 'FLOAT')
            ]
            
            for column_name, sqlite_type, pg_type in columns_to_add:
                # Check if column already exists
                if IS_PRODUCTION:
                    # PostgreSQL check
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'assessments' 
                        AND column_name = %s
                    """, (column_name,))
                    result = cursor.fetchone()
                    column_exists = bool(result)
                else:
                    # SQLite check
                    cursor.execute("PRAGMA table_info(assessments)")
                    columns_info = cursor.fetchall()
                    column_exists = any(col[1] == column_name for col in columns_info)
                
                if not column_exists:
                    # Add column
                    alter_query = adapt_query_for_db(
                        sqlite_query=f"ALTER TABLE assessments ADD COLUMN {column_name} {sqlite_type}",
                        postgresql_query=f"ALTER TABLE assessments ADD COLUMN {column_name} {pg_type}"
                    )
                    execute_query(alter_query, fetch_all=False)
                    logger.info(f"Added {column_name} column to assessments table")
                else:
                    logger.info(f"{column_name} column already exists in assessments table")
                    
            conn.commit()
            return True
                
    except Exception as e:
        logger.error(f"Error adding missing assessment columns: {e}")
        return False


def add_trainer_id_to_assessments():
    """Add trainer_id column to assessments table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if column already exists
            if IS_PRODUCTION:
                # PostgreSQL check
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'assessments' 
                    AND column_name = 'trainer_id'
                """)
                result = cursor.fetchone()
                column_exists = bool(result)
            else:
                # SQLite check
                cursor.execute("PRAGMA table_info(assessments)")
                columns_info = cursor.fetchall()
                column_exists = any(col[1] == 'trainer_id' for col in columns_info)
            
            if not column_exists:
                # Add trainer_id column
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE assessments ADD COLUMN trainer_id INTEGER",
                    postgresql_query="ALTER TABLE assessments ADD COLUMN trainer_id INTEGER"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added trainer_id column to assessments table")
                
                # Update existing records to set trainer_id based on client's trainer
                update_query = adapt_query_for_db(
                    sqlite_query="""
                        UPDATE assessments 
                        SET trainer_id = (
                            SELECT trainer_id 
                            FROM clients 
                            WHERE clients.id = assessments.client_id
                        )
                        WHERE trainer_id IS NULL
                    """,
                    postgresql_query="""
                        UPDATE assessments 
                        SET trainer_id = clients.trainer_id
                        FROM clients 
                        WHERE clients.id = assessments.client_id
                        AND assessments.trainer_id IS NULL
                    """
                )
                execute_query(update_query, fetch_all=False)
                logger.info("Updated existing assessments with trainer_id")
                
                conn.commit()
                return True
            else:
                logger.info("trainer_id column already exists in assessments table")
                return True
                
    except Exception as e:
        logger.error(f"Error adding trainer_id column to assessments: {e}")
        return False


def add_missing_assessment_columns():
    """Add missing columns to assessments table"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check which columns exist
            if IS_PRODUCTION:
                # PostgreSQL check
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'assessments' 
                    AND column_name IN ('farmer_carry_score', 'harvard_step_test_heart_rate', 'harvard_step_test_duration')
                """)
                rows = cursor.fetchall()
                # Handle RealDictCursor results
                if rows and isinstance(rows[0], dict):
                    existing_columns = [row['column_name'] for row in rows]
                else:
                    existing_columns = [row[0] for row in rows] if rows else []
            else:
                # SQLite check
                cursor.execute("PRAGMA table_info(assessments)")
                columns_info = cursor.fetchall()
                existing_columns = [col[1] for col in columns_info]
            
            # Add missing columns
            if 'farmer_carry_score' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE assessments ADD COLUMN farmer_carry_score INTEGER",
                    postgresql_query="ALTER TABLE assessments ADD COLUMN farmer_carry_score INTEGER"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added farmer_carry_score column to assessments table")
            
            if 'harvard_step_test_heart_rate' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE assessments ADD COLUMN harvard_step_test_heart_rate INTEGER",
                    postgresql_query="ALTER TABLE assessments ADD COLUMN harvard_step_test_heart_rate INTEGER"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added harvard_step_test_heart_rate column to assessments table")
            
            if 'harvard_step_test_duration' not in existing_columns:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE assessments ADD COLUMN harvard_step_test_duration REAL",
                    postgresql_query="ALTER TABLE assessments ADD COLUMN harvard_step_test_duration FLOAT"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added harvard_step_test_duration column to assessments table")
                
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error adding missing assessment columns: {e}")
        return False


def add_trainer_id_to_session_tables():
    """Add trainer_id column to session-related tables if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Add updated_at column to session_packages first
            if IS_PRODUCTION:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'session_packages' 
                    AND column_name = 'updated_at'
                """)
                result = cursor.fetchone()
                updated_at_exists = bool(result)
            else:
                cursor.execute("PRAGMA table_info(session_packages)")
                columns_info = cursor.fetchall()
                updated_at_exists = any(col[1] == 'updated_at' for col in columns_info)
            
            if not updated_at_exists:
                alter_query = adapt_query_for_db(
                    sqlite_query="ALTER TABLE session_packages ADD COLUMN updated_at DATETIME",
                    postgresql_query="ALTER TABLE session_packages ADD COLUMN updated_at TIMESTAMP"
                )
                execute_query(alter_query, fetch_all=False)
                logger.info("Added updated_at column to session_packages table")
            
            # Tables to update with trainer_id
            tables_to_update = ['session_packages', 'sessions', 'payments']
            
            for table_name in tables_to_update:
                # Check if column already exists
                if IS_PRODUCTION:
                    # PostgreSQL check
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND column_name = 'trainer_id'
                    """, (table_name,))
                    result = cursor.fetchone()
                    column_exists = bool(result)
                else:
                    # SQLite check
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    column_exists = any(col[1] == 'trainer_id' for col in columns_info)
                
                if not column_exists:
                    # Add trainer_id column
                    alter_query = adapt_query_for_db(
                        sqlite_query=f"ALTER TABLE {table_name} ADD COLUMN trainer_id INTEGER",
                        postgresql_query=f"ALTER TABLE {table_name} ADD COLUMN trainer_id INTEGER"
                    )
                    execute_query(alter_query, fetch_all=False)
                    logger.info(f"Added trainer_id column to {table_name} table")
                    
                    # For existing records, set trainer_id based on client's trainer
                    if table_name in ['session_packages', 'sessions']:
                        update_query = adapt_query_for_db(
                            sqlite_query=f"""
                                UPDATE {table_name} 
                                SET trainer_id = (
                                    SELECT trainer_id 
                                    FROM clients 
                                    WHERE clients.id = {table_name}.client_id
                                )
                                WHERE trainer_id IS NULL
                            """,
                            postgresql_query=f"""
                                UPDATE {table_name} 
                                SET trainer_id = clients.trainer_id
                                FROM clients 
                                WHERE clients.id = {table_name}.client_id
                                AND {table_name}.trainer_id IS NULL
                            """
                        )
                        execute_query(update_query, fetch_all=False)
                        logger.info(f"Updated existing {table_name} records with trainer_id")
                    elif table_name == 'payments':
                        # For payments, get trainer_id through session_packages
                        update_query = adapt_query_for_db(
                            sqlite_query="""
                                UPDATE payments 
                                SET trainer_id = (
                                    SELECT trainer_id 
                                    FROM clients 
                                    WHERE clients.id = payments.client_id
                                )
                                WHERE trainer_id IS NULL AND package_id IS NOT NULL
                            """,
                            postgresql_query="""
                                UPDATE payments 
                                SET trainer_id = clients.trainer_id
                                FROM clients 
                                WHERE clients.id = payments.client_id
                                AND payments.trainer_id IS NULL 
                                AND payments.package_id IS NOT NULL
                            """
                        )
                        execute_query(update_query, fetch_all=False)
                        logger.info(f"Updated existing {table_name} records with trainer_id")
                else:
                    logger.info(f"trainer_id column already exists in {table_name} table")
                    
            conn.commit()
            return True
                
    except Exception as e:
        logger.error(f"Error adding trainer_id column to session tables: {e}")
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
        # Add any missing columns
        if add_missing_assessment_columns():
            logger.info("Missing assessment columns added successfully")
        
        # Add trainer_id to session tables
        if add_trainer_id_to_session_tables():
            logger.info("trainer_id columns added to session tables successfully")
        
        logger.info("Database migration completed successfully!")
        return True
    else:
        logger.error("Database migration failed!")
        return False


if __name__ == "__main__":
    run_migration()