#!/usr/bin/env python
"""
Main Data Migration Script from Streamlit to Django
Migrates all data from the cleaned Streamlit SQLite database to Django models

Version: 2.0 - Updated for cleaned database structure
"""

import os
import sys
import sqlite3
import django
from datetime import datetime
from decimal import Decimal
import json
import logging
from pathlib import Path

# Setup Django environment
django_project_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(django_project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings_minimal')
django.setup()

# Import Django models
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from apps.clients.models import Client
from apps.assessments.models import Assessment
try:
    from apps.sessions.models import SessionPackage, Session, Payment
except ImportError:
    # Fall back to training_sessions if sessions app doesn't exist
    from apps.training_sessions.models import SessionPackage, Session, Payment

User = get_user_model()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StreamlitToJangoMigrator:
    """Migrates data from cleaned Streamlit SQLite database to Django models."""
    
    def __init__(self, source_db_path):
        self.source_db_path = source_db_path
        self.conn = None
        self.cursor = None
        self.trainer_map = {}  # Maps old trainer IDs to new User objects
        self.client_map = {}   # Maps old client IDs to new Client objects
        self.package_map = {}  # Maps old package IDs to new SessionPackage objects
        self.stats = {
            'trainers': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'clients': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'assessments': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'session_packages': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'sessions': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0},
            'payments': {'processed': 0, 'created': 0, 'skipped': 0, 'errors': 0}
        }
        
    def connect(self):
        """Connect to the source SQLite database."""
        try:
            self.conn = sqlite3.connect(self.source_db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to Streamlit database: {self.source_db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def migrate_all(self):
        """Run all migrations in order."""
        logger.info("Starting data migration from Streamlit to Django...")
        
        try:
            self.connect()
            
            # Use Django's transaction to ensure atomicity
            with transaction.atomic():
                # Migrate in dependency order
                self.migrate_trainers()
                self.migrate_clients()
                self.migrate_assessments()
                self.migrate_session_packages()
                self.migrate_sessions()
                self.migrate_payments()
                
            logger.info("Migration completed successfully!")
            
            # Save migration report
            self.save_migration_report()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close()
    
    def migrate_trainers(self):
        """Migrate trainers to Django User model."""
        logger.info("Starting trainer migration...")
        
        self.cursor.execute("SELECT * FROM trainers ORDER BY id")
        trainers = self.cursor.fetchall()
        
        for trainer in trainers:
            self.stats['trainers']['processed'] += 1
            
            try:
                # Check if user already exists
                user = User.objects.filter(username=trainer['username']).first()
                
                if user:
                    logger.info(f"User {trainer['username']} already exists, updating...")
                    # Update existing user
                    user.email = trainer['email']
                    user.first_name = trainer['name'].split()[0] if trainer['name'] else ''
                    user.last_name = ' '.join(trainer['name'].split()[1:]) if trainer['name'] and len(trainer['name'].split()) > 1 else ''
                    user.failed_login_attempts = trainer['failed_login_attempts'] or 0
                    user.save()
                    self.stats['trainers']['skipped'] += 1
                else:
                    # Create new user
                    user = User(
                        username=trainer['username'],
                        email=trainer['email'],
                        first_name=trainer['name'].split()[0] if trainer['name'] else '',
                        last_name=' '.join(trainer['name'].split()[1:]) if trainer['name'] and len(trainer['name'].split()) > 1 else '',
                        is_staff=True,  # All trainers are staff
                        is_active=True,
                        failed_login_attempts=trainer['failed_login_attempts'] or 0
                    )
                    # Set the password hash directly - it's already bcrypt hashed
                    user.password = trainer['password_hash']
                    
                    # Handle timestamps
                    if trainer['created_at']:
                        user.date_joined = timezone.make_aware(datetime.fromisoformat(trainer['created_at']))
                    if trainer['last_login']:
                        user.last_login = timezone.make_aware(datetime.fromisoformat(trainer['last_login']))
                    if trainer['locked_until']:
                        user.locked_until = timezone.make_aware(datetime.fromisoformat(trainer['locked_until']))
                    
                    user.save()
                    self.stats['trainers']['created'] += 1
                    logger.info(f"Created user: {user.username}")
                
                # Store mapping for foreign key references
                self.trainer_map[trainer['id']] = user
                
            except Exception as e:
                self.stats['trainers']['errors'] += 1
                logger.error(f"Error migrating trainer {trainer['username']}: {e}")
                raise
    
    def migrate_clients(self):
        """Migrate clients to Django Client model."""
        logger.info("Starting client migration...")
        
        self.cursor.execute("SELECT * FROM clients ORDER BY id")
        clients = self.cursor.fetchall()
        
        for client in clients:
            self.stats['clients']['processed'] += 1
            
            try:
                # Get the Django user from mapping
                trainer = self.trainer_map.get(client['trainer_id'])
                if not trainer:
                    logger.error(f"Trainer ID {client['trainer_id']} not found in mappings")
                    self.stats['clients']['errors'] += 1
                    continue
                
                # Check if client already exists
                existing = Client.objects.filter(
                    name=client['name'],
                    trainer=trainer
                ).first()
                
                if existing:
                    logger.info(f"Client {client['name']} already exists for trainer {trainer.username}")
                    self.client_map[client['id']] = existing
                    self.stats['clients']['skipped'] += 1
                    continue
                
                # Create new client
                django_client = Client.objects.create(
                    trainer=trainer,
                    name=client['name'],
                    age=client['age'],
                    gender=client['gender'],
                    height=Decimal(str(client['height'])),
                    weight=Decimal(str(client['weight'])),
                    email=client['email'] or '',
                    phone=client['phone'] or ''
                )
                
                # Set timestamps
                if client['created_at']:
                    django_client.created_at = timezone.make_aware(datetime.fromisoformat(client['created_at']))
                if client['updated_at']:
                    django_client.updated_at = timezone.make_aware(datetime.fromisoformat(client['updated_at']))
                django_client.save()
                
                # Store mapping
                self.client_map[client['id']] = django_client
                self.stats['clients']['created'] += 1
                logger.info(f"Created client: {django_client.name}")
                
            except Exception as e:
                self.stats['clients']['errors'] += 1
                logger.error(f"Error migrating client {client['name']}: {e}")
                raise
    
    def migrate_assessments(self):
        """Migrate assessments to Django Assessment model."""
        logger.info("Starting assessment migration...")
        
        self.cursor.execute("SELECT * FROM assessments ORDER BY id")
        assessments = self.cursor.fetchall()
        
        for assessment in assessments:
            self.stats['assessments']['processed'] += 1
            
            try:
                # Get mapped IDs
                client = self.client_map.get(assessment['client_id'])
                trainer = self.trainer_map.get(assessment['trainer_id'])
                
                if not client or not trainer:
                    logger.error(f"Missing mapping for assessment: client={assessment['client_id']}, trainer={assessment['trainer_id']}")
                    self.stats['assessments']['errors'] += 1
                    continue
                
                # Parse assessment date
                assessment_date = datetime.fromisoformat(assessment['date']).date()
                
                # Check if assessment already exists
                existing = Assessment.objects.filter(
                    client=client,
                    date=assessment_date
                ).first()
                
                if existing:
                    logger.info(f"Assessment already exists for client {client.name} on {assessment_date}")
                    self.stats['assessments']['skipped'] += 1
                    continue
                
                # Create assessment (skip compensations fields not in Django model)
                django_assessment = Assessment.objects.create(
                    client=client,
                    trainer=trainer,
                    date=assessment_date,
                    # Movement assessments
                    overhead_squat_score=assessment['overhead_squat_score'] or 0,
                    overhead_squat_notes=assessment['overhead_squat_notes'] or '',
                    
                    push_up_score=assessment['push_up_score'] or 0,
                    push_up_reps=assessment['push_up_reps'] or 0,
                    push_up_notes=assessment['push_up_notes'] or '',
                    
                    # Balance tests
                    single_leg_balance_left_eyes_open=int(assessment['single_leg_balance_left_eyes_open'] or 0),
                    single_leg_balance_right_eyes_open=int(assessment['single_leg_balance_right_eyes_open'] or 0),
                    single_leg_balance_left_eyes_closed=int(assessment['single_leg_balance_left_eyes_closed'] or 0),
                    single_leg_balance_right_eyes_closed=int(assessment['single_leg_balance_right_eyes_closed'] or 0),
                    single_leg_balance_notes=assessment['single_leg_balance_notes'] or '',
                    
                    # Flexibility
                    toe_touch_score=assessment['toe_touch_score'] or 0,
                    toe_touch_distance=float(assessment['toe_touch_distance'] or 0),
                    toe_touch_notes=assessment['toe_touch_notes'] or '',
                    
                    # Shoulder mobility
                    shoulder_mobility_left=float(assessment['shoulder_mobility_left'] or 0),
                    shoulder_mobility_right=float(assessment['shoulder_mobility_right'] or 0),
                    shoulder_mobility_score=assessment['shoulder_mobility_score'] or 0,
                    shoulder_mobility_notes=assessment['shoulder_mobility_notes'] or '',
                    
                    # Farmer carry
                    farmer_carry_weight=float(assessment['farmer_carry_weight'] or 0),
                    farmer_carry_distance=float(assessment['farmer_carry_distance'] or 0),
                    farmer_carry_score=assessment['farmer_carry_score'] or 0,
                    farmer_carry_notes=assessment['farmer_carry_notes'] or '',
                    
                    # Harvard step test
                    harvard_step_test_heart_rate=assessment['harvard_step_test_heart_rate'] or 0,
                    harvard_step_test_duration=float(assessment['harvard_step_test_duration'] or 0),
                    harvard_step_test_notes=assessment['harvard_step_test_notes'] or '',
                    
                    # Scores
                    overall_score=float(assessment['overall_score'] or 0),
                    strength_score=float(assessment['strength_score'] or 0),
                    mobility_score=float(assessment['mobility_score'] or 0),
                    balance_score=float(assessment['balance_score'] or 0),
                    cardio_score=float(assessment['cardio_score'] or 0)
                )
                
                # Set timestamp if available
                if assessment['created_at']:
                    django_assessment.created_at = timezone.make_aware(datetime.fromisoformat(assessment['created_at']))
                    django_assessment.save()
                
                self.stats['assessments']['created'] += 1
                logger.info(f"Created assessment for client {client.name}")
                
            except Exception as e:
                self.stats['assessments']['errors'] += 1
                logger.error(f"Error migrating assessment {assessment['id']}: {e}")
                raise
    
    def migrate_session_packages(self):
        """Migrate session packages to Django SessionPackage model."""
        logger.info("Starting session package migration...")
        
        self.cursor.execute("SELECT * FROM session_packages ORDER BY id")
        packages = self.cursor.fetchall()
        
        for package in packages:
            self.stats['session_packages']['processed'] += 1
            
            try:
                # Get mapped IDs
                client = self.client_map.get(package['client_id'])
                trainer = self.trainer_map.get(package['trainer_id'])
                
                if not client or not trainer:
                    logger.error(f"Missing mapping for package: client={package['client_id']}, trainer={package['trainer_id']}")
                    self.stats['session_packages']['errors'] += 1
                    continue
                
                # Create session package
                django_package = SessionPackage.objects.create(
                    client=client,
                    trainer=trainer,
                    package_name=package['package_name'] or f"{package['total_sessions']}회 패키지",
                    total_sessions=package['total_sessions'],
                    session_price=package['session_price'],
                    total_amount=package['total_amount'],
                    remaining_sessions=package['remaining_sessions'],
                    remaining_credits=package['remaining_credits'],
                    is_active=bool(package['is_active']),
                    notes=package['notes'] or '',
                    # Fee fields
                    gross_amount=package['gross_amount'] or package['total_amount'],
                    vat_amount=package['vat_amount'] or 0,
                    card_fee_amount=package['card_fee_amount'] or 0,
                    net_amount=package['net_amount'] or package['total_amount'],
                    vat_rate=Decimal(str(package['vat_rate'])) if package['vat_rate'] else Decimal('0.10'),
                    card_fee_rate=Decimal(str(package['card_fee_rate'])) if package['card_fee_rate'] else Decimal('0.035'),
                    fee_calculation_method=package['fee_calculation_method'] or 'inclusive'
                )
                
                # Set timestamps
                if package['created_at']:
                    django_package.created_at = timezone.make_aware(datetime.fromisoformat(package['created_at']))
                # Check if updated_at column exists
                if 'updated_at' in package.keys() and package['updated_at']:
                    django_package.updated_at = timezone.make_aware(datetime.fromisoformat(package['updated_at']))
                django_package.save()
                
                # Store mapping
                self.package_map[package['id']] = django_package
                self.stats['session_packages']['created'] += 1
                logger.info(f"Created session package: {django_package.package_name}")
                
            except Exception as e:
                self.stats['session_packages']['errors'] += 1
                logger.error(f"Error migrating session package {package['id']}: {e}")
                raise
    
    def migrate_sessions(self):
        """Migrate sessions to Django Session model."""
        logger.info("Starting session migration...")
        
        self.cursor.execute("SELECT * FROM sessions ORDER BY id")
        sessions = self.cursor.fetchall()
        
        for session in sessions:
            self.stats['sessions']['processed'] += 1
            
            try:
                # Get mapped IDs
                client = self.client_map.get(session['client_id'])
                package = self.package_map.get(session['package_id'])
                
                if not client or not package:
                    logger.error(f"Missing mapping for session: client={session['client_id']}, package={session['package_id']}")
                    self.stats['sessions']['errors'] += 1
                    continue
                
                # Get trainer_id - use from session or from package
                trainer_id = session['trainer_id'] if 'trainer_id' in session.keys() else None
                if trainer_id:
                    trainer = self.trainer_map.get(trainer_id)
                else:
                    trainer = package.trainer
                
                # Parse date and time
                session_date = datetime.fromisoformat(session['session_date']).date()
                session_time = None
                if session['session_time']:
                    try:
                        # Try parsing different time formats
                        time_str = session['session_time']
                        # Handle microseconds format
                        if '.' in time_str:
                            time_str = time_str.split('.')[0]  # Remove microseconds
                        if len(time_str.split(':')) == 2:
                            session_time = datetime.strptime(time_str, '%H:%M').time()
                        else:
                            session_time = datetime.strptime(time_str, '%H:%M:%S').time()
                    except Exception as e:
                        logger.warning(f"Could not parse session time {session['session_time']}: {e}")
                
                # Create session
                django_session = Session.objects.create(
                    client=client,
                    package=package,
                    trainer=trainer,
                    session_date=session_date,
                    session_time=session_time,
                    session_duration=session['session_duration'],
                    session_cost=Decimal(str(session['session_cost'])),
                    status=session['status'] or 'scheduled',
                    notes=session['notes'] or ''
                )
                
                # Set timestamps
                if session['created_at']:
                    django_session.created_at = timezone.make_aware(datetime.fromisoformat(session['created_at']))
                if 'completed_at' in session.keys() and session['completed_at']:
                    django_session.completed_at = timezone.make_aware(datetime.fromisoformat(session['completed_at']))
                django_session.save()
                
                self.stats['sessions']['created'] += 1
                logger.info(f"Created session for client {client.name} on {session_date}")
                
            except Exception as e:
                self.stats['sessions']['errors'] += 1
                logger.error(f"Error migrating session {session['id']}: {e}")
                raise
    
    def migrate_payments(self):
        """Migrate payments to Django Payment model."""
        logger.info("Starting payment migration...")
        
        self.cursor.execute("SELECT * FROM payments ORDER BY id")
        payments = self.cursor.fetchall()
        
        for payment in payments:
            self.stats['payments']['processed'] += 1
            
            try:
                # Get mapped IDs
                client = self.client_map.get(payment['client_id'])
                package = self.package_map.get(payment['package_id']) if payment['package_id'] else None
                
                if not client:
                    logger.error(f"Missing client mapping for payment: client={payment['client_id']}")
                    self.stats['payments']['errors'] += 1
                    continue
                
                # Get trainer - use from payment or client
                trainer_id = payment['trainer_id'] if 'trainer_id' in payment.keys() else None
                if trainer_id:
                    trainer = self.trainer_map.get(trainer_id)
                else:
                    trainer = client.trainer
                
                # Parse payment date
                payment_date = datetime.fromisoformat(payment['payment_date']).date()
                
                # Create payment
                django_payment = Payment.objects.create(
                    client=client,
                    trainer=trainer,
                    package=package,
                    amount=Decimal(str(payment['amount'])),
                    payment_date=payment_date,
                    payment_method=payment['payment_method'] or 'card',
                    description=payment['description'] or '',
                    # Fee fields
                    gross_amount=payment['gross_amount'] or int(payment['amount']),
                    vat_amount=payment['vat_amount'] or 0,
                    card_fee_amount=payment['card_fee_amount'] or 0,
                    net_amount=payment['net_amount'] or int(payment['amount']),
                    vat_rate=Decimal(str(payment['vat_rate'])) if payment['vat_rate'] else Decimal('0.10'),
                    card_fee_rate=Decimal(str(payment['card_fee_rate'])) if payment['card_fee_rate'] else Decimal('0.035')
                )
                
                # Set timestamp
                if payment['created_at']:
                    django_payment.created_at = timezone.make_aware(datetime.fromisoformat(payment['created_at']))
                    django_payment.save()
                
                self.stats['payments']['created'] += 1
                logger.info(f"Created payment for client {client.name} on {payment_date}")
                
            except Exception as e:
                self.stats['payments']['errors'] += 1
                logger.error(f"Error migrating payment {payment['id']}: {e}")
                raise
    
    def save_migration_report(self):
        """Save migration statistics to a JSON file."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_database': self.source_db_path,
            'statistics': self.stats,
            'mappings': {
                'trainers_count': len(self.trainer_map),
                'clients_count': len(self.client_map),
                'packages_count': len(self.package_map)
            },
            'summary': {
                'total_processed': sum(stat['processed'] for stat in self.stats.values()),
                'total_created': sum(stat['created'] for stat in self.stats.values()),
                'total_skipped': sum(stat['skipped'] for stat in self.stats.values()),
                'total_errors': sum(stat['errors'] for stat in self.stats.values())
            }
        }
        
        with open('migration_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info("Migration report saved to migration_report.json")
        
        # Print summary
        print("\n" + "="*50)
        print("MIGRATION SUMMARY")
        print("="*50)
        for model, stats in self.stats.items():
            print(f"\n{model.upper()}:")
            print(f"  Processed: {stats['processed']}")
            print(f"  Created: {stats['created']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Errors: {stats['errors']}")
        print("\n" + "="*50)
        print(f"TOTAL:")
        print(f"  Processed: {report['summary']['total_processed']}")
        print(f"  Created: {report['summary']['total_created']}")
        print(f"  Skipped: {report['summary']['total_skipped']}")
        print(f"  Errors: {report['summary']['total_errors']}")
        print("="*50)


def main():
    """Main entry point for the migration script."""
    # Path to the source SQLite database
    source_db_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'fitness_assessment.db'
    
    if not source_db_path.exists():
        logger.error(f"Source database not found at {source_db_path}")
        sys.exit(1)
    
    print(f"Source database: {source_db_path}")
    print(f"Django database: {os.environ.get('DATABASE_NAME', 'default')}")
    print(f"\nThis will migrate data from the cleaned Streamlit database to Django.")
    print("Make sure the Django database is properly configured and migrations are applied.")
    
    # Check if '--auto' flag is provided for automated runs
    auto_mode = '--auto' in sys.argv
    
    if not auto_mode:
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            sys.exit(0)
    
    # Run migration
    migrator = StreamlitToJangoMigrator(str(source_db_path))
    migrator.migrate_all()


if __name__ == '__main__':
    main()