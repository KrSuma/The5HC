# Import appropriate settings based on environment
import os
from decouple import config

# Determine which settings to use
DEBUG = config('DEBUG', default=False, cast=bool)

if DEBUG:
    from .development import *
else:
    from .production import *