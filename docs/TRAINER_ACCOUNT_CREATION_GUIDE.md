# Trainer Account Creation Guide

This guide explains the various methods to create trainer accounts in The5HC system.

## Current System Structure

### Organizations
The system currently has two organizations:
1. **The5HC 피트니스 센터** (slug: `the5hc-fitness-center`)
   - Max trainers: 50
   - Current trainers: 10
2. **테스트 피트니스** (slug: empty string)
   - Max trainers: 50
   - Current trainers: 1

### Trainer Roles
- **Owner** (`owner`): Full administrative access, can manage other trainers
- **Senior** (`senior`): Can manage trainers and view organization metrics
- **Trainer** (`trainer`): Basic trainer access

## Method 1: Django Management Command (Recommended)

A custom management command has been created for easy trainer creation:

```bash
# Basic usage
python manage.py create_trainer <username> <email>

# With all options
python manage.py create_trainer johndoe john@example.com \
  --password="securepass123" \
  --first-name="John" \
  --last-name="Doe" \
  --organization="the5hc-fitness-center" \
  --role="trainer" \
  --session-price=60000 \
  --is-staff

# Create an owner account
python manage.py create_trainer owner_user owner@the5hc.com \
  --role="owner" \
  --first-name="Owner" \
  --last-name="User"

# Create a senior trainer
python manage.py create_trainer senior_trainer senior@the5hc.com \
  --role="senior" \
  --first-name="Senior" \
  --last-name="Trainer"
```

### Command Options:
- `username`: Required. The login username
- `email`: Required. Must be unique
- `--password`: Default is "testpass123"
- `--first-name`: Trainer's first name
- `--last-name`: Trainer's last name
- `--organization`: Organization slug (default: "the5hc-fitness-center")
- `--role`: One of "owner", "senior", "trainer" (default: "trainer")
- `--session-price`: Price per session in KRW (default: 50000)
- `--is-staff`: Give Django admin access
- `--is-superuser`: Give full Django superuser permissions

## Method 2: Django Admin Interface

1. Access Django admin at `/admin/`
2. Login with a superuser account
3. Navigate to "Accounts > Users" and create a new user
4. Then navigate to "Trainers > Trainers" and create a trainer profile for that user

## Method 3: Django Shell

```python
# Access Django shell
python manage.py shell

# Import necessary models
from django.contrib.auth import get_user_model
from apps.trainers.models import Organization, Trainer

User = get_user_model()

# Get organization
org = Organization.objects.get(slug='the5hc-fitness-center')

# Create user
user = User.objects.create_user(
    username='new_trainer',
    email='new_trainer@example.com',
    password='securepassword123',
    first_name='New',
    last_name='Trainer'
)

# Create trainer profile
trainer = Trainer.objects.create(
    user=user,
    organization=org,
    role='trainer',
    session_price=50000,
    is_active=True
)

print(f"Created trainer: {trainer.get_display_name()}")
```

## Method 4: Through Invitation System (In-App)

1. Login as an owner or senior trainer
2. Navigate to "트레이너 관리" (Trainer Management)
3. Click "트레이너 초대" (Invite Trainer)
4. Fill out the invitation form with:
   - Email address
   - First and last name (optional)
   - Role
   - Personal message (optional)
5. The invited trainer will receive an invitation (Note: Email functionality not yet implemented)

## Method 5: Data Migration Script

For bulk creation or migration from another system:

```python
# Create a script in scripts/ directory
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'the5hc.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.trainers.models import Organization, Trainer

User = get_user_model()

# List of trainers to create
trainers_data = [
    {
        'username': 'trainer1',
        'email': 'trainer1@example.com',
        'password': 'pass123',
        'first_name': 'Trainer',
        'last_name': 'One',
        'role': 'trainer',
    },
    # Add more trainers...
]

org = Organization.objects.get(slug='the5hc-fitness-center')

for data in trainers_data:
    user = User.objects.create_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    
    Trainer.objects.create(
        user=user,
        organization=org,
        role=data['role'],
        session_price=50000,
        is_active=True
    )
    
    print(f"Created: {data['username']}")
```

## Existing Test Accounts

The system currently has these test accounts:
- `krsuma` - Owner of The5HC 피트니스 센터
- `test_trainer` - Test trainer with owner role (created in Session 5)
- `api_test_user` - API testing account
- Various other test accounts

## Important Notes

1. **Email Uniqueness**: Each trainer must have a unique email address
2. **Username Uniqueness**: Usernames must be unique across the system
3. **Organization Limits**: Check that the organization hasn't reached its trainer limit
4. **Password Security**: Use strong passwords in production
5. **Role Permissions**:
   - Owners can manage all aspects of the organization
   - Senior trainers can manage other trainers
   - Regular trainers can only manage their own clients

## Troubleshooting

### "Organization has reached maximum trainers"
- Check current trainer count with the management command
- Update organization's `max_trainers` field in Django admin or database

### "User already exists"
- The username or email is already taken
- Use a different username/email or check existing users

### Permission Issues
- Ensure the user creating trainers has appropriate permissions
- Superusers can always create trainers through admin/shell

## Production Deployment

When creating trainers in production (Heroku):

```bash
# SSH into Heroku
heroku run bash

# Run the management command
python manage.py create_trainer <username> <email> [options]

# Or use Django shell
python manage.py shell
```

Remember to use secure passwords and proper email addresses in production environments.