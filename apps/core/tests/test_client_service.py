"""
Comprehensive tests for ClientService class.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from django.utils import timezone
from django.db.models import QuerySet

from apps.core.services.client_service import ClientService
from apps.trainers.factories import OrganizationFactory, TrainerFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.sessions.factories import SessionPackageFactory, SessionFactory
from apps.accounts.factories import UserFactory


@pytest.mark.django_db
class TestClientService:
    """Test cases for ClientService functionality."""
    
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
    def another_trainer_user(self, organization):
        """Create another trainer in same organization."""
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
    def service(self, trainer_user):
        """Create ClientService instance."""
        return ClientService(user=trainer_user)
    
    @pytest.fixture
    def sample_client(self, trainer_user):
        """Create sample client."""
        return ClientFactory(
            trainer=trainer_user,
            name='김철수',
            gender='M',
            age=30,
            height=175,
            weight=70
        )
    
    @pytest.fixture
    def sample_client_data(self):
        """Sample data for creating a client."""
        return {
            'name': '이영희',
            'gender': 'F',
            'age': 28,
            'height': 165,
            'weight': 55,
            'email': 'test@example.com',
            'phone': '010-1234-5678',
            'medical_conditions': '',
            'athletic_background': ''
        }
    
    def test_get_annotated_queryset(self, service, sample_client):
        """Test annotated queryset includes all calculated fields."""
        # Create some test data
        assessment = AssessmentFactory(client=sample_client, overall_score=85.5)
        session = SessionFactory(
            client=sample_client,
            session_date=timezone.now().date()
        )
        
        queryset = service.get_annotated_queryset()
        client = queryset.get(pk=sample_client.pk)
        
        # Check BMI calculation
        expected_bmi = 70 / (1.75 * 1.75)
        assert abs(client.calculated_bmi - expected_bmi) < 0.01
        
        # Check latest score
        assert client.latest_score == 85.5
        
        # Check recent activity
        assert client.has_recent_activity is True
    
    def test_get_annotated_queryset_no_activity(self, service, sample_client):
        """Test annotated queryset when client has no recent activity."""
        # Create old data (more than 30 days)
        old_date = timezone.now() - timedelta(days=40)
        assessment = AssessmentFactory(
            client=sample_client,
            overall_score=75.0,
            date=old_date.date()
        )
        
        queryset = service.get_annotated_queryset()
        client = queryset.get(pk=sample_client.pk)
        
        assert client.latest_score == 75.0
        assert client.has_recent_activity is False
    
    def test_search_and_filter_text_search(self, service, trainer_user):
        """Test text search functionality."""
        # Create test clients
        client1 = ClientFactory(trainer=trainer_user, name='김철수', email='kim@test.com')
        client2 = ClientFactory(trainer=trainer_user, name='이영희', phone='010-1234-5678')
        client3 = ClientFactory(trainer=trainer_user, name='박민수', email='park@test.com')
        
        # Search by name
        results = service.search_and_filter({'search': '김철수'})
        assert results.count() == 1
        assert results.first() == client1
        
        # Search by email
        results = service.search_and_filter({'search': 'park@test.com'})
        assert results.count() == 1
        assert results.first() == client3
        
        # Search by phone
        results = service.search_and_filter({'search': '010-1234'})
        assert results.count() == 1
        assert results.first() == client2
    
    def test_search_and_filter_gender(self, service, trainer_user):
        """Test gender filter."""
        male_client = ClientFactory(trainer=trainer_user, gender='M')
        female_client = ClientFactory(trainer=trainer_user, gender='F')
        
        # Filter males
        results = service.search_and_filter({'gender': 'M'})
        assert results.count() == 1
        assert results.first() == male_client
        
        # Filter females
        results = service.search_and_filter({'gender': 'F'})
        assert results.count() == 1
        assert results.first() == female_client
    
    def test_search_and_filter_age_range(self, service, trainer_user):
        """Test age range filters."""
        young_client = ClientFactory(trainer=trainer_user, age=20)
        middle_client = ClientFactory(trainer=trainer_user, age=30)
        old_client = ClientFactory(trainer=trainer_user, age=50)
        
        # Age minimum
        results = service.search_and_filter({'age_min': 25})
        assert results.count() == 2
        assert young_client not in results
        
        # Age maximum
        results = service.search_and_filter({'age_max': 35})
        assert results.count() == 2
        assert old_client not in results
        
        # Age range
        results = service.search_and_filter({'age_min': 25, 'age_max': 35})
        assert results.count() == 1
        assert results.first() == middle_client
    
    def test_search_and_filter_bmi_range(self, service, trainer_user):
        """Test BMI range filter."""
        # Create clients with different BMIs
        underweight = ClientFactory(trainer=trainer_user, height=170, weight=50)  # BMI ~17.3
        normal = ClientFactory(trainer=trainer_user, height=170, weight=65)      # BMI ~22.5
        overweight = ClientFactory(trainer=trainer_user, height=170, weight=75)  # BMI ~25.9
        obese = ClientFactory(trainer=trainer_user, height=170, weight=90)       # BMI ~31.1
        
        # Test each category
        results = service.search_and_filter({'bmi_range': 'underweight'})
        assert results.count() == 1
        assert results.first() == underweight
        
        results = service.search_and_filter({'bmi_range': 'normal'})
        assert results.count() == 1
        assert results.first() == normal
        
        results = service.search_and_filter({'bmi_range': 'overweight'})
        assert results.count() == 0  # 25.9 is above overweight threshold
        
        results = service.search_and_filter({'bmi_range': 'obese'})
        assert results.count() == 2  # Both overweight and obese clients
    
    def test_search_and_filter_registration_date(self, service, trainer_user):
        """Test registration date range filter."""
        # Create clients with different registration dates
        old_client = ClientFactory(trainer=trainer_user)
        old_client.created_at = timezone.now() - timedelta(days=60)
        old_client.save()
        
        recent_client = ClientFactory(trainer=trainer_user)
        recent_client.created_at = timezone.now() - timedelta(days=10)
        recent_client.save()
        
        # Filter by start date
        start_date = (timezone.now() - timedelta(days=30)).date()
        results = service.search_and_filter({'registration_start': start_date})
        assert results.count() == 1
        assert results.first() == recent_client
        
        # Filter by end date
        end_date = (timezone.now() - timedelta(days=40)).date()
        results = service.search_and_filter({'registration_end': end_date})
        assert results.count() == 1
        assert results.first() == old_client
    
    def test_search_and_filter_medical_conditions(self, service, trainer_user):
        """Test medical conditions filter."""
        healthy_client = ClientFactory(trainer=trainer_user, medical_conditions='')
        medical_client = ClientFactory(trainer=trainer_user, medical_conditions='고혈압')
        
        # Has medical conditions
        results = service.search_and_filter({'has_medical_conditions': 'yes'})
        assert results.count() == 1
        assert results.first() == medical_client
        
        # No medical conditions
        results = service.search_and_filter({'has_medical_conditions': 'no'})
        assert results.count() == 1
        assert results.first() == healthy_client
    
    def test_search_and_filter_athletic_background(self, service, trainer_user):
        """Test athletic background filter."""
        no_background = ClientFactory(trainer=trainer_user, athletic_background='')
        athlete = ClientFactory(trainer=trainer_user, athletic_background='축구 선수')
        
        # Has athletic background
        results = service.search_and_filter({'has_athletic_background': 'yes'})
        assert results.count() == 1
        assert results.first() == athlete
        
        # No athletic background
        results = service.search_and_filter({'has_athletic_background': 'no'})
        assert results.count() == 1
        assert results.first() == no_background
    
    def test_search_and_filter_activity_status(self, service, trainer_user):
        """Test activity status filter."""
        # Create active client (recent session)
        active_client = ClientFactory(trainer=trainer_user)
        SessionFactory(client=active_client, session_date=timezone.now().date())
        
        # Create inactive client (old session)
        inactive_client = ClientFactory(trainer=trainer_user)
        old_session = SessionFactory(client=inactive_client)
        old_session.session_date = timezone.now().date() - timedelta(days=40)
        old_session.save()
        
        # Need to use annotated queryset for activity status
        results = service.search_and_filter({'activity_status': 'active'})
        assert active_client in results
        assert inactive_client not in results
        
        results = service.search_and_filter({'activity_status': 'inactive'})
        assert inactive_client in results
        assert active_client not in results
    
    def test_search_and_filter_latest_score_range(self, service, trainer_user):
        """Test latest score range filter."""
        # Create clients with different assessment scores
        high_score = ClientFactory(trainer=trainer_user)
        AssessmentFactory(client=high_score, overall_score=92)
        
        mid_score = ClientFactory(trainer=trainer_user)
        AssessmentFactory(client=mid_score, overall_score=75)
        
        low_score = ClientFactory(trainer=trainer_user)
        AssessmentFactory(client=low_score, overall_score=45)
        
        # Test score ranges
        results = service.search_and_filter({'latest_score_range': '90-100'})
        assert high_score in results
        assert results.count() == 1
        
        results = service.search_and_filter({'latest_score_range': '70-79'})
        assert mid_score in results
        assert results.count() == 1
        
        results = service.search_and_filter({'latest_score_range': '0-59'})
        assert low_score in results
        assert results.count() == 1
    
    def test_search_and_filter_sorting(self, service, trainer_user):
        """Test sorting functionality."""
        client1 = ClientFactory(trainer=trainer_user, name='가나다')
        client2 = ClientFactory(trainer=trainer_user, name='라마바')
        client3 = ClientFactory(trainer=trainer_user, name='사아자')
        
        # Default sort (by created_at descending)
        results = service.search_and_filter({})
        assert results.first() == client3  # Most recent
        
        # Sort by name
        results = service.search_and_filter({'sort_by': 'name'})
        assert list(results) == [client1, client2, client3]
    
    def test_get_client_statistics(self, service, sample_client):
        """Test client statistics calculation."""
        # Create test data
        assessment1 = AssessmentFactory(client=sample_client, overall_score=80)
        assessment2 = AssessmentFactory(client=sample_client, overall_score=90)
        
        package = SessionPackageFactory(client=sample_client, total_amount=Decimal('1000000'))
        session1 = SessionFactory(client=sample_client, status='completed')
        session2 = SessionFactory(client=sample_client, status='cancelled')
        
        stats = service.get_client_statistics(sample_client)
        
        # Check counts
        assert stats['total_assessments'] == 2
        assert stats['total_sessions'] == 2
        assert stats['active_packages'] == 1
        assert stats['total_packages'] == 1
        
        # Check assessment stats
        assert stats['avg_score'] == 85.0
        assert stats['max_score'] == 90
        
        # Check session stats
        assert stats['completed_sessions'] == 1
        assert stats['cancelled_sessions'] == 1
        
        # Check financial stats
        assert stats['total_revenue'] > 0
        assert stats['total_gross'] == Decimal('1000000')
        
        # Check activity status
        assert stats['is_active'] is True
        assert stats['days_since_last_activity'] == 0
    
    def test_get_client_timeline(self, service, sample_client):
        """Test client timeline generation."""
        # Create various activities
        assessment = AssessmentFactory(
            client=sample_client,
            overall_score=85,
            date=timezone.now().date()
        )
        
        session = SessionFactory(
            client=sample_client,
            session_date=timezone.now().date() - timedelta(days=1)
        )
        
        package = SessionPackageFactory(
            client=sample_client,
            package_name='10회 패키지'
        )
        
        timeline = service.get_client_timeline(sample_client, limit=10)
        
        # Check timeline structure
        assert len(timeline) >= 3
        
        # Check timeline contains all activity types
        activity_types = [item['type'] for item in timeline]
        assert 'assessment' in activity_types
        assert 'session' in activity_types
        assert 'package' in activity_types
        
        # Check timeline is sorted by date descending
        dates = [item['date'] for item in timeline]
        assert dates == sorted(dates, reverse=True)
        
        # Check timeline item structure
        assessment_item = next(item for item in timeline if item['type'] == 'assessment')
        assert assessment_item['icon'] == '📊'
        assert '85.0점' in assessment_item['description']
    
    def test_create_client_success(self, service, sample_client_data):
        """Test successful client creation."""
        client, success = service.create_client(sample_client_data)
        
        assert success is True
        assert client is not None
        assert client.name == '이영희'
        assert client.gender == 'F'
        assert client.age == 28
        assert client.trainer == service.user
        assert not service.has_errors
    
    def test_create_client_missing_required_fields(self, service):
        """Test client creation with missing required fields."""
        incomplete_data = {
            'name': '김철수',
            'gender': 'M'
            # Missing age, height, weight
        }
        
        client, success = service.create_client(incomplete_data)
        
        assert success is False
        assert client is None
        assert service.has_errors
        assert any('age' in error for error in service.errors)
        assert any('height' in error for error in service.errors)
        assert any('weight' in error for error in service.errors)
    
    def test_create_client_exception_handling(self, service, sample_client_data):
        """Test client creation handles exceptions."""
        with patch.object(service, 'save_with_audit', side_effect=Exception("Database error")):
            client, success = service.create_client(sample_client_data)
            
            assert success is False
            assert client is None
            assert service.has_errors
            assert any("고객 생성 중 오류가 발생했습니다" in error for error in service.errors)
    
    def test_update_client_success(self, service, sample_client):
        """Test successful client update."""
        update_data = {
            'name': '김철수 (수정)',
            'age': 31,
            'weight': 72
        }
        
        success = service.update_client(sample_client, update_data)
        
        assert success is True
        sample_client.refresh_from_db()
        assert sample_client.name == '김철수 (수정)'
        assert sample_client.age == 31
        assert sample_client.weight == 72
    
    def test_update_client_no_permission(self, service, other_org_trainer):
        """Test update client without permission."""
        # Create client from different organization
        other_client = ClientFactory(trainer=other_org_trainer)
        
        success = service.update_client(other_client, {'name': 'Updated'})
        
        assert success is False
        assert service.has_errors
        assert "권한이 없습니다" in service.get_errors_string()
    
    def test_update_client_no_changes(self, service, sample_client):
        """Test update client with no actual changes."""
        update_data = {
            'name': sample_client.name,
            'age': sample_client.age
        }
        
        with patch.object(service, 'save_with_audit') as mock_save:
            success = service.update_client(sample_client, update_data)
            
            assert success is True
            # save_with_audit should not be called if no changes
            mock_save.assert_not_called()
    
    def test_export_clients_data(self, service, trainer_user):
        """Test client data export preparation."""
        # Create test clients
        client1 = ClientFactory(
            trainer=trainer_user,
            name='김철수',
            gender='M',
            age=30,
            height=175,
            weight=70,
            email='kim@test.com',
            medical_conditions='고혈압'
        )
        
        assessment = AssessmentFactory(client=client1, overall_score=85.5)
        
        # Get annotated queryset for export
        queryset = service.get_annotated_queryset()
        export_data = service.export_clients_data(queryset)
        
        assert len(export_data) == 1
        
        data = export_data[0]
        assert data['이름'] == '김철수'
        assert data['성별'] == '남성'
        assert data['나이'] == 30
        assert data['BMI'] == '22.9'
        assert data['최근 점수'] == '85.5점'
        assert data['의료 상태'] == '있음'
        assert data['운동 경력'] == '없음'
    
    def test_get_dashboard_metrics(self, service, trainer_user):
        """Test dashboard metrics calculation."""
        # Create test data
        client1 = ClientFactory(trainer=trainer_user)
        client2 = ClientFactory(trainer=trainer_user)
        client3 = ClientFactory(trainer=trainer_user)
        
        # Make client1 active
        SessionFactory(client=client1, session_date=timezone.now().date())
        
        # Make client2 inactive (old session)
        old_session = SessionFactory(client=client2)
        old_session.session_date = timezone.now().date() - timedelta(days=40)
        old_session.save()
        
        # Create assessment for client1
        AssessmentFactory(client=client1)
        
        # Set client3 as new this month
        client3.created_at = timezone.now()
        client3.save()
        
        metrics = service.get_dashboard_metrics()
        
        assert metrics['total_clients'] == 3
        assert metrics['active_clients'] == 1
        assert metrics['inactive_clients'] == 2
        assert metrics['new_clients_this_month'] >= 1
        assert metrics['clients_with_assessments'] == 1
        assert metrics['assessment_completion_rate'] == pytest.approx(33.33, rel=0.1)
        assert metrics['activity_rate'] == pytest.approx(33.33, rel=0.1)
    
    def test_organization_filtering(self, service, trainer_user, other_org_trainer):
        """Test that service only returns clients from user's organization."""
        # Create clients in different organizations
        org_client = ClientFactory(trainer=trainer_user)
        other_org_client = ClientFactory(trainer=other_org_trainer)
        
        queryset = service.get_queryset()
        
        assert org_client in queryset
        assert other_org_client not in queryset
    
    def test_edge_cases(self, service, sample_client):
        """Test various edge cases."""
        # Timeline with no activities
        empty_client = ClientFactory(trainer=service.user)
        timeline = service.get_client_timeline(empty_client)
        assert len(timeline) == 0
        
        # Statistics for client with no data
        stats = service.get_client_statistics(empty_client)
        assert stats['total_assessments'] == 0
        assert stats['total_sessions'] == 0
        assert stats['days_since_last_activity'] is None
        
        # Export empty queryset
        empty_queryset = service.get_queryset().none()
        export_data = service.export_clients_data(empty_queryset)
        assert len(export_data) == 0
        
        # Dashboard metrics with no clients
        empty_service = ClientService(user=service.user)
        with patch.object(empty_service, 'get_queryset') as mock_queryset:
            mock_queryset.return_value = service.model.objects.none()
            metrics = empty_service.get_dashboard_metrics()
            assert metrics['total_clients'] == 0
            assert metrics['assessment_completion_rate'] == 0
            assert metrics['activity_rate'] == 0