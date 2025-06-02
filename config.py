"""
Centralized configuration module for the fitness assessment application
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import os
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "fitness_assessment.db"
    timeout: float = 30.0
    check_same_thread: bool = False
    
    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    pool_recycle: int = 3600  # 1 hour


@dataclass
class SecurityConfig:
    """Security configuration"""
    # Password policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = False
    
    # Bcrypt settings
    bcrypt_rounds: int = 12
    
    # Session settings
    session_timeout_minutes: int = 30
    absolute_session_timeout_minutes: int = 480  # 8 hours
    
    # Rate limiting
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 5
    
    # CSRF settings
    csrf_token_length: int = 32
    csrf_header_name: str = "X-CSRF-Token"


@dataclass
class UIConfig:
    """UI configuration"""
    # Application info
    app_name: str = "더파이브 헬스케어 Fitness Assessment System"
    app_version: str = "2.0.0"
    
    # Theme colors
    primary_color: str = "#ff4b4b"
    success_color: str = "#4bb543"
    warning_color: str = "#f0ad4e"
    info_color: str = "#3498db"
    danger_color: str = "#dc3545"
    
    # Layout settings
    sidebar_width: int = 300
    main_column_width: int = 1200
    
    # Font settings
    font_regular: str = "NanumGothic.ttf"
    font_bold: str = "NanumGothicBold.ttf"
    font_size_small: int = 10
    font_size_default: int = 12
    font_size_large: int = 14
    font_size_xlarge: int = 16
    
    # Pagination
    default_page_size: int = 10
    max_page_size: int = 100
    
    # Chart settings
    chart_height: int = 400
    chart_colors: List[str] = field(default_factory=lambda: [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57"
    ])


@dataclass
class AssessmentConfig:
    """Assessment configuration"""
    # Scoring settings
    max_overall_score: float = 100.0
    category_max_score: float = 25.0
    
    # Test configurations
    overhead_squat_max_score: int = 3
    pushup_max_score: int = 3
    toe_touch_max_score: int = 3
    
    # Balance test timeouts (seconds)
    balance_test_max_duration: float = 60.0
    balance_test_eyes_open_target: float = 45.0
    balance_test_eyes_closed_target: float = 30.0
    
    # Harvard step test
    harvard_step_height_cm: float = 45.0
    harvard_step_duration_minutes: float = 3.0
    harvard_recovery_time_seconds: int = 60
    
    # Farmer's carry defaults
    farmers_carry_default_distance_m: float = 40.0


@dataclass 
class ScoringThresholds:
    """Scoring thresholds for assessments"""
    
    # Push-up thresholds by age and gender
    pushup_thresholds: Dict[str, Dict[str, List[Dict[str, Any]]]] = field(
        default_factory=lambda: {
            'male': {
                'age_ranges': [
                    {'min': 0, 'max': 29, 'excellent': 36, 'good': 29, 'average': 22, 'poor': 16},
                    {'min': 30, 'max': 39, 'excellent': 30, 'good': 24, 'average': 17, 'poor': 12},
                    {'min': 40, 'max': 49, 'excellent': 25, 'good': 20, 'average': 13, 'poor': 9},
                    {'min': 50, 'max': 59, 'excellent': 20, 'good': 15, 'average': 10, 'poor': 6},
                    {'min': 60, 'max': 120, 'excellent': 15, 'good': 10, 'average': 8, 'poor': 4}
                ]
            },
            'female': {
                'age_ranges': [
                    {'min': 0, 'max': 29, 'excellent': 30, 'good': 23, 'average': 15, 'poor': 9},
                    {'min': 30, 'max': 39, 'excellent': 27, 'good': 20, 'average': 13, 'poor': 7},
                    {'min': 40, 'max': 49, 'excellent': 24, 'good': 15, 'average': 11, 'poor': 4},
                    {'min': 50, 'max': 59, 'excellent': 21, 'good': 11, 'average': 7, 'poor': 1},
                    {'min': 60, 'max': 120, 'excellent': 17, 'good': 12, 'average': 5, 'poor': 1}
                ]
            }
        }
    )
    
    # Balance thresholds
    balance_thresholds: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            'eyes_open': {'excellent': 45.0, 'good': 30.0, 'average': 15.0, 'poor': 10.0},
            'eyes_closed': {'excellent': 30.0, 'good': 20.0, 'average': 10.0, 'poor': 5.0}
        }
    )
    
    # Harvard step test thresholds
    harvard_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            'excellent': 90.0,
            'good': 80.0,
            'average': 65.0,
            'poor': 55.0
        }
    )
    
    # Farmer's carry weight percentages (of body weight)
    farmers_carry_percentages: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            'male': {'excellent': 1.0, 'good': 0.75, 'average': 0.5, 'poor': 0.25},
            'female': {'excellent': 0.75, 'good': 0.5, 'average': 0.35, 'poor': 0.2}
        }
    )


@dataclass
class CacheConfig:
    """Cache configuration"""
    # Cache sizes
    client_cache_size: int = 500
    assessment_cache_size: int = 1000
    trainer_cache_size: int = 100
    stats_cache_size: int = 200
    query_cache_size: int = 500
    
    # TTL settings (seconds)
    client_cache_ttl: int = 600  # 10 minutes
    assessment_cache_ttl: int = 300  # 5 minutes
    trainer_cache_ttl: int = 1800  # 30 minutes
    stats_cache_ttl: int = 60  # 1 minute
    query_cache_ttl: int = 300  # 5 minutes
    
    # Cache warming
    enable_cache_warming: bool = True
    cache_warm_on_startup: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    # Log file settings
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Log retention
    log_retention_days: int = 30
    
    # Performance logging thresholds
    slow_query_threshold_ms: float = 100.0
    slow_operation_threshold_ms: float = 1000.0


@dataclass
class EmailConfig:
    """Email configuration (for future use)"""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    use_tls: bool = True
    
    from_email: str = "noreply@fitness-assessment.com"
    from_name: str = "Fitness Assessment System"


@dataclass
class APIConfig:
    """API configuration (for future use)"""
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    api_key_header: str = "X-API-Key"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


@dataclass
class AppConfig:
    """Main application configuration"""
    # Environment
    environment: str = os.getenv("APP_ENV", "development")
    debug: bool = environment == "development"
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    assessment: AssessmentConfig = field(default_factory=AssessmentConfig)
    scoring: ScoringThresholds = field(default_factory=ScoringThresholds)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Paths
    @property
    def root_dir(self) -> Path:
        """Get application root directory"""
        return Path(__file__).parent
    
    @property
    def font_dir(self) -> Path:
        """Get font directory"""
        return self.root_dir
    
    @property
    def log_dir(self) -> Path:
        """Get log directory"""
        return self.root_dir / self.logging.log_dir
    
    @property
    def temp_dir(self) -> Path:
        """Get temporary directory"""
        temp = self.root_dir / "temp"
        temp.mkdir(exist_ok=True)
        return temp


# Global configuration instance
config = AppConfig()


# Configuration loading from environment or file
def load_config_from_env():
    """Load configuration from environment variables"""
    # Database
    if db_path := os.getenv("DB_PATH"):
        config.database.path = db_path
    
    # Security
    if session_timeout := os.getenv("SESSION_TIMEOUT_MINUTES"):
        config.security.session_timeout_minutes = int(session_timeout)
    
    if bcrypt_rounds := os.getenv("BCRYPT_ROUNDS"):
        config.security.bcrypt_rounds = int(bcrypt_rounds)
    
    # Logging
    if log_level := os.getenv("LOG_LEVEL"):
        config.logging.log_level = log_level
    
    if log_dir := os.getenv("LOG_DIR"):
        config.logging.log_dir = log_dir


# Load configuration on module import
load_config_from_env()


# Configuration validation
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate database path
    if not config.database.path:
        errors.append("Database path is required")
    
    # Validate security settings
    if config.security.min_password_length < 6:
        errors.append("Minimum password length must be at least 6")
    
    if config.security.bcrypt_rounds < 10:
        errors.append("Bcrypt rounds should be at least 10 for security")
    
    # Validate cache settings
    if config.cache.client_cache_size < 100:
        errors.append("Client cache size should be at least 100")
    
    # Validate logging
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.log_level.upper() not in valid_log_levels:
        errors.append(f"Invalid log level: {config.logging.log_level}")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")


# Validate on import
try:
    validate_config()
except ValueError as e:
    print(f"Warning: {e}")


# Helper functions for accessing configuration
def get_db_path() -> str:
    """Get database path"""
    return config.database.path


def get_font_path(font_type: str = "regular") -> Path:
    """Get font file path"""
    if font_type == "bold":
        return config.font_dir / config.ui.font_bold
    return config.font_dir / config.ui.font_regular


def get_scoring_thresholds(test_type: str) -> Dict[str, Any]:
    """Get scoring thresholds for a specific test"""
    if test_type == "pushup":
        return config.scoring.pushup_thresholds
    elif test_type == "balance":
        return config.scoring.balance_thresholds
    elif test_type == "harvard":
        return config.scoring.harvard_thresholds
    elif test_type == "farmers_carry":
        return config.scoring.farmers_carry_percentages
    else:
        raise ValueError(f"Unknown test type: {test_type}")


# Development vs Production settings
if config.environment == "production":
    # Override settings for production
    config.security.session_timeout_minutes = 15
    config.security.bcrypt_rounds = 14
    config.logging.log_level = "WARNING"
    config.cache.enable_cache_warming = True
    config.debug = False
else:
    # Development settings
    config.security.session_timeout_minutes = 60
    config.logging.log_level = "DEBUG"
    config.cache.enable_cache_warming = False