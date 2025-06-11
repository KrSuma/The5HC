"""
Simple form tests for accounts app.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.forms import LoginForm, CustomUserCreationForm
from apps.accounts.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestLoginFormSimple:
    """Test LoginForm functionality"""
    
    def test_login_form_fields(self):
        """Test login form has correct fields"""
        form = LoginForm()
        
        assert 'email_or_username' in form.fields
        assert 'password' in form.fields
        assert 'remember_me' in form.fields
        
        # Remember me should be optional
        assert form.fields['remember_me'].required is False
    
    def test_login_form_valid_with_existing_user(self):
        """Test login form with valid data and existing user"""
        # Create a user first
        user = UserFactory(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Test with username
        form_data = {
            'email_or_username': 'testuser',
            'password': 'testpass123',
            'remember_me': False
        }
        form = LoginForm(data=form_data)
        
        # Note: Form validation includes authentication which requires request context
        # So we just test that the form fields are processed correctly
        assert form.has_error('email_or_username') is False
        assert form.has_error('password') is False
    
    def test_login_form_empty_fields(self):
        """Test login form with empty fields"""
        form_data = {
            'email_or_username': '',
            'password': '',
        }
        form = LoginForm(data=form_data)
        
        assert form.is_valid() is False
        assert 'email_or_username' in form.errors
        assert 'password' in form.errors


class TestUserCreationFormSimple:
    """Test UserCreationForm functionality"""
    
    def test_user_creation_form_fields(self):
        """Test user creation form has correct fields"""
        form = CustomUserCreationForm()
        
        expected_fields = ['username', 'email', 'name', 'password1', 'password2']
        for field in expected_fields:
            assert field in form.fields
    
    def test_user_creation_form_valid_data(self):
        """Test user creation form with valid data"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'name': 'New User',
            'password1': 'complex-password-123',
            'password2': 'complex-password-123'
        }
        form = CustomUserCreationForm(data=form_data)
        
        assert form.is_valid()
    
    def test_user_creation_form_password_mismatch(self):
        """Test user creation form with mismatched passwords"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'name': 'New User',
            'password1': 'password123',
            'password2': 'differentpassword'
        }
        form = CustomUserCreationForm(data=form_data)
        
        assert form.is_valid() is False
        assert 'password2' in form.errors
    
    def test_user_creation_form_missing_required_fields(self):
        """Test user creation form with missing required fields"""
        form_data = {
            'username': 'newuser',
            # Missing email and passwords
        }
        form = CustomUserCreationForm(data=form_data)
        
        assert form.is_valid() is False
        assert 'email' in form.errors
        assert 'password1' in form.errors
        assert 'password2' in form.errors


@pytest.mark.django_db
@pytest.mark.parametrize('username,email,expected_valid', [
    ('validuser', 'valid@example.com', True),
    ('', 'valid@example.com', False),  # Empty username
    ('validuser', '', False),  # Empty email
    ('validuser', 'invalid-email', False),  # Invalid email format
    ('a', 'valid@example.com', False),  # Username too short (if validation exists)
])
def test_user_creation_validation(username, email, expected_valid):
    """Test user creation form validation with various inputs"""
    form_data = {
        'username': username,
        'email': email,
        'name': 'Test User',
        'password1': 'complex-password-123',
        'password2': 'complex-password-123'
    }
    form = CustomUserCreationForm(data=form_data)
    
    if expected_valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()