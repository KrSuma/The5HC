"""
Database abstraction layer with repository pattern
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from database import get_db_connection, DatabaseError
from app_logging import audit_logger, perf_logger, error_logger, log_database_operation

T = TypeVar('T')


# Base entity classes
@dataclass
class BaseEntity:
    """Base class for all entities"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass 
class Trainer(BaseEntity):
    """Trainer entity"""
    username: str = ""
    password_hash: str = ""
    name: str = ""
    email: str = ""
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class Client(BaseEntity):
    """Client entity"""
    trainer_id: int = 0
    name: str = ""
    age: int = 0
    gender: str = ""
    height: float = 0.0
    weight: float = 0.0
    email: Optional[str] = ""
    phone: Optional[str] = ""
    
    @property
    def bmi(self) -> float:
        """Calculate BMI"""
        if self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return 0.0


@dataclass
class Assessment(BaseEntity):
    """Assessment entity"""
    client_id: int = 0
    trainer_id: int = 0
    date: str = ""
    
    # Test scores
    overhead_squat_score: Optional[int] = None
    overhead_squat_notes: Optional[str] = ""
    overhead_squat_compensations: Optional[str] = ""
    
    push_up_score: Optional[int] = None
    push_up_reps: Optional[int] = None
    push_up_notes: Optional[str] = ""
    push_up_compensations: Optional[str] = ""
    
    single_leg_balance_left_eyes_open: Optional[float] = None
    single_leg_balance_right_eyes_open: Optional[float] = None
    single_leg_balance_left_eyes_closed: Optional[float] = None
    single_leg_balance_right_eyes_closed: Optional[float] = None
    single_leg_balance_notes: Optional[str] = ""
    
    toe_touch_score: Optional[int] = None
    toe_touch_distance: Optional[float] = None
    toe_touch_notes: Optional[str] = ""
    toe_touch_compensations: Optional[str] = ""
    
    shoulder_mobility_left: Optional[float] = None
    shoulder_mobility_right: Optional[float] = None
    shoulder_mobility_notes: Optional[str] = ""
    shoulder_mobility_compensations: Optional[str] = ""
    
    farmer_carry_weight: Optional[float] = None
    farmer_carry_distance: Optional[float] = None
    farmer_carry_notes: Optional[str] = ""
    farmer_carry_compensations: Optional[str] = ""
    
    harvard_step_test_heart_rate: Optional[int] = None
    harvard_step_test_duration: Optional[float] = None
    harvard_step_test_notes: Optional[str] = ""
    
    # Category scores
    overall_score: Optional[float] = None
    strength_score: Optional[float] = None
    mobility_score: Optional[float] = None
    balance_score: Optional[float] = None
    cardio_score: Optional[float] = None


