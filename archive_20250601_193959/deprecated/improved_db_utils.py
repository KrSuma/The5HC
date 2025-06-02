# db_utils.py - Database utilities and functions with improved error handling and security

import sqlite3
import hashlib
import os
import hmac
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union


# Initialize database with context manager
def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()

            # Create trainers table
            c.execute('''
                CREATE TABLE IF NOT EXISTS trainers
                (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL
                )
                ''')

            # Create clients table
            c.execute('''
                CREATE TABLE IF NOT EXISTS clients
                (
                    id INTEGER PRIMARY KEY,
                    trainer_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    height REAL NOT NULL,
                    weight REAL NOT NULL,
                    email TEXT,
                    phone TEXT,
                    registration_date TEXT NOT NULL,
                    FOREIGN KEY (trainer_id) REFERENCES trainers (id)
                )
                ''')

            # Create assessments table
            c.execute('''
                CREATE TABLE IF NOT EXISTS assessments
                (
                    id INTEGER PRIMARY KEY,
                    client_id INTEGER NOT NULL,
                    trainer_id INTEGER NOT NULL,
                    date TEXT NOT NULL,

                    overhead_squat_score INTEGER,
                    overhead_squat_notes TEXT,

                    push_up_score INTEGER,
                    push_up_reps INTEGER,
                    push_up_notes TEXT,

                    single_leg_balance_right_open INTEGER,
                    single_leg_balance_left_open INTEGER,
                    single_leg_balance_right_closed INTEGER,
                    single_leg_balance_left_closed INTEGER,
                    single_leg_balance_notes TEXT,

                    toe_touch_score INTEGER,
                    toe_touch_distance REAL,
                    toe_touch_notes TEXT,

                    shoulder_mobility_right REAL,
                    shoulder_mobility_left REAL,
                    shoulder_mobility_score INTEGER,
                    shoulder_mobility_notes TEXT,

                    farmers_carry_weight REAL,
                    farmers_carry_distance REAL,
                    farmers_carry_time REAL,
                    farmers_carry_score INTEGER,
                    farmers_carry_notes TEXT,

                    step_test_hr1 INTEGER,
                    step_test_hr2 INTEGER,
                    step_test_hr3 INTEGER,
                    step_test_pfi REAL,
                    step_test_score INTEGER,
                    step_test_notes TEXT,

                    overall_score REAL,
                    strength_score REAL,
                    mobility_score REAL,
                    balance_score REAL,
                    cardio_score REAL,

                    FOREIGN KEY (client_id) REFERENCES clients (id),
                    FOREIGN KEY (trainer_id) REFERENCES trainers (id)
                )
                ''')

            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise


# Improved password hashing with salt
def hash_password(password: str) -> Tuple[str, str]:
    """
    Hash a password with a random salt.
    
    Args:
        password: The password to hash
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    salt = os.urandom(16)
    salt_hex = salt.hex()
    pwdhash = hmac.new(salt, password.encode(), hashlib.sha256).digest().hex()
    return pwdhash, salt_hex


# Verify a password against a stored hash and salt
def verify_password(stored_password: str, salt: str, provided_password: str) -> bool:
    """
    Verify a password against a stored hash and salt.
    
    Args:
        stored_password: The stored password hash
        salt: The stored salt in hexadecimal format
        provided_password: The password to verify
        
    Returns:
        True if the password matches, False otherwise
    """
    salt_bytes = bytes.fromhex(salt)
    pwdhash = hmac.new(salt_bytes, provided_password.encode(), hashlib.sha256).digest().hex()
    return pwdhash == stored_password


# User authentication with improved security
def authenticate(username: str, password: str) -> Optional[int]:
    """
    Authenticate a user with the given username and password.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        The trainer ID if authentication is successful, None otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, password, salt FROM trainers WHERE username = ?", (username,))
            result = c.fetchone()

            if result and verify_password(result[1], result[2], password):
                return result[0]  # Return trainer_id
            return None
    except sqlite3.Error as e:
        print(f"Authentication error: {e}")
        return None


