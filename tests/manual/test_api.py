#!/usr/bin/env python
"""
Quick test script for The5HC API
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User

def test_api_endpoints():
    """Test basic API functionality"""
    print("Testing The5HC API Endpoints...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='api_test_user',
        defaults={
            'email': 'api_test@example.com',
            'first_name': 'API',
            'last_name': 'Test'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("✅ Created test user")
    
    # Create API client
    client = APIClient()
    
    # Test authentication
    print("\n1. Testing Authentication...")
    response = client.post('/api/v1/auth/login/', {
        'email_or_username': 'api_test_user',
        'password': 'testpass123'
    })
    
    if response.status_code == 200:
        print("✅ Login successful")
        tokens = response.json()
        access_token = tokens['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    else:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    # Test endpoints
    endpoints = [
        ('/api/v1/users/me/', 'GET', 'User Profile'),
        ('/api/v1/clients/', 'GET', 'Client List'),
        ('/api/v1/assessments/', 'GET', 'Assessment List'),
        ('/api/v1/packages/', 'GET', 'Package List'),
        ('/api/v1/sessions/', 'GET', 'Session List'),
        ('/api/v1/payments/', 'GET', 'Payment List'),
        ('/api/v1/users/dashboard_stats/', 'GET', 'Dashboard Stats'),
    ]
    
    print("\n2. Testing API Endpoints...")
    for url, method, name in endpoints:
        if method == 'GET':
            response = client.get(url)
        elif method == 'POST':
            response = client.post(url, {})
        
        status_icon = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status_icon} {name}: {response.status_code}")
    
    # Test API documentation
    print("\n3. Testing API Documentation...")
    doc_endpoints = [
        ('/api/v1/schema/', 'OpenAPI Schema'),
        ('/api/v1/docs/', 'Swagger UI'),
        ('/api/v1/redoc/', 'ReDoc'),
    ]
    
    for url, name in doc_endpoints:
        response = client.get(url)
        status_icon = "✅" if response.status_code in [200, 301, 302] else "❌"
        print(f"{status_icon} {name}: {response.status_code}")
    
    print("\n✨ API testing complete!")

if __name__ == '__main__':
    test_api_endpoints()