"""
Development settings
"""
from .base import *

# Development specific settings
DEBUG = True

# Allow testserver for API tests
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Development apps
INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

# Debug toolbar middleware
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable caching in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Static files
COMPRESS_ENABLED = False