#!/usr/bin/env python
"""
Test script to verify form refactoring deployment.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.assessments.views import AssessmentForm
from apps.assessments.forms.refactored_forms import AssessmentWithTestsForm

print("=" * 80)
print("Form Refactoring Deployment Test")
print("=" * 80)

# Check if the import worked correctly
print(f"\n1. Import Check:")
print(f"   AssessmentForm type: {type(AssessmentForm)}")
print(f"   Is refactored form? {AssessmentForm == AssessmentWithTestsForm}")

# Check form structure
print(f"\n2. Form Structure:")
if hasattr(AssessmentForm, 'sub_forms'):
    print(f"   ✅ Refactored form has sub_forms attribute")
    print(f"   Sub-forms: {list(AssessmentForm.sub_forms.keys())}")
else:
    print(f"   ❌ Not using refactored form structure")

# Check form fields
print(f"\n3. Form Fields:")
form_instance = AssessmentForm()
if hasattr(form_instance, 'forms'):
    print(f"   ✅ Form instance has 'forms' attribute (composite form)")
    for name, form in form_instance.forms.items():
        print(f"      - {name}: {form.__class__.__name__}")
else:
    print(f"   ❌ Form instance doesn't have 'forms' attribute")
    if hasattr(form_instance, 'fields'):
        print(f"   Available fields: {list(form_instance.fields.keys())[:5]}...")
    else:
        print(f"   No 'fields' attribute")

# Check key methods
print(f"\n4. Key Methods:")
methods_to_check = ['save', 'is_valid', 'clean']
for method in methods_to_check:
    if hasattr(form_instance, method):
        print(f"   ✅ Has {method} method")
    else:
        print(f"   ❌ Missing {method} method")

# Summary
print(f"\n{'=' * 80}")
if AssessmentForm == AssessmentWithTestsForm:
    print("✅ SUCCESS: Form refactoring has been deployed!")
    print("   The application is now using the modular form structure.")
else:
    print("❌ FAILED: Form refactoring is not active.")
    print("   Still using the original monolithic form.")
print("=" * 80)