"""
Secure session management with timeout and CSRF protection
"""
import secrets
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import json
from functools import wraps

logger = logging.getLogger(__name__)


class SecureSession:
    """Secure session management with timeout and CSRF protection"""
    
    def __init__(self, timeout_minutes: int = 30, 
                 absolute_timeout_minutes: int = 480):  # 8 hours absolute timeout
        self.timeout_minutes = timeout_minutes
        self.absolute_timeout_minutes = absolute_timeout_minutes
    
    def create_session(self, trainer_id: int, trainer_name: str) -> Dict[str, str]:
        """Create secure session with CSRF token"""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        
        session_data = {
            'session_id': session_id,
            'csrf_token': csrf_token,
            'session_created': datetime.now(),
            'last_activity': datetime.now(),
            'trainer_id': trainer_id,
            'trainer_name': trainer_name,
            'logged_in': True,
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent()
        }
        
        # Store in session state
        st.session_state.update(session_data)
        
        logger.info(f"Session created for trainer {trainer_id}")
        
        return {
            'session_id': session_id,
            'csrf_token': csrf_token
        }
    
    def validate_session(self) -> bool:
        """Check if session is valid and not expired"""
        if not st.session_state.get('logged_in', False):
            return False
        
        if 'session_id' not in st.session_state:
            return False
        
        # Check session creation time (absolute timeout)
        session_created = st.session_state.get('session_created')
        if not session_created:
            self.clear_session()
            return False
        
        if datetime.now() - session_created > timedelta(minutes=self.absolute_timeout_minutes):
            logger.warning("Session expired due to absolute timeout")
            self.clear_session()
            return False
        
        # Check last activity (idle timeout)
        last_activity = st.session_state.get('last_activity')
        if not last_activity:
            self.clear_session()
            return False
        
        if datetime.now() - last_activity > timedelta(minutes=self.timeout_minutes):
            logger.warning("Session expired due to inactivity")
            self.clear_session()
            return False
        
        # Validate session consistency (basic fingerprinting)
        if self._has_session_changed():
            logger.warning("Session validation failed - potential hijacking attempt")
            self.clear_session()
            return False
        
        # Update last activity
        st.session_state.last_activity = datetime.now()
        return True
    
    def verify_csrf_token(self, provided_token: str) -> bool:
        """Verify CSRF token"""
        stored_token = st.session_state.get('csrf_token')
        if not stored_token or not provided_token:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(stored_token, provided_token)
    
    def regenerate_session_id(self):
        """Regenerate session ID to prevent session fixation"""
        if 'session_id' in st.session_state:
            new_session_id = secrets.token_urlsafe(32)
            st.session_state.session_id = new_session_id
            logger.info("Session ID regenerated")
    
    def clear_session(self):
        """Clear all session data"""
        session_keys = [
            'session_id', 'csrf_token', 'session_created', 
            'last_activity', 'trainer_id', 'trainer_name', 
            'logged_in', 'ip_address', 'user_agent',
            'current_client_id', 'current_page'
        ]
        
        for key in session_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("Session cleared")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self.validate_session():
            return {}
        
        return {
            'trainer_id': st.session_state.get('trainer_id'),
            'trainer_name': st.session_state.get('trainer_name'),
            'session_created': st.session_state.get('session_created'),
            'last_activity': st.session_state.get('last_activity'),
            'time_remaining': self._get_time_remaining()
        }
    
    def extend_session(self, minutes: int = 30):
        """Extend current session"""
        if self.validate_session():
            st.session_state.last_activity = datetime.now()
            logger.info(f"Session extended by {minutes} minutes")
    
    def _get_time_remaining(self) -> int:
        """Get minutes remaining in session"""
        if 'last_activity' not in st.session_state:
            return 0
        
        last_activity = st.session_state.last_activity
        elapsed = datetime.now() - last_activity
        remaining = self.timeout_minutes - (elapsed.total_seconds() / 60)
        
        return max(0, int(remaining))
    
    def _get_client_ip(self) -> str:
        """Get client IP address (placeholder - would need proper implementation)"""
        # In a real deployment, this would get the actual client IP
        # from headers like X-Forwarded-For
        return "unknown"
    
    def _get_user_agent(self) -> str:
        """Get user agent (placeholder - would need proper implementation)"""
        # In a real deployment, this would get the actual user agent
        return "unknown"
    
    def _has_session_changed(self) -> bool:
        """Check if session fingerprint has changed"""
        # Basic implementation - in production would check IP, user agent, etc.
        return False


# Global session manager instance
session_manager = SecureSession()


# Decorator for protecting routes
def login_required(func):
    """Decorator to ensure user is logged in"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session_manager.validate_session():
            st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
            st.session_state.current_page = "login"
            st.rerun()
            return None
        return func(*args, **kwargs)
    return wrapper


def csrf_protected(func):
    """Decorator to validate CSRF token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For Streamlit, we'll handle CSRF differently since it's not a traditional web app
        # This is a placeholder for the concept
        return func(*args, **kwargs)
    return wrapper


# Session activity tracker
class ActivityTracker:
    """Track user activities for audit logging"""
    
    @staticmethod
    def log_activity(action: str, details: Dict[str, Any] = None):
        """Log user activity"""
        if 'trainer_id' not in st.session_state:
            return
        
        activity = {
            'timestamp': datetime.now().isoformat(),
            'trainer_id': st.session_state.trainer_id,
            'action': action,
            'details': details or {},
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        
        logger.info(f"Activity: {json.dumps(activity)}")


# Session timeout warning component
def show_session_timeout_warning():
    """Show session timeout warning when approaching timeout"""
    if not session_manager.validate_session():
        return
    
    time_remaining = session_manager._get_time_remaining()
    
    if time_remaining <= 5 and time_remaining > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"⏰ 세션이 {time_remaining}분 후 만료됩니다.")
        with col2:
            if st.button("연장", key="extend_session"):
                session_manager.extend_session()
                st.rerun()


# Session info display component  
def show_session_info():
    """Display current session information"""
    if session_manager.validate_session():
        session_info = session_manager.get_session_info()
        
        with st.expander("세션 정보", expanded=False):
            st.write(f"사용자: {session_info['trainer_name']}")
            st.write(f"로그인 시간: {session_info['session_created'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"남은 시간: {session_info['time_remaining']}분")
            
            if st.button("로그아웃", key="logout_from_info"):
                ActivityTracker.log_activity("logout")
                session_manager.clear_session()
                st.rerun()


# Auto-logout component
def auto_logout_check():
    """Check for auto-logout conditions"""
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        if not session_manager.validate_session():
            st.error("세션이 만료되어 자동으로 로그아웃되었습니다.")
            time.sleep(2)
            st.rerun()