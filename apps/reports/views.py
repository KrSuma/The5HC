from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import logging

from apps.assessments.models import Assessment
from apps.clients.models import Client
from apps.reports.models import AssessmentReport
from apps.reports.services import ReportGenerator, WEASYPRINT_AVAILABLE

logger = logging.getLogger(__name__)


@login_required
def report_list(request):
    """List all generated reports"""
    # Get filters
    search_query = request.GET.get('search', '')
    report_type = request.GET.get('type', '')
    
    # Base queryset
    reports = AssessmentReport.objects.select_related(
        'assessment__client',
        'generated_by'
    ).order_by('-generated_at')
    
    # Apply search filter
    if search_query:
        reports = reports.filter(
            Q(assessment__client__name__icontains=search_query) |
            Q(assessment__client__email__icontains=search_query)
        )
    
    # Apply type filter
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'report_type': report_type,
        'report_types': AssessmentReport.REPORT_TYPES,
    }
    
    return render(request, 'reports/report_list.html', context)


@login_required
def generate_report(request, assessment_id):
    """Generate a new report for an assessment"""
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    
    # Check if WeasyPrint is available
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, 'PDF 생성 기능을 사용할 수 없습니다. WeasyPrint가 설치되지 않았습니다.')
        return redirect('assessments:detail', pk=assessment_id)
    
    try:
        # Generate detailed report directly
        generator = ReportGenerator()
        report = generator.generate_assessment_report(
            assessment_id=assessment.id,
            report_type='detailed',  # Always generate detailed report
            user=request.user
        )
        
        messages.success(request, '보고서가 성공적으로 생성되었습니다.')
        return redirect('reports:download', report_id=report.id)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        messages.error(request, '보고서 생성 중 오류가 발생했습니다.')
        return redirect('assessments:detail', pk=assessment_id)


@login_required
def download_report(request, report_id):
    """Download a generated report"""
    report = get_object_or_404(AssessmentReport, pk=report_id)
    
    try:
        # Open the file
        file_handle = report.file_path.open()
        
        # Create response
        response = FileResponse(
            file_handle,
            content_type='application/pdf'
        )
        
        # Set filename
        response['Content-Disposition'] = f'attachment; filename="{report.filename}"'
        
        return response
        
    except FileNotFoundError:
        messages.error(request, '보고서 파일을 찾을 수 없습니다.')
        return redirect('reports:list')


@login_required
def view_report(request, report_id):
    """View a report in the browser"""
    report = get_object_or_404(AssessmentReport, pk=report_id)
    
    try:
        # Open the file
        file_handle = report.file_path.open()
        
        # Create response
        response = FileResponse(
            file_handle,
            content_type='application/pdf'
        )
        
        # Set to display inline
        response['Content-Disposition'] = f'inline; filename="{report.filename}"'
        
        return response
        
    except FileNotFoundError:
        messages.error(request, '보고서 파일을 찾을 수 없습니다.')
        return redirect('reports:list')


@login_required
@require_POST
def delete_report(request, report_id):
    """Delete a report"""
    report = get_object_or_404(AssessmentReport, pk=report_id)
    
    # Delete the file
    if report.file_path:
        report.file_path.delete()
    
    # Delete the record
    report.delete()
    
    messages.success(request, '보고서가 삭제되었습니다.')
    
    # Return to the referrer or report list
    return redirect(request.META.get('HTTP_REFERER', 'reports:list'))


@login_required
def client_reports(request, client_id):
    """View all reports for a specific client"""
    client = get_object_or_404(Client, pk=client_id)
    
    reports = AssessmentReport.objects.filter(
        assessment__client=client
    ).select_related(
        'assessment',
        'generated_by'
    ).order_by('-generated_at')
    
    context = {
        'client': client,
        'reports': reports,
    }
    
    return render(request, 'reports/client_reports.html', context)


@login_required
def assessment_reports(request, assessment_id):
    """View all reports for a specific assessment"""
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    
    reports = AssessmentReport.objects.filter(
        assessment=assessment
    ).select_related(
        'generated_by'
    ).order_by('-generated_at')
    
    context = {
        'assessment': assessment,
        'reports': reports,
    }
    
    return render(request, 'reports/assessment_reports.html', context)