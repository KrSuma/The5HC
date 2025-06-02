"""
Improved service layer with security, caching, and proper error handling
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import streamlit as st

from database import (
    hash_password, verify_password, validate_email, sanitize_input,
    register_trainer as db_register_trainer,
    authenticate as db_authenticate,
    add_client as db_add_client,
    get_clients as db_get_clients,
    get_client_details as db_get_client_details,
    save_assessment as db_save_assessment,
    get_assessments as db_get_assessments,
    get_assessment_details as db_get_assessment_details,
    get_trainer_stats as db_get_trainer_stats,
    rate_limiter
)

from models import (
    RepositoryFactory, UnitOfWork,
    Trainer, Client, Assessment
)

from auth import session_manager, ActivityTracker, login_required
from cache import cache_manager, cached, ClientCache, AssessmentCache, StatsCache
from app_logging import security_logger, audit_logger, error_logger, app_logger, log_execution_time
from config import config

import scoring as scoring
import recommendations as recommendations


class AuthService:
    """Enhanced authentication service with security features"""
    
    @staticmethod
    def register(username: str, password: str, name: str, email: str) -> Tuple[bool, str]:
        """Register new trainer with validation"""
        try:
            # Validate inputs
            username = sanitize_input(username, 50)
            name = sanitize_input(name, 100)
            email = sanitize_input(email, 100)
            
            if not username or not name:
                return False, "사용자명과 이름은 필수입니다."
            
            if not validate_email(email):
                return False, "올바른 이메일 형식이 아닙니다."
            
            # Validate password strength
            if len(password) < config.security.min_password_length:
                return False, f"비밀번호는 최소 {config.security.min_password_length}자 이상이어야 합니다."
            
            # Register trainer
            success = db_register_trainer(username, password, name, email)
            
            if success:
                app_logger.info(f"Trainer registered: {username}")
                return True, "등록이 완료되었습니다!"
            else:
                return False, "사용자명이 이미 존재합니다."
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'register', 'username': username})
            return False, "등록 중 오류가 발생했습니다."
    
    @staticmethod
    @log_execution_time("authentication")
    def login(username: str, password: str) -> Tuple[bool, str]:
        """Authenticate trainer with rate limiting"""
        try:
            # Check rate limit
            allowed, locked_until = rate_limiter.check_rate_limit(username)
            if not allowed:
                security_logger.log_auth_attempt(username, False, reason="rate_limited")
                return False, f"너무 많은 로그인 시도로 계정이 잠겼습니다. {locked_until.strftime('%H:%M')}까지 기다려주세요."
            
            # Authenticate
            trainer_id = db_authenticate(username, password)
            
            if trainer_id:
                # Get trainer details
                trainer_repo = RepositoryFactory.get_trainer_repository()
                trainer = trainer_repo.get_by_username(username)
                
                if trainer:
                    # Create session
                    session_data = session_manager.create_session(trainer_id, trainer.name)
                    
                    # Log successful login
                    security_logger.log_auth_attempt(username, True)
                    ActivityTracker.log_activity("login", {"username": username})
                    
                    # Warm up cache
                    if config.cache.enable_cache_warming:
                        ClientService._warm_cache(trainer_id)
                    
                    return True, "로그인 성공!"
            
            # Log failed attempt
            security_logger.log_auth_attempt(username, False, reason="invalid_credentials")
            rate_limiter.record_failed_attempt(username)
            
            return False, "잘못된 사용자명 또는 비밀번호입니다."
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'login', 'username': username})
            return False, "로그인 중 오류가 발생했습니다."
    
    @staticmethod
    def logout():
        """Logout current user"""
        if 'trainer_id' in st.session_state:
            ActivityTracker.log_activity("logout")
            
        session_manager.clear_session()
        cache_manager.invalidate_all()


class ClientService:
    """Enhanced client service with caching"""
    
    @staticmethod
    @login_required
    @cached(cache_name='clients', ttl=600)
    def get_trainer_clients(trainer_id: int) -> List[Tuple[int, str]]:
        """Get all clients for a trainer with caching"""
        return db_get_clients(trainer_id)
    
    @staticmethod
    @login_required
    @cached(cache_name='clients', ttl=600, key_prefix='client_details')
    def get_client_details(client_id: int) -> Optional[Dict[str, Any]]:
        """Get client details with caching"""
        details = db_get_client_details(client_id)
        
        if details:
            # Calculate BMI
            details['bmi'] = ClientService.calculate_bmi(details)
            
            # Log data access
            audit_logger.log_data_access(
                st.session_state.get('trainer_id', 0),
                'client',
                client_id,
                'read'
            )
        
        return details
    
    @staticmethod
    @login_required
    def add_client(trainer_id: int, name: str, age: int, gender: str,
                  height: float, weight: float, email: str = "", phone: str = "") -> Tuple[bool, str]:
        """Add new client with validation"""
        try:
            client_id = db_add_client(
                trainer_id, name, age, gender, 
                height, weight, email, phone
            )
            
            if client_id:
                # Invalidate cache
                cache = cache_manager.get_cache('clients')
                cache.invalidate(f"get_trainer_clients:{trainer_id}")
                
                # Log action
                ActivityTracker.log_activity(
                    "add_client", 
                    {"client_id": client_id, "name": name}
                )
                
                return True, f"고객 '{name}'이(가) 추가되었습니다!"
            
            return False, "고객 추가에 실패했습니다."
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            error_logger.log_error(e, context={'action': 'add_client'})
            return False, "고객 추가 중 오류가 발생했습니다."
    
    @staticmethod
    def calculate_bmi(client: Dict[str, Any]) -> float:
        """Calculate BMI for client"""
        if client['height'] > 0:
            height_m = client['height'] / 100
            return round(client['weight'] / (height_m ** 2), 1)
        return 0.0
    
    @staticmethod
    def _warm_cache(trainer_id: int):
        """Pre-load trainer's clients into cache"""
        try:
            ClientService.get_trainer_clients(trainer_id)
        except Exception:
            pass


