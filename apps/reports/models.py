from django.db import models
from django.conf import settings
from apps.assessments.models import Assessment


class AssessmentReport(models.Model):
    """PDF report for fitness assessments"""
    
    REPORT_TYPES = [
        ('summary', '요약 보고서'),
        ('detailed', '상세 보고서'),
    ]
    
    assessment = models.ForeignKey(
        Assessment, 
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="평가"
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="생성자"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시"
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='detailed',
        verbose_name="보고서 유형"
    )
    file_path = models.FileField(
        upload_to='reports/assessments/%Y/%m/',
        verbose_name="파일 경로"
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name="파일 크기 (bytes)"
    )
    
    class Meta:
        verbose_name = "평가 보고서"
        verbose_name_plural = "평가 보고서"
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['assessment', '-generated_at']),
        ]
    
    def __str__(self):
        return f"{self.assessment.client.name} - {self.get_report_type_display()} ({self.generated_at.strftime('%Y-%m-%d')})"
    
    @property
    def filename(self):
        """Generate a user-friendly filename"""
        date_str = self.assessment.assessment_date.strftime('%Y%m%d')
        client_name = self.assessment.client.name.replace(' ', '_')
        return f"fitness_assessment_{client_name}_{date_str}.pdf"
