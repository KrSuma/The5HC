"""
Authentication service with security features
"""
from typing import Optional, Tuple
from datetime import datetime, timedelta
import bcrypt
import secrets

from ..core.models import Trainer
from ..core.constants import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES
from ..data.repositories import RepositoryFactory
from ..utils.logging import security_logger, audit_logger, error_logger, app_logger
from ..utils.validators import validate_email, sanitize_input
from ..config.settings import SecurityConfig


class RateLimiter:
    """Rate limiting for login attempts"""
    
    def __init__(self):
        self._attempts = {}
        self._lockouts = {}
    
    def check_rate_limit(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """Check if user is rate limited"""
        # Check if locked out
        if username in self._lockouts:
            lockout_until = self._lockouts[username]
            if datetime.now() < lockout_until:
                return False, lockout_until
            else:
                # Lockout expired
                del self._lockouts[username]
                if username in self._attempts:
                    del self._attempts[username]
        
        return True, None
    
    def record_failure(self, username: str):
        """Record failed login attempt"""
        if username not in self._attempts:
            self._attempts[username] = 0
        
        self._attempts[username] += 1
        
        if self._attempts[username] >= MAX_LOGIN_ATTEMPTS:
            lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            self._lockouts[username] = lockout_until
            security_logger.log_auth_attempt(username, False, reason="account_locked")
    
    def clear_attempts(self, username: str):
        """Clear login attempts after successful login"""
        if username in self._attempts:
            del self._attempts[username]
        if username in self._lockouts:
            del self._lockouts[username]


class SessionManager:
    """Manage user sessions"""
    
    def __init__(self):
        self._sessions = {}
        self._session_timeout = timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES)
    
    def create_session(self, trainer_id: int, username: str) -> dict:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'trainer_id': trainer_id,
            'username': username,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        self._sessions[session_id] = session_data
        return {
            'session_id': session_id,
            'trainer_id': trainer_id,
            'username': username
        }
    
    def validate_session(self, session_id: str) -> Optional[dict]:
        """Validate and refresh session"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # Check timeout
        if datetime.now() - session['last_activity'] > self._session_timeout:
            del self._sessions[session_id]
            return None
        
        # Update last activity
        session['last_activity'] = datetime.now()
        return session
    
    def end_session(self, session_id: str):
        """End session"""
        if session_id in self._sessions:
            del self._sessions[session_id]


class AuthService:
    """Enhanced authentication service with security features"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.session_manager = SessionManager()
        self.trainer_repo = RepositoryFactory.get_trainer_repository()
    
    def register(self, username: str, password: str, name: str, email: str) -> Tuple[bool, str]:
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
            if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
                return False, f"비밀번호는 최소 {SecurityConfig.MIN_PASSWORD_LENGTH}자 이상이어야 합니다."
            
            # Check if username exists
            existing = self.trainer_repo.get_by_username(username)
            if existing:
                return False, "사용자명이 이미 존재합니다."
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create trainer
            trainer = Trainer(
                username=username,
                password_hash=password_hash,
                name=name,
                email=email
            )
            
            trainer_id = self.trainer_repo.create(trainer)
            
            if trainer_id:
                app_logger.info(f"Trainer registered: {username}")
                return True, "등록이 완료되었습니다!"
            else:
                return False, "등록 중 오류가 발생했습니다."
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'register', 'username': username})
            return False, "등록 중 오류가 발생했습니다."
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """Authenticate trainer with rate limiting"""
        try:
            # Check rate limit
            allowed, locked_until = self.rate_limiter.check_rate_limit(username)
            if not allowed:
                security_logger.log_auth_attempt(username, False, reason="rate_limited")
                return False, f"너무 많은 로그인 시도로 계정이 잠겼습니다. {locked_until.strftime('%H:%M')}까지 기다려주세요.", None
            
            # Get trainer
            trainer = self.trainer_repo.get_by_username(username)
            
            if not trainer:
                self.rate_limiter.record_failure(username)
                security_logger.log_auth_attempt(username, False, reason="invalid_username")
                return False, "잘못된 사용자명 또는 비밀번호입니다.", None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), trainer.password_hash.encode('utf-8')):
                self.rate_limiter.record_failure(username)
                security_logger.log_auth_attempt(username, False, reason="invalid_password")
                
                # Update failed attempts in database
                trainer.failed_login_attempts += 1
                if trainer.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    trainer.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                self.trainer_repo.update(trainer)
                
                return False, "잘못된 사용자명 또는 비밀번호입니다.", None
            
            # Clear rate limit
            self.rate_limiter.clear_attempts(username)
            
            # Update last login
            trainer.last_login = datetime.now()
            trainer.failed_login_attempts = 0
            trainer.locked_until = None
            self.trainer_repo.update(trainer)
            
            # Create session
            session_data = self.session_manager.create_session(trainer.id, trainer.username)
            
            # Log successful login
            security_logger.log_auth_attempt(username, True)
            audit_logger.log_auth_event(trainer.id, "login")
            
            return True, "로그인 성공!", session_data
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'login', 'username': username})
            return False, "로그인 중 오류가 발생했습니다.", None
    
    def logout(self, session_id: str):
        """Logout user"""
        session = self.session_manager.validate_session(session_id)
        if session:
            audit_logger.log_auth_event(session['trainer_id'], "logout")
            self.session_manager.end_session(session_id)
    
    def validate_session(self, session_id: str) -> Optional[dict]:
        """Validate user session"""
        return self.session_manager.validate_session(session_id)
    
    def change_password(self, trainer_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change trainer password"""
        try:
            trainer = self.trainer_repo.get_by_id(trainer_id)
            if not trainer:
                return False, "트레이너를 찾을 수 없습니다."
            
            # Verify old password
            if not bcrypt.checkpw(old_password.encode('utf-8'), trainer.password_hash.encode('utf-8')):
                return False, "현재 비밀번호가 올바르지 않습니다."
            
            # Validate new password
            if len(new_password) < SecurityConfig.MIN_PASSWORD_LENGTH:
                return False, f"새 비밀번호는 최소 {SecurityConfig.MIN_PASSWORD_LENGTH}자 이상이어야 합니다."
            
            # Update password
            trainer.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            if self.trainer_repo.update(trainer):
                audit_logger.log_auth_event(trainer_id, "password_changed")
                return True, "비밀번호가 변경되었습니다."
            else:
                return False, "비밀번호 변경 중 오류가 발생했습니다."
                
        except Exception as e:
            error_logger.log_error(e, context={'action': 'change_password', 'trainer_id': trainer_id})
            return False, "비밀번호 변경 중 오류가 발생했습니다."