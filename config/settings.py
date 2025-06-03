"""
Application configuration settings
"""
import os
from typing import Dict, Any

# Environment detection
IS_PRODUCTION = bool(os.environ.get('DATABASE_URL'))

# Application settings
APP_CONFIG = {
    'debug': os.environ.get('DEBUG', 'False').lower() == 'true',
    'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
    'secret_key': os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production'),
    'app_name': 'Fitness Assessment System',
    'version': '1.0.0'
}

# Security settings
SECURITY_CONFIG = {
    'password_min_length': 8,
    'bcrypt_rounds': 12,
    'session_timeout_hours': 24,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 30
}

# Database settings
DATABASE_CONFIG = {
    'sqlite_path': 'data/fitness_assessment.db',
    'timeout': 30.0,
    'pool_size': 5,
    'max_overflow': 10
}

# PDF generation settings
PDF_CONFIG = {
    'max_file_size_mb': 10,
    'weasyprint_timeout': 30,
    'default_font': 'NanumGothic',
    'logo_path': 'assets/images/logo.png'
}

# Streamlit configuration
STREAMLIT_CONFIG = {
    'port': int(os.environ.get('PORT', 8501)),
    'address': '0.0.0.0',
    'enable_cors': False,
    'enable_xsrf_protection': False,
    'max_upload_size': 50,  # MB
    'theme': {
        'primary_color': '#FF4B4B',
        'background_color': '#FFFFFF',
        'secondary_background_color': '#F0F2F6',
        'text_color': '#262730'
    }
}

# Cache configuration
CACHE_CONFIG = {
    'ttl_hours': 24,
    'max_entries': 1000,
    'cleanup_interval_hours': 6
}

# Assessment scoring configuration
SCORING_CONFIG = {
    'categories': {
        'strength': {'weight': 0.25, 'max_score': 25},
        'mobility': {'weight': 0.25, 'max_score': 25},
        'balance': {'weight': 0.25, 'max_score': 25},
        'cardio': {'weight': 0.25, 'max_score': 25}
    },
    'grade_thresholds': {
        'excellent': 80,
        'good': 60,
        'average': 40,
        'poor': 0
    }
}

# Session management configuration
SESSION_CONFIG = {
    'default_duration_minutes': 60,
    'advance_booking_days': 90,
    'cancellation_hours': 24,
    'package_expiry_days': 365
}

# Export configuration object
class Config:
    """Configuration object with all settings"""
    
    def __init__(self):
        self.is_production = IS_PRODUCTION
        self.app = APP_CONFIG
        self.security = SECURITY_CONFIG
        self.database = DATABASE_CONFIG
        self.pdf = PDF_CONFIG
        self.streamlit = STREAMLIT_CONFIG
        self.cache = CACHE_CONFIG
        self.scoring = SCORING_CONFIG
        self.session = SESSION_CONFIG
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        section_config = getattr(self, section, {})
        if isinstance(section_config, dict):
            return section_config.get(key, default)
        return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'is_production': self.is_production,
            'app': self.app,
            'security': self.security,
            'database': self.database,
            'pdf': self.pdf,
            'streamlit': self.streamlit,
            'cache': self.cache,
            'scoring': self.scoring,
            'session': self.session
        }

# Create global config instance
config = Config()