"""
Repository implementations for data access
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
import sqlite3

from ..core.models import BaseEntity, Trainer, Client, Assessment
from ..utils.logging import audit_logger, perf_logger, error_logger
# TODO: Import log_database_operation once logging is properly organized
from .database import get_db_connection, DatabaseError
from .database_config import IS_PRODUCTION


T = TypeVar('T')


def execute_db_query(cursor, query: str, params: tuple = None):
    """Execute query with proper placeholder conversion for PostgreSQL"""
    if IS_PRODUCTION and params:
        # Convert SQLite ? placeholders to PostgreSQL %s
        query = query.replace('?', '%s')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)


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


class BaseRepository(IRepository[T]):
    """Base repository with common database operations"""
    
    def __init__(self, table_name: str, entity_class: type):
        self.table_name = table_name
        self.entity_class = entity_class
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            execute_db_query(cursor, f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
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
            
            execute_db_query(cursor, query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def _row_to_entity(self, row) -> T:
        """Convert database row to entity"""
        if isinstance(row, dict):
            # PostgreSQL with RealDictCursor returns dictionaries
            data = row
        else:
            # SQLite returns Row objects
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


class TrainerRepository(BaseRepository[Trainer]):
    """Repository for trainer operations"""
    
    def __init__(self):
        super().__init__('trainers', Trainer)
    
    def get_by_username(self, username: str) -> Optional[Trainer]:
        """Get trainer by username"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            execute_db_query(cursor,
                "SELECT * FROM trainers WHERE username = ?", 
                (username,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    
    def create(self, entity: Trainer) -> Optional[int]:
        """Create new trainer"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING id
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    result = cursor.fetchone()
                    trainer_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    trainer_id = cursor.lastrowid
                
                conn.commit()
                audit_logger.log_data_modification(
                    trainer_id, 'trainer', trainer_id, {'action': 'create'}
                )
                
                return trainer_id
                
        except sqlite3.IntegrityError:
            return None
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'trainer'})
            raise
    
    
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
                
                execute_db_query(cursor, query, list(data.values()) + [entity.id])
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
    
    
    def get_by_trainer(self, trainer_id: int) -> List[Client]:
        """Get all clients for a trainer"""
        return self.get_all(trainer_id=trainer_id)
    
    def find_by_trainer(self, trainer_id: int) -> List[Client]:
        """Alias for get_by_trainer for compatibility"""
        return self.get_by_trainer(trainer_id)
    
    
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
            execute_db_query(cursor, query, (trainer_id, search_pattern, search_pattern))
            
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    
    def create(self, entity: Client) -> Optional[int]:
        """Create new client"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING id
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    result = cursor.fetchone()
                    client_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    client_id = cursor.lastrowid
                
                conn.commit()
                audit_logger.log_data_modification(
                    entity.trainer_id, 'client', client_id, {'action': 'create'}
                )
                
                return client_id
                
        except Exception as e:
            error_logger.log_error(e, context={'entity': 'client'})
            raise
    
    
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
                
                execute_db_query(cursor, query, list(data.values()) + [entity.id])
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
    
    
    def get_by_client(self, client_id: int) -> List[Assessment]:
        """Get all assessments for a client"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            execute_db_query(cursor,
                "SELECT * FROM assessments WHERE client_id = ? ORDER BY date DESC",
                (client_id,)
            )
            
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def find_by_client(self, client_id: int) -> List[Assessment]:
        """Alias for get_by_client for compatibility"""
        return self.get_by_client(client_id)
    
    
    def get_latest_by_client(self, client_id: int) -> Optional[Assessment]:
        """Get latest assessment for a client"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            execute_db_query(cursor,
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
    
    
    def get_progress(self, client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get assessment progress data"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            execute_db_query(cursor,
                """SELECT date, overall_score, strength_score, 
                          mobility_score, balance_score, cardio_score
                   FROM assessments 
                   WHERE client_id = ? 
                   ORDER BY date DESC 
                   LIMIT ?""",
                (client_id, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    
    def create(self, entity: Assessment) -> Optional[int]:
        """Create new assessment"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                data = self._entity_to_dict(entity, exclude_id=True)
                columns = list(data.keys())
                placeholders = ['?' for _ in columns]
                
                if IS_PRODUCTION:
                    # PostgreSQL - use RETURNING clause
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING id
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    result = cursor.fetchone()
                    assessment_id = result['id'] if isinstance(result, dict) else result[0]
                else:
                    # SQLite - use lastrowid
                    query = f"""
                        INSERT INTO {self.table_name} ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    execute_db_query(cursor, query, list(data.values()))
                    assessment_id = cursor.lastrowid
                
                conn.commit()
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