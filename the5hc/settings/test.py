"""
Test-specific Django settings for The5HC project.
These settings optimize for fast test execution and isolated testing.
"""
from .base import *

# Database configuration for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database for speed
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Disable migrations for faster test execution
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable static file compression and processing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
COMPRESS_ENABLED = False

# Security settings for testing
SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Disable CSRF for easier testing
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Logging configuration for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',  # Only show errors during tests
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Timezone for consistent testing
USE_TZ = True
TIME_ZONE = 'Asia/Seoul'

# Test-specific media settings
MEDIA_ROOT = '/tmp/the5hc_test_media'
MEDIA_URL = '/test_media/'

# Disable external services during testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# WeasyPrint settings for testing
WEASYPRINT_BASEURL = 'file://'

# English locale for testing (avoid Korean locale issues in test environment)
LANGUAGE_CODE = 'en-us'
USE_I18N = False
USE_L10N = False

# Test-specific installed apps (if needed)
INSTALLED_APPS = INSTALLED_APPS + [
    # Add test-specific apps here if needed
]

# Disable unnecessary middleware for testing
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.accounts.middleware.AuthenticationMiddleware',
]

# Test runner configuration
TEST_RUNNER = 'django.test.runner.DiscoverRunner'