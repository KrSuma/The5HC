"""
Simplified pytest test for accounts to verify setup.
"""
import pytest
from apps.accounts.factories import UserFactory


@pytest.mark.django_db
class TestAccountsSimple:
    """Simple test to verify pytest and factories are working"""
    
    def test_user_factory_creation(self):
        """Test that UserFactory creates users correctly"""
        user = UserFactory(
            username='testuser',
            email='test@example.com'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active is True
        
    def test_user_factory_with_password(self):
        """Test UserFactory password handling"""
        user = UserFactory(password='custompass123')
        
        assert user.check_password('custompass123')
        assert not user.check_password('wrongpass')
        
    def test_admin_user_factory(self):
        """Test AdminUserFactory creates superusers"""
        from apps.accounts.factories import AdminUserFactory
        
        admin = AdminUserFactory()
        
        assert admin.is_staff is True
        assert admin.is_superuser is True