"""
Migration to add VAT and card processing fee columns
"""
import logging
from src.data.database_config import get_db_connection, IS_PRODUCTION, execute_query, adapt_query_for_db
from decimal import Decimal

logger = logging.getLogger(__name__)


def add_fee_columns_to_session_packages():
    """Add fee-related columns to session_packages table"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Define columns to add
            columns_to_add = [
                ('gross_amount', 'INTEGER', 'INTEGER'),
                ('vat_amount', 'INTEGER', 'INTEGER'),
                ('card_fee_amount', 'INTEGER', 'INTEGER'),
                ('net_amount', 'INTEGER', 'INTEGER'),
                ('vat_rate', 'DECIMAL(5,2)', 'DECIMAL(5,2)', '0.10'),
                ('card_fee_rate', 'DECIMAL(5,2)', 'DECIMAL(5,2)', '0.035'),
                ('fee_calculation_method', 'TEXT', 'VARCHAR(20)', "'inclusive'")
            ]
            
            for column_info in columns_to_add:
                column_name = column_info[0]
                sqlite_type = column_info[1]
                pg_type = column_info[2]
                default_value = column_info[3] if len(column_info) > 3 else None
                
                # Check if column already exists
                if IS_PRODUCTION:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'session_packages' 
                        AND column_name = %s
                    """, (column_name,))
                    result = cursor.fetchone()
                    column_exists = bool(result)
                else:
                    cursor.execute("PRAGMA table_info(session_packages)")
                    columns_info = cursor.fetchall()
                    column_exists = any(col[1] == column_name for col in columns_info)
                
                if not column_exists:
                    # Build ALTER TABLE query
                    if default_value:
                        alter_query = adapt_query_for_db(
                            sqlite_query=f"ALTER TABLE session_packages ADD COLUMN {column_name} {sqlite_type} DEFAULT {default_value}",
                            postgresql_query=f"ALTER TABLE session_packages ADD COLUMN {column_name} {pg_type} DEFAULT {default_value}"
                        )
                    else:
                        alter_query = adapt_query_for_db(
                            sqlite_query=f"ALTER TABLE session_packages ADD COLUMN {column_name} {sqlite_type}",
                            postgresql_query=f"ALTER TABLE session_packages ADD COLUMN {column_name} {pg_type}"
                        )
                    
                    execute_query(alter_query, fetch_all=False)
                    logger.info(f"Added {column_name} column to session_packages table")
                else:
                    logger.info(f"{column_name} column already exists in session_packages table")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error adding fee columns to session_packages: {e}")
        return False


def add_fee_columns_to_payments():
    """Add fee-related columns to payments table"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Define columns to add
            columns_to_add = [
                ('gross_amount', 'INTEGER', 'INTEGER'),
                ('vat_amount', 'INTEGER', 'INTEGER'),
                ('card_fee_amount', 'INTEGER', 'INTEGER'),
                ('net_amount', 'INTEGER', 'INTEGER'),
                ('vat_rate', 'DECIMAL(5,2)', 'DECIMAL(5,2)'),
                ('card_fee_rate', 'DECIMAL(5,2)', 'DECIMAL(5,2)')
            ]
            
            for column_info in columns_to_add:
                column_name = column_info[0]
                sqlite_type = column_info[1]
                pg_type = column_info[2]
                
                # Check if column already exists
                if IS_PRODUCTION:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'payments' 
                        AND column_name = %s
                    """, (column_name,))
                    result = cursor.fetchone()
                    column_exists = bool(result)
                else:
                    cursor.execute("PRAGMA table_info(payments)")
                    columns_info = cursor.fetchall()
                    column_exists = any(col[1] == column_name for col in columns_info)
                
                if not column_exists:
                    alter_query = adapt_query_for_db(
                        sqlite_query=f"ALTER TABLE payments ADD COLUMN {column_name} {sqlite_type}",
                        postgresql_query=f"ALTER TABLE payments ADD COLUMN {column_name} {pg_type}"
                    )
                    
                    execute_query(alter_query, fetch_all=False)
                    logger.info(f"Added {column_name} column to payments table")
                else:
                    logger.info(f"{column_name} column already exists in payments table")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error adding fee columns to payments: {e}")
        return False


