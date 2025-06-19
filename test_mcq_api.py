#!/usr/bin/env python
"""
Quick test script for MCQ API endpoints.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
sys.path.insert(0, os.path.abspath('.'))
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Create a test client
client = APIClient()

# Get user model
User = get_user_model()

# Try to get a test user
try:
    user = User.objects.get(username='test_trainer')
    print(f"✓ Found test user: {user.username}")
except User.DoesNotExist:
    print("✗ Test user 'test_trainer' not found")
    sys.exit(1)

# Generate JWT token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

# Set authentication header
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

# Test MCQ endpoints
print("\n=== Testing MCQ API Endpoints ===\n")

# 1. Test Categories endpoint
print("1. Testing /api/v1/mcq/categories/")
response = client.get('/api/v1/mcq/categories/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   Categories found: {len(data)}")
    if isinstance(data, list) and data:
        for cat in data:
            if isinstance(cat, dict):
                print(f"   - {cat.get('name_ko', cat.get('name'))}")
            else:
                print(f"   - {cat}")
else:
    print(f"   Error: {response.content}")

# 2. Test Questions endpoint
print("\n2. Testing /api/v1/mcq/questions/")
response = client.get('/api/v1/mcq/questions/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   Total questions: {data.get('count', len(data))}")
else:
    print(f"   Error: {response.content}")

# 3. Test Question search
print("\n3. Testing /api/v1/mcq/questions/?search=운동")
response = client.get('/api/v1/mcq/questions/', {'search': '운동'})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    results = data.get('results', data) if isinstance(data, dict) else data
    print(f"   Questions matching '운동': {len(results)}")
else:
    print(f"   Error: {response.content}")

# 4. Test Analytics endpoints
print("\n4. Testing /api/v1/mcq/analytics/category-scores/")
response = client.get('/api/v1/mcq/analytics/category-scores/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   Category scores retrieved: {len(response.json())}")
else:
    print(f"   Error: {response.content}")

print("\n=== MCQ API Test Complete ===")