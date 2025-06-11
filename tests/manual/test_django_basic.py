"""
Basic Django test to verify django-pytest integration.
"""
import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_user_creation():
    """Test creating a user with Django User model"""
    User = get_user_model()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    assert user.username == 'testuser'
    assert user.email == 'test@example.com'
    assert user.check_password('testpass123')


@pytest.mark.django_db
class TestDjangoBasic:
    """Test Django basic functionality"""
    
    def test_user_model_str(self):
        """Test user model string representation"""
        User = get_user_model()
        
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )
        
        # Test string representation (depends on custom model implementation)
        assert str(user) is not None
        assert len(str(user)) > 0