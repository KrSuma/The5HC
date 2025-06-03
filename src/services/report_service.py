"""
PDF report generation service
"""
from typing import Optional, Tuple
import os
from datetime import datetime
from fpdf import FPDF

from ..core.models import Assessment, Client
from ..core.recommendations import generate_recommendations
from ..core.constants import PDF_FONT_FAMILY, PDF_TITLE_FONT_SIZE, PDF_HEADING_FONT_SIZE, PDF_BODY_FONT_SIZE
from ..data.repositories import RepositoryFactory
from ..utils.logging import error_logger, app_logger


class PDFReport(FPDF):
    """Custom PDF class for fitness assessment reports"""
    
    def header(self):
        """Page header"""
        self.set_font(PDF_FONT_FAMILY, 'B', 16)
        self.cell(0, 10, '더파이브 헬스케어 Fitness Assessment Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """Page footer"""
        self.set_y(-15)
        self.set_font(PDF_FONT_FAMILY, '', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


class ReportService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        self.assessment_repo = RepositoryFactory.get_assessment_repository()
        self.client_repo = RepositoryFactory.get_client_repository()
        self.font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'fonts')
    
    def generate_report(self, assessment_id: int) -> Tuple[bool, str, Optional[bytes]]:
        """Generate PDF report for an assessment"""
        try:
            # Get assessment and client data
            assessment = self.assessment_repo.get_by_id(assessment_id)
            if not assessment:
                return False, "평가를 찾을 수 없습니다.", None
            
            client = self.client_repo.get_by_id(assessment.client_id)
            if not client:
                return False, "고객을 찾을 수 없습니다.", None
            
            # Create PDF
            pdf = PDFReport()
            
            # Add Korean font support
            pdf.add_font(PDF_FONT_FAMILY, '', os.path.join(self.font_dir, 'NanumGothic.ttf'), uni=True)
            pdf.add_font(PDF_FONT_FAMILY, 'B', os.path.join(self.font_dir, 'NanumGothicBold.ttf'), uni=True)
            
            pdf.add_page()
            
            # Client information section
            self._add_client_info(pdf, client, assessment)
            
            # Overall scores section
            self._add_overall_scores(pdf, assessment)
            
            # Individual test results
            pdf.add_page()
            self._add_test_results(pdf, assessment)
            
            # Recommendations
            pdf.add_page()
            self._add_recommendations(pdf, assessment, client)
            
            # Generate PDF bytes
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            app_logger.info(f"PDF report generated for assessment {assessment_id}")
            return True, "리포트가 생성되었습니다.", pdf_bytes
            
        except Exception as e:
            error_logger.log_error(e, context={'action': 'generate_report', 'assessment_id': assessment_id})
            return False, "리포트 생성 중 오류가 발생했습니다.", None
    
    def _add_client_info(self, pdf: PDFReport, client: Client, assessment: Assessment):
        """Add client information section"""
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_HEADING_FONT_SIZE)
        pdf.cell(0, 10, '고객 정보', 0, 1)
        pdf.ln(5)
        
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        pdf.cell(0, 8, f'이름: {client.name}', 0, 1)
        pdf.cell(0, 8, f'나이: {client.age}세', 0, 1)
        pdf.cell(0, 8, f'성별: {"남성" if client.gender == "male" else "여성"}', 0, 1)
        pdf.cell(0, 8, f'신장: {client.height}cm', 0, 1)
        pdf.cell(0, 8, f'체중: {client.weight}kg', 0, 1)
        pdf.cell(0, 8, f'BMI: {client.bmi}', 0, 1)
        pdf.cell(0, 8, f'평가일: {assessment.date}', 0, 1)
        pdf.ln(10)
    
    def _add_overall_scores(self, pdf: PDFReport, assessment: Assessment):
        """Add overall scores section"""
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_HEADING_FONT_SIZE)
        pdf.cell(0, 10, '종합 점수', 0, 1)
        pdf.ln(5)
        
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        
        # Overall score with color coding
        overall_score = assessment.overall_score or 0
        pdf.cell(50, 8, '전체 점수:', 0, 0)
        
        # Set color based on score
        if overall_score >= 85:
            pdf.set_text_color(0, 150, 0)  # Green
        elif overall_score >= 70:
            pdf.set_text_color(0, 100, 200)  # Blue
        elif overall_score >= 50:
            pdf.set_text_color(255, 165, 0)  # Orange
        else:
            pdf.set_text_color(255, 0, 0)  # Red
        
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE + 2)
        pdf.cell(0, 8, f'{overall_score:.1f} / 100', 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        pdf.ln(5)
        
        # Category scores
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        categories = [
            ('근력', assessment.strength_score),
            ('유연성', assessment.mobility_score),
            ('균형', assessment.balance_score),
            ('심폐지구력', assessment.cardio_score)
        ]
        
        for name, score in categories:
            if score is not None:
                pdf.cell(50, 8, f'{name}:', 0, 0)
                pdf.cell(0, 8, f'{score:.1f} / 100', 0, 1)
        
        pdf.ln(10)
    
    def _add_test_results(self, pdf: PDFReport, assessment: Assessment):
        """Add individual test results"""
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_HEADING_FONT_SIZE)
        pdf.cell(0, 10, '개별 테스트 결과', 0, 1)
        pdf.ln(5)
        
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        
        # Overhead Squat
        if assessment.overhead_squat_score is not None:
            pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE)
            pdf.cell(0, 8, '1. 오버헤드 스쿼트', 0, 1)
            pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
            pdf.cell(0, 8, f'   점수: {assessment.overhead_squat_score}/3', 0, 1)
            if assessment.overhead_squat_notes:
                pdf.multi_cell(0, 8, f'   메모: {assessment.overhead_squat_notes}')
            pdf.ln(5)
        
        # Push-up Test
        if assessment.push_up_score is not None:
            pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE)
            pdf.cell(0, 8, '2. 푸시업 테스트', 0, 1)
            pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
            if assessment.push_up_reps:
                pdf.cell(0, 8, f'   반복 횟수: {assessment.push_up_reps}회', 0, 1)
            pdf.cell(0, 8, f'   점수: {assessment.push_up_score}/100', 0, 1)
            if assessment.push_up_notes:
                pdf.multi_cell(0, 8, f'   메모: {assessment.push_up_notes}')
            pdf.ln(5)
        
        # Single Leg Balance
        if assessment.single_leg_balance_left_eyes_open is not None:
            pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE)
            pdf.cell(0, 8, '3. 외발 균형 테스트', 0, 1)
            pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
            pdf.cell(0, 8, f'   왼발 (눈 뜬 상태): {assessment.single_leg_balance_left_eyes_open:.1f}초', 0, 1)
            pdf.cell(0, 8, f'   오른발 (눈 뜬 상태): {assessment.single_leg_balance_right_eyes_open:.1f}초', 0, 1)
            if assessment.single_leg_balance_left_eyes_closed:
                pdf.cell(0, 8, f'   왼발 (눈 감은 상태): {assessment.single_leg_balance_left_eyes_closed:.1f}초', 0, 1)
            if assessment.single_leg_balance_right_eyes_closed:
                pdf.cell(0, 8, f'   오른발 (눈 감은 상태): {assessment.single_leg_balance_right_eyes_closed:.1f}초', 0, 1)
            if assessment.single_leg_balance_notes:
                pdf.multi_cell(0, 8, f'   메모: {assessment.single_leg_balance_notes}')
            pdf.ln(5)
        
        # Continue with other tests...
        # (Similar format for toe touch, shoulder mobility, farmer's carry, and Harvard step test)
    
    def _add_recommendations(self, pdf: PDFReport, assessment: Assessment, client: Client):
        """Add recommendations section"""
        pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_HEADING_FONT_SIZE)
        pdf.cell(0, 10, '운동 권장사항', 0, 1)
        pdf.ln(5)
        
        # Generate recommendations
        recommendations = generate_recommendations(assessment, client)
        
        pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
        
        for category, items in recommendations.items():
            if items:
                pdf.set_font(PDF_FONT_FAMILY, 'B', PDF_BODY_FONT_SIZE)
                category_name = {
                    'strength': '근력 향상',
                    'mobility': '유연성 향상',
                    'balance': '균형 향상',
                    'cardio': '심폐지구력 향상',
                    'general': '일반 권장사항'
                }.get(category, category)
                
                pdf.cell(0, 8, f'{category_name}:', 0, 1)
                pdf.set_font(PDF_FONT_FAMILY, '', PDF_BODY_FONT_SIZE)
                
                for item in items:
                    pdf.multi_cell(0, 8, f'   • {item}')
                
                pdf.ln(5)