"""
Comprehensive tests for ReportService class.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from django.utils import timezone
from django.core.files.base import ContentFile

from apps.core.services.report_service import ReportService
from apps.trainers.factories import OrganizationFactory, TrainerFactory
from apps.clients.factories import ClientFactory
from apps.assessments.factories import AssessmentFactory
from apps.reports.factories import AssessmentReportFactory
from apps.accounts.factories import UserFactory
from apps.reports.models import AssessmentReport


@pytest.mark.django_db
class TestReportService:
    """Test cases for ReportService functionality."""
    
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
        return ClientFactory(trainer=trainer_user)
    
    @pytest.fixture
    def assessment(self, client):
        """Create test assessment."""
        return AssessmentFactory(
            client=client,
            overall_score=85.5
        )
    
    @pytest.fixture
    def other_org_assessment(self, other_org_trainer):
        """Create assessment from different organization."""
        other_client = ClientFactory(trainer=other_org_trainer)
        return AssessmentFactory(client=other_client)
    
    @pytest.fixture
    def service(self, trainer_user):
        """Create ReportService instance."""
        return ReportService(user=trainer_user)
    
    @pytest.fixture
    def mock_generator(self):
        """Mock ReportGenerator."""
        mock = Mock()
        mock.generate_assessment_report.return_value = Mock(spec=AssessmentReport)
        return mock
    
    def test_init_with_generator(self, trainer_user):
        """Test service initialization creates ReportGenerator."""
        service = ReportService(user=trainer_user)
        assert service.user == trainer_user
        assert hasattr(service, 'generator')
        assert service.generator is not None
    
    @patch('apps.core.services.report_service.ReportGenerator')
    def test_generate_assessment_report_success(self, mock_generator_class, service, assessment):
        """Test successful report generation."""
        # Setup mock
        mock_report = AssessmentReportFactory.build(assessment=assessment)
        mock_generator = Mock()
        mock_generator.generate_assessment_report.return_value = mock_report
        mock_generator_class.return_value = mock_generator
        service.generator = mock_generator
        
        report, success = service.generate_assessment_report(
            assessment_id=assessment.pk,
            report_type='detailed'
        )
        
        assert success is True
        assert report == mock_report
        mock_generator.generate_assessment_report.assert_called_once_with(
            assessment_id=assessment.pk,
            report_type='detailed',
            user=service.user
        )
    
    def test_generate_assessment_report_no_permission(self, service, other_org_assessment):
        """Test report generation without permission."""
        report, success = service.generate_assessment_report(
            assessment_id=other_org_assessment.pk
        )
        
        assert success is False
        assert report is None
        assert "권한이 없습니다" in service.get_errors_string()
    
    def test_generate_assessment_report_nonexistent(self, service):
        """Test report generation for non-existent assessment."""
        report, success = service.generate_assessment_report(
            assessment_id=99999
        )
        
        assert success is False
        assert report is None
        assert "평가를 찾을 수 없습니다." in service.errors
    
    def test_generate_assessment_report_reuse_recent(self, service, assessment):
        """Test report generation reuses recent report."""
        # Create recent report (less than 24 hours old)
        recent_report = AssessmentReportFactory(
            assessment=assessment,
            generated_by=service.user,
            created_at=timezone.now() - timedelta(hours=12)
        )
        
        with patch.object(service, 'get_latest_report', return_value=recent_report):
            with patch.object(service, '_is_report_recent', return_value=True):
                report, success = service.generate_assessment_report(assessment.pk)
                
                assert success is True
                assert report == recent_report
                # Generator should not be called
                service.generator.generate_assessment_report.assert_not_called()
    
    @patch('apps.core.services.report_service.ReportGenerator')
    def test_generate_assessment_report_exception(self, mock_generator_class, service, assessment):
        """Test report generation handles exceptions."""
        mock_generator = Mock()
        mock_generator.generate_assessment_report.side_effect = Exception("PDF generation failed")
        mock_generator_class.return_value = mock_generator
        service.generator = mock_generator
        
        report, success = service.generate_assessment_report(assessment.pk)
        
        assert success is False
        assert report is None
        assert "보고서 생성 중 오류가 발생했습니다" in service.get_errors_string()
    
    def test_get_latest_report(self, service, assessment):
        """Test getting latest report for assessment."""
        # Create multiple reports
        old_report = AssessmentReportFactory(
            assessment=assessment,
            created_at=timezone.now() - timedelta(days=2)
        )
        new_report = AssessmentReportFactory(
            assessment=assessment,
            created_at=timezone.now() - timedelta(hours=1)
        )
        
        latest = service.get_latest_report(assessment.pk)
        assert latest == new_report
    
    def test_get_latest_report_none_exists(self, service, assessment):
        """Test getting latest report when none exists."""
        latest = service.get_latest_report(assessment.pk)
        assert latest is None
    
    def test_is_report_recent(self, service):
        """Test checking if report is recent."""
        # Recent report (12 hours old)
        recent_report = Mock()
        recent_report.created_at = timezone.now() - timedelta(hours=12)
        assert service._is_report_recent(recent_report, hours=24) is True
        
        # Old report (25 hours old)
        old_report = Mock()
        old_report.created_at = timezone.now() - timedelta(hours=25)
        assert service._is_report_recent(old_report, hours=24) is False
        
        # Edge case - exactly 24 hours
        edge_report = Mock()
        edge_report.created_at = timezone.now() - timedelta(hours=24)
        assert service._is_report_recent(edge_report, hours=24) is False
    
    @patch.object(ReportService, 'generate_assessment_report')
    def test_bulk_generate_reports(self, mock_generate, service):
        """Test bulk report generation."""
        # Setup mock responses
        mock_generate.side_effect = [
            (Mock(), True),   # Success
            (None, False),    # Failure
            (Mock(), True),   # Success
            (None, False),    # Failure
            (Mock(), True),   # Success
        ]
        
        assessment_ids = [1, 2, 3, 4, 5]
        successful, failed = service.bulk_generate_reports(assessment_ids, 'summary')
        
        assert successful == 3
        assert failed == 2
        assert mock_generate.call_count == 5
        
        # Check all calls were made with correct parameters
        for i, assessment_id in enumerate(assessment_ids):
            assert mock_generate.call_args_list[i][0] == (assessment_id, 'summary')
    
    def test_get_client_report_history(self, service, client):
        """Test getting client's report history."""
        # Create assessments and reports for the client
        assessment1 = AssessmentFactory(client=client)
        assessment2 = AssessmentFactory(client=client)
        
        report1 = AssessmentReportFactory(
            assessment=assessment1,
            created_at=timezone.now() - timedelta(days=30)
        )
        report2 = AssessmentReportFactory(
            assessment=assessment2,
            created_at=timezone.now() - timedelta(days=10)
        )
        report3 = AssessmentReportFactory(
            assessment=assessment1,
            created_at=timezone.now() - timedelta(days=5)
        )
        
        # Create report for different client
        other_client = ClientFactory(trainer=service.user)
        other_assessment = AssessmentFactory(client=other_client)
        other_report = AssessmentReportFactory(assessment=other_assessment)
        
        history = service.get_client_report_history(client.pk)
        
        # Should be ordered by created_at descending
        assert list(history) == [report3, report2, report1]
        assert other_report not in history
    
    def test_delete_old_reports(self, service):
        """Test deleting old reports."""
        # Create reports with different ages
        new_report = AssessmentReportFactory()
        new_report.created_at = timezone.now() - timedelta(days=30)
        new_report.save()
        
        old_report1 = AssessmentReportFactory()
        old_report1.created_at = timezone.now() - timedelta(days=100)
        old_report1.save()
        
        old_report2 = AssessmentReportFactory()
        old_report2.created_at = timezone.now() - timedelta(days=120)
        old_report2.save()
        
        # Mock file deletion
        with patch.object(old_report1.file_path, 'delete') as mock_delete1:
            with patch.object(old_report2.file_path, 'delete') as mock_delete2:
                count = service.delete_old_reports(days=90)
                
                assert count == 2
                mock_delete1.assert_called_once()
                mock_delete2.assert_called_once()
        
        # Verify only old reports were deleted
        assert AssessmentReport.objects.filter(pk=new_report.pk).exists()
        assert not AssessmentReport.objects.filter(pk=old_report1.pk).exists()
        assert not AssessmentReport.objects.filter(pk=old_report2.pk).exists()
    
    def test_delete_old_reports_no_file(self, service):
        """Test deleting old reports without files."""
        # Create old report without file
        old_report = AssessmentReportFactory(file_path=None)
        old_report.created_at = timezone.now() - timedelta(days=100)
        old_report.save()
        
        count = service.delete_old_reports(days=90)
        
        assert count == 1
        assert not AssessmentReport.objects.filter(pk=old_report.pk).exists()
    
    def test_get_report_statistics(self, service, trainer_user):
        """Test report statistics generation."""
        # Create various reports
        for _ in range(5):
            AssessmentReportFactory(
                report_type='detailed',
                generated_by=trainer_user,
                file_size=1024 * 100,  # 100KB
                created_at=timezone.now() - timedelta(days=5)
            )
        
        for _ in range(3):
            AssessmentReportFactory(
                report_type='summary',
                generated_by=trainer_user,
                file_size=1024 * 50,  # 50KB
                created_at=timezone.now() - timedelta(days=15)
            )
        
        # Create report from another user
        other_user = UserFactory()
        AssessmentReportFactory(generated_by=other_user)
        
        stats = service.get_report_statistics()
        
        assert stats['total_reports'] >= 8
        assert stats['reports_by_type']['detailed'] >= 5
        assert stats['reports_by_type']['summary'] >= 3
        assert stats['recent_activity']['last_7_days'] >= 5
        assert stats['recent_activity']['last_30_days'] >= 8
        assert stats['average_file_size'] > 0
        
        # Check top generators
        top_generators = stats['top_generators']
        assert len(top_generators) > 0
        assert any(g['generated_by__username'] == trainer_user.username for g in top_generators)
    
    def test_regenerate_report_success(self, service, assessment):
        """Test successful report regeneration."""
        # Create existing report
        old_report = AssessmentReportFactory(
            assessment=assessment,
            report_type='summary',
            file_path=ContentFile(b"Old content", name="old.pdf")
        )
        
        # Mock new report generation
        new_report = AssessmentReportFactory.build(
            assessment=assessment,
            report_type='summary'
        )
        
        with patch.object(service, 'get_object', return_value=old_report):
            with patch.object(service, 'generate_assessment_report', return_value=(new_report, True)):
                with patch.object(old_report.file_path, 'delete') as mock_delete:
                    regenerated, success = service.regenerate_report(old_report.pk)
                    
                    assert success is True
                    assert regenerated == new_report
                    mock_delete.assert_called_once()
    
    def test_regenerate_report_not_found(self, service):
        """Test regenerating non-existent report."""
        with patch.object(service, 'get_object', return_value=None):
            regenerated, success = service.regenerate_report(99999)
            
            assert success is False
            assert regenerated is None
    
    def test_regenerate_report_generation_fails(self, service, assessment):
        """Test regeneration when new report generation fails."""
        old_report = AssessmentReportFactory(assessment=assessment)
        
        with patch.object(service, 'get_object', return_value=old_report):
            with patch.object(service, 'generate_assessment_report', return_value=(None, False)):
                regenerated, success = service.regenerate_report(old_report.pk)
                
                assert success is False
                assert regenerated is None
                # Old report should still exist
                assert AssessmentReport.objects.filter(pk=old_report.pk).exists()
    
    def test_get_reports_for_export_filters(self, service, trainer_user):
        """Test report filtering for export."""
        # Create test data
        client1 = ClientFactory(trainer=trainer_user)
        client2 = ClientFactory(trainer=trainer_user)
        
        assessment1 = AssessmentFactory(client=client1)
        assessment2 = AssessmentFactory(client=client2)
        
        # Reports with different attributes
        report1 = AssessmentReportFactory(
            assessment=assessment1,
            report_type='detailed',
            generated_by=trainer_user,
            created_at=timezone.now() - timedelta(days=10)
        )
        
        report2 = AssessmentReportFactory(
            assessment=assessment2,
            report_type='summary',
            generated_by=trainer_user,
            created_at=timezone.now() - timedelta(days=5)
        )
        
        other_trainer = UserFactory()
        report3 = AssessmentReportFactory(
            assessment=assessment1,
            generated_by=other_trainer,
            created_at=timezone.now() - timedelta(days=3)
        )
        
        # Test date range filter
        filters = {
            'start_date': (timezone.now() - timedelta(days=7)).date(),
            'end_date': timezone.now().date()
        }
        results = service.get_reports_for_export(filters)
        assert report1 not in results
        assert report2 in results
        assert report3 in results
        
        # Test report type filter
        filters = {'report_type': 'detailed'}
        results = service.get_reports_for_export(filters)
        assert report1 in results
        assert report2 not in results
        
        # Test client filter
        filters = {'client_id': client1.pk}
        results = service.get_reports_for_export(filters)
        assert report1 in results
        assert report2 not in results
        assert report3 in results
        
        # Test trainer filter
        filters = {'trainer_id': trainer_user.pk}
        results = service.get_reports_for_export(filters)
        assert report1 in results
        assert report2 in results
        assert report3 not in results
    
    def test_archive_report_success(self, service, assessment):
        """Test successful report archiving."""
        report = AssessmentReportFactory(assessment=assessment)
        
        # Add is_archived attribute for testing
        report.is_archived = False
        
        with patch.object(service, 'get_object', return_value=report):
            with patch.object(service, 'check_permission', return_value=True):
                with patch.object(service, 'save_with_audit', return_value=True) as mock_save:
                    success = service.archive_report(report.pk)
                    
                    assert success is True
                    assert report.is_archived is True
                    mock_save.assert_called_once()
    
    def test_archive_report_no_permission(self, service, assessment):
        """Test archiving report without permission."""
        report = AssessmentReportFactory(assessment=assessment)
        
        with patch.object(service, 'get_object', return_value=report):
            with patch.object(service, 'check_permission', return_value=False):
                success = service.archive_report(report.pk)
                
                assert success is False
                assert "권한이 없습니다" in service.get_errors_string()
    
    def test_archive_report_no_archive_field(self, service, assessment):
        """Test archiving report when model doesn't support archiving."""
        report = AssessmentReportFactory(assessment=assessment)
        
        with patch.object(service, 'get_object', return_value=report):
            with patch.object(service, 'check_permission', return_value=True):
                # Report doesn't have is_archived field
                success = service.archive_report(report.pk)
                
                assert success is True
                # Should delete instead
                assert not AssessmentReport.objects.filter(pk=report.pk).exists()
    
    def test_archive_report_not_found(self, service):
        """Test archiving non-existent report."""
        success = service.archive_report(99999)
        assert success is False
    
    def test_edge_cases(self, service, assessment):
        """Test various edge cases."""
        # Empty bulk generation
        successful, failed = service.bulk_generate_reports([])
        assert successful == 0
        assert failed == 0
        
        # Get statistics with no reports
        with patch.object(service, 'get_queryset') as mock_queryset:
            mock_queryset.return_value = AssessmentReport.objects.none()
            stats = service.get_report_statistics()
            assert stats['total_reports'] == 0
            assert stats['average_file_size'] == 0
            assert len(stats['top_generators']) == 0
        
        # Delete old reports with no old reports
        count = service.delete_old_reports(days=0)  # Delete all
        
        # Get client history for non-existent client
        history = service.get_client_report_history(99999)
        assert history.count() == 0
        
        # Report with timezone-aware created_at
        tz_report = Mock()
        tz_report.created_at = timezone.now()
        assert isinstance(service._is_report_recent(tz_report), bool)
    
    @pytest.mark.parametrize("report_type", ['detailed', 'summary'])
    def test_report_types(self, service, assessment, report_type):
        """Test different report types."""
        with patch.object(service.generator, 'generate_assessment_report') as mock_generate:
            mock_generate.return_value = Mock(spec=AssessmentReport)
            
            report, success = service.generate_assessment_report(
                assessment.pk,
                report_type=report_type
            )
            
            assert success is True
            mock_generate.assert_called_with(
                assessment_id=assessment.pk,
                report_type=report_type,
                user=service.user
            )