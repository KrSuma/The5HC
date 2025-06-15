"""
Factory Boy factories for the trainers app models.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from faker import Faker

from .models import Organization, Trainer, TrainerInvitation, AuditLog, Notification

User = get_user_model()
fake = Faker('ko_KR')


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n:04d}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    name = factory.LazyAttribute(lambda obj: f'{obj.first_name} {obj.last_name}')
    is_active = True
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')


class OrganizationFactory(DjangoModelFactory):
    """Factory for creating Organization instances."""
    
    class Meta:
        model = Organization
        django_get_or_create = ('slug',)
    
    name = factory.Sequence(lambda n: f'{fake.company()} {n}')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    address = factory.LazyFunction(lambda: fake.address())
    phone = factory.LazyFunction(lambda: fake.phone_number())
    email = factory.LazyAttribute(lambda obj: f'contact@{obj.name.lower().replace(" ", "")}.com')
    max_trainers = 10
    timezone = 'Asia/Seoul'
    business_hours = factory.LazyFunction(lambda: {
        'monday': {'open': '09:00', 'close': '22:00'},
        'tuesday': {'open': '09:00', 'close': '22:00'},
        'wednesday': {'open': '09:00', 'close': '22:00'},
        'thursday': {'open': '09:00', 'close': '22:00'},
        'friday': {'open': '09:00', 'close': '22:00'},
        'saturday': {'open': '09:00', 'close': '18:00'},
        'sunday': {'open': '10:00', 'close': '18:00'}
    })


class TrainerFactory(DjangoModelFactory):
    """Factory for creating Trainer instances."""
    
    class Meta:
        model = Trainer
        django_get_or_create = ('user',)
    
    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = 'trainer'
    bio = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    certifications = factory.LazyFunction(lambda: [fake.word() for _ in range(3)])
    specialties = factory.LazyFunction(lambda: [fake.word() for _ in range(3)])
    years_of_experience = factory.LazyFunction(lambda: fake.random_int(min=1, max=20))
    is_active = True
    session_price = 50000
    availability_schedule = factory.LazyFunction(lambda: {
        'monday': [{'start': '09:00', 'end': '18:00'}],
        'tuesday': [{'start': '09:00', 'end': '18:00'}],
        'wednesday': [{'start': '09:00', 'end': '18:00'}],
        'thursday': [{'start': '09:00', 'end': '18:00'}],
        'friday': [{'start': '09:00', 'end': '18:00'}],
    })


class OwnerTrainerFactory(TrainerFactory):
    """Factory for creating organization owner trainers."""
    role = 'owner'


class SeniorTrainerFactory(TrainerFactory):
    """Factory for creating senior trainers."""
    role = 'senior'


class AssistantTrainerFactory(TrainerFactory):
    """Factory for creating assistant trainers."""
    role = 'assistant'


class TrainerInvitationFactory(DjangoModelFactory):
    """Factory for creating TrainerInvitation instances."""
    
    class Meta:
        model = TrainerInvitation
        django_get_or_create = ('invitation_code',)
    
    organization = factory.SubFactory(OrganizationFactory)
    email = factory.LazyFunction(lambda: fake.email())
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    invited_by = factory.LazyAttribute(lambda obj: UserFactory())
    role = 'trainer'
    invitation_code = factory.LazyFunction(lambda: fake.uuid4())
    message = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    status = 'pending'
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))


class AuditLogFactory(DjangoModelFactory):
    """Factory for creating AuditLog instances."""
    
    class Meta:
        model = AuditLog
    
    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    action = factory.LazyFunction(lambda: fake.random_element(elements=[choice[0] for choice in AuditLog.ACTION_CHOICES]))
    ip_address = factory.LazyFunction(lambda: fake.ipv4())
    user_agent = factory.LazyFunction(lambda: fake.user_agent())
    extra_data = factory.LazyFunction(lambda: {'test': 'data'})


class NotificationFactory(DjangoModelFactory):
    """Factory for creating Notification instances."""
    
    class Meta:
        model = Notification
    
    user = factory.SubFactory(UserFactory)
    notification_type = factory.LazyFunction(lambda: fake.random_element(elements=[choice[0] for choice in Notification.NOTIFICATION_TYPES]))
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
    message = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    is_read = False


# Helper functions for creating test data
def create_organization_with_trainers(num_trainers=3, **org_kwargs):
    """Create an organization with multiple trainers."""
    org = OrganizationFactory(**org_kwargs)
    owner = OwnerTrainerFactory(organization=org)
    trainers = [owner]
    
    for _ in range(num_trainers - 1):
        trainers.append(TrainerFactory(organization=org))
    
    return org, trainers


def create_trainer_with_notifications(num_notifications=5, **trainer_kwargs):
    """Create a trainer with multiple notifications."""
    trainer = TrainerFactory(**trainer_kwargs)
    notifications = NotificationFactory.create_batch(
        num_notifications,
        user=trainer.user
    )
    return trainer, notifications