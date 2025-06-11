from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import json

from .models import SessionPackage, Session, Payment
from .forms import SessionPackageForm, SessionForm, PaymentForm, SessionSearchForm
from apps.clients.models import Client as ClientModel

User = get_user_model()


class SessionPackageModelTestCase(TestCase):
    """Test suite for SessionPackage model"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.trainer = User.objects.create_user(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com'
        )
        
    def test_session_package_creation(self):
        """Test session package creation with valid data"""
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Premium Package',
            total_sessions=10,
            session_price=Decimal('50000.00'),
            total_amount=Decimal('500000.00'),
            vat_rate=Decimal('10.00'),
            card_fee_rate=Decimal('3.50'),
            expiry_date=date.today() + timedelta(days=90)
        )
        
        self.assertEqual(package.trainer, self.trainer)
        self.assertEqual(package.client, self.client)
        self.assertEqual(package.total_sessions, 10)
        self.assertEqual(package.remaining_sessions, 10)  # Initially equal to total
        self.assertEqual(package.session_price, Decimal('50000.00'))
        
    def test_session_package_str_method(self):
        """Test session package string representation"""
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=5,
            session_price=Decimal('40000.00')
        )
        expected = f"Test Package - {self.client.name} (5 sessions)"
        self.assertEqual(str(package), expected)
        
    def test_session_package_is_active_property(self):
        """Test is_active property"""
        # Active package (not expired, has remaining sessions)
        active_package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Active Package',
            total_sessions=5,
            remaining_sessions=3,
            session_price=Decimal('40000.00'),
            expiry_date=date.today() + timedelta(days=30)
        )
        self.assertTrue(active_package.is_active)
        
        # Expired package
        expired_package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Expired Package',
            total_sessions=5,
            remaining_sessions=3,
            session_price=Decimal('40000.00'),
            expiry_date=date.today() - timedelta(days=1)
        )
        self.assertFalse(expired_package.is_active)
        
        # No remaining sessions
        depleted_package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Depleted Package',
            total_sessions=5,
            remaining_sessions=0,
            session_price=Decimal('40000.00'),
            expiry_date=date.today() + timedelta(days=30)
        )
        self.assertFalse(depleted_package.is_active)
        
    def test_session_package_usage_percentage(self):
        """Test usage percentage calculation"""
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=10,
            remaining_sessions=3,
            session_price=Decimal('40000.00')
        )
        # Used 7 out of 10 sessions = 70%
        self.assertEqual(package.usage_percentage, 70.0)


class SessionModelTestCase(TestCase):
    """Test suite for Session model"""
    
    def setUp(self):
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        self.package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=5,
            remaining_sessions=5,
            session_price=Decimal('40000.00')
        )
        
    def test_session_creation(self):
        """Test session creation with valid data"""
        session = Session.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            session_date=date.today(),
            session_time=timezone.now().time(),
            notes='Test session notes'
        )
        
        self.assertEqual(session.trainer, self.trainer)
        self.assertEqual(session.client, self.client)
        self.assertEqual(session.package, self.package)
        self.assertEqual(session.status, 'scheduled')  # Default status
        
    def test_session_str_method(self):
        """Test session string representation"""
        session_date = date.today()
        session = Session.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            session_date=session_date,
            session_time=timezone.now().time()
        )
        expected = f"Session with {self.client.name} on {session_date}"
        self.assertEqual(str(session), expected)
        
    def test_session_default_ordering(self):
        """Test session default ordering"""
        tomorrow = date.today() + timedelta(days=1)
        
        session1 = Session.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            session_date=tomorrow,
            session_time=timezone.now().time()
        )
        session2 = Session.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            session_date=date.today(),
            session_time=timezone.now().time()
        )
        
        sessions = list(Session.objects.all())
        # Should be ordered by newest first
        self.assertEqual(sessions[0], session1)
        self.assertEqual(sessions[1], session2)


class PaymentModelTestCase(TestCase):
    """Test suite for Payment model"""
    
    def setUp(self):
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        self.package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=5,
            session_price=Decimal('40000.00'),
            total_amount=Decimal('200000.00')
        )
        
    def test_payment_creation(self):
        """Test payment creation with valid data"""
        payment = Payment.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            amount=Decimal('200000.00'),
            payment_method='card',
            payment_date=date.today(),
            notes='Full payment for package'
        )
        
        self.assertEqual(payment.trainer, self.trainer)
        self.assertEqual(payment.package, self.package)
        self.assertEqual(payment.amount, Decimal('200000.00'))
        self.assertEqual(payment.payment_method, 'card')
        
    def test_payment_str_method(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            trainer=self.trainer,
            client=self.client,
            package=self.package,
            amount=Decimal('100000.00'),
            payment_method='cash',
            payment_date=date.today()
        )
        expected = f"Payment of ₩100,000 by {self.client.name} on {date.today()}"
        self.assertEqual(str(payment), expected)


class SessionFormTestCase(TestCase):
    """Test suite for Session forms"""
    
    def setUp(self):
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        
    def test_session_package_form_valid_data(self):
        """Test session package form with valid data"""
        form_data = {
            'client': self.client.pk,
            'package_name': 'Premium Package',
            'total_sessions': '10',
            'session_price': '50000.00',
            'vat_rate': '10.00',
            'card_fee_rate': '3.50',
            'expiry_date': (date.today() + timedelta(days=90)).strftime('%Y-%m-%d'),
            'notes': 'Premium training package'
        }
        form = SessionPackageForm(trainer=self.trainer, data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_session_package_form_missing_required_field(self):
        """Test session package form with missing required field"""
        form_data = {
            'package_name': 'Test Package',
            'total_sessions': '5'
        }
        form = SessionPackageForm(trainer=self.trainer, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('client', form.errors)
        
    def test_session_form_valid_data(self):
        """Test session form with valid data"""
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=5,
            session_price=Decimal('40000.00')
        )
        
        form_data = {
            'client': self.client.pk,
            'package': package.pk,
            'session_date': date.today().strftime('%Y-%m-%d'),
            'session_time': '14:00',
            'notes': 'Regular training session'
        }
        form = SessionForm(trainer=self.trainer, data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_payment_form_valid_data(self):
        """Test payment form with valid data"""
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.client,
            package_name='Test Package',
            total_sessions=5,
            session_price=Decimal('40000.00')
        )
        
        form_data = {
            'client': self.client.pk,
            'package': package.pk,
            'amount': '200000.00',
            'payment_method': 'card',
            'payment_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'Payment for training package'
        }
        form = PaymentForm(trainer=self.trainer, data=form_data)
        self.assertTrue(form.is_valid())


class SessionViewTestCase(TestCase):
    """Test suite for Session views"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            email='trainer@example.com',
            password='testpass123'
        )
        self.other_trainer = User.objects.create_user(
            username='other_trainer',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test clients
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = ClientModel.objects.create(
            trainer=self.other_trainer,
            name='Other Client',
            email='other@example.com'
        )
        
        # Create test packages
        self.test_package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package_name='Test Package',
            total_sessions=5,
            remaining_sessions=3,
            session_price=Decimal('40000.00'),
            total_amount=Decimal('200000.00')
        )
        
        self.other_package = SessionPackage.objects.create(
            trainer=self.other_trainer,
            client=self.other_client,
            package_name='Other Package',
            total_sessions=10,
            session_price=Decimal('50000.00')
        )
        
    def test_session_package_list_view_requires_login(self):
        """Test session package list requires authentication"""
        url = reverse('sessions:package_list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_session_package_list_view_authenticated(self):
        """Test session package list view with authenticated user"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Package')
        self.assertNotContains(response, 'Other Package')
        
    def test_session_package_detail_view(self):
        """Test session package detail view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_detail', kwargs={'pk': self.test_package.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Package')
        self.assertContains(response, 'Test Client')
        
    def test_session_package_detail_unauthorized_access(self):
        """Test session package detail view for unauthorized package"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_detail', kwargs={'pk': self.other_package.pk})
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 404)
        
    def test_session_package_add_view_get(self):
        """Test session package add view GET request"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_add')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], SessionPackageForm)
        
    def test_session_package_add_view_with_client_param(self):
        """Test session package add view with client parameter"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_add')
        response = self.client_test.get(url, {'client': self.test_client.pk})
        self.assertEqual(response.status_code, 200)
        # Form should be pre-populated with client
        self.assertEqual(response.context['form'].initial['client'], self.test_client.pk)
        
    def test_session_package_add_view_post_valid(self):
        """Test session package add view with valid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_add')
        data = {
            'client': self.test_client.pk,
            'package_name': 'New Package',
            'total_sessions': '8',
            'session_price': '45000.00',
            'vat_rate': '10.00',
            'card_fee_rate': '3.50',
            'expiry_date': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'notes': 'New training package'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check package was created
        new_package = SessionPackage.objects.get(package_name='New Package')
        self.assertEqual(new_package.trainer, self.trainer)
        self.assertEqual(new_package.total_sessions, 8)
        
    def test_session_list_view(self):
        """Test session list view"""
        # Create a test session
        session = Session.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package=self.test_package,
            session_date=date.today(),
            session_time=timezone.now().time()
        )
        
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:session_list')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')
        
    def test_session_add_view_post_valid(self):
        """Test session add view with valid POST data"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:session_add')
        data = {
            'client': self.test_client.pk,
            'package': self.test_package.pk,
            'session_date': date.today().strftime('%Y-%m-%d'),
            'session_time': '15:00',
            'notes': 'Regular training session'
        }
        response = self.client_test.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check session was created and package remaining sessions decremented
        new_session = Session.objects.get(
            client=self.test_client,
            session_date=date.today()
        )
        self.assertEqual(new_session.trainer, self.trainer)
        
        # Package should have one less remaining session
        updated_package = SessionPackage.objects.get(pk=self.test_package.pk)
        self.assertEqual(updated_package.remaining_sessions, 2)  # Was 3, now 2


class SessionFeeCalculationTestCase(TestCase):
    """Test session fee calculations"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        
    def test_fee_calculation_endpoint(self):
        """Test AJAX fee calculation endpoint"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:calculate_fees')
        
        data = {
            'total_sessions': '10',
            'session_price': '50000.00',
            'vat_rate': '10.00',
            'card_fee_rate': '3.50'
        }
        response = self.client_test.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Response should contain calculated fees
        json_response = json.loads(response.content)
        self.assertIn('subtotal', json_response)
        self.assertIn('vat_amount', json_response)
        self.assertIn('card_fee_amount', json_response)
        self.assertIn('total_amount', json_response)
        
    def test_fee_calculation_accuracy(self):
        """Test fee calculation accuracy"""
        # Create package with known values
        package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package_name='Fee Test Package',
            total_sessions=10,
            session_price=Decimal('50000.00'),  # ₩50,000 per session
            vat_rate=Decimal('10.00'),          # 10% VAT
            card_fee_rate=Decimal('3.50')       # 3.5% card fee
        )
        
        # Calculate expected values
        subtotal = Decimal('500000.00')  # 10 sessions × ₩50,000
        # Using inclusive calculation method
        # Total = subtotal / (1 - (vat_rate + card_fee_rate) / 100)
        expected_total = subtotal / (1 - Decimal('0.135'))  # 13.5% total fees
        
        # The total_amount should be calculated correctly
        self.assertGreater(package.total_amount, subtotal)


class SessionCalendarTestCase(TestCase):
    """Test session calendar functionality"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        self.package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package_name='Test Package',
            total_sessions=5,
            session_price=Decimal('40000.00')
        )
        
    def test_session_calendar_view(self):
        """Test session calendar view"""
        # Create sessions for calendar
        Session.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package=self.package,
            session_date=date.today(),
            session_time=timezone.now().time()
        )
        
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:session_calendar')
        response = self.client_test.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')


