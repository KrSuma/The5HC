"""
Client management service
"""
from typing import Optional, List, Tuple
from datetime import datetime

from ..core.models import Client
from ..data.repositories import RepositoryFactory
from ..data.cache import cache_manager, ClientCache
from ..utils.logging import audit_logger, error_logger, app_logger
from ..utils.validators import sanitize_input, validate_phone_number


class ClientService:
    """Service for managing clients"""
    
    def __init__(self):
        self.client_repo = RepositoryFactory.get_client_repository()
        self.client_cache = ClientCache()
    
    def create_client(self, trainer_id: int, name: str, age: int, gender: str, 
                     height: float, weight: float, email: str = "", phone: str = "") -> Tuple[bool, str, Optional[int]]:
        """Create new client"""
        try:
            # Validate inputs
            name = sanitize_input(name, 100)
            email = sanitize_input(email, 100) if email else ""
            phone = sanitize_input(phone, 20) if phone else ""
            
            if not name:
                return False, "이름은 필수입니다.", None
            
            if age < 1 or age > 120:
                return False, "올바른 나이를 입력해주세요.", None
            
            if gender not in ['male', 'female']:
                return False, "성별을 선택해주세요.", None
            
            if height <= 0 or weight <= 0:
                return False, "올바른 신장과 체중을 입력해주세요.", None
            
            if phone and not validate_phone_number(phone):
                return False, "올바른 전화번호 형식이 아닙니다.", None
            
            # Create client
            client = Client(
                trainer_id=trainer_id,
                name=name,
                age=age,
                gender=gender,
                height=height,
                weight=weight,
                email=email,
                phone=phone
            )
            
            client_id = self.client_repo.create(client)
            
            if client_id:
                # Clear cache
                self.client_cache.invalidate_list(trainer_id)
                
                app_logger.info(f"Client created: {name} (ID: {client_id})")
                audit_logger.log_data_modification(trainer_id, 'client', client_id, {'action': 'create'})
                
                return True, "고객이 등록되었습니다.", client_id
            else:
                return False, "고객 등록 중 오류가 발생했습니다.", None
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'create_client', 'trainer_id': trainer_id})
            return False, "고객 등록 중 오류가 발생했습니다.", None
    
    def get_clients(self, trainer_id: int) -> List[Client]:
        """Get all clients for a trainer"""
        try:
            # Check cache first
            cached_clients = self.client_cache.get_list(trainer_id)
            if cached_clients is not None:
                return cached_clients
            
            # Get from database
            clients = self.client_repo.get_by_trainer(trainer_id)
            
            # Cache the results
            self.client_cache.set_list(trainer_id, clients)
            
            return clients
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_clients', 'trainer_id': trainer_id})
            return []
    
    def get_client(self, client_id: int) -> Optional[Client]:
        """Get client by ID"""
        try:
            # Check cache first
            cached_client = self.client_cache.get(client_id)
            if cached_client:
                return cached_client
            
            # Get from database
            client = self.client_repo.get_by_id(client_id)
            
            if client:
                # Cache the result
                self.client_cache.set(client_id, client)
            
            return client
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_client', 'client_id': client_id})
            return None
    
    def update_client(self, client: Client) -> Tuple[bool, str]:
        """Update client information"""
        try:
            # Validate inputs
            client.name = sanitize_input(client.name, 100)
            client.email = sanitize_input(client.email, 100) if client.email else ""
            client.phone = sanitize_input(client.phone, 20) if client.phone else ""
            
            if not client.name:
                return False, "이름은 필수입니다."
            
            if client.age < 1 or client.age > 120:
                return False, "올바른 나이를 입력해주세요."
            
            if client.height <= 0 or client.weight <= 0:
                return False, "올바른 신장과 체중을 입력해주세요."
            
            if client.phone and not validate_phone_number(client.phone):
                return False, "올바른 전화번호 형식이 아닙니다."
            
            # Update client
            success = self.client_repo.update(client)
            
            if success:
                # Clear cache
                self.client_cache.invalidate(client.id)
                self.client_cache.invalidate_list(client.trainer_id)
                
                app_logger.info(f"Client updated: {client.name} (ID: {client.id})")
                audit_logger.log_data_modification(client.trainer_id, 'client', client.id, {'action': 'update'})
                
                return True, "고객 정보가 업데이트되었습니다."
            else:
                return False, "고객 정보 업데이트 중 오류가 발생했습니다."
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'update_client', 'client_id': client.id})
            return False, "고객 정보 업데이트 중 오류가 발생했습니다."
    
    def search_clients(self, trainer_id: int, search_term: str) -> List[Client]:
        """Search clients by name or email"""
        try:
            search_term = sanitize_input(search_term, 100)
            if not search_term:
                return []
            
            return self.client_repo.search(trainer_id, search_term)
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'search_clients', 'trainer_id': trainer_id})
            return []
    
    def get_client_stats(self, trainer_id: int) -> dict:
        """Get statistics for trainer's clients"""
        try:
            clients = self.get_clients(trainer_id)
            
            if not clients:
                return {
                    'total_clients': 0,
                    'avg_age': 0,
                    'gender_distribution': {'male': 0, 'female': 0},
                    'avg_bmi': 0
                }
            
            total = len(clients)
            avg_age = sum(c.age for c in clients) / total
            gender_dist = {
                'male': sum(1 for c in clients if c.gender == 'male'),
                'female': sum(1 for c in clients if c.gender == 'female')
            }
            avg_bmi = sum(c.bmi for c in clients) / total
            
            return {
                'total_clients': total,
                'avg_age': round(avg_age, 1),
                'gender_distribution': gender_dist,
                'avg_bmi': round(avg_bmi, 1)
            }
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_client_stats', 'trainer_id': trainer_id})
            return {
                'total_clients': 0,
                'avg_age': 0,
                'gender_distribution': {'male': 0, 'female': 0},
                'avg_bmi': 0
            }
    
    @staticmethod
    def _warm_cache(trainer_id: int):
        """Warm up cache for trainer"""
        try:
            service = ClientService()
            service.get_clients(trainer_id)
        except Exception as e:
            error_logger.log_error(e, context={'action': 'warm_cache', 'trainer_id': trainer_id})