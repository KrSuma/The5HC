"""
Factory classes for the sessions app models.
Following django-test.md guidelines for pytest testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta

from apps.sessions.models import SessionPackage, Session, Payment, FeeAuditLog
from apps.clients.factories import ClientFactory
from apps.accounts.factories import UserFactory

fake = Faker('ko_KR')


class SessionPackageFactory(DjangoModelFactory):
    """Factory for creating SessionPackage instances"""
    
    class Meta:
        model = SessionPackage
    
    # Relationships
    client = factory.SubFactory(ClientFactory)
    trainer = factory.SubFactory(UserFactory)
    
    # Package details
    package_name = factory.LazyFunction(lambda: random.choice([
        'PT 10회 패키지', 'PT 20회 패키지', 'PT 30회 패키지',
        '그룹 PT 15회', '다이어트 특별 패키지', '재활 운동 패키지'
    ]))
    
    total_amount = factory.LazyFunction(lambda: Decimal(str(random.randint(300, 2000) * 1000)))  # 300k-2M KRW
    session_price = factory.LazyAttribute(lambda obj: obj.total_amount / obj.total_sessions)
    total_sessions = factory.LazyFunction(lambda: random.choice([10, 15, 20, 25, 30]))
    remaining_sessions = factory.LazyAttribute(lambda obj: random.randint(0, obj.total_sessions))
    remaining_credits = factory.LazyAttribute(lambda obj: obj.remaining_sessions * obj.session_price)
    
    # Status
    is_active = True
    notes = factory.LazyFunction(lambda: fake.sentence())
    
    # Fee rates (Korean standard)
    vat_rate = Decimal('0.10')  # 10% VAT
    card_fee_rate = Decimal('0.035')  # 3.5% card processing fee
    fee_calculation_method = 'inclusive'
    
    # Fee amounts will be calculated automatically by the model


class SmallPackageFactory(SessionPackageFactory):
    """Factory for small session packages (5-10 sessions)"""
    
    package_name = factory.LazyFunction(lambda: random.choice([
        'PT 체험 5회', 'PT 입문 10회', '단기 집중 8회'
    ]))
    total_sessions = factory.LazyFunction(lambda: random.randint(5, 10))
    total_amount = factory.LazyFunction(lambda: Decimal(str(random.randint(200, 800) * 1000)))


class LargePackageFactory(SessionPackageFactory):
    """Factory for large session packages (40+ sessions)"""
    
    package_name = factory.LazyFunction(lambda: random.choice([
        'PT 장기 50회', 'VIP 패키지 60회', '연간 특별 패키지'
    ]))
    total_sessions = factory.LazyFunction(lambda: random.randint(40, 60))
    total_amount = factory.LazyFunction(lambda: Decimal(str(random.randint(2500, 5000) * 1000)))


class ExpiredPackageFactory(SessionPackageFactory):
    """Factory for expired/used packages"""
    
    remaining_sessions = 0
    remaining_credits = Decimal('0.00')
    is_active = False


class NewPackageFactory(SessionPackageFactory):
    """Factory for new, unused packages"""
    
    remaining_sessions = factory.SelfAttribute('total_sessions')
    remaining_credits = factory.SelfAttribute('total_amount')


class SessionFactory(DjangoModelFactory):
    """Factory for creating Session instances"""
    
    class Meta:
        model = Session
    
    # Relationships
    client = factory.SubFactory(ClientFactory)
    package = factory.SubFactory(SessionPackageFactory)
    trainer = factory.LazyAttribute(lambda obj: obj.package.trainer)
    
    # Session details
    session_date = factory.LazyFunction(lambda: fake.date_this_month())
    session_time = factory.LazyFunction(lambda: fake.time())
    session_duration = factory.LazyFunction(lambda: random.choice([60, 90, 120]))  # minutes
    session_cost = factory.LazyAttribute(lambda obj: obj.package.session_price)
    
    # Status
    status = 'completed'
    notes = factory.LazyFunction(lambda: fake.sentence())


class ScheduledSessionFactory(SessionFactory):
    """Factory for scheduled (future) sessions"""
    
    session_date = factory.LazyFunction(lambda: fake.date_between(start_date='today', end_date='+30d'))
    status = 'scheduled'
    completed_at = None


class CompletedSessionFactory(SessionFactory):
    """Factory for completed sessions"""
    
    session_date = factory.LazyFunction(lambda: fake.date_between(start_date='-30d', end_date='today'))
    status = 'completed'
    completed_at = factory.LazyFunction(lambda: fake.date_time_this_month(tzinfo=timezone.get_current_timezone()))


class CancelledSessionFactory(SessionFactory):
    """Factory for cancelled sessions"""
    
    status = 'cancelled'
    notes = factory.LazyFunction(lambda: f'취소 사유: {fake.sentence()}')
    completed_at = None


class PaymentFactory(DjangoModelFactory):
    """Factory for creating Payment instances"""
    
    class Meta:
        model = Payment
    
    # Relationships
    client = factory.SubFactory(ClientFactory)
    package = factory.SubFactory(SessionPackageFactory)
    trainer = factory.LazyAttribute(lambda obj: obj.package.trainer)
    
    # Payment details
    amount = factory.LazyAttribute(lambda obj: obj.package.total_amount)
    payment_method = factory.LazyFunction(lambda: random.choice(['card', 'cash', 'transfer']))
    description = factory.LazyFunction(lambda: fake.sentence())
    payment_date = factory.LazyFunction(lambda: fake.date_this_month())
    
    # Fee rates
    vat_rate = Decimal('0.10')
    card_fee_rate = Decimal('0.035')


class CashPaymentFactory(PaymentFactory):
    """Factory for cash payments"""
    
    payment_method = 'cash'
    description = '현금 결제'


class CardPaymentFactory(PaymentFactory):
    """Factory for card payments"""
    
    payment_method = 'card'
    description = '카드 결제'


class TransferPaymentFactory(PaymentFactory):
    """Factory for bank transfer payments"""
    
    payment_method = 'transfer'
    description = '계좌이체'


class FeeAuditLogFactory(DjangoModelFactory):
    """Factory for creating FeeAuditLog instances"""
    
    class Meta:
        model = FeeAuditLog
    
    # Relationships
    package = factory.SubFactory(SessionPackageFactory)
    created_by = factory.LazyAttribute(lambda obj: obj.package.trainer)
    
    # Calculation details
    calculation_type = 'inclusive'
    gross_amount = factory.LazyAttribute(lambda obj: int(obj.package.total_amount))
    vat_rate = Decimal('0.10')
    card_fee_rate = Decimal('0.035')
    
    # Calculate fee amounts
    vat_amount = factory.LazyAttribute(lambda obj: int(obj.gross_amount * 0.087))  # Approximate
    card_fee_amount = factory.LazyAttribute(lambda obj: int(obj.gross_amount * 0.030))  # Approximate
    net_amount = factory.LazyAttribute(lambda obj: obj.gross_amount - obj.vat_amount - obj.card_fee_amount)
    
    calculation_details = factory.LazyAttribute(lambda obj: {
        'original_amount': float(obj.package.total_amount),
        'method': 'inclusive',
        'total_fee_rate': 0.135
    })


# Trait-based factories
class SessionPackageWithTraitsFactory(SessionPackageFactory):
    """
    Factory with traits for different package types.
    Usage:
    - SessionPackageWithTraitsFactory()  # Regular package
    - SessionPackageWithTraitsFactory(small=True)  # Small package
    - SessionPackageWithTraitsFactory(expired=True)  # Expired package
    """
    
    class Params:
        small = factory.Trait(
            total_sessions=factory.LazyFunction(lambda: random.randint(5, 10)),
            total_amount=factory.LazyFunction(lambda: Decimal(str(random.randint(200, 800) * 1000)))
        )
        large = factory.Trait(
            total_sessions=factory.LazyFunction(lambda: random.randint(40, 60)),
            total_amount=factory.LazyFunction(lambda: Decimal(str(random.randint(2500, 5000) * 1000)))
        )
        expired = factory.Trait(
            remaining_sessions=0,
            remaining_credits=Decimal('0.00'),
            is_active=False
        )
        new = factory.Trait(
            remaining_sessions=factory.SelfAttribute('total_sessions'),
            remaining_credits=factory.SelfAttribute('total_amount')
        )
        premium = factory.Trait(
            package_name='VIP 프리미엄 패키지',
            total_amount=factory.LazyFunction(lambda: Decimal(str(random.randint(3000, 6000) * 1000))),
            total_sessions=factory.LazyFunction(lambda: random.randint(50, 100))
        )


class SessionWithTraitsFactory(SessionFactory):
    """
    Factory with traits for different session types.
    """
    
    class Params:
        scheduled = factory.Trait(
            session_date=factory.LazyFunction(lambda: fake.date_between(start_date='today', end_date='+30d')),
            status='scheduled',
            completed_at=None
        )
        completed = factory.Trait(
            session_date=factory.LazyFunction(lambda: fake.date_between(start_date='-30d', end_date='today')),
            status='completed',
            completed_at=factory.LazyFunction(lambda: fake.date_time_this_month(tzinfo=timezone.get_current_timezone()))
        )
        cancelled = factory.Trait(
            status='cancelled',
            notes=factory.LazyFunction(lambda: f'취소 사유: {fake.sentence()}'),
            completed_at=None
        )
        long = factory.Trait(
            session_duration=120
        )
        short = factory.Trait(
            session_duration=60
        )


# Helper functions
def create_package_with_sessions(client=None, trainer=None, total_sessions=10, completed_sessions=5):
    """
    Create a package with specified number of completed sessions.
    
    Usage:
        package = create_package_with_sessions(client=client, total_sessions=20, completed_sessions=10)
    """
    if not client:
        client = ClientFactory()
    if not trainer:
        trainer = UserFactory()
    
    package = SessionPackageFactory(
        client=client,
        trainer=trainer,
        total_sessions=total_sessions,
        remaining_sessions=total_sessions - completed_sessions
    )
    
    # Create completed sessions
    sessions = []
    for i in range(completed_sessions):
        session = CompletedSessionFactory(
            client=client,
            package=package,
            trainer=trainer,
            session_date=fake.date_between(start_date='-60d', end_date='today')
        )
        sessions.append(session)
    
    return package, sessions


def create_client_payment_history(client=None, trainer=None, num_payments=3):
    """
    Create a payment history for a client.
    
    Usage:
        payments = create_client_payment_history(client=client, num_payments=5)
    """
    if not client:
        client = ClientFactory()
    if not trainer:
        trainer = UserFactory()
    
    payments = []
    for i in range(num_payments):
        package = SessionPackageFactory(client=client, trainer=trainer)
        payment = PaymentFactory(
            client=client,
            package=package,
            trainer=trainer,
            payment_date=fake.date_between(start_date='-365d', end_date='today')
        )
        payments.append(payment)
    
    return payments


def create_monthly_session_schedule(client=None, trainer=None, sessions_per_week=2, weeks=4):
    """
    Create a monthly session schedule.
    
    Usage:
        sessions = create_monthly_session_schedule(client=client, sessions_per_week=3, weeks=4)
    """
    if not client:
        client = ClientFactory()
    if not trainer:
        trainer = UserFactory()
    
    package = SessionPackageFactory(
        client=client,
        trainer=trainer,
        total_sessions=sessions_per_week * weeks
    )
    
    sessions = []
    start_date = date.today()
    
    for week in range(weeks):
        for session_num in range(sessions_per_week):
            session_date = start_date + timedelta(weeks=week, days=session_num * 2)  # Every other day
            session = ScheduledSessionFactory(
                client=client,
                package=package,
                trainer=trainer,
                session_date=session_date
            )
            sessions.append(session)
    
    return package, sessions