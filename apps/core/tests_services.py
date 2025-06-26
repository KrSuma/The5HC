"""
Tests for the service layer.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.services import ClientService, PaymentService
from apps.clients.models import Client
from apps.sessions.models import SessionPackage, Session, Payment
from apps.trainers.models import Organization, Trainer

User = get_user_model()


@pytest.mark.django_db
class TestClientService:
    """Test ClientService functionality."""
    
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(
            name="Test Organization",
            code="TEST"
        )
    
    @pytest.fixture
    def trainer_user(self, organization):
        user = User.objects.create_user(
            username='trainer',
            password='testpass123'
        )
        Trainer.objects.create(
            user=user,
            organization=organization
        )
        return user
    
    @pytest.fixture
    def client_service(self, trainer_user):
        return ClientService(user=trainer_user)
    
    @pytest.fixture
    def sample_client_data(self):
        return {
            'name': '김철수',
            'gender': 'M',
            'age': 30,
            'height': 175,
            'weight': 70,
            'email': 'test@example.com',
            'phone': '010-1234-5678'
        }
    
    def test_create_client_success(self, client_service, sample_client_data):
        """Test successful client creation."""
        client, success = client_service.create_client(sample_client_data)
        
        assert success is True
        assert client is not None
        assert client.name == '김철수'
        assert client.trainer == client_service.user
        assert not client_service.has_errors
    
    def test_create_client_missing_required_fields(self, client_service):
        """Test client creation with missing required fields."""
        incomplete_data = {'name': '김철수'}
        
        client, success = client_service.create_client(incomplete_data)
        
        assert success is False
        assert client is None
        assert client_service.has_errors
        assert any('필수 입력 항목' in error for error in client_service.errors)
    
    def test_get_annotated_queryset(self, client_service, sample_client_data):
        """Test annotated queryset includes calculated fields."""
        client, _ = client_service.create_client(sample_client_data)
        
        queryset = client_service.get_annotated_queryset()
        annotated_client = queryset.get(pk=client.pk)
        
        # Check BMI calculation
        expected_bmi = 70 / (1.75 * 1.75)  # weight / height^2
        assert abs(annotated_client.calculated_bmi - expected_bmi) < 0.1
    
    def test_search_and_filter(self, client_service, sample_client_data):
        """Test search and filter functionality."""
        # Create test clients
        client1_data = sample_client_data.copy()
        client1_data['name'] = '김철수'
        client1_data['age'] = 25
        
        client2_data = sample_client_data.copy()
        client2_data['name'] = '이영희'
        client2_data['age'] = 35
        client2_data['gender'] = 'F'
        
        client_service.create_client(client1_data)
        client_service.create_client(client2_data)
        
        # Test name search
        results = client_service.search_and_filter({'search': '김철수'})
        assert results.count() == 1
        assert results.first().name == '김철수'
        
        # Test gender filter
        results = client_service.search_and_filter({'gender': 'F'})
        assert results.count() == 1
        assert results.first().name == '이영희'
        
        # Test age range
        results = client_service.search_and_filter({'age_min': 30})
        assert results.count() == 1
        assert results.first().age >= 30
    
    def test_get_client_statistics(self, client_service, sample_client_data):
        """Test client statistics calculation."""
        client, _ = client_service.create_client(sample_client_data)
        
        stats = client_service.get_client_statistics(client)
        
        assert 'total_assessments' in stats
        assert 'total_sessions' in stats
        assert 'active_packages' in stats
        assert stats['total_assessments'] == 0  # No assessments yet
        assert stats['total_sessions'] == 0     # No sessions yet


@pytest.mark.django_db
class TestPaymentService:
    """Test PaymentService functionality."""
    
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(
            name="Test Organization",
            code="TEST"
        )
    
    @pytest.fixture
    def trainer_user(self, organization):
        user = User.objects.create_user(
            username='trainer',
            password='testpass123'
        )
        Trainer.objects.create(
            user=user,
            organization=organization
        )
        return user
    
    @pytest.fixture
    def client(self, trainer_user):
        return Client.objects.create(
            trainer=trainer_user,
            name='테스트 고객',
            gender='M',
            age=30,
            height=175,
            weight=70
        )
    
    @pytest.fixture
    def payment_service(self, trainer_user):
        return PaymentService(user=trainer_user)
    
    def test_calculate_fees(self, payment_service):
        """Test fee calculation logic."""
        gross_amount = Decimal('1135000')  # 1,135,000 KRW
        
        fees = payment_service.calculate_fees(gross_amount)
        
        # Check calculated values
        assert fees['gross_amount'] == gross_amount
        assert fees['vat_rate'] == Decimal('0.10')
        assert fees['card_fee_rate'] == Decimal('0.035')
        
        # Base amount should be 1,000,000
        expected_base = Decimal('1000000')
        assert abs(fees['base_amount'] - expected_base) < Decimal('0.01')
        
        # VAT should be 100,000 (10% of base)
        expected_vat = Decimal('100000')
        assert abs(fees['vat_amount'] - expected_vat) < Decimal('0.01')
        
        # Card fee should be 35,000 (3.5% of base)
        expected_card_fee = Decimal('35000')
        assert abs(fees['card_fee'] - expected_card_fee) < Decimal('0.01')
        
        # Net amount equals base amount
        assert fees['net_amount'] == fees['base_amount']
    
    def test_create_session_package(self, payment_service, client):
        """Test session package creation."""
        package_data = {
            'client_id': client.pk,
            'package_name': '10회 패키지',
            'total_sessions': 10,
            'total_amount': Decimal('1135000'),
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=90)
        }
        
        package, success = payment_service.create_session_package(package_data)
        
        assert success is True
        assert package is not None
        assert package.client == client
        assert package.package_name == '10회 패키지'
        assert package.total_sessions == 10
        assert package.remaining_sessions == 10
        assert package.is_active is True
        
        # Check fee calculations
        assert package.total_amount == Decimal('1135000')
        assert package.vat_amount > 0
        assert package.card_fee > 0
        assert package.net_amount > 0
    
    def test_create_session_package_missing_client(self, payment_service):
        """Test package creation with invalid client."""
        package_data = {
            'client_id': 9999,  # Non-existent client
            'package_name': '10회 패키지',
            'total_sessions': 10,
            'total_amount': Decimal('1000000')
        }
        
        package, success = payment_service.create_session_package(package_data)
        
        assert success is False
        assert package is None
        assert payment_service.has_errors
        assert '고객을 찾을 수 없습니다.' in payment_service.errors
    
    def test_record_payment(self, payment_service, client):
        """Test payment recording."""
        # Create a package first
        package_data = {
            'client_id': client.pk,
            'package_name': '10회 패키지',
            'total_sessions': 10,
            'total_amount': Decimal('1000000')
        }
        
        package, _ = payment_service.create_session_package(package_data)
        
        # Record payment
        payment, success = payment_service.record_payment(
            package=package,
            amount=Decimal('500000'),
            payment_method='card',
            notes='첫 번째 결제'
        )
        
        assert success is True
        assert payment is not None
        assert payment.amount == Decimal('500000')
        assert payment.payment_method == 'card'
        assert payment.session_package == package
    
    def test_record_payment_exceeds_balance(self, payment_service, client):
        """Test payment that exceeds remaining balance."""
        # Create small package
        package_data = {
            'client_id': client.pk,
            'package_name': '1회 패키지',
            'total_sessions': 1,
            'total_amount': Decimal('100000')
        }
        
        package, _ = payment_service.create_session_package(package_data)
        
        # Try to pay more than package amount
        payment, success = payment_service.record_payment(
            package=package,
            amount=Decimal('200000')  # More than package total
        )
        
        assert success is False
        assert payment is None
        assert payment_service.has_errors
        assert '잔액' in payment_service.get_errors_string()
    
    def test_use_session(self, payment_service, client):
        """Test using a session from package."""
        # Create package
        package_data = {
            'client_id': client.pk,
            'package_name': '5회 패키지',
            'total_sessions': 5,
            'total_amount': Decimal('500000')
        }
        
        package, _ = payment_service.create_session_package(package_data)
        original_remaining = package.remaining_sessions
        
        # Use a session
        session, success = payment_service.use_session(
            package=package,
            session_date=timezone.now().date(),
            notes='첫 번째 세션'
        )
        
        assert success is True
        assert session is not None
        assert session.client == client
        assert session.session_package == package
        
        # Check remaining sessions decreased
        package.refresh_from_db()
        assert package.remaining_sessions == original_remaining - 1
    
    def test_use_session_no_remaining(self, payment_service, client):
        """Test using session when none remaining."""
        # Create package with no remaining sessions
        package = SessionPackage.objects.create(
            client=client,
            trainer=payment_service.user,
            package_name='소진된 패키지',
            total_sessions=5,
            remaining_sessions=0,  # No sessions left
            total_amount=Decimal('500000'),
            net_amount=Decimal('450000'),
            is_active=True
        )
        
        session, success = payment_service.use_session(package)
        
        assert success is False
        assert session is None
        assert payment_service.has_errors
        assert '남은 세션이 없습니다.' in payment_service.errors
    
    def test_get_financial_summary(self, payment_service, client):
        """Test financial summary calculation."""
        # Create some packages and payments
        package_data = {
            'client_id': client.pk,
            'package_name': '10회 패키지',
            'total_sessions': 10,
            'total_amount': Decimal('1000000')
        }
        
        package, _ = payment_service.create_session_package(package_data)
        payment_service.record_payment(package, Decimal('500000'))
        
        # Get summary
        summary = payment_service.get_financial_summary()
        
        assert 'total_packages' in summary
        assert 'total_gross_revenue' in summary
        assert 'total_collected' in summary
        assert 'collection_rate' in summary
        assert summary['total_packages'] >= 1
        assert summary['total_gross_revenue'] >= Decimal('1000000')


class ServiceIntegrationTest(TestCase):
    """Integration tests for services working together."""
    
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Integration Test Org",
            code="INTEG"
        )
        
        self.user = User.objects.create_user(
            username='integration_user',
            password='testpass123'
        )
        
        TrainerProfile.objects.create(
            user=self.user,
            organization=self.organization
        )
    
    def test_client_and_payment_services_integration(self):
        """Test ClientService and PaymentService working together."""
        # Create client using ClientService
        client_service = ClientService(user=self.user)
        client_data = {
            'name': '통합테스트 고객',
            'gender': 'F',
            'age': 28,
            'height': 165,
            'weight': 55
        }
        
        client, success = client_service.create_client(client_data)
        self.assertTrue(success)
        
        # Create package using PaymentService
        payment_service = PaymentService(user=self.user)
        package_data = {
            'client_id': client.pk,
            'package_name': '통합테스트 패키지',
            'total_sessions': 8,
            'total_amount': Decimal('800000')
        }
        
        package, success = payment_service.create_session_package(package_data)
        self.assertTrue(success)
        
        # Use some sessions
        for i in range(3):
            session, success = payment_service.use_session(package)
            self.assertTrue(success)
        
        # Get updated client statistics
        stats = client_service.get_client_statistics(client)
        
        # Verify integration
        self.assertEqual(stats['total_sessions'], 3)
        self.assertEqual(stats['active_packages'], 1)
        self.assertGreater(stats['total_revenue'], 0)