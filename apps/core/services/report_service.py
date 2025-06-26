"""
Report service handling all business logic related to report generation.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from io import BytesIO

from django.db import transaction
from django.db.models import Q, Count, Avg
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

from .base import BaseService
from apps.reports.models import AssessmentReport
from apps.reports.services import ReportGenerator
from apps.assessments.models import Assessment
from apps.clients.models import Client

logger = logging.getLogger(__name__)


class ReportService(BaseService):
    """
    Service class for report generation and management.
    
    This service encapsulates all business logic related to generating,
    storing, and managing assessment reports.
    """
    
    model = AssessmentReport
    
    def __init__(self, user=None):
        """Initialize with ReportGenerator instance."""
        super().__init__(user)
        self.generator = ReportGenerator()
    
    def generate_assessment_report(self, assessment_id: int, 
                                 report_type: str = 'detailed') -> Tuple[Optional[AssessmentReport], bool]:
        """
        Generate a PDF report for an assessment.
        
        Args:
            assessment_id: ID of the assessment
            report_type: Type of report ('summary' or 'detailed')
            
        Returns:
            Tuple of (report, success)
        """
        self.clear_errors()
        
        try:
            # Get assessment and check permissions
            assessment = Assessment.objects.select_related('client').get(pk=assessment_id)
            
            if not self.check_permission(assessment, 'view'):
                self.add_error("이 평가에 대한 보고서를 생성할 권한이 없습니다.")
                return None, False
            
            # Check if report already exists
            existing_report = self.get_latest_report(assessment_id)
            if existing_report and self._is_report_recent(existing_report):
                return existing_report, True
            
            # Generate new report using ReportGenerator
            report = self.generator.generate_assessment_report(
                assessment_id=assessment_id,
                report_type=report_type,
                user=self.user
            )
            
            # Log audit
            self._log_audit(
                report, 
                action='create',
                metadata={
                    'assessment_id': assessment_id,
                    'report_type': report_type
                }
            )
            
            return report, True
            
        except Assessment.DoesNotExist:
            self.add_error("평가를 찾을 수 없습니다.")
            return None, False
        except Exception as e:
            logger.exception(f"Error generating report for assessment {assessment_id}")
            self.add_error(f"보고서 생성 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def get_latest_report(self, assessment_id: int) -> Optional[AssessmentReport]:
        """
        Get the most recent report for an assessment.
        
        Args:
            assessment_id: ID of the assessment
            
        Returns:
            Latest AssessmentReport or None
        """
        return self.model.objects.filter(
            assessment_id=assessment_id
        ).order_by('-created_at').first()
    
    def _is_report_recent(self, report: AssessmentReport, hours: int = 24) -> bool:
        """
        Check if a report is recent enough to reuse.
        
        Args:
            report: AssessmentReport instance
            hours: Number of hours to consider recent
            
        Returns:
            bool: True if report is recent
        """
        age = datetime.now(report.created_at.tzinfo) - report.created_at
        return age.total_seconds() < (hours * 3600)
    
    def bulk_generate_reports(self, assessment_ids: List[int], 
                            report_type: str = 'summary') -> Tuple[int, int]:
        """
        Generate reports for multiple assessments.
        
        Args:
            assessment_ids: List of assessment IDs
            report_type: Type of report to generate
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for assessment_id in assessment_ids:
            report, success = self.generate_assessment_report(assessment_id, report_type)
            if success:
                successful += 1
            else:
                failed += 1
                logger.warning(f"Failed to generate report for assessment {assessment_id}: {self.get_errors_string()}")
        
        return successful, failed
    
    def get_client_report_history(self, client_id: int) -> QuerySet:
        """
        Get all reports for a specific client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            QuerySet of AssessmentReports
        """
        return self.get_queryset().filter(
            assessment__client_id=client_id
        ).select_related('assessment', 'generated_by').order_by('-created_at')
    
    def delete_old_reports(self, days: int = 90) -> int:
        """
        Delete reports older than specified days.
        
        Args:
            days: Number of days to keep reports
            
        Returns:
            Number of reports deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_reports = self.get_queryset().filter(
            created_at__lt=cutoff_date
        )
        
        count = old_reports.count()
        
        # Delete associated files
        for report in old_reports:
            if report.file_path:
                report.file_path.delete()
        
        # Delete records
        old_reports.delete()
        
        logger.info(f"Deleted {count} reports older than {days} days")
        return count
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about report generation.
        
        Returns:
            Dictionary of report statistics
        """
        queryset = self.get_queryset()
        
        # Basic counts
        total_reports = queryset.count()
        
        # Reports by type
        reports_by_type = dict(
            queryset.values('report_type').annotate(
                count=Count('id')
            ).values_list('report_type', 'count')
        )
        
        # Recent activity
        last_7_days = datetime.now() - timedelta(days=7)
        last_30_days = datetime.now() - timedelta(days=30)
        
        recent_stats = {
            'last_7_days': queryset.filter(created_at__gte=last_7_days).count(),
            'last_30_days': queryset.filter(created_at__gte=last_30_days).count()
        }
        
        # Average file size
        avg_size = queryset.aggregate(
            avg_size=Avg('file_size')
        )['avg_size'] or 0
        
        # Most active trainers
        top_generators = queryset.values(
            'generated_by__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'total_reports': total_reports,
            'reports_by_type': reports_by_type,
            'recent_activity': recent_stats,
            'average_file_size': avg_size,
            'top_generators': list(top_generators),
            'storage_used': queryset.aggregate(
                total=Count('file_size')
            )['total'] or 0
        }
    
    def regenerate_report(self, report_id: int) -> Tuple[Optional[AssessmentReport], bool]:
        """
        Regenerate an existing report.
        
        Args:
            report_id: ID of the report to regenerate
            
        Returns:
            Tuple of (report, success)
        """
        self.clear_errors()
        
        try:
            # Get existing report
            old_report = self.get_object(report_id)
            if not old_report:
                return None, False
            
            # Generate new report
            new_report, success = self.generate_assessment_report(
                assessment_id=old_report.assessment_id,
                report_type=old_report.report_type
            )
            
            if success:
                # Delete old report file
                if old_report.file_path:
                    old_report.file_path.delete()
                old_report.delete()
                
                return new_report, True
            else:
                return None, False
                
        except Exception as e:
            logger.exception(f"Error regenerating report {report_id}")
            self.add_error(f"보고서 재생성 중 오류가 발생했습니다: {str(e)}")
            return None, False
    
    def get_reports_for_export(self, filters: Dict[str, Any]) -> QuerySet:
        """
        Get filtered reports for export.
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered QuerySet
        """
        queryset = self.get_queryset()
        
        # Date range filter
        start_date = filters.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        
        end_date = filters.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Report type filter
        report_type = filters.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Client filter
        client_id = filters.get('client_id')
        if client_id:
            queryset = queryset.filter(assessment__client_id=client_id)
        
        # Trainer filter
        trainer_id = filters.get('trainer_id')
        if trainer_id:
            queryset = queryset.filter(generated_by_id=trainer_id)
        
        return queryset.select_related(
            'assessment', 
            'assessment__client',
            'generated_by'
        ).order_by('-created_at')
    
    def archive_report(self, report_id: int) -> bool:
        """
        Archive a report (soft delete).
        
        Args:
            report_id: ID of the report to archive
            
        Returns:
            bool: True if successful
        """
        self.clear_errors()
        
        report = self.get_object(report_id)
        if not report:
            return False
        
        if not self.check_permission(report, 'delete'):
            self.add_error("이 보고서를 보관할 권한이 없습니다.")
            return False
        
        # Add archived flag if model supports it
        if hasattr(report, 'is_archived'):
            report.is_archived = True
            return self.save_with_audit(
                report, 
                action='archive',
                metadata={'archived_at': datetime.now().isoformat()}
            )
        else:
            # Otherwise just delete
            report.delete()
            return True