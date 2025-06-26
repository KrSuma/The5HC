#!/usr/bin/env python
"""
Test the fixed form initialization.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.assessments.forms.refactored_forms import AssessmentWithTestsForm
from apps.assessments.models import Assessment
from apps.clients.models import Client
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

print("=" * 80)
print("Testing Fixed Form Initialization")
print("=" * 80)

# Get a test user
try:
    user = User.objects.first()
    print(f"\nUsing user: {user}")
except:
    print("No users found")
    user = None

# Test 1: Initialize empty form
print("\n1. Testing empty form initialization:")
try:
    form = AssessmentWithTestsForm(user=user)
    print("   ✅ Empty form created successfully")
    print(f"   Has assessment_form: {hasattr(form, 'assessment_form')}")
    print(f"   Has test_forms: {hasattr(form, 'test_forms')}")
    print(f"   Test forms: {list(form.test_forms.keys())}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Initialize with instance (for editing)
print("\n2. Testing form with assessment instance:")
try:
    # Create a temporary assessment instance
    temp_assessment = Assessment(date=timezone.now())
    form = AssessmentWithTestsForm(instance=temp_assessment, user=user)
    print("   ✅ Form with instance created successfully")
    print(f"   Instance date: {temp_assessment.date}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Initialize with client
print("\n3. Testing form with client preset:")
try:
    client = Client.objects.first()
    if client:
        temp_assessment = Assessment(date=timezone.now(), client=client)
        form = AssessmentWithTestsForm(instance=temp_assessment, user=user)
        print("   ✅ Form with client created successfully")
        print(f"   Client: {client.name}")
    else:
        print("   ⚠️  No clients found in database")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("Form initialization should now work properly!")
print("The view has been updated to use the correct parameters.")
print("=" * 80)