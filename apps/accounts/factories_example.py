"""
Example factory_boy implementation for User model.
This demonstrates how to create factories following the guidelines.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from faker import Faker

User = get_user_model()
fake = Faker('ko_KR')  # Korean locale for realistic Korean names


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)  # Prevent duplicates in tests
    
    # Sequential unique username
    username = factory.Sequence(lambda n: f'trainer{n:04d}')
    
    # Email based on username
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    
    # Korean names using Faker
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    
    # Optional fields
    phone = factory.LazyFunction(lambda: fake.phone_number())
    organization = factory.LazyFunction(lambda: fake.company())
    
    # Default active status
    is_active = True
    is_staff = False
    is_superuser = False
    
    # Activity tracking fields
    login_attempts = 0
    is_locked = False
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """
        Handle password setting after user creation.
        Can be used as:
        - UserFactory()  # Uses default password 'testpass123'
        - UserFactory(password='custom')  # Uses custom password
        - UserFactory(password=None)  # No password set
        """
        if not create:
            return
            
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')
    
    @factory.post_generation
    def groups(obj, create, extracted, **kwargs):
        """
        Handle group assignment after creation.
        Usage: UserFactory(groups=['trainers', 'premium'])
        """
        if not create or not extracted:
            return
            
        if extracted:
            for group_name in extracted:
                from django.contrib.auth.models import Group
                group, _ = Group.objects.get_or_create(name=group_name)
                obj.groups.add(group)
    
    @factory.post_generation
    def permissions(obj, create, extracted, **kwargs):
        """
        Handle permission assignment after creation.
        Usage: UserFactory(permissions=['can_view_reports', 'can_edit_clients'])
        """
        if not create or not extracted:
            return
            
        if extracted:
            from django.contrib.auth.models import Permission
            for perm_codename in extracted:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    obj.user_permissions.add(permission)
                except Permission.DoesNotExist:
                    pass


class AdminUserFactory(UserFactory):
    """Factory for creating admin/superuser instances"""
    
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f'admin{n:04d}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@admin.com')


class LockedUserFactory(UserFactory):
    """Factory for creating locked user accounts (for testing lockout)"""
    
    is_locked = True
    login_attempts = 5
    last_login_attempt = factory.LazyFunction(fake.date_time_this_month)


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive user accounts"""
    
    is_active = False


# Trait-based approach (alternative pattern)
class UserWithTraitsFactory(UserFactory):
    """
    Factory with traits for different user types.
    Usage:
    - UserWithTraitsFactory()  # Regular user
    - UserWithTraitsFactory(admin=True)  # Admin user
    - UserWithTraitsFactory(locked=True)  # Locked user
    """
    
    class Params:
        admin = factory.Trait(
            is_staff=True,
            is_superuser=True,
            username=factory.Sequence(lambda n: f'admin{n:04d}')
        )
        locked = factory.Trait(
            is_locked=True,
            login_attempts=5
        )
        inactive = factory.Trait(
            is_active=False
        )


# Example batch creation helper
def create_test_users(count=5, **kwargs):
    """
    Helper function to create multiple test users.
    
    Usage:
        users = create_test_users(5)  # 5 regular users
        admins = create_test_users(3, is_staff=True)  # 3 staff users
    """
    return UserFactory.create_batch(count, **kwargs)


# Example usage in tests:
"""
# Basic usage
user = UserFactory()
assert user.username == 'trainer0001'
assert user.check_password('testpass123')

# Custom password
user = UserFactory(password='custom123')
assert user.check_password('custom123')

# Admin user
admin = AdminUserFactory()
assert admin.is_superuser

# Multiple users
users = UserFactory.create_batch(10)
assert len(users) == 10

# User with specific attributes
trainer = UserFactory(
    username='special_trainer',
    email='special@example.com',
    first_name='특별한',
    last_name='트레이너'
)

# Using traits
admin = UserWithTraitsFactory(admin=True)
locked_user = UserWithTraitsFactory(locked=True)
"""