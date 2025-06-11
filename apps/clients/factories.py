"""
Factory classes for the clients app models.
Following django-test.md guidelines for pytest testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from decimal import Decimal
import random

from apps.clients.models import Client
from apps.accounts.factories import UserFactory

fake = Faker('ko_KR')  # Korean locale for realistic Korean data


class ClientFactory(DjangoModelFactory):
    """Factory for creating Client instances"""
    
    class Meta:
        model = Client
    
    # Relationships
    trainer = factory.SubFactory(UserFactory)
    
    # Personal information
    name = factory.LazyFunction(lambda: fake.name())
    age = factory.LazyFunction(lambda: random.randint(18, 70))
    gender = factory.LazyFunction(lambda: random.choice(['male', 'female']))
    
    # Physical measurements with realistic ranges
    height = factory.LazyFunction(lambda: round(random.uniform(150.0, 190.0), 1))
    weight = factory.LazyFunction(lambda: round(random.uniform(45.0, 100.0), 1))
    
    # Contact information
    email = factory.LazyAttribute(lambda obj: f'{obj.name.replace(" ", "").lower()}@example.com')
    phone = factory.LazyFunction(lambda: fake.phone_number())


class MaleClientFactory(ClientFactory):
    """Factory for creating male client instances"""
    
    gender = 'male'
    name = factory.LazyFunction(lambda: fake.name_male())
    height = factory.LazyFunction(lambda: round(random.uniform(165.0, 190.0), 1))
    weight = factory.LazyFunction(lambda: round(random.uniform(60.0, 100.0), 1))


class FemaleClientFactory(ClientFactory):
    """Factory for creating female client instances"""
    
    gender = 'female'
    name = factory.LazyFunction(lambda: fake.name_female())
    height = factory.LazyFunction(lambda: round(random.uniform(150.0, 175.0), 1))
    weight = factory.LazyFunction(lambda: round(random.uniform(45.0, 80.0), 1))


class YoungClientFactory(ClientFactory):
    """Factory for creating young client instances (18-30)"""
    
    age = factory.LazyFunction(lambda: random.randint(18, 30))


class MiddleAgedClientFactory(ClientFactory):
    """Factory for creating middle-aged client instances (31-50)"""
    
    age = factory.LazyFunction(lambda: random.randint(31, 50))


class SeniorClientFactory(ClientFactory):
    """Factory for creating senior client instances (51-70)"""
    
    age = factory.LazyFunction(lambda: random.randint(51, 70))


class ClientWithContactFactory(ClientFactory):
    """Factory for creating clients with guaranteed contact information"""
    
    email = factory.LazyAttribute(lambda obj: f'{obj.name.replace(" ", "").lower()}@gmail.com')
    phone = factory.LazyFunction(lambda: f'010-{random.randint(1000,9999)}-{random.randint(1000,9999)}')


class ClientWithoutContactFactory(ClientFactory):
    """Factory for creating clients without contact information"""
    
    email = None
    phone = None


# Trait-based approach
class ClientWithTraitsFactory(ClientFactory):
    """
    Factory with traits for different client types.
    Usage:
    - ClientWithTraitsFactory()  # Regular client
    - ClientWithTraitsFactory(male=True)  # Male client
    - ClientWithTraitsFactory(overweight=True)  # Overweight client
    - ClientWithTraitsFactory(underweight=True)  # Underweight client
    """
    
    class Params:
        male = factory.Trait(
            gender='male',
            name=factory.LazyFunction(lambda: fake.name_male()),
            height=factory.LazyFunction(lambda: round(random.uniform(165.0, 190.0), 1)),
            weight=factory.LazyFunction(lambda: round(random.uniform(60.0, 100.0), 1))
        )
        female = factory.Trait(
            gender='female',
            name=factory.LazyFunction(lambda: fake.name_female()),
            height=factory.LazyFunction(lambda: round(random.uniform(150.0, 175.0), 1)),
            weight=factory.LazyFunction(lambda: round(random.uniform(45.0, 80.0), 1))
        )
        young = factory.Trait(
            age=factory.LazyFunction(lambda: random.randint(18, 30))
        )
        senior = factory.Trait(
            age=factory.LazyFunction(lambda: random.randint(51, 70))
        )
        overweight = factory.Trait(
            # BMI > 25 (assuming average height)
            weight=factory.LazyFunction(lambda: round(random.uniform(85.0, 120.0), 1))
        )
        underweight = factory.Trait(
            # BMI < 18.5 (assuming average height)
            weight=factory.LazyFunction(lambda: round(random.uniform(35.0, 55.0), 1))
        )
        no_contact = factory.Trait(
            email=None,
            phone=None
        )


# Specialized factories for testing edge cases
class SmallClientFactory(ClientFactory):
    """Factory for creating very small clients (testing edge cases)"""
    
    height = factory.LazyFunction(lambda: round(random.uniform(140.0, 155.0), 1))
    weight = factory.LazyFunction(lambda: round(random.uniform(35.0, 50.0), 1))
    age = factory.LazyFunction(lambda: random.randint(18, 25))


class LargeClientFactory(ClientFactory):
    """Factory for creating very large clients (testing edge cases)"""
    
    height = factory.LazyFunction(lambda: round(random.uniform(185.0, 200.0), 1))
    weight = factory.LazyFunction(lambda: round(random.uniform(90.0, 130.0), 1))
    age = factory.LazyFunction(lambda: random.randint(25, 45))


# Helper functions
def create_test_clients(count=5, trainer=None, **kwargs):
    """
    Helper function to create multiple test clients.
    
    Usage:
        clients = create_test_clients(5)  # 5 clients with random trainers
        clients = create_test_clients(3, trainer=trainer)  # 3 clients for specific trainer
        male_clients = create_test_clients(5, gender='male')  # 5 male clients
    """
    if trainer:
        kwargs['trainer'] = trainer
    return ClientFactory.create_batch(count, **kwargs)


def create_diverse_client_group(trainer=None):
    """
    Create a diverse group of clients for comprehensive testing.
    Returns a dict with different client types.
    """
    if not trainer:
        trainer = UserFactory()
    
    return {
        'male_young': MaleClientFactory(trainer=trainer, age=25),
        'female_young': FemaleClientFactory(trainer=trainer, age=23),
        'male_middle': MaleClientFactory(trainer=trainer, age=40),
        'female_middle': FemaleClientFactory(trainer=trainer, age=38),
        'male_senior': MaleClientFactory(trainer=trainer, age=60),
        'female_senior': FemaleClientFactory(trainer=trainer, age=58),
        'overweight': ClientWithTraitsFactory(trainer=trainer, overweight=True),
        'underweight': ClientWithTraitsFactory(trainer=trainer, underweight=True),
        'no_contact': ClientWithTraitsFactory(trainer=trainer, no_contact=True),
    }


def create_clients_with_bmi_categories(trainer=None):
    """
    Create clients representing different BMI categories.
    Returns a dict with clients in each BMI category.
    """
    if not trainer:
        trainer = UserFactory()
    
    return {
        'underweight': ClientFactory(trainer=trainer, height=170.0, weight=50.0),  # BMI ~17.3
        'normal': ClientFactory(trainer=trainer, height=170.0, weight=65.0),       # BMI ~22.5
        'overweight': ClientFactory(trainer=trainer, height=170.0, weight=75.0),   # BMI ~26.0
        'obese': ClientFactory(trainer=trainer, height=170.0, weight=90.0),        # BMI ~31.1
        'severely_obese': ClientFactory(trainer=trainer, height=170.0, weight=110.0) # BMI ~38.1
    }