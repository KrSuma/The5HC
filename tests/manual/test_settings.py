#!/usr/bin/env python
"""Test Django settings loading"""
import os
import sys
from pathlib import Path

# Add the project to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings')

try:
    # Import settings
    from the5hc import settings
    print("Settings module loaded successfully")
    
    # Try to import base settings
    from the5hc.settings import base
    print("Base settings loaded")
    
    # Check database configuration
    if hasattr(base, 'DATABASES'):
        print(f"DATABASES configured: {base.DATABASES}")
    else:
        print("No DATABASES configuration found")
        
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()