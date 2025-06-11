# Import from base settings - for development use
try:
    from .settings.development import *
except ImportError:
    from .settings.base import *
