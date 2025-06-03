"""
Production configuration for Heroku deployment
"""
import os

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_PRODUCTION = bool(DATABASE_URL)

# Streamlit configuration
STREAMLIT_CONFIG = {
    'server.port': int(os.environ.get('PORT', 8501)),
    'server.address': '0.0.0.0',
    'server.enableCORS': False,
    'server.enableXsrfProtection': False,
    'server.maxUploadSize': 50,  # MB
    'browser.gatherUsageStats': False,
}

# Application settings
APP_CONFIG = {
    'debug': os.environ.get('DEBUG', 'False').lower() == 'true',
    'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
    'secret_key': os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production'),
}

# Security settings
SECURITY_CONFIG = {
    'password_min_length': 8,
    'bcrypt_rounds': 12,
    'session_timeout_hours': 24,
}

# PDF generation settings
PDF_CONFIG = {
    'max_file_size_mb': 10,
    'weasyprint_timeout': 30,
}

def get_config():
    """Get configuration based on environment"""
    return {
        'database_url': DATABASE_URL,
        'is_production': IS_PRODUCTION,
        'streamlit': STREAMLIT_CONFIG,
        'app': APP_CONFIG,
        'security': SECURITY_CONFIG,
        'pdf': PDF_CONFIG,
    }