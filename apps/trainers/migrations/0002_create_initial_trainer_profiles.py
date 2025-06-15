from django.db import migrations
from django.conf import settings


def create_initial_trainer_profiles(apps, schema_editor):
    """
    Create trainer profiles for existing users.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])
    Organization = apps.get_model('trainers', 'Organization')
    Trainer = apps.get_model('trainers', 'Trainer')
    
    # Skip if no users exist
    if not User.objects.exists():
        return
    
    # Create default organization
    default_org = Organization.objects.create(
        name='The5HC 피트니스 센터',
        slug='the5hc-fitness-center',
        description='기본 피트니스 센터',
        timezone='Asia/Seoul',
        max_trainers=10
    )
    
    # Create trainer profiles for existing users
    for user in User.objects.all():
        Trainer.objects.create(
            user=user,
            organization=default_org,
            role='owner' if user.is_superuser else 'trainer',
            session_price=50000,
            is_active=True
        )


def reverse_initial_trainer_profiles(apps, schema_editor):
    """
    Remove trainer profiles and organization.
    """
    Organization = apps.get_model('trainers', 'Organization')
    Trainer = apps.get_model('trainers', 'Trainer')
    
    Trainer.objects.all().delete()
    Organization.objects.filter(slug='the5hc-fitness-center').delete()


class Migration(migrations.Migration):
    
    dependencies = [
        ('trainers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    
    operations = [
        migrations.RunPython(
            create_initial_trainer_profiles,
            reverse_initial_trainer_profiles
        ),
    ]