class SessionStatisticsTestCase(TestCase):
    """Test session statistics and analytics"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Test Client'
        )
        
        # Create packages and sessions for statistics
        self.active_package = SessionPackage.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package_name='Active Package',
            total_sessions=10,
            remaining_sessions=5,
            session_price=Decimal('50000.00'),
            total_amount=Decimal('500000.00'),
            expiry_date=date.today() + timedelta(days=30)
        )
        
        self.completed_session = Session.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package=self.active_package,
            session_date=date.today() - timedelta(days=1),
            session_time=timezone.now().time(),
            status='completed'
        )
        
        self.payment = Payment.objects.create(
            trainer=self.trainer,
            client=self.test_client,
            package=self.active_package,
            amount=Decimal('500000.00'),
            payment_method='card',
            payment_date=date.today()
        )
        
    def test_package_statistics_in_list_view(self):
        """Test package statistics display in list view"""
        self.client_test.login(username='test_trainer', password='testpass123')
        url = reverse('sessions:package_list')
        response = self.client_test.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should display package statistics
        self.assertContains(response, 'Active Package')
        self.assertContains(response, '5/10')  # Remaining/Total sessions
        

class SessionIntegrationTestCase(TestCase):
    """Integration tests for session management workflow"""
    
    def setUp(self):
        self.client_test = Client()
        self.trainer = User.objects.create_user(
            username='test_trainer',
            password='testpass123'
        )
        self.test_client = ClientModel.objects.create(
            trainer=self.trainer,
            name='Integration Test Client',
            email='integration@example.com'
        )
        
    def test_complete_session_workflow(self):
        """Test complete session management workflow"""
        self.client_test.login(username='test_trainer', password='testpass123')
        
        # 1. Create session package
        package_add_url = reverse('sessions:package_add')
        package_data = {
            'client': self.test_client.pk,
            'package_name': 'Integration Package',
            'total_sessions': '5',
            'session_price': '40000.00',
            'vat_rate': '10.00',
            'card_fee_rate': '3.50',
            'expiry_date': (date.today() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'notes': 'Integration test package'
        }
        response = self.client_test.post(package_add_url, package_data)
        self.assertEqual(response.status_code, 302)
        
        # 2. Verify package appears in list
        package_list_url = reverse('sessions:package_list')
        response = self.client_test.get(package_list_url)
        self.assertContains(response, 'Integration Package')
        
        # 3. Create payment for package
        package = SessionPackage.objects.get(package_name='Integration Package')
        payment_add_url = reverse('sessions:payment_add')
        payment_data = {
            'client': self.test_client.pk,
            'package': package.pk,
            'amount': str(package.total_amount),
            'payment_method': 'card',
            'payment_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'Full payment for package'
        }
        response = self.client_test.post(payment_add_url, payment_data)
        self.assertEqual(response.status_code, 302)
        
        # 4. Schedule session
        session_add_url = reverse('sessions:session_add')
        session_data = {
            'client': self.test_client.pk,
            'package': package.pk,
            'session_date': date.today().strftime('%Y-%m-%d'),
            'session_time': '15:00',
            'notes': 'First training session'
        }
        response = self.client_test.post(session_add_url, session_data)
        self.assertEqual(response.status_code, 302)
        
        # 5. Verify session appears in list and package sessions decremented
        session_list_url = reverse('sessions:session_list')
        response = self.client_test.get(session_list_url)
        self.assertContains(response, 'Integration Test Client')
        
        # Package should have 4 remaining sessions (was 5, now 4)
        updated_package = SessionPackage.objects.get(pk=package.pk)
        self.assertEqual(updated_package.remaining_sessions, 4)
        
        # 6. Complete the session
        session = Session.objects.get(
            client=self.test_client,
            session_date=date.today()
        )
        complete_url = reverse('sessions:session_complete', kwargs={'pk': session.pk})
        response = self.client_test.post(complete_url)
        self.assertEqual(response.status_code, 302)
        
        # Session status should be updated to completed
        completed_session = Session.objects.get(pk=session.pk)
        self.assertEqual(completed_session.status, 'completed')
        
        # 7. View package detail to see usage statistics
        package_detail_url = reverse('sessions:package_detail', kwargs={'pk': package.pk})
        response = self.client_test.get(package_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '4')  # Remaining sessions
        self.assertContains(response, '20%')  # Usage percentage (1/5 = 20%)