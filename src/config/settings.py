"""
Application configuration settings
"""
import os
from pathlib import Path


class DatabaseConfig:
    """Database configuration"""
    DB_PATH = os.path.join(Path(__file__).parent.parent.parent, 'data', 'fitness_assessment.db')
    TIMEOUT = 30.0
    BACKUP_DIR = os.path.join(Path(__file__).parent.parent.parent, 'data', 'backups')


class SecurityConfig:
    """Security configuration"""
    MIN_PASSWORD_LENGTH = 8
    SESSION_TIMEOUT_MINUTES = 60
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 5
    BCRYPT_ROUNDS = 12


class CacheConfig:
    """Cache configuration"""
    ENABLE_CACHE = True
    ENABLE_CACHE_WARMING = True
    DEFAULT_TTL = 300  # 5 minutes
    CLIENT_CACHE_TTL = 600  # 10 minutes
    ASSESSMENT_CACHE_TTL = 300  # 5 minutes
    STATS_CACHE_TTL = 180  # 3 minutes


class LoggingConfig:
    """Logging configuration"""
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DIR = os.path.join(Path(__file__).parent.parent.parent, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'fitness_app.log')
    AUDIT_LOG_FILE = os.path.join(LOG_DIR, 'audit.log')
    SECURITY_LOG_FILE = os.path.join(LOG_DIR, 'security.log')
    ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')
    PERFORMANCE_LOG_FILE = os.path.join(LOG_DIR, 'performance.log')


class UIConfig:
    """UI configuration"""
    APP_TITLE = "더파이브 헬스케어 Fitness Assessment System"
    PAGE_ICON = "💪"
    LAYOUT = "wide"
    SIDEBAR_STATE = "auto"


class ReportConfig:
    """Report configuration"""
    FONT_DIR = os.path.join(Path(__file__).parent.parent.parent, 'assets', 'fonts')
    TEMP_DIR = os.path.join(Path(__file__).parent.parent.parent, 'temp')


class AppConfig:
    """Main application configuration"""
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Component configs
    database = DatabaseConfig()
    security = SecurityConfig()
    cache = CacheConfig()
    logging = LoggingConfig()
    ui = UIConfig()
    report = ReportConfig()


# Global configuration instance
config = AppConfig()