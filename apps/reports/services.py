import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    FontConfiguration = None

from apps.assessments.models import Assessment
from apps.reports.models import AssessmentReport

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Service for generating PDF reports from assessments"""
    
    def __init__(self):
        if WEASYPRINT_AVAILABLE:
            self.font_config = FontConfiguration()
        else:
            self.font_config = None
    
    def generate_assessment_report(
        self, 
        assessment_id: int, 
        report_type: str = 'detailed',
        user=None
    ) -> AssessmentReport:
        """
        Generate a PDF report for an assessment
        
        Args:
            assessment_id: ID of the assessment
            report_type: Type of report ('summary' or 'detailed')
            user: User generating the report
            
        Returns:
            AssessmentReport instance
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available. Please install system dependencies.")
            
        try:
            # Get assessment with related data
            assessment = Assessment.objects.select_related('client').get(id=assessment_id)
            
            # Calculate scores
            scores = self._calculate_scores(assessment)
            
            # Calculate BMI
            bmi = self._calculate_bmi(assessment.client.height, assessment.client.weight)
            
            # Get test results formatted for display
            test_results = self._format_test_results(assessment)
            
            # Get suggestions
            suggestions = self._get_suggestions(scores)
            
            # Get training program
            training_program = self._get_training_program(assessment.client, scores)
            
            # Calculate follow-up dates
            intermediate_check = assessment.created_at.date() + timedelta(days=45)
            next_assessment = assessment.created_at.date() + timedelta(days=90)
            
            # Prepare context for template
            context = {
                'assessment': assessment,
                'client': assessment.client,
                'trainer_name': user.get_full_name() if user else '트레이너',
                'bmi': bmi,
                'scores': scores,
                'strength_pct': min(100, max(0, (scores['strength'] / 5) * 100)),
                'mobility_pct': min(100, max(0, (scores['mobility'] / 5) * 100)),
                'balance_pct': min(100, max(0, (scores['balance'] / 5) * 100)),
                'cardio_pct': min(100, max(0, (scores['cardio'] / 5) * 100)),
                'overall_rating': self._get_overall_rating(scores['overall']),
                'test_results': test_results,
                'suggestions': suggestions,
                'training_program': training_program,
                'intermediate_check': intermediate_check,
                'next_assessment': next_assessment,
            }
            
            # Render HTML
            html_string = render_to_string('reports/assessment_report.html', context)
            
            # Convert to PDF
            pdf_file = self._html_to_pdf(html_string)
            
            # Create report record
            report = AssessmentReport.objects.create(
                assessment=assessment,
                generated_by=user,
                report_type=report_type,
                file_size=pdf_file.getbuffer().nbytes
            )
            
            # Save PDF file
            filename = f"assessment_report_{assessment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report.file_path.save(filename, ContentFile(pdf_file.getvalue()))
            
            logger.info(f"Generated report for assessment {assessment_id}")
            return report
            
        except Assessment.DoesNotExist:
            logger.error(f"Assessment {assessment_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _html_to_pdf(self, html_string: str) -> BytesIO:
        """Convert HTML to PDF using WeasyPrint"""
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint is not available.")
            
        # Get font path
        font_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'fonts')
        
        # CSS for Korean font and page setup
        font_css = CSS(string=f'''
            @font-face {{
                font-family: 'NanumGothic';
                src: url('file://{font_path}/NanumGothic.ttf');
                font-weight: normal;
            }}
            @font-face {{
                font-family: 'NanumGothic';
                src: url('file://{font_path}/NanumGothicBold.ttf');
                font-weight: bold;
            }}
            @page {{
                size: A4;
                margin: 15mm 15mm 15mm 15mm;
            }}
            body {{
                font-family: 'NanumGothic', 'Noto Sans KR', sans-serif;
                margin: 0;
                padding: 0;
            }}
            .page {{
                width: 100%;
                max-width: 100%;
                margin: 0;
                padding: 0;
                box-shadow: none;
            }}
        ''', font_config=self.font_config)
        
        # Generate PDF
        pdf_file = BytesIO()
        HTML(string=html_string).write_pdf(
            pdf_file,
            stylesheets=[font_css],
            font_config=self.font_config
        )
        pdf_file.seek(0)
        
        return pdf_file
    
    def _calculate_scores(self, assessment: Assessment) -> Dict[str, float]:
        """Get category scores from assessment data"""
        
        # Use the pre-calculated scores from the assessment model
        return {
            'strength': float(assessment.strength_score or 0),
            'mobility': float(assessment.mobility_score or 0),
            'balance': float(assessment.balance_score or 0),
            'cardio': float(assessment.cardio_score or 0),
            'overall': float(assessment.overall_score or 0)
        }
    
    def _calculate_bmi(self, height: float, weight: float) -> float:
        """Calculate BMI"""
        height_m = height / 100
        return round(weight / (height_m ** 2), 1)
    
    def _get_overall_rating(self, score: float) -> str:
        """Get overall rating based on score"""
        if score >= 80:
            return "우수"
        elif score >= 60:
            return "양호"
        elif score >= 40:
            return "보통"
        else:
            return "개선필요"
    
    def _format_test_results(self, assessment: Assessment) -> List[Dict[str, Any]]:
        """Format test results for display"""
        
        test_mapping = [
            ("오버헤드 스쿼트", assessment.overhead_squat_score, "점", "strength"),
            ("푸쉬업", assessment.push_up_reps, "회", "strength"),
            ("발끝 닿기", assessment.toe_touch_distance, "cm", "mobility"),
            ("어깨 유연성", assessment.shoulder_mobility_score, "점", "mobility"),
            ("한발 서기 (우-눈뜨고)", assessment.single_leg_balance_right_eyes_open, "초", "balance"),
            ("한발 서기 (좌-눈뜨고)", assessment.single_leg_balance_left_eyes_open, "초", "balance"),
            ("한발 서기 (우-눈감고)", assessment.single_leg_balance_right_eyes_closed, "초", "balance"),
            ("한발 서기 (좌-눈감고)", assessment.single_leg_balance_left_eyes_closed, "초", "balance"),
            ("파머스 캐리", assessment.farmer_carry_time, "초", "strength"),
            ("하버드 스텝 테스트", self._get_harvard_step_score(assessment), "점", "cardio"),
        ]
        
        results = []
        for name, value, unit, category in test_mapping:
            if value is not None:
                grade, grade_class = self._get_grade(value, category)
                results.append({
                    'name': name,
                    'value': value,
                    'unit': unit,
                    'grade': grade,
                    'grade_class': grade_class
                })
        
        return results
    
    def _get_harvard_step_score(self, assessment: Assessment) -> Optional[int]:
        """Get Harvard step test score"""
        if hasattr(assessment, '_harvard_step_test_score'):
            return assessment._harvard_step_test_score
        return None
    
    def _get_grade(self, value: float, category: str) -> tuple:
        """Get grade and CSS class based on value"""
        # Simplified grading logic - would need proper thresholds per test
        if value >= 80:
            return "우수", "excellent"
        elif value >= 60:
            return "양호", "good"
        elif value >= 40:
            return "보통", "average"
        else:
            return "개선필요", "improvement"
    
    def _get_suggestions(self, scores: Dict[str, float]) -> Dict[str, List[str]]:
        """Get improvement suggestions based on scores"""
        
        suggestions = {}
        
        # Strength suggestions
        if scores['strength'] < 3:
            suggestions['strength'] = [
                "주 3회 이상 근력 운동 실시",
                "점진적 과부하 원칙 적용",
                "복합 운동 위주로 구성"
            ]
        
        # Mobility suggestions
        if scores['mobility'] < 3:
            suggestions['mobility'] = [
                "매일 10-15분 스트레칭",
                "요가나 필라테스 병행",
                "관절 가동 범위 운동"
            ]
        
        # Balance suggestions
        if scores['balance'] < 3:
            suggestions['balance'] = [
                "균형 감각 향상 운동",
                "코어 강화 운동 추가",
                "한 발 서기 연습"
            ]
        
        # Cardio suggestions
        if scores['cardio'] < 3:
            suggestions['cardio'] = [
                "주 150분 이상 유산소 운동",
                "인터벌 트레이닝 도입",
                "점진적 강도 증가"
            ]
        
        return suggestions
    
    def _get_training_program(self, client: Any, scores: Dict[str, float]) -> List[Dict[str, str]]:
        """Generate personalized training program"""
        
        program = [
            {
                'name': '1-4주차',
                'details': '기초 체력 구축 및 운동 적응 단계'
            },
            {
                'name': '5-8주차',
                'details': '운동 강도 증가 및 근력 향상 집중'
            },
            {
                'name': '9-12주차',
                'details': '종합적 체력 향상 및 목표 달성'
            }
        ]
        
        return program