def create_fee_audit_log_table():
    """Create fee_audit_log table for tracking fee calculations"""
    try:
        # Create fee_audit_log table
        create_query = adapt_query_for_db(
            sqlite_query="""
            CREATE TABLE IF NOT EXISTS fee_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_id INTEGER,
                payment_id INTEGER,
                calculation_type TEXT NOT NULL,
                gross_amount INTEGER NOT NULL,
                vat_amount INTEGER NOT NULL,
                card_fee_amount INTEGER NOT NULL,
                net_amount INTEGER NOT NULL,
                vat_rate DECIMAL(5,2) NOT NULL,
                card_fee_rate DECIMAL(5,2) NOT NULL,
                calculation_details TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (package_id) REFERENCES session_packages(id),
                FOREIGN KEY (payment_id) REFERENCES payments(id),
                FOREIGN KEY (created_by) REFERENCES trainers(id)
            )
            """,
            postgresql_query="""
            CREATE TABLE IF NOT EXISTS fee_audit_log (
                id SERIAL PRIMARY KEY,
                package_id INTEGER,
                payment_id INTEGER,
                calculation_type VARCHAR(20) NOT NULL,
                gross_amount INTEGER NOT NULL,
                vat_amount INTEGER NOT NULL,
                card_fee_amount INTEGER NOT NULL,
                net_amount INTEGER NOT NULL,
                vat_rate DECIMAL(5,2) NOT NULL,
                card_fee_rate DECIMAL(5,2) NOT NULL,
                calculation_details TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (package_id) REFERENCES session_packages(id),
                FOREIGN KEY (payment_id) REFERENCES payments(id),
                FOREIGN KEY (created_by) REFERENCES trainers(id)
            )
            """
        )
        
        execute_query(create_query, fetch_all=False)
        logger.info("Created fee_audit_log table successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating fee_audit_log table: {e}")
        return False


