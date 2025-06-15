"""
Production settings
"""
from .base import *
import dj_database_url

# Security settings
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database configuration from DATABASE_URL
if config('DATABASE_URL', default=''):
    DATABASES['default'] = dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

# Static files handling with whitenoise
# Find the position of SecurityMiddleware and insert WhiteNoise after it
security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Compress settings
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# CORS settings for API
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
if not CORS_ALLOWED_ORIGINS:
    # Default to allowing the Heroku app domain
    CORS_ALLOWED_ORIGINS = [
        f"https://{ALLOWED_HOSTS[0]}" if ALLOWED_HOSTS else "https://the5hc.herokuapp.com",
    ]

# CSRF trusted origins for Django 4.0+
if not config('CSRF_TRUSTED_ORIGINS', default=''):
    CSRF_TRUSTED_ORIGINS = [
        f"https://{ALLOWED_HOSTS[0]}" if ALLOWED_HOSTS else "https://the5hc.herokuapp.com",
        "https://the5hc-ed48c8d8fe2e.herokuapp.com",  # Heroku app URL
    ]

# Email configuration (example with Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)

# Logging - Heroku uses stdout for logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}