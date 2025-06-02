"""
Security-related tests
"""
import pytest
import time
from datetime import datetime, timedelta
from database import (
    hash_password, verify_password, validate_email, 
    sanitize_input, AuthRateLimiter
)
from auth import SecureSession
import secrets


class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        """Test bcrypt password hashing"""
        password = "TestPassword123!"
        
        # Test hashing
        hashed = hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        
        # Test verification
        assert verify_password(hashed, password) == True
        assert verify_password(hashed, "WrongPassword") == False
    
    def test_password_validation(self):
        """Test password validation rules"""
        # Too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            hash_password("short")
        
        # Empty password
        with pytest.raises(ValueError):
            hash_password("")
    
    def test_different_passwords_different_hashes(self):
        """Test that same password generates different hashes (due to salt)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different salts
        assert verify_password(hash1, password)
        assert verify_password(hash2, password)


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        assert validate_email("user@example.com") == True
        assert validate_email("test.user+tag@example.co.uk") == True
        
        # Invalid emails
        assert validate_email("notanemail") == False
        assert validate_email("@example.com") == False
        assert validate_email("user@") == False
        assert validate_email("user@.com") == False
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Basic sanitization
        assert sanitize_input("  test  ") == "test"
        assert sanitize_input(None) == ""
        assert sanitize_input(123) == "123"
        
        # Control character removal
        assert sanitize_input("test\x00\x01\x02") == "test"
        assert sanitize_input("line1\nline2") == "line1\nline2"  # Newlines are allowed
        
        # Length limiting
        long_input = "a" * 300
        assert len(sanitize_input(long_input, max_length=100)) == 100


class TestRateLimiting:
    """Test authentication rate limiting"""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality"""
        limiter = AuthRateLimiter(max_attempts=3, window_minutes=1)
        
        # Should allow initial attempts
        allowed, locked_until = limiter.check_rate_limit("testuser")
        assert allowed == True
        assert locked_until is None
        
        # Record failed attempts
        for _ in range(3):
            limiter.record_failed_attempt("testuser")
        
        # Should be blocked after max attempts
        allowed, locked_until = limiter.check_rate_limit("testuser")
        assert allowed == False
        assert locked_until is not None
        assert locked_until > datetime.now()
    
    def test_rate_limiter_reset(self):
        """Test rate limiter reset on successful login"""
        limiter = AuthRateLimiter(max_attempts=3, window_minutes=1)
        
        # Record some failed attempts
        limiter.record_failed_attempt("testuser")
        limiter.record_failed_attempt("testuser")
        
        # Reset should clear attempts
        limiter.reset_attempts("testuser")
        
        # Should allow attempts again
        allowed, _ = limiter.check_rate_limit("testuser")
        assert allowed == True


class TestSessionSecurity:
    """Test session management security"""
    
    def test_session_creation(self):
        """Test secure session creation"""
        session = SecureSession(timeout_minutes=30)
        
        session_data = session.create_session(
            trainer_id=1,
            trainer_name="Test Trainer"
        )
        
        assert 'session_id' in session_data
        assert 'csrf_token' in session_data
        assert len(session_data['session_id']) >= 32
        assert len(session_data['csrf_token']) >= 32
        assert session_data['session_id'] != session_data['csrf_token']
    
    def test_session_timeout(self):
        """Test session timeout"""
        # Mock session state
        import streamlit as st
        
        # Create session with 1 second timeout for testing
        session = SecureSession(timeout_minutes=1/60)  # 1 second
        
        st.session_state.update({
            'logged_in': True,
            'session_id': 'test_session',
            'last_activity': datetime.now() - timedelta(seconds=2),  # Expired
            'session_created': datetime.now()
        })
        
        # Should be invalid due to timeout
        assert session.validate_session() == False
    
    def test_csrf_token_verification(self):
        """Test CSRF token verification"""
        session = SecureSession()
        
        # Generate tokens
        token = secrets.token_urlsafe(32)
        import streamlit as st
        st.session_state['csrf_token'] = token
        
        # Verify correct token
        assert session.verify_csrf_token(token) == True
        
        # Verify incorrect token
        assert session.verify_csrf_token("wrong_token") == False
        
        # Verify empty token
        assert session.verify_csrf_token("") == False


class TestSecurityIntegration:
    """Integration tests for security features"""
    
    @pytest.fixture
    def setup_test_db(self, tmp_path):
        """Set up temporary test database"""
        import sys
        sys.path.insert(0, str(tmp_path))
        
        # Override database path
        from database import DatabaseConfig
        original_path = DatabaseConfig.DB_PATH
        DatabaseConfig.DB_PATH = str(tmp_path / "test.db")
        
        # Initialize database
        from database import init_db
        init_db()
        
        yield
        
        # Cleanup
        DatabaseConfig.DB_PATH = original_path
    
    def test_secure_registration_flow(self, setup_test_db):
        """Test complete secure registration flow"""
        from database import register_trainer
        
        # Test successful registration
        success = register_trainer(
            username="testuser",
            password="SecurePass123!",
            name="Test User",
            email="test@example.com"
        )
        assert success == True
        
        # Test duplicate registration
        success = register_trainer(
            username="testuser",
            password="AnotherPass123!",
            name="Test User 2",
            email="test2@example.com"
        )
        assert success == False
    
    def test_secure_authentication_flow(self, setup_test_db):
        """Test complete secure authentication flow"""
        from database import register_trainer, authenticate
        
        # Register user
        register_trainer(
            username="authtest",
            password="AuthPass123!",
            name="Auth Test",
            email="auth@example.com"
        )
        
        # Test successful authentication
        trainer_id = authenticate("authtest", "AuthPass123!")
        assert trainer_id is not None
        
        # Test failed authentication
        trainer_id = authenticate("authtest", "WrongPassword")
        assert trainer_id is None
        
        # Test rate limiting after multiple failures
        for _ in range(5):
            authenticate("authtest", "WrongPassword")
        
        # Should be rate limited now
        trainer_id = authenticate("authtest", "AuthPass123!")
        assert trainer_id is None  # Even correct password fails due to rate limit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])