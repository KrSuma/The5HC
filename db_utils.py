# db_utils.py - Database utilities and functions

import sqlite3
import hashlib
from datetime import datetime


# Initialize database
def init_db():
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    # Create trainers table
    c.execute('''
              CREATE TABLE IF NOT EXISTS trainers
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY,
                  username
                  TEXT
                  UNIQUE
                  NOT
                  NULL,
                  password
                  TEXT
                  NOT
                  NULL,
                  name
                  TEXT
                  NOT
                  NULL,
                  email
                  TEXT
                  UNIQUE
                  NOT
                  NULL
              )
              ''')

    # Create clients table
    c.execute('''
              CREATE TABLE IF NOT EXISTS clients
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY,
                  trainer_id
                  INTEGER
                  NOT
                  NULL,
                  name
                  TEXT
                  NOT
                  NULL,
                  age
                  INTEGER
                  NOT
                  NULL,
                  gender
                  TEXT
                  NOT
                  NULL,
                  height
                  REAL
                  NOT
                  NULL,
                  weight
                  REAL
                  NOT
                  NULL,
                  email
                  TEXT,
                  phone
                  TEXT,
                  registration_date
                  TEXT
                  NOT
                  NULL,
                  FOREIGN
                  KEY
              (
                  trainer_id
              ) REFERENCES trainers
              (
                  id
              )
                  )
              ''')

    # Create assessments table
    c.execute('''
              CREATE TABLE IF NOT EXISTS assessments
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY,
                  client_id
                  INTEGER
                  NOT
                  NULL,
                  trainer_id
                  INTEGER
                  NOT
                  NULL,
                  date
                  TEXT
                  NOT
                  NULL,

                  overhead_squat_score
                  INTEGER,
                  overhead_squat_notes
                  TEXT,

                  push_up_score
                  INTEGER,
                  push_up_reps
                  INTEGER,
                  push_up_notes
                  TEXT,

                  single_leg_balance_right_open
                  INTEGER,
                  single_leg_balance_left_open
                  INTEGER,
                  single_leg_balance_right_closed
                  INTEGER,
                  single_leg_balance_left_closed
                  INTEGER,
                  single_leg_balance_notes
                  TEXT,

                  toe_touch_score
                  INTEGER,
                  toe_touch_distance
                  REAL,
                  toe_touch_notes
                  TEXT,

                  shoulder_mobility_right
                  REAL,
                  shoulder_mobility_left
                  REAL,
                  shoulder_mobility_score
                  INTEGER,
                  shoulder_mobility_notes
                  TEXT,

                  farmers_carry_weight
                  REAL,
                  farmers_carry_distance
                  REAL,
                  farmers_carry_time
                  REAL,
                  farmers_carry_score
                  INTEGER,
                  farmers_carry_notes
                  TEXT,

                  step_test_hr1
                  INTEGER,
                  step_test_hr2
                  INTEGER,
                  step_test_hr3
                  INTEGER,
                  step_test_pfi
                  REAL,
                  step_test_score
                  INTEGER,
                  step_test_notes
                  TEXT,

                  overall_score
                  REAL,
                  strength_score
                  REAL,
                  mobility_score
                  REAL,
                  balance_score
                  REAL,
                  cardio_score
                  REAL,

                  FOREIGN
                  KEY
              (
                  client_id
              ) REFERENCES clients
              (
                  id
              ),
                  FOREIGN KEY
              (
                  trainer_id
              ) REFERENCES trainers
              (
                  id
              )
                  )
              ''')

    conn.commit()
    conn.close()


# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# User authentication
def authenticate(username, password):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    c.execute("SELECT id, password FROM trainers WHERE username = ?", (username,))
    result = c.fetchone()

    conn.close()

    if result and result[1] == hash_password(password):
        return result[0]  # Return trainer_id
    return None


# User registration
def register_trainer(username, password, name, email):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO trainers (username, password, name, email) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), name, email)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False

    conn.close()
    return success


# Add a new client
def add_client(trainer_id, name, age, gender, height, weight, email, phone):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    registration_date = datetime.now().strftime("%Y-%m-%d")

    c.execute(
        "INSERT INTO clients (trainer_id, name, age, gender, height, weight, email, phone, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (trainer_id, name, age, gender, height, weight, email, phone, registration_date)
    )

    conn.commit()
    client_id = c.lastrowid
    conn.close()

    return client_id


# Get clients for a trainer
def get_clients(trainer_id):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    c.execute("SELECT id, name FROM clients WHERE trainer_id = ? ORDER BY name", (trainer_id,))
    clients = c.fetchall()

    conn.close()
    return clients


# Get client details
def get_client_details(client_id):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    c.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = c.fetchone()

    conn.close()

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


# Save assessment data
def save_assessment(assessment_data):
    conn = sqlite3.connect('fitness_assessment.db')
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
    conn.close()

    return assessment_id


# Get assessments for a client
def get_client_assessments(client_id):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    c.execute("SELECT id, date, overall_score FROM assessments WHERE client_id = ? ORDER BY date DESC", (client_id,))
    assessments = c.fetchall()

    conn.close()
    return assessments


# Get specific assessment details
def get_assessment_details(assessment_id):
    conn = sqlite3.connect('fitness_assessment.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    assessment = dict(c.fetchone())

    conn.close()
    return assessment


# Get recent assessments for dashboard
def get_recent_assessments(trainer_id, limit = 10):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    c.execute("""
              SELECT a.id, c.name, a.date, a.overall_score
              FROM assessments a
                       JOIN clients c ON a.client_id = c.id
              WHERE a.trainer_id = ?
              ORDER BY a.date DESC LIMIT ?
              """, (trainer_id, limit))

    assessments = c.fetchall()
    conn.close()
    return assessments


# Get stats for dashboard
def get_trainer_stats(trainer_id):
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    # Count total clients
    c.execute("SELECT COUNT(*) FROM clients WHERE trainer_id = ?", (trainer_id,))
    total_clients = c.fetchone()[0]

    # Count total assessments
    c.execute("SELECT COUNT(*) FROM assessments WHERE trainer_id = ?", (trainer_id,))
    total_assessments = c.fetchone()[0]

    conn.close()
    return {
        'total_clients': total_clients,
        'total_assessments': total_assessments
    }