"""
Factory classes for the reports app models.
Following django-test.md guidelines for pytest testing.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.core.files.base import ContentFile
from django.utils import timezone
import random
import os
from io import BytesIO

from apps.reports.models import AssessmentReport
from apps.assessments.factories import AssessmentFactory
from apps.accounts.factories import UserFactory

fake = Faker('ko_KR')


class AssessmentReportFactory(DjangoModelFactory):
    """Factory for creating AssessmentReport instances"""
    
    class Meta:
        model = AssessmentReport
    
    # Relationships
    assessment = factory.SubFactory(AssessmentFactory)
    generated_by = factory.SubFactory(UserFactory)
    
    # Report details
    report_type = factory.LazyFunction(lambda: random.choice(['summary', 'detailed']))
    
    # File handling
    file_path = factory.LazyAttribute(lambda obj: _create_dummy_pdf_file(obj))
    file_size = factory.LazyFunction(lambda: random.randint(50000, 500000))  # 50KB to 500KB


class SummaryReportFactory(AssessmentReportFactory):
    """Factory for summary report types"""
    
    report_type = 'summary'
    file_size = factory.LazyFunction(lambda: random.randint(30000, 150000))  # Smaller for summary


class DetailedReportFactory(AssessmentReportFactory):
    """Factory for detailed report types"""
    
    report_type = 'detailed'
    file_size = factory.LazyFunction(lambda: random.randint(100000, 500000))  # Larger for detailed


class RecentReportFactory(AssessmentReportFactory):
    """Factory for recently generated reports"""
    
    generated_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.get_current_timezone())
    )


class OldReportFactory(AssessmentReportFactory):
    """Factory for older reports"""
    
    generated_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-1y', end_date='-30d', tzinfo=timezone.get_current_timezone())
    )


# Trait-based approach
class AssessmentReportWithTraitsFactory(AssessmentReportFactory):
    """
    Factory with traits for different report types.
    Usage:
    - AssessmentReportWithTraitsFactory()  # Regular report
    - AssessmentReportWithTraitsFactory(summary=True)  # Summary report
    - AssessmentReportWithTraitsFactory(recent=True)  # Recent report
    - AssessmentReportWithTraitsFactory(large=True)  # Large file
    """
    
    class Params:
        summary = factory.Trait(
            report_type='summary',
            file_size=factory.LazyFunction(lambda: random.randint(30000, 150000))
        )
        detailed = factory.Trait(
            report_type='detailed',
            file_size=factory.LazyFunction(lambda: random.randint(100000, 500000))
        )
        recent = factory.Trait(
            generated_at=factory.LazyFunction(
                lambda: fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.get_current_timezone())
            )
        )
        old = factory.Trait(
            generated_at=factory.LazyFunction(
                lambda: fake.date_time_between(start_date='-1y', end_date='-30d', tzinfo=timezone.get_current_timezone())
            )
        )
        large = factory.Trait(
            file_size=factory.LazyFunction(lambda: random.randint(800000, 2000000))  # 800KB to 2MB
        )
        small = factory.Trait(
            file_size=factory.LazyFunction(lambda: random.randint(10000, 50000))  # 10KB to 50KB
        )


def _create_dummy_pdf_file(obj):
    """
    Create a dummy PDF file for testing purposes.
    This creates a minimal file that can be used in tests.
    """
    # Create minimal PDF content for testing
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/Contents 5 0 R
>>
endobj

4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Report) Tj
ET
endstream
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000136 00000 n 
0000000272 00000 n 
0000000339 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
433
%%EOF"""
    
    # Generate filename based on assessment
    if hasattr(obj, 'assessment') and obj.assessment:
        client_name = getattr(obj.assessment.client, 'name', 'unknown').replace(' ', '_')
        date_str = timezone.now().strftime('%Y%m%d')
        filename = f"test_report_{client_name}_{date_str}.pdf"
    else:
        filename = f"test_report_{fake.uuid4()[:8]}.pdf"
    
    # Create Django file object
    file_obj = ContentFile(pdf_content, name=filename)
    return file_obj


# Helper functions
def create_reports_for_assessment(assessment, count=2, report_types=None):
    """
    Create multiple reports for a single assessment.
    
    Usage:
        reports = create_reports_for_assessment(assessment, count=3)
        reports = create_reports_for_assessment(assessment, report_types=['summary', 'detailed'])
    """
    if report_types is None:
        report_types = ['summary', 'detailed']
    
    reports = []
    for i in range(count):
        report_type = report_types[i % len(report_types)]
        report = AssessmentReportFactory(
            assessment=assessment,
            report_type=report_type,
            generated_by=assessment.trainer
        )
        reports.append(report)
    
    return reports


def create_trainer_report_history(trainer, num_reports=10):
    """
    Create a history of reports generated by a trainer.
    
    Usage:
        reports = create_trainer_report_history(trainer, num_reports=20)
    """
    reports = []
    for i in range(num_reports):
        # Create assessment first
        assessment = AssessmentFactory(trainer=trainer)
        
        # Create report for the assessment
        report = AssessmentReportFactory(
            assessment=assessment,
            generated_by=trainer,
            generated_at=fake.date_time_between(
                start_date='-6M', 
                end_date='now', 
                tzinfo=timezone.get_current_timezone()
            )
        )
        reports.append(report)
    
    return reports


def create_client_report_timeline(client, trainer=None, months=6):
    """
    Create a timeline of reports for a client over specified months.
    
    Usage:
        reports = create_client_report_timeline(client, months=12)
    """
    if not trainer:
        trainer = UserFactory()
    
    reports = []
    for i in range(months):
        # Create assessment for each month
        assessment_date = fake.date_time_between(
            start_date=f'-{months-i}M',
            end_date=f'-{months-i-1}M',
            tzinfo=timezone.get_current_timezone()
        )
        
        assessment = AssessmentFactory(
            client=client,
            trainer=trainer,
            date=assessment_date
        )
        
        # Create report for the assessment
        report_date = assessment_date + timezone.timedelta(days=random.randint(1, 7))
        report = AssessmentReportFactory(
            assessment=assessment,
            generated_by=trainer,
            generated_at=report_date
        )
        reports.append(report)
    
    return reports


def create_report_size_distribution():
    """
    Create reports with different file sizes for testing storage and performance.
    Returns a dict with different size categories.
    """
    return {
        'tiny': AssessmentReportWithTraitsFactory(small=True, file_size=5000),     # 5KB
        'small': AssessmentReportWithTraitsFactory(small=True, file_size=50000),   # 50KB
        'medium': AssessmentReportFactory(file_size=200000),                       # 200KB
        'large': AssessmentReportWithTraitsFactory(large=True, file_size=800000),  # 800KB
        'huge': AssessmentReportWithTraitsFactory(large=True, file_size=2000000),  # 2MB
    }


def create_report_type_samples():
    """
    Create sample reports of each type for testing.
    Returns a dict with different report types.
    """
    assessment = AssessmentFactory()
    
    return {
        'summary_recent': SummaryReportFactory(
            assessment=assessment,
            generated_at=timezone.now() - timezone.timedelta(days=1)
        ),
        'detailed_recent': DetailedReportFactory(
            assessment=assessment,
            generated_at=timezone.now() - timezone.timedelta(days=2)
        ),
        'summary_old': SummaryReportFactory(
            assessment=assessment,
            generated_at=timezone.now() - timezone.timedelta(days=90)
        ),
        'detailed_old': DetailedReportFactory(
            assessment=assessment,
            generated_at=timezone.now() - timezone.timedelta(days=120)
        ),
    }