# Repository interfaces
class IRepository(ABC, Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def get_all(self, **filters) -> List[T]:
        """Get all entities with optional filters"""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> Optional[int]:
        """Create new entity and return ID"""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> bool:
        """Update existing entity"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID"""
        pass


# Base repository implementation
class BaseRepository(IRepository[T]):
    """Base repository with common database operations"""
    
    def __init__(self, table_name: str, entity_class: type):
        self.table_name = table_name
        self.entity_class = entity_class
    
    @log_database_operation
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    @log_database_operation
    def get_all(self, **filters) -> List[T]:
        """Get all entities with optional filters"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build WHERE clause from filters
            where_clauses = []
            params = []
            
            for key, value in filters.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)
            
            query = f"SELECT * FROM {self.table_name}"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def _row_to_entity(self, row: sqlite3.Row) -> T:
        """Convert database row to entity"""
        data = dict(row)
        return self.entity_class(**data)
    
    def _entity_to_dict(self, entity: T, exclude_id: bool = False) -> Dict[str, Any]:
        """Convert entity to dictionary for database operations"""
        data = {}
        for field in entity.__dataclass_fields__:
            value = getattr(entity, field)
            if field == 'id' and exclude_id:
                continue
            if value is not None:
                data[field] = value
        return data


# Specific repository implementations
class TrainerRepository(BaseRepository[Trainer]):
    """Repository for trainer operations"""
    
    def __init__(self):
        super().__init__('trainers', Trainer)
    
    @log_database_operation
    def get_by_username(self, username: str) -> Optional[Trainer]:
        """Get trainer by username"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM trainers WHERE username = ?", 
                (username,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    @log_database_operation
    def create(self, entity: Trainer) -> Optional[int]:
        """Create new trainer"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(query, list(data.values()))
                conn.commit()
                
                trainer_id = cursor.lastrowid
                audit_logger.log_data_modification(
                    trainer_id, 'trainer', trainer_id, {'action': 'create'}
                )
                
                return trainer_id
                
        except sqlite3.IntegrityError:
            return None
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'trainer'})
            raise
    
    @log_database_operation
    def update(self, entity: Trainer) -> bool:
        """Update trainer"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                set_clauses = [f"{col} = ?" for col in data.keys()]
                
                query = f"""
                    UPDATE {self.table_name}
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, list(data.values()) + [entity.id])
                conn.commit()
                
                if cursor.rowcount > 0:
                    audit_logger.log_data_modification(
                        entity.id, 'trainer', entity.id, {'action': 'update'}
                    )
                    return True
                    
                return False
                
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'trainer', 'id': entity.id})
            raise
    
    def delete(self, id: int) -> bool:
        """Trainers should not be deleted - deactivate instead"""
        raise NotImplementedError("Trainers cannot be deleted")


class ClientRepository(BaseRepository[Client]):
    """Repository for client operations"""
    
    def __init__(self):
        super().__init__('clients', Client)
    
    @log_database_operation
    def get_by_trainer(self, trainer_id: int) -> List[Client]:
        """Get all clients for a trainer"""
        return self.get_all(trainer_id=trainer_id)
    
    @log_database_operation
    def search(self, trainer_id: int, search_term: str) -> List[Client]:
        """Search clients by name or email"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM clients 
                WHERE trainer_id = ? 
                AND (name LIKE ? OR email LIKE ?)
                ORDER BY name
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (trainer_id, search_pattern, search_pattern))
            
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    @log_database_operation
    def create(self, entity: Client) -> Optional[int]:
        """Create new client"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(query, list(data.values()))
                conn.commit()
                
                client_id = cursor.lastrowid
                audit_logger.log_data_modification(
                    entity.trainer_id, 'client', client_id, {'action': 'create'}
                )
                
                return client_id
                
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'client'})
            raise
    
    @log_database_operation
    def update(self, entity: Client) -> bool:
        """Update client"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                data['updated_at'] = datetime.now()
                set_clauses = [f"{col} = ?" for col in data.keys()]
                
                query = f"""
                    UPDATE {self.table_name}
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                
                cursor.execute(query, list(data.values()) + [entity.id])
                conn.commit()
                
                if cursor.rowcount > 0:
                    audit_logger.log_data_modification(
                        entity.trainer_id, 'client', entity.id, {'action': 'update'}
                    )
                    return True
                    
                return False
                
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'client', 'id': entity.id})
            raise
    
    def delete(self, id: int) -> bool:
        """Soft delete client (should implement soft delete in production)"""
        # In production, implement soft delete instead
        raise NotImplementedError("Use soft delete for clients")


class AssessmentRepository(BaseRepository[Assessment]):
    """Repository for assessment operations"""
    
    def __init__(self):
        super().__init__('assessments', Assessment)
    
    @log_database_operation
    def get_by_client(self, client_id: int) -> List[Assessment]:
        """Get all assessments for a client"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM assessments WHERE client_id = ? ORDER BY date DESC",
                (client_id,)
            )
            
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    @log_database_operation
    def get_latest_by_client(self, client_id: int) -> Optional[Assessment]:
        """Get latest assessment for a client"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM assessments 
                   WHERE client_id = ? 
                   ORDER BY date DESC 
                   LIMIT 1""",
                (client_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    @log_database_operation
    def get_progress(self, client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get assessment progress data"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT date, overall_score, strength_score, 
                          mobility_score, balance_score, cardio_score
                   FROM assessments 
                   WHERE client_id = ? 
                   ORDER BY date DESC 
                   LIMIT ?""",
                (client_id, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    @log_database_operation
    def create(self, entity: Assessment) -> Optional[int]:
        """Create new assessment"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(query, list(data.values()))
                conn.commit()
                
                assessment_id = cursor.lastrowid
                audit_logger.log_data_modification(
                    entity.trainer_id, 'assessment', assessment_id, {'action': 'create'}
                )
                
                return assessment_id
                
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'assessment'})
            raise
    
    def update(self, entity: Assessment) -> bool:
        """Assessments should not be updated once created"""
        raise NotImplementedError("Assessments are immutable")
    
    def delete(self, id: int) -> bool:
        """Assessments should not be deleted"""
        raise NotImplementedError("Assessments cannot be deleted")


# Unit of Work pattern for managing transactions
class UnitOfWork:
    """Unit of Work for managing database transactions"""
    
    def __init__(self):
        self.trainers = TrainerRepository()
        self.clients = ClientRepository()
        self.assessments = AssessmentRepository()
        self._connection = None
        self._transaction_active = False
    
    def __enter__(self):
        """Start transaction"""
        self._connection = sqlite3.connect(
            'fitness_assessment.db',
            isolation_level=None  # Autocommit off
        )
        self._connection.execute("BEGIN")
        self._transaction_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End transaction"""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        
        if self._connection:
            self._connection.close()
            self._connection = None
        
        self._transaction_active = False
    
    def commit(self):
        """Commit transaction"""
        if self._connection and self._transaction_active:
            self._connection.commit()
            perf_logger.logger.info("Transaction committed")
    
    def rollback(self):
        """Rollback transaction"""
        if self._connection and self._transaction_active:
            self._connection.rollback()
            perf_logger.logger.warning("Transaction rolled back")


# Factory for getting repositories
class RepositoryFactory:
    """Factory for creating repository instances"""
    
    _instances = {}
    
    @classmethod
    def get_trainer_repository(cls) -> TrainerRepository:
        """Get trainer repository instance"""
        if 'trainer' not in cls._instances:
            cls._instances['trainer'] = TrainerRepository()
        return cls._instances['trainer']
    
    @classmethod
    def get_client_repository(cls) -> ClientRepository:
        """Get client repository instance"""
        if 'client' not in cls._instances:
            cls._instances['client'] = ClientRepository()
        return cls._instances['client']
    
    @classmethod
    def get_assessment_repository(cls) -> AssessmentRepository:
        """Get assessment repository instance"""
        if 'assessment' not in cls._instances:
            cls._instances['assessment'] = AssessmentRepository()
        return cls._instances['assessment']