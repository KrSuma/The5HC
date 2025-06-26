"""
Comprehensive tests for PaymentService class.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from django.db.models import F

from apps.core.services.payment_service import PaymentService
from apps.trainers.factories import OrganizationFactory, TrainerFactory
from apps.clients.factories import ClientFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory, PaymentFactory
from apps.accounts.factories import UserFactory
from apps.sessions.models import SessionPackage, Session, Payment, FeeAuditLog


@pytest.mark.django_db
class TestPaymentService:
    """Test cases for PaymentService functionality."""
    
    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return OrganizationFactory()
    
    @pytest.fixture
    def trainer_user(self, organization):
        """Create user with trainer profile."""
        user = UserFactory()
        TrainerFactory(user=user, organization=organization)
        return user
    
    @pytest.fixture
    def other_org_trainer(self):
        """Create trainer from different organization."""
        other_org = OrganizationFactory()
        user = UserFactory()
        TrainerFactory(user=user, organization=other_org)
        return user
    
    @pytest.fixture
    def client(self, trainer_user):
        """Create test client."""
        return ClientFactory(
            trainer=trainer_user,
            name='테스트 고객',
            gender='M',
            age=30
        )
    
    @pytest.fixture
    def other_org_client(self, other_org_trainer):
        """Create client from different organization."""
        return ClientFactory(trainer=other_org_trainer)
    
    @pytest.fixture
    def service(self, trainer_user):
        """Create PaymentService instance."""
        return PaymentService(user=trainer_user)
    
    @pytest.fixture
    def sample_package(self, client, trainer_user):
        """Create sample session package."""
        return SessionPackageFactory(
            client=client,
            trainer=trainer_user,
            package_name='10회 패키지',
            total_sessions=10,
            remaining_sessions=10,
            total_amount=Decimal('1000000'),
            is_active=True
        )
    
    def test_calculate_fees_standard_case(self, service):
        """Test fee calculation with standard amounts."""
        gross_amount = Decimal('1135000')  # 1,135,000 KRW
        
        fees = service.calculate_fees(gross_amount)
        
        # Check all components
        assert fees['gross_amount'] == gross_amount
        assert fees['vat_rate'] == Decimal('0.10')
        assert fees['card_fee_rate'] == Decimal('0.035')
        
        # Base amount should be 1,000,000
        assert fees['base_amount'] == Decimal('1000000.00')
        
        # VAT should be 100,000 (10% of base)
        assert fees['vat_amount'] == Decimal('100000.00')
        
        # Card fee should be 35,000 (3.5% of base)
        assert fees['card_fee'] == Decimal('35000.00')
        
        # Net amount equals base amount
        assert fees['net_amount'] == fees['base_amount']
        
        # Verify calculation
        assert fees['calculated_gross'] == gross_amount
    
    @pytest.mark.parametrize("gross_amount,expected_base", [
        (Decimal('113500'), Decimal('100000.00')),      # 100,000 base
        (Decimal('567500'), Decimal('500000.00')),      # 500,000 base
        (Decimal('2270000'), Decimal('2000000.00')),    # 2,000,000 base
        (Decimal('11350'), Decimal('10000.00')),        # 10,000 base
        (Decimal('1'), Decimal('0.88')),                # Edge case: 1 won
    ])
    def test_calculate_fees_various_amounts(self, service, gross_amount, expected_base):
        """Test fee calculation with various amounts."""
        fees = service.calculate_fees(gross_amount)
        
        assert fees['base_amount'] == expected_base
        
        # Verify reverse calculation
        calculated_total = fees['base_amount'] + fees['vat_amount'] + fees['card_fee']
        assert abs(calculated_total - gross_amount) < Decimal('0.01')
    
    def test_create_session_package_success(self, service, client):
        """Test successful session package creation."""
        package_data = {
            'client_id': client.pk,
            'package_name': '20회 패키지',
            'total_sessions': 20,
            'total_amount': Decimal('2270000'),  # 2,000,000 base + fees
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=90)
        }
        
        package, success = service.create_session_package(package_data)
        
        assert success is True
        assert package is not None
        assert package.client == client
        assert package.package_name == '20회 패키지'
        assert package.total_sessions == 20
        assert package.remaining_sessions == 20
        assert package.is_active is True
        
        # Check fee calculations
        assert package.total_amount == Decimal('2270000')
        assert package.net_amount == Decimal('2000000.00')
        assert package.vat_amount == Decimal('200000.00')
        assert package.card_fee == Decimal('70000.00')
    
    def test_create_session_package_missing_fields(self, service):
        """Test package creation with missing required fields."""
        incomplete_data = {
            'package_name': 'Test Package',
            'total_sessions': 10
            # Missing client_id and total_amount
        }
        
        package, success = service.create_session_package(incomplete_data)
        
        assert success is False
        assert package is None
        assert service.has_errors
        assert any('client_id' in error for error in service.errors)
        assert any('total_amount' in error for error in service.errors)
    
    def test_create_session_package_invalid_client(self, service):
        """Test package creation with non-existent client."""
        package_data = {
            'client_id': 99999,  # Non-existent
            'package_name': 'Test Package',
            'total_sessions': 10,
            'total_amount': Decimal('1000000')
        }
        
        package, success = service.create_session_package(package_data)
        
        assert success is False
        assert package is None
        assert service.has_errors
        assert "고객을 찾을 수 없습니다." in service.errors
    
    def test_create_session_package_different_org_client(self, service, other_org_client):
        """Test package creation for client from different organization."""
        package_data = {
            'client_id': other_org_client.pk,
            'package_name': 'Test Package',
            'total_sessions': 10,
            'total_amount': Decimal('1000000')
        }
        
        package, success = service.create_session_package(package_data)
        
        assert success is False
        assert package is None
        assert "고객을 찾을 수 없습니다." in service.errors
    
    @patch('apps.core.services.payment_service.FeeAuditLog.objects.create')
    def test_log_fee_audit_success(self, mock_create, service, sample_package):
        """Test fee audit logging."""
        fee_breakdown = {
            'gross_amount': Decimal('1135000'),
            'vat_amount': Decimal('100000'),
            'vat_rate': Decimal('0.10'),
            'card_fee': Decimal('35000'),
            'card_fee_rate': Decimal('0.035'),
            'net_amount': Decimal('1000000')
        }
        
        service._log_fee_audit(sample_package, fee_breakdown)
        
        mock_create.assert_called_once_with(
            session_package=sample_package,
            gross_amount=fee_breakdown['gross_amount'],
            vat_amount=fee_breakdown['vat_amount'],
            vat_rate=fee_breakdown['vat_rate'],
            card_fee=fee_breakdown['card_fee'],
            card_fee_rate=fee_breakdown['card_fee_rate'],
            net_amount=fee_breakdown['net_amount'],
            created_by=service.user
        )
    
    @patch('apps.core.services.payment_service.logger')
    @patch('apps.core.services.payment_service.FeeAuditLog.objects.create')
    def test_log_fee_audit_failure(self, mock_create, mock_logger, service, sample_package):
        """Test fee audit logging handles failures gracefully."""
        mock_create.side_effect = Exception("Database error")
        fee_breakdown = {'gross_amount': Decimal('1000000')}
        
        # Should not raise exception
        service._log_fee_audit(sample_package, fee_breakdown)
        
        mock_logger.error.assert_called_once()
    
    def test_record_payment_success(self, service, sample_package):
        """Test successful payment recording."""
        payment, success = service.record_payment(
            package=sample_package,
            amount=Decimal('500000'),
            payment_method='card',
            notes='첫 번째 결제'
        )
        
        assert success is True
        assert payment is not None
        assert payment.amount == Decimal('500000')
        assert payment.payment_method == 'card'
        assert payment.notes == '첫 번째 결제'
        assert payment.session_package == sample_package
        assert payment.trainer == service.user
    
    def test_record_payment_no_permission(self, service, other_org_trainer):
        """Test payment recording without permission."""
        # Create package from different organization
        other_package = SessionPackageFactory(trainer=other_org_trainer)
        
        payment, success = service.record_payment(
            package=other_package,
            amount=Decimal('100000')
        )
        
        assert success is False
        assert payment is None
        assert "권한이 없습니다" in service.get_errors_string()
    
    def test_record_payment_invalid_amount(self, service, sample_package):
        """Test payment recording with invalid amount."""
        # Zero amount
        payment, success = service.record_payment(
            package=sample_package,
            amount=Decimal('0')
        )
        
        assert success is False
        assert "결제 금액은 0보다 커야 합니다." in service.errors
        
        # Negative amount
        payment, success = service.record_payment(
            package=sample_package,
            amount=Decimal('-100000')
        )
        
        assert success is False
    
    def test_record_payment_exceeds_balance(self, service, sample_package):
        """Test payment that exceeds remaining balance."""
        # First payment
        service.record_payment(sample_package, Decimal('800000'))
        
        # Try to pay more than remaining (200,000 left)
        payment, success = service.record_payment(
            package=sample_package,
            amount=Decimal('300000')
        )
        
        assert success is False
        assert payment is None
        assert "잔액" in service.get_errors_string()
    
    def test_record_payment_marks_package_paid(self, service, sample_package):
        """Test package is marked as paid when fully paid."""
        # Pay full amount
        payment, success = service.record_payment(
            package=sample_package,
            amount=sample_package.total_amount
        )
        
        assert success is True
        sample_package.refresh_from_db()
        assert sample_package.is_paid is True
    
    def test_use_session_success(self, service, sample_package):
        """Test successful session usage."""
        initial_remaining = sample_package.remaining_sessions
        
        session, success = service.use_session(
            package=sample_package,
            session_date=timezone.now().date(),
            notes='첫 번째 세션'
        )
        
        assert success is True
        assert session is not None
        assert session.client == sample_package.client
        assert session.session_package == sample_package
        assert session.session_type == 'PT'
        assert session.status == 'completed'
        assert session.notes == '첫 번째 세션'
        
        # Check remaining sessions decreased
        sample_package.refresh_from_db()
        assert sample_package.remaining_sessions == initial_remaining - 1
    
    def test_use_session_no_permission(self, service, other_org_trainer):
        """Test using session without permission."""
        other_package = SessionPackageFactory(trainer=other_org_trainer)
        
        session, success = service.use_session(other_package)
        
        assert success is False
        assert session is None
        assert "권한이 없습니다" in service.errors
    
    def test_use_session_inactive_package(self, service, sample_package):
        """Test using session from inactive package."""
        sample_package.is_active = False
        sample_package.save()
        
        session, success = service.use_session(sample_package)
        
        assert success is False
        assert "비활성 패키지입니다." in service.errors
    
    def test_use_session_no_remaining(self, service, sample_package):
        """Test using session when none remaining."""
        sample_package.remaining_sessions = 0
        sample_package.save()
        
        session, success = service.use_session(sample_package)
        
        assert success is False
        assert "남은 세션이 없습니다." in service.errors
    
    def test_use_session_expired_package(self, service, sample_package):
        """Test using session from expired package."""
        sample_package.end_date = timezone.now().date() - timedelta(days=1)
        sample_package.save()
        
        session, success = service.use_session(sample_package)
        
        assert success is False
        assert "만료된 패키지입니다." in service.errors
    
    def test_use_session_deactivates_when_empty(self, service, sample_package):
        """Test package is deactivated when last session is used."""
        sample_package.remaining_sessions = 1
        sample_package.save()
        
        session, success = service.use_session(sample_package)
        
        assert success is True
        sample_package.refresh_from_db()
        assert sample_package.remaining_sessions == 0
        assert sample_package.is_active is False
    
    def test_cancel_session_success(self, service, sample_package):
        """Test successful session cancellation."""
        # First create a session
        session, _ = service.use_session(sample_package)
        initial_remaining = sample_package.remaining_sessions
        
        # Cancel it
        success = service.cancel_session(session, reason="고객 요청")
        
        assert success is True
        session.refresh_from_db()
        assert session.status == 'cancelled'
        assert "고객 요청" in session.notes
        
        # Check session restored to package
        sample_package.refresh_from_db()
        assert sample_package.remaining_sessions == initial_remaining + 1
        assert sample_package.is_active is True
    
    def test_cancel_session_no_permission(self, service, other_org_trainer):
        """Test cancelling session without permission."""
        other_session = SessionFactory(trainer=other_org_trainer)
        
        success = service.cancel_session(other_session)
        
        assert success is False
        assert "권한이 없습니다" in service.errors
    
    def test_cancel_session_already_cancelled(self, service, sample_package):
        """Test cancelling already cancelled session."""
        session = SessionFactory(
            client=sample_package.client,
            session_package=sample_package,
            status='cancelled'
        )
        
        success = service.cancel_session(session)
        
        assert success is False
        assert "이미 취소된 세션입니다." in service.errors
    
    def test_get_package_statistics(self, service, sample_package):
        """Test package statistics calculation."""
        # Use some sessions
        for _ in range(3):
            service.use_session(sample_package)
        
        # Cancel one session
        session = sample_package.sessions.first()
        service.cancel_session(session)
        
        # Record payment
        service.record_payment(sample_package, Decimal('500000'))
        
        stats = service.get_package_statistics(sample_package)
        
        assert stats['total_sessions'] == 10
        assert stats['used_sessions'] == 2  # 3 used, 1 cancelled
        assert stats['remaining_sessions'] == 8
        assert stats['usage_rate'] == 20.0
        assert stats['total_paid'] == Decimal('500000')
        assert stats['remaining_balance'] == Decimal('500000')
        assert stats['payment_completion_rate'] == 50.0
        assert stats['completed_count'] == 2
        assert stats['cancelled_count'] == 1
    
    def test_get_package_statistics_with_expiry(self, service, sample_package):
        """Test package statistics with expiry date."""
        # Set expiry date
        sample_package.end_date = timezone.now().date() + timedelta(days=30)
        sample_package.save()
        
        stats = service.get_package_statistics(sample_package)
        
        assert stats['days_until_expiry'] == 30
        assert stats['is_expired'] is False
        
        # Test expired package
        sample_package.end_date = timezone.now().date() - timedelta(days=5)
        sample_package.save()
        
        stats = service.get_package_statistics(sample_package)
        
        assert stats['days_until_expiry'] == -5
        assert stats['is_expired'] is True
    
    def test_get_financial_summary(self, service, client):
        """Test financial summary calculation."""
        # Create packages and payments
        package1 = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('1135000'),
            net_amount=Decimal('1000000'),
            vat_amount=Decimal('100000'),
            card_fee=Decimal('35000'),
            total_sessions=10
        )
        
        package2 = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('2270000'),
            net_amount=Decimal('2000000'),
            vat_amount=Decimal('200000'),
            card_fee=Decimal('70000'),
            total_sessions=20
        )
        
        # Record payments
        PaymentFactory(session_package=package1, amount=Decimal('1135000'))
        PaymentFactory(session_package=package2, amount=Decimal('1000000'))
        
        # Use some sessions
        SessionFactory(
            client=client,
            trainer=service.user,
            session_package=package1,
            status='completed'
        )
        
        summary = service.get_financial_summary()
        
        assert summary['total_packages'] == 2
        assert summary['total_gross_revenue'] == Decimal('3405000')
        assert summary['total_net_revenue'] == Decimal('3000000')
        assert summary['total_vat'] == Decimal('300000')
        assert summary['total_card_fees'] == Decimal('105000')
        assert summary['total_sessions_sold'] == 30
        assert summary['total_collected'] == Decimal('2135000')
        assert summary['collection_rate'] == pytest.approx(62.7, rel=0.1)
        assert summary['active_packages'] == 2
        assert summary['total_sessions_conducted'] == 1
    
    def test_get_financial_summary_date_range(self, service, client):
        """Test financial summary with date range."""
        # Create old package (outside range)
        old_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('1000000')
        )
        old_package.created_at = timezone.now() - timedelta(days=60)
        old_package.save()
        
        # Create recent package (in range)
        recent_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('2000000')
        )
        
        # Get summary for last 30 days
        start_date = (timezone.now() - timedelta(days=30)).date()
        summary = service.get_financial_summary(start_date=start_date)
        
        assert summary['total_packages'] == 1
        assert summary['total_gross_revenue'] == Decimal('2000000')
    
    def test_get_expiring_packages(self, service, client):
        """Test getting expiring packages."""
        # Create packages with different expiry dates
        expiring_soon = SessionPackageFactory(
            client=client,
            trainer=service.user,
            end_date=timezone.now().date() + timedelta(days=15),
            is_active=True
        )
        
        expiring_later = SessionPackageFactory(
            client=client,
            trainer=service.user,
            end_date=timezone.now().date() + timedelta(days=45),
            is_active=True
        )
        
        already_expired = SessionPackageFactory(
            client=client,
            trainer=service.user,
            end_date=timezone.now().date() - timedelta(days=5),
            is_active=True
        )
        
        # Get packages expiring in next 30 days
        expiring = service.get_expiring_packages(days_ahead=30)
        
        assert expiring_soon in expiring
        assert expiring_later not in expiring
        assert already_expired not in expiring
    
    def test_get_payment_due_packages(self, service, client):
        """Test getting packages with outstanding payments."""
        # Fully paid package
        paid_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('1000000'),
            is_active=True
        )
        PaymentFactory(session_package=paid_package, amount=Decimal('1000000'))
        
        # Partially paid package
        partial_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('2000000'),
            is_active=True
        )
        PaymentFactory(session_package=partial_package, amount=Decimal('1000000'))
        
        # Unpaid package
        unpaid_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('3000000'),
            is_active=True
        )
        
        due_packages = service.get_payment_due_packages()
        
        # Check results
        assert paid_package not in due_packages
        assert partial_package in due_packages
        assert unpaid_package in due_packages
        
        # Check annotated payment_due amounts
        for package in due_packages:
            if package == partial_package:
                assert package.payment_due == Decimal('1000000')
            elif package == unpaid_package:
                assert package.payment_due == Decimal('3000000')
    
    def test_edge_cases(self, service, sample_package, client):
        """Test various edge cases."""
        # Cancel session without package
        orphan_session = SessionFactory(client=client, session_package=None)
        success = service.cancel_session(orphan_session)
        assert success is True  # Should still work
        
        # Package statistics with no data
        empty_package = SessionPackageFactory(
            client=client,
            trainer=service.user,
            total_amount=Decimal('1000000')
        )
        stats = service.get_package_statistics(empty_package)
        assert stats['used_sessions'] == 0
        assert stats['usage_rate'] == 0
        assert stats['total_paid'] == Decimal('0')
        
        # Financial summary with no data
        empty_service = PaymentService(user=service.user)
        with patch.object(empty_service, 'get_queryset') as mock_queryset:
            mock_queryset.return_value = SessionPackage.objects.none()
            summary = empty_service.get_financial_summary()
            assert summary['total_packages'] == 0
            assert summary['collection_rate'] == 0
        
        # Zero amount fee calculation
        fees = service.calculate_fees(Decimal('0'))
        assert fees['base_amount'] == Decimal('0.00')
        assert fees['vat_amount'] == Decimal('0.00')
        assert fees['card_fee'] == Decimal('0.00')