"""
Simple model tests for accounts app that don't rely on views/templates.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.factories import UserFactory, AdminUserFactory, InactiveUserFactory, LockedUserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModelBasic:
    """Test User model basic functionality"""
    
    def test_create_user_with_factory(self):
        """Test creating a user with UserFactory"""
        user = UserFactory(
            username='testuser1',
            email='testuser1@example.com',
            name='Test User'
        )
        
        assert user.username == 'testuser1'
        assert user.email == 'testuser1@example.com'
        assert user.name == 'Test User'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_create_admin_user(self):
        """Test creating an admin user"""
        admin = AdminUserFactory(
            username='admin1',
            email='admin1@example.com'
        )
        
        assert admin.username == 'admin1'
        assert admin.email == 'admin1@example.com'
        assert admin.is_staff is True
        assert admin.is_superuser is True
    
    def test_password_hashing(self):
        """Test password is properly hashed"""
        user = UserFactory(password='mypassword123')
        
        # Password should be hashed, not plain text
        assert user.password != 'mypassword123'
        # In test settings, we use MD5 for speed
        assert user.password.startswith('md5$') or user.password.startswith('pbkdf2_sha256$') or user.password.startswith('bcrypt$')
        assert user.check_password('mypassword123')
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = UserFactory(username='johndoe', name='John Doe')
        
        assert str(user) == 'johndoe - John Doe'
        
        # Test without name
        user_no_name = UserFactory(username='janedoe', name='')
        assert str(user_no_name) == 'janedoe - '
    
    def test_failed_login_attempts(self):
        """Test failed login attempt tracking"""
        user = UserFactory()
        
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        
        # Increment failed attempts
        user.increment_failed_login_attempts()
        assert user.failed_login_attempts == 1
        
        # Reset attempts
        user.reset_failed_login_attempts()
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
    
    def test_account_lockout(self):
        """Test account lockout after max attempts"""
        user = UserFactory()
        
        # Simulate 5 failed attempts
        for i in range(5):
            user.increment_failed_login_attempts()
        
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.is_account_locked() is True
    
    def test_inactive_user_factory(self):
        """Test creating inactive users"""
        user = InactiveUserFactory()
        
        assert user.is_active is False
        assert user.email.endswith('@example.com')
    
    def test_locked_user_factory(self):
        """Test creating locked users"""
        user = LockedUserFactory()
        
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.is_account_locked() is True


@pytest.mark.django_db
class TestUserQuerySet:
    """Test custom user queryset methods"""
    
    def test_user_creation_saves_to_db(self):
        """Test that users are saved to database"""
        user = UserFactory(username='dbtest')
        
        # Verify user exists in database
        assert User.objects.filter(username='dbtest').exists()
        
        # Verify we can retrieve the user
        db_user = User.objects.get(username='dbtest')
        assert db_user.id == user.id
        assert db_user.username == 'dbtest'
    
    def test_multiple_users_creation(self):
        """Test creating multiple users"""
        users = [
            UserFactory(username=f'user{i}')
            for i in range(5)
        ]
        
        assert User.objects.count() >= 5
        
        for i, user in enumerate(users):
            assert user.username == f'user{i}'


@pytest.mark.django_db
@pytest.mark.parametrize('factory_class,expected_attrs', [
    (UserFactory, {'is_active': True, 'is_staff': False, 'is_superuser': False}),
    (AdminUserFactory, {'is_active': True, 'is_staff': True, 'is_superuser': True}),
    (InactiveUserFactory, {'is_active': False, 'is_staff': False, 'is_superuser': False}),
])
def test_user_factory_types(factory_class, expected_attrs):
    """Test different user factory types produce correct attributes"""
    user = factory_class()
    
    for attr, expected_value in expected_attrs.items():
        assert getattr(user, attr) == expected_value