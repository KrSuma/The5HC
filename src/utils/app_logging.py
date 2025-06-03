"""
Comprehensive logging configuration with structured logging and monitoring
"""
import logging
import logging.handlers
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from pathlib import Path
import os


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName
        }
        
        # Add custom fields if present
        for field in ['user_id', 'trainer_id', 'client_id', 'action', 
                      'ip_address', 'session_id', 'request_id']:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class SecurityLogger:
    """Specialized logger for security-related events"""
    
    def __init__(self, name: str = 'security'):
        self.logger = logging.getLogger(name)
    
    def log_auth_attempt(self, username: str, success: bool, 
                         ip_address: str = None, reason: str = None):
        """Log authentication attempt"""
        extra = {
            'action': 'auth_attempt',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'reason': reason
        }
        
        if success:
            self.logger.info(f"Successful authentication: {username}", extra=extra)
        else:
            self.logger.warning(f"Failed authentication: {username}", extra=extra)
    
    def log_access_denied(self, user_id: int, resource: str, reason: str):
        """Log access denied events"""
        extra = {
            'action': 'access_denied',
            'user_id': user_id,
            'resource': resource,
            'reason': reason
        }
        self.logger.warning(f"Access denied to {resource}", extra=extra)
    
    def log_suspicious_activity(self, user_id: Optional[int], 
                                activity: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        extra = {
            'action': 'suspicious_activity',
            'user_id': user_id,
            'activity': activity,
            'details': details
        }
        self.logger.error(f"Suspicious activity detected: {activity}", extra=extra)


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, name: str = 'performance'):
        self.logger = logging.getLogger(name)
    
    def log_operation_time(self, operation: str, duration_ms: float, 
                          details: Dict[str, Any] = None):
        """Log operation execution time"""
        extra = {
            'action': 'performance',
            'operation': operation,
            'duration_ms': duration_ms,
            'details': details or {}
        }
        
        level = logging.INFO
        if duration_ms > 1000:  # Warn if operation takes more than 1 second
            level = logging.WARNING
        elif duration_ms > 5000:  # Error if more than 5 seconds
            level = logging.ERROR
            
        self.logger.log(level, f"Operation {operation} took {duration_ms}ms", extra=extra)
    
    def log_database_query(self, query: str, duration_ms: float, 
                          row_count: int = None):
        """Log database query performance"""
        extra = {
            'action': 'db_query',
            'query': query[:200],  # Truncate long queries
            'duration_ms': duration_ms,
            'row_count': row_count
        }
        
        if duration_ms > 100:  # Warn if query takes more than 100ms
            self.logger.warning(f"Slow query detected ({duration_ms}ms)", extra=extra)
        else:
            self.logger.debug(f"Query executed in {duration_ms}ms", extra=extra)


class AuditLogger:
    """Logger for audit trail"""
    
    def __init__(self, name: str = 'audit'):
        self.logger = logging.getLogger(name)
    
    def log_data_access(self, user_id: int, entity_type: str, 
                       entity_id: int, action: str):
        """Log data access for audit trail"""
        extra = {
            'action': 'data_access',
            'user_id': user_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'access_type': action
        }
        self.logger.info(f"Data access: {entity_type}:{entity_id}", extra=extra)
    
    def log_data_modification(self, user_id: int, entity_type: str, 
                             entity_id: int, changes: Dict[str, Any]):
        """Log data modifications"""
        extra = {
            'action': 'data_modification',
            'user_id': user_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'changes': changes
        }
        self.logger.info(f"Data modified: {entity_type}:{entity_id}", extra=extra)
    
    def log_admin_action(self, admin_id: int, action: str, 
                        target_user_id: int = None, details: Dict[str, Any] = None):
        """Log administrative actions"""
        extra = {
            'action': 'admin_action',
            'admin_id': admin_id,
            'admin_action': action,
            'target_user_id': target_user_id,
            'details': details or {}
        }
        self.logger.warning(f"Admin action: {action}", extra=extra)


class ErrorLogger:
    """Enhanced error logging with context"""
    
    def __init__(self, name: str = 'error'):
        self.logger = logging.getLogger(name)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  user_id: int = None, request_id: str = None):
        """Log error with full context"""
        extra = {
            'action': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'user_id': user_id,
            'request_id': request_id
        }
        self.logger.error(f"Error occurred: {type(error).__name__}", 
                         exc_info=True, extra=extra)
    
    def log_critical(self, message: str, error: Exception = None,
                    context: Dict[str, Any] = None):
        """Log critical errors that need immediate attention"""
        extra = {
            'action': 'critical_error',
            'context': context or {}
        }
        
        if error:
            extra['error_type'] = type(error).__name__
            extra['error_message'] = str(error)
            
        self.logger.critical(message, exc_info=bool(error), extra=extra)


# Decorators for automatic logging
def log_execution_time(operation_name: str = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger.log_operation_time(
                    operation_name or func.__name__,
                    duration_ms,
                    {'args': str(args)[:100], 'kwargs': str(kwargs)[:100]}
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                error_logger.log_error(
                    e,
                    context={
                        'function': func.__name__,
                        'duration_ms': duration_ms
                    }
                )
                raise
                
        return wrapper
    return decorator


def log_database_operation(func):
    """Decorator for database operation logging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract query from args if present
            query = args[0] if args and isinstance(args[0], str) else "Unknown query"
            
            perf_logger.log_database_query(
                query,
                duration_ms,
                row_count=len(result) if hasattr(result, '__len__') else None
            )
            
            return result
        except Exception as e:
            error_logger.log_error(
                e,
                context={'function': func.__name__, 'args': str(args)[:200]}
            )
            raise
            
    return wrapper


def audit_data_access(entity_type: str):
    """Decorator for auditing data access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract user_id from session state
            import streamlit as st
            user_id = st.session_state.get('trainer_id')
            
            # Try to extract entity_id from args
            entity_id = args[0] if args else None
            
            if user_id and entity_id:
                audit_logger.log_data_access(
                    user_id, entity_type, entity_id, func.__name__
                )
            
            return func(*args, **kwargs)
            
        return wrapper
    return decorator


# Configure logging
def setup_logging(log_level: str = 'INFO', log_dir: str = 'logs'):
    """Setup comprehensive logging configuration"""
    
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with simple format for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handlers with structured format
    log_files = {
        'app': 'app.log',
        'security': 'security.log',
        'performance': 'performance.log',
        'audit': 'audit.log',
        'error': 'error.log'
    }
    
    for logger_name, filename in log_files.items():
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, filename),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        
        # Add handler to specific logger
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        
        # Don't propagate to root logger to avoid duplication
        logger.propagate = False
    
    # Also add all logs to a combined file
    combined_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'combined.log'),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10
    )
    combined_handler.setLevel(logging.DEBUG)
    combined_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(combined_handler)
    
    logging.info("Logging configured successfully")


# Create logger instances
app_logger = logging.getLogger('app')
security_logger = SecurityLogger()
perf_logger = PerformanceLogger()
audit_logger = AuditLogger()
error_logger = ErrorLogger()


# Utility function for getting a logger with context
def get_logger(name: str, **context) -> logging.LoggerAdapter:
    """Get a logger with additional context"""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, context)


# Initialize logging when module is imported
setup_logging()