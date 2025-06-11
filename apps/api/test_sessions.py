"""
Tests for Session-related API endpoints (Packages, Sessions, Payments)
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.factories import UserFactory
from apps.clients.factories import ClientFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory, PaymentFactory
from apps.sessions.models import SessionPackage, Session, Payment


@pytest.mark.django_db
class TestSessionPackageAPI:
    """Test SessionPackage API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create test clients
        self.client1 = ClientFactory(trainer=self.user)
        self.client2 = ClientFactory(trainer=self.user)
        
        # Create test packages
        self.package1 = SessionPackageFactory(
            client=self.client1,
            trainer=self.user,
            is_active=True
        )
        self.package2 = SessionPackageFactory(
            client=self.client2,
            trainer=self.user,
            is_active=False
        )
        self.other_package = SessionPackageFactory(trainer=self.other_user)
    
    def test_list_packages_success(self):
        """Test listing packages for authenticated user"""
        response = self.client.get('/api/v1/packages/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        package_ids = [p['id'] for p in response.data['results']]
        assert self.package1.id in package_ids
        assert self.package2.id in package_ids
        assert self.other_package.id not in package_ids
    
    def test_filter_packages_by_active_status(self):
        """Test filtering packages by active status"""
        # Filter active packages
        response = self.client.get('/api/v1/packages/', {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == self.package1.id
        
        # Filter inactive packages
        response = self.client.get('/api/v1/packages/', {'is_active': 'false'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == self.package2.id
    
    def test_create_package_success(self):
        """Test creating a new package"""
        data = {
            'client': self.client1.id,
            'package_type': '10회',
            'total_sessions': 10,
            'remaining_sessions': 10,
            'price_per_session': 50000,
            'total_price': 500000,
            'is_active': True,
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=60)).isoformat(),
            'notes': '신규 패키지'
        }
        
        response = self.client.post('/api/v1/packages/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['client'] == self.client1.id
        assert response.data['trainer'] == self.user.id
        assert response.data['total_sessions'] == 10
        assert response.data['remaining_sessions'] == 10
    
    def test_package_sessions_endpoint(self):
        """Test getting sessions for a package"""
        # Create sessions
        session1 = SessionFactory(package=self.package1)
        session2 = SessionFactory(package=self.package1)
        other_session = SessionFactory(package=self.package2)
        
        response = self.client.get(f'/api/v1/packages/{self.package1.id}/sessions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        session_ids = [s['id'] for s in response.data]
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert other_session.id not in session_ids
    
    def test_package_payments_endpoint(self):
        """Test getting payments for a package"""
        # Create payments
        payment1 = PaymentFactory(package=self.package1, trainer=self.user, client=self.client1)
        payment2 = PaymentFactory(package=self.package1, trainer=self.user, client=self.client1)
        other_payment = PaymentFactory(package=self.package2, trainer=self.user, client=self.client2)
        
        response = self.client.get(f'/api/v1/packages/{self.package1.id}/payments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        payment_ids = [p['id'] for p in response.data]
        assert payment1.id in payment_ids
        assert payment2.id in payment_ids
        assert other_payment.id not in payment_ids
    
    def test_complete_session_endpoint(self):
        """Test completing a session from package"""
        # Create package with remaining sessions
        package = SessionPackageFactory(
            client=self.client1,
            trainer=self.user,
            total_sessions=10,
            remaining_sessions=5
        )
        
        data = {
            'date': date.today().isoformat(),
            'time': '10:00',
            'duration': 60,
            'cost': 50000,
            'notes': '세션 완료'
        }
        
        response = self.client.post(f'/api/v1/packages/{package.id}/complete_session/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['package'] == package.id
        assert response.data['status'] == 'completed'
        
        # Verify remaining sessions decreased
        package.refresh_from_db()
        assert package.remaining_sessions == 4
    
    def test_complete_session_no_remaining(self):
        """Test completing session when no sessions remaining"""
        # Create package with no remaining sessions
        package = SessionPackageFactory(
            client=self.client1,
            trainer=self.user,
            total_sessions=10,
            remaining_sessions=0
        )
        
        data = {
            'date': date.today().isoformat(),
            'time': '10:00'
        }
        
        response = self.client.post(f'/api/v1/packages/{package.id}/complete_session/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert '남은 세션이 없습니다' in response.data['error']


@pytest.mark.django_db
class TestSessionAPI:
    """Test Session API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create test data
        self.client1 = ClientFactory(trainer=self.user)
        self.package1 = SessionPackageFactory(client=self.client1, trainer=self.user)
        self.package2 = SessionPackageFactory(client=self.client1, trainer=self.user)
        
        # Create test sessions
        self.session1 = SessionFactory(package=self.package1)
        self.session2 = SessionFactory(package=self.package2)
    
    def test_list_sessions_success(self):
        """Test listing sessions"""
        response = self.client.get('/api/v1/sessions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_filter_sessions_by_date_range(self):
        """Test filtering sessions by date range"""
        # Create sessions with different dates
        old_session = SessionFactory(
            package=self.package1,
            session_date=date.today() - timedelta(days=30)
        )
        recent_session = SessionFactory(
            package=self.package1,
            session_date=date.today()
        )
        
        # Filter by date range
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()
        
        response = self.client.get('/api/v1/sessions/', {
            'start_date': start_date,
            'end_date': end_date
        })
        
        assert response.status_code == status.HTTP_200_OK
        session_ids = [s['id'] for s in response.data['results']]
        assert recent_session.id in session_ids
        assert old_session.id not in session_ids
    
    def test_filter_sessions_by_attendance(self):
        """Test filtering sessions by attendance status"""
        # Update session attendance
        self.session1.attendance_status = 'present'
        self.session1.save()
        self.session2.attendance_status = 'absent'
        self.session2.save()
        
        response = self.client.get('/api/v1/sessions/', {'attendance': 'present'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == self.session1.id
    
    def test_session_calendar_endpoint(self):
        """Test calendar view of sessions"""
        # Create sessions for specific month
        today = date.today()
        session1 = SessionFactory(
            package=self.package1,
            session_date=today,
            session_time=datetime.strptime('10:00', '%H:%M').time()
        )
        session2 = SessionFactory(
            package=self.package1,
            session_date=today,
            session_time=datetime.strptime('14:00', '%H:%M').time()
        )
        
        response = self.client.get('/api/v1/sessions/calendar/', {
            'month': today.month,
            'year': today.year
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert today.isoformat() in response.data
        assert len(response.data[today.isoformat()]) >= 2
        
        # Check session data
        sessions = response.data[today.isoformat()]
        times = [s['time'] for s in sessions]
        assert '10:00' in times
        assert '14:00' in times


@pytest.mark.django_db
class TestPaymentAPI:
    """Test Payment API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = UserFactory()
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create test data
        self.client1 = ClientFactory(trainer=self.user)
        self.client2 = ClientFactory(trainer=self.user)
        self.package1 = SessionPackageFactory(client=self.client1, trainer=self.user)
        
        # Create test payments
        self.payment1 = PaymentFactory(
            client=self.client1,
            trainer=self.user,
            package=self.package1,
            payment_method='card'
        )
        self.payment2 = PaymentFactory(
            client=self.client2,
            trainer=self.user,
            payment_method='cash'
        )
    
    def test_list_payments_success(self):
        """Test listing payments"""
        response = self.client.get('/api/v1/payments/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_filter_payments_by_method(self):
        """Test filtering payments by payment method"""
        response = self.client.get('/api/v1/payments/', {'method': 'card'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['payment_method'] == 'card'
    
    def test_create_payment_success(self):
        """Test creating a new payment"""
        data = {
            'client': self.client1.id,
            'package': self.package1.id,
            'amount': 500000,
            'payment_date': date.today().isoformat(),
            'payment_method': 'transfer',
            'description': '10회 패키지 결제',
            'vat_amount': 45455,
            'card_fee_amount': 15909,
            'net_amount': 438636
        }
        
        response = self.client.post('/api/v1/payments/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['trainer'] == self.user.id
        assert response.data['amount'] == '500000.00'
        assert response.data['payment_method'] == 'transfer'
    
    def test_payment_summary_endpoint(self):
        """Test payment summary statistics"""
        # Create additional payments
        PaymentFactory(
            client=self.client1,
            trainer=self.user,
            amount=Decimal('100000'),
            payment_date=date.today()
        )
        PaymentFactory(
            client=self.client1,
            trainer=self.user,
            amount=Decimal('200000'),
            payment_date=date.today() - timedelta(days=30)
        )
        
        response = self.client.get('/api/v1/payments/summary/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_amount' in response.data
        assert 'total_payments' in response.data
        assert 'average_payment' in response.data
        assert 'by_method' in response.data
    
    def test_payment_summary_with_date_filter(self):
        """Test payment summary with date range filter"""
        # Filter for current month
        start_date = date.today().replace(day=1).isoformat()
        end_date = date.today().isoformat()
        
        response = self.client.get('/api/v1/payments/summary/', {
            'start_date': start_date,
            'end_date': end_date
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_amount' in response.data
        
        # Should only include payments from current month
        total_payments = Payment.objects.filter(
            trainer=self.user,
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).count()
        assert response.data['total_payments'] == total_payments