# User registration with improved security
def register_trainer(username: str, password: str, name: str, email: str) -> bool:
    """
    Register a new trainer with the given details.
    
    Args:
        username: The username for the new trainer
        password: The password for the new trainer
        name: The name of the new trainer
        email: The email of the new trainer
        
    Returns:
        True if registration is successful, False otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            
            # Hash the password with a salt
            password_hash, salt = hash_password(password)
            
            c.execute(
                "INSERT INTO trainers (username, password, salt, name, email) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, salt, name, email)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        # Username or email already exists
        return False
    except sqlite3.Error as e:
        print(f"Registration error: {e}")
        return False


# Add a new client with improved error handling
def add_client(trainer_id: int, name: str, age: int, gender: str, height: float, 
               weight: float, email: str, phone: str) -> Optional[int]:
    """
    Add a new client for the given trainer.
    
    Args:
        trainer_id: The ID of the trainer adding the client
        name: The name of the client
        age: The age of the client
        gender: The gender of the client
        height: The height of the client in cm
        weight: The weight of the client in kg
        email: The email of the client
        phone: The phone number of the client
        
    Returns:
        The client ID if successful, None otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            registration_date = datetime.now().strftime("%Y-%m-%d")

            c.execute(
                "INSERT INTO clients (trainer_id, name, age, gender, height, weight, email, phone, registration_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (trainer_id, name, age, gender, height, weight, email, phone, registration_date)
            )
            conn.commit()
            return c.lastrowid
    except sqlite3.Error as e:
        print(f"Add client error: {e}")
        return None


# Get clients for a trainer with error handling
def get_clients(trainer_id: int) -> List[Tuple[int, str]]:
    """
    Get all clients for the given trainer.
    
    Args:
        trainer_id: The ID of the trainer
        
    Returns:
        A list of tuples containing client IDs and names
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, name FROM clients WHERE trainer_id = ? ORDER BY name", (trainer_id,))
            clients = c.fetchall()
            return clients
    except sqlite3.Error as e:
        print(f"Get clients error: {e}")
        return []


# Get client details with improved error handling and return types
def get_client_details(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the details of the client with the given ID.
    
    Args:
        client_id: The ID of the client
        
    Returns:
        A dictionary containing the client details if found, None otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            client = c.fetchone()

            if client:
                return {
                    'id': client[0],
                    'trainer_id': client[1],
                    'name': client[2],
                    'age': client[3],
                    'gender': client[4],
                    'height': client[5],
                    'weight': client[6],
                    'email': client[7],
                    'phone': client[8],
                    'registration_date': client[9]
                }
            return None
    except sqlite3.Error as e:
        print(f"Get client details error: {e}")
        return None


# Save assessment data with improved error handling
def save_assessment(assessment_data: Dict[str, Any]) -> Optional[int]:
    """
    Save an assessment with the given data.
    
    Args:
        assessment_data: A dictionary containing the assessment data
        
    Returns:
        The assessment ID if successful, None otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()

            c.execute('''
                INSERT INTO assessments (client_id, trainer_id, date,
                                        overhead_squat_score, overhead_squat_notes,
                                        push_up_score, push_up_reps, push_up_notes,
                                        single_leg_balance_right_open, single_leg_balance_left_open,
                                        single_leg_balance_right_closed, single_leg_balance_left_closed,
                                        single_leg_balance_notes,
                                        toe_touch_score, toe_touch_distance, toe_touch_notes,
                                        shoulder_mobility_right, shoulder_mobility_left, shoulder_mobility_score,
                                        shoulder_mobility_notes,
                                        farmers_carry_weight, farmers_carry_distance, farmers_carry_time,
                                        farmers_carry_score, farmers_carry_notes,
                                        step_test_hr1, step_test_hr2, step_test_hr3, step_test_pfi, step_test_score,
                                        step_test_notes,
                                        overall_score, strength_score, mobility_score, balance_score, cardio_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?)
                ''', (
                    assessment_data['client_id'], assessment_data['trainer_id'], assessment_data['date'],
                    assessment_data['overhead_squat_score'], assessment_data['overhead_squat_notes'],
                    assessment_data['push_up_score'], assessment_data['push_up_reps'], assessment_data['push_up_notes'],
                    assessment_data['single_leg_balance_right_open'], assessment_data['single_leg_balance_left_open'],
                    assessment_data['single_leg_balance_right_closed'], assessment_data['single_leg_balance_left_closed'],
                    assessment_data['single_leg_balance_notes'],
                    assessment_data['toe_touch_score'], assessment_data['toe_touch_distance'],
                    assessment_data['toe_touch_notes'],
                    assessment_data['shoulder_mobility_right'], assessment_data['shoulder_mobility_left'],
                    assessment_data['shoulder_mobility_score'], assessment_data['shoulder_mobility_notes'],
                    assessment_data['farmers_carry_weight'], assessment_data['farmers_carry_distance'],
                    assessment_data['farmers_carry_time'], assessment_data['farmers_carry_score'],
                    assessment_data['farmers_carry_notes'],
                    assessment_data['step_test_hr1'], assessment_data['step_test_hr2'], assessment_data['step_test_hr3'],
                    assessment_data['step_test_pfi'], assessment_data['step_test_score'],
                    assessment_data['step_test_notes'],
                    assessment_data['overall_score'], assessment_data['strength_score'],
                    assessment_data['mobility_score'], assessment_data['balance_score'], assessment_data['cardio_score']
                ))

            assessment_id = c.lastrowid
            conn.commit()
            return assessment_id
    except sqlite3.Error as e:
        print(f"Save assessment error: {e}")
        return None