class AssessmentService:
    """Enhanced assessment service with caching and validation"""
    
    @staticmethod
    @login_required
    def save_assessment(assessment_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Save assessment with validation and scoring"""
        try:
            # Validate required fields
            required = ['client_id', 'trainer_id', 'date']
            for field in required:
                if field not in assessment_data:
                    return False, f"필수 필드가 누락되었습니다: {field}"
            
            # Calculate scores if not provided
            if 'overall_score' not in assessment_data:
                scores = AssessmentService._calculate_scores(assessment_data)
                assessment_data.update(scores)
            
            # Save assessment
            assessment_id = db_save_assessment(assessment_data)
            
            if assessment_id:
                # Invalidate caches
                client_id = assessment_data['client_id']
                cache = cache_manager.get_cache('assessments')
                cache.invalidate(f"get_client_assessments:{client_id}")
                
                # Invalidate stats cache
                trainer_id = assessment_data['trainer_id']
                stats_cache = cache_manager.get_cache('stats')
                stats_cache.invalidate(f"get_trainer_stats:{trainer_id}")
                
                # Log action
                ActivityTracker.log_activity(
                    "save_assessment",
                    {"assessment_id": assessment_id, "client_id": client_id}
                )
                
                return True, "평가가 저장되었습니다!"
            
            return False, "평가 저장에 실패했습니다."
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'save_assessment'})
            return False, "평가 저장 중 오류가 발생했습니다."
    
    @staticmethod
    @login_required
    @cached(cache_name='assessments', ttl=300)
    def get_client_assessments(client_id: int) -> List[Dict[str, Any]]:
        """Get all assessments for a client"""
        assessments = db_get_assessments(client_id)
        
        # Log data access
        if assessments:
            audit_logger.log_data_access(
                st.session_state.get('trainer_id', 0),
                'assessments',
                client_id,
                'list'
            )
        
        return assessments
    
    @staticmethod
    @login_required
    @cached(cache_name='assessments', ttl=300, key_prefix='assessment_details')
    def get_assessment_details(assessment_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed assessment information"""
        details = db_get_assessment_details(assessment_id)
        
        if details:
            audit_logger.log_data_access(
                st.session_state.get('trainer_id', 0),
                'assessment',
                assessment_id,
                'read'
            )
        
        return details
    
    @staticmethod
    def _calculate_scores(assessment_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate assessment scores"""
        # Get client details for age/gender
        client = ClientService.get_client_details(assessment_data['client_id'])
        if not client:
            raise ValueError("Client not found")
        
        scores = {
            'strength_score': 0.0,
            'mobility_score': 0.0,
            'balance_score': 0.0,
            'cardio_score': 0.0
        }
        
        # Calculate individual test scores
        # (Implementation would use the scoring module)
        
        # Calculate overall score
        scores['overall_score'] = sum(scores.values())
        
        return scores


class DashboardService:
    """Enhanced dashboard service with caching"""
    
    @staticmethod
    @login_required
    @cached(cache_name='stats', ttl=60)
    def get_trainer_stats(trainer_id: int) -> Dict[str, Any]:
        """Get trainer statistics with caching"""
        return db_get_trainer_stats(trainer_id)
    
    @staticmethod
    @login_required
    def search_clients(trainer_id: int, search_term: str) -> List[Dict[str, Any]]:
        """Search clients by name or email"""
        try:
            client_repo = RepositoryFactory.get_client_repository()
            clients = client_repo.search(trainer_id, search_term)
            
            return [
                {
                    'id': c.id,
                    'name': c.name,
                    'age': c.age,
                    'gender': c.gender,
                    'bmi': c.bmi
                }
                for c in clients
            ]
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'search_clients'})
            return []

    @staticmethod
    @login_required
    @cached(cache_name='assessments', ttl=60)
    def get_recent_assessments(trainer_id: int, limit: int = 10) -> List[Tuple[int, str, str, float]]:
        """Get recent assessments for the given trainer"""
        try:
            # Get all clients for this trainer
            client_repo = RepositoryFactory.get_client_repository()
            trainer_clients = client_repo.find_by_trainer(trainer_id)
            
            if not trainer_clients:
                return []
            
            # Get assessments for all clients
            assessment_repo = RepositoryFactory.get_assessment_repository()
            all_assessments = []
            
            for client in trainer_clients:
                assessments = assessment_repo.find_by_client(client.id)
                for assessment in assessments:
                    all_assessments.append((
                        assessment.id,
                        client.name,
                        assessment.date,
                        assessment.overall_score
                    ))
            
            # Sort by date (most recent first) and limit results
            all_assessments.sort(key=lambda x: x[2], reverse=True)
            return all_assessments[:limit]
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_recent_assessments'})
            return []

    @staticmethod
    @login_required
    def search_assessments(trainer_id: int, search_criteria: Dict[str, Any]) -> List[Tuple[int, str, str, float]]:
        """Search assessments based on criteria"""
        try:
            # Get all clients for this trainer
            client_repo = RepositoryFactory.get_client_repository()
            trainer_clients = client_repo.find_by_trainer(trainer_id)
            
            if not trainer_clients:
                return []
            
            # Get assessments for all clients
            assessment_repo = RepositoryFactory.get_assessment_repository()
            all_assessments = []
            
            for client in trainer_clients:
                # Check if client matches criteria
                if 'client_id' in search_criteria and client.id != search_criteria['client_id']:
                    continue
                    
                assessments = assessment_repo.find_by_client(client.id)
                for assessment in assessments:
                    # Apply date filters
                    if 'date_start' in search_criteria:
                        if assessment.date < search_criteria['date_start']:
                            continue
                    if 'date_end' in search_criteria:
                        if assessment.date > search_criteria['date_end']:
                            continue
                    
                    # Apply score filters
                    if 'score_min' in search_criteria:
                        if assessment.overall_score < search_criteria['score_min']:
                            continue
                    if 'score_max' in search_criteria:
                        if assessment.overall_score > search_criteria['score_max']:
                            continue
                    
                    all_assessments.append((
                        assessment.id,
                        client.name,
                        assessment.date,
                        assessment.overall_score
                    ))
            
            # Sort by date (most recent first)
            all_assessments.sort(key=lambda x: x[2], reverse=True)
            return all_assessments
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'search_assessments'})
            return []


class AnalyticsService:
    """Enhanced analytics service"""
    
    @staticmethod
    @login_required
    @cached(cache_name='stats', ttl=120)
    def get_client_progress(client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get client progress data"""
        try:
            assessment_repo = RepositoryFactory.get_assessment_repository()
            return assessment_repo.get_progress(client_id, limit)
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_client_progress'})
            return []
    
    @staticmethod
    def detect_asymmetries(assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect asymmetries in assessment"""
        asymmetries = []
        
        # Check balance asymmetries
        if all(key in assessment for key in [
            'single_leg_balance_left_eyes_open', 
            'single_leg_balance_right_eyes_open'
        ]):
            left = assessment['single_leg_balance_left_eyes_open'] or 0
            right = assessment['single_leg_balance_right_eyes_open'] or 0
            
            if left > 0 and right > 0:
                diff_percent = abs(left - right) / max(left, right) * 100
                if diff_percent > 20:
                    asymmetries.append({
                        'test': '외발서기 (눈뜨고)',
                        'left': left,
                        'right': right,
                        'difference': f"{diff_percent:.1f}%",
                        'severity': 'high' if diff_percent > 40 else 'medium'
                    })
        
        # Check shoulder mobility asymmetries
        if all(key in assessment for key in [
            'shoulder_mobility_left',
            'shoulder_mobility_right'
        ]):
            left = assessment['shoulder_mobility_left'] or 0
            right = assessment['shoulder_mobility_right'] or 0
            
            if abs(left - right) > 3:
                asymmetries.append({
                    'test': '어깨 유연성',
                    'left': f"{left}cm",
                    'right': f"{right}cm", 
                    'difference': f"{abs(left - right)}cm",
                    'severity': 'high' if abs(left - right) > 5 else 'medium'
                })
        
        return asymmetries
    
    @staticmethod
    def identify_priority_areas(assessment: Dict[str, Any]) -> List[str]:
        """Identify priority areas for improvement"""
        priorities = []
        
        # Check category scores
        if assessment.get('strength_score', 0) < 15:
            priorities.append("근력 강화")
        
        if assessment.get('mobility_score', 0) < 15:
            priorities.append("유연성 개선")
        
        if assessment.get('balance_score', 0) < 15:
            priorities.append("균형 능력 향상")
        
        if assessment.get('cardio_score', 0) < 15:
            priorities.append("심폐지구력 개선")
        
        # Check for severe asymmetries
        asymmetries = AnalyticsService.detect_asymmetries(assessment)
        if any(a['severity'] == 'high' for a in asymmetries):
            priorities.insert(0, "좌우 불균형 교정")
        
        return priorities[:3]  # Return top 3 priorities


class RecommendationService:
    """Service for generating personalized recommendations"""
    
    @staticmethod
    @login_required
    def get_recommendations(client_id: int, assessment_id: int) -> Dict[str, Any]:
        """Get personalized recommendations"""
        try:
            # Get client and assessment details
            client = ClientService.get_client_details(client_id)
            assessment = AssessmentService.get_assessment_details(assessment_id)
            
            if not client or not assessment:
                return {}
            
            # Generate recommendations
            recommender = recommendations.PersonalizedRecommendations(
                age=client['age'],
                gender=client['gender'],
                assessment_results=assessment
            )
            
            return recommender.generate_recommendations()
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'get_recommendations'})
            return {}


class AppInitService:
    """Application initialization service"""
    
    @staticmethod
    def initialize():
        """Initialize application"""
        try:
            # Initialize database
            from database import init_db
            init_db()
            
            # Check fonts
            AppInitService.check_fonts()
            
            # Log initialization
            app_logger.info("Application initialized successfully")
            
        except Exception as e:
            error_logger.log_critical("Application initialization failed", error=e)
            raise
    
    @staticmethod
    def check_fonts():
        """Check if required fonts are available"""
        from pathlib import Path
        
        font_regular = Path(config.ui.font_regular)
        font_bold = Path(config.ui.font_bold)
        
        if not font_regular.exists() or not font_bold.exists():
            app_logger.warning("Required fonts not found")
            # Could download or use fallback fonts