def migrate_existing_data():
    """Migrate existing package and payment data to include fee calculations"""
    try:
        from src.utils.fee_calculator import FeeCalculator
        
        calculator = FeeCalculator()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Migrate session_packages
            logger.info("Migrating existing session packages...")
            
            # Get all packages without fee data
            cursor.execute("""
                SELECT id, total_amount, session_price, total_sessions, remaining_sessions, remaining_credits
                FROM session_packages 
                WHERE gross_amount IS NULL
            """)
            
            packages = cursor.fetchall()
            logger.info(f"Found {len(packages)} packages to migrate")
            
            for package in packages:
                if IS_PRODUCTION and isinstance(package, dict):
                    # Handle RealDictCursor
                    pkg_id = package['id']
                    total_amount = int(package['total_amount'])
                    session_price = int(package['session_price'])
                    total_sessions = package['total_sessions']
                    remaining_sessions = package['remaining_sessions']
                    remaining_credits = int(package['remaining_credits'])
                else:
                    # Handle tuple results
                    pkg_id, total_amount, session_price, total_sessions, remaining_sessions, remaining_credits = package
                    total_amount = int(total_amount)
                    session_price = int(session_price)
                    remaining_credits = int(remaining_credits)
                
                # Calculate fee breakdown assuming total_amount was gross
                breakdown = calculator.calculate_fee_breakdown(total_amount)
                
                # Calculate the proportion of credits used
                if total_amount > 0:
                    usage_ratio = remaining_credits / total_amount
                else:
                    usage_ratio = 1.0
                
                # Recalculate based on gross amount (before deductions)
                new_total_sessions = total_amount // session_price
                new_remaining_credits = int(breakdown['net_amount'] * usage_ratio)
                
                # Adjust remaining sessions proportionally
                if total_sessions > 0:
                    session_ratio = remaining_sessions / total_sessions
                    new_remaining_sessions = int(new_total_sessions * session_ratio)
                else:
                    new_remaining_sessions = new_total_sessions
                
                # Update package
                update_query = """
                    UPDATE session_packages 
                    SET gross_amount = %s,
                        vat_amount = %s,
                        card_fee_amount = %s,
                        net_amount = %s,
                        vat_rate = %s,
                        card_fee_rate = %s,
                        total_sessions = %s,
                        remaining_sessions = %s,
                        remaining_credits = %s
                    WHERE id = %s
                """
                
                if IS_PRODUCTION:
                    cursor.execute(update_query, (
                        breakdown['gross_amount'],
                        breakdown['vat_amount'],
                        breakdown['card_fee_amount'],
                        breakdown['net_amount'],
                        breakdown['vat_rate'],
                        breakdown['card_fee_rate'],
                        new_total_sessions,
                        new_remaining_sessions,
                        new_remaining_credits,
                        pkg_id
                    ))
                else:
                    cursor.execute(update_query.replace('%s', '?'), (
                        breakdown['gross_amount'],
                        breakdown['vat_amount'],
                        breakdown['card_fee_amount'],
                        breakdown['net_amount'],
                        breakdown['vat_rate'],
                        breakdown['card_fee_rate'],
                        new_total_sessions,
                        new_remaining_sessions,
                        new_remaining_credits,
                        pkg_id
                    ))
                
                logger.info(f"Migrated package {pkg_id}: {total_amount} -> {breakdown['net_amount']} (net)")
            
            # Migrate payments
            logger.info("Migrating existing payments...")
            
            cursor.execute("""
                SELECT id, amount
                FROM payments 
                WHERE gross_amount IS NULL
            """)
            
            payments = cursor.fetchall()
            logger.info(f"Found {len(payments)} payments to migrate")
            
            for payment in payments:
                if IS_PRODUCTION and isinstance(payment, dict):
                    payment_id = payment['id']
                    amount = int(payment['amount'])
                else:
                    payment_id, amount = payment
                    amount = int(amount)
                
                # Calculate fee breakdown
                breakdown = calculator.calculate_fee_breakdown(amount)
                
                # Update payment
                update_query = """
                    UPDATE payments 
                    SET gross_amount = %s,
                        vat_amount = %s,
                        card_fee_amount = %s,
                        net_amount = %s,
                        vat_rate = %s,
                        card_fee_rate = %s
                    WHERE id = %s
                """
                
                if IS_PRODUCTION:
                    cursor.execute(update_query, (
                        breakdown['gross_amount'],
                        breakdown['vat_amount'],
                        breakdown['card_fee_amount'],
                        breakdown['net_amount'],
                        breakdown['vat_rate'],
                        breakdown['card_fee_rate'],
                        payment_id
                    ))
                else:
                    cursor.execute(update_query.replace('%s', '?'), (
                        breakdown['gross_amount'],
                        breakdown['vat_amount'],
                        breakdown['card_fee_amount'],
                        breakdown['net_amount'],
                        breakdown['vat_rate'],
                        breakdown['card_fee_rate'],
                        payment_id
                    ))
                
                logger.info(f"Migrated payment {payment_id}: {amount} -> {breakdown['net_amount']} (net)")
            
            conn.commit()
            logger.info("Data migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error migrating existing data: {e}")
        return False


def run_fee_migration():
    """Run the complete fee columns migration"""
    logger.info("Starting fee columns migration...")
    
    # Step 1: Add columns to session_packages
    if not add_fee_columns_to_session_packages():
        logger.error("Failed to add fee columns to session_packages")
        return False
    
    # Step 2: Add columns to payments
    if not add_fee_columns_to_payments():
        logger.error("Failed to add fee columns to payments")
        return False
    
    # Step 3: Create fee_audit_log table
    if not create_fee_audit_log_table():
        logger.error("Failed to create fee_audit_log table")
        return False
    
    # Step 4: Migrate existing data
    if not migrate_existing_data():
        logger.error("Failed to migrate existing data")
        return False
    
    logger.info("Fee columns migration completed successfully!")
    return True


if __name__ == "__main__":
    run_fee_migration()