# Get assessments for a client with improved error handling
def get_client_assessments(client_id: int) -> List[Tuple[int, str, float]]:
    """
    Get all assessments for the given client.
    
    Args:
        client_id: The ID of the client
        
    Returns:
        A list of tuples containing assessment ID, date, and overall score
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, date, overall_score FROM assessments WHERE client_id = ? ORDER BY date DESC", 
                (client_id,)
            )
            assessments = c.fetchall()
            return assessments
    except sqlite3.Error as e:
        print(f"Get client assessments error: {e}")
        return []


# Get specific assessment details with improved error handling
def get_assessment_details(assessment_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the details of the assessment with the given ID.
    
    Args:
        assessment_id: The ID of the assessment
        
    Returns:
        A dictionary containing the assessment details if found, None otherwise
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
            assessment = c.fetchone()
            return dict(assessment) if assessment else None
    except sqlite3.Error as e:
        print(f"Get assessment details error: {e}")
        return None


# Get recent assessments for dashboard with improved error handling
def get_recent_assessments(trainer_id: int, limit: int = 10) -> List[Tuple[int, str, str, float]]:
    """
    Get recent assessments for the given trainer.
    
    Args:
        trainer_id: The ID of the trainer
        limit: The maximum number of assessments to return
        
    Returns:
        A list of tuples containing assessment ID, client name, date, and overall score
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            c.execute("""
                SELECT a.id, c.name, a.date, a.overall_score
                FROM assessments a
                JOIN clients c ON a.client_id = c.id
                WHERE a.trainer_id = ?
                ORDER BY a.date DESC LIMIT ?
                """, (trainer_id, limit))
            return c.fetchall()
    except sqlite3.Error as e:
        print(f"Get recent assessments error: {e}")
        return []


# Get stats for dashboard with improved error handling and query optimization
def get_trainer_stats(trainer_id: int) -> Dict[str, int]:
    """
    Get statistics for the given trainer.
    
    Args:
        trainer_id: The ID of the trainer
        
    Returns:
        A dictionary containing statistics for the trainer
    """
    try:
        with sqlite3.connect('fitness_assessment.db') as conn:
            c = conn.cursor()
            
            # Optimized query to get both counts in one go
            c.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM clients WHERE trainer_id = ?) AS total_clients,
                    (SELECT COUNT(*) FROM assessments WHERE trainer_id = ?) AS total_assessments
                """, (trainer_id, trainer_id))
            
            result = c.fetchone()
            
            return {
                'total_clients': result[0],
                'total_assessments': result[1]
            }
    except sqlite3.Error as e:
        print(f"Get trainer stats error: {e}")
        return {'total_clients': 0, 'total_assessments': 0}
