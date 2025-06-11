#!/usr/bin/env python
import os
import sys

# First, let's check what's in the settings module
print("Checking Django settings...")

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the settings module
from the5hc.settings import development

print(f"DATABASES in development settings: {development.DATABASES}")

# Now let's set up Django with development settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'the5hc.settings.development'

import django
django.setup()

from django.conf import settings
print(f"Django settings DATABASES: {settings.DATABASES}")