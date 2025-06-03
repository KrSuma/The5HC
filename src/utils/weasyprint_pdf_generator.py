# weasyprint_pdf_generator.py - PDF generation using WeasyPrint from HTML reports

import io
from typing import Dict, List, Any, Optional
import weasyprint
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from src.utils.html_report_generator import create_html_report


def create_weasyprint_pdf(client_details: Dict[str, Any], 
                         assessment_data: Dict[str, Any], 
                         category_scores: Dict[str, float], 
                         suggestions: Dict[str, List[str]],
                         trainer_name: str = "트레이너") -> bytes:
    """
    Create a PDF report using WeasyPrint from HTML content
    
    Args:
        client_details: Dictionary with client information
        assessment_data: Dictionary with assessment data
        category_scores: Dictionary with category scores
        suggestions: Dictionary with improvement suggestions
        trainer_name: Name of the trainer conducting the assessment
        
    Returns:
        bytes: PDF report as bytes
    """
    try:
        # Generate HTML content using our existing HTML report generator
        html_content = create_html_report(
            client_details, 
            assessment_data, 
            category_scores, 
            suggestions,
            trainer_name
        )
        
        # Add print-specific CSS optimizations
        print_css = """
        @page {
            size: A4;
            margin: 10mm;
        }
        
        body {
            font-size: 9px !important;
        }
        
        .page {
            width: 100% !important;
            height: auto !important;
            margin: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            page-break-inside: avoid;
        }
        
        .header {
            page-break-inside: avoid;
        }
        
        .top-section {
            page-break-inside: avoid;
        }
        
        .test-results {
            page-break-inside: avoid;
        }
        
        .bottom-section {
            page-break-inside: avoid;
        }
        
        .footer {
            position: static !important;
            margin-top: 20px;
        }
        
        /* Ensure grid layouts work in print */
        .top-section {
            display: flex !important;
            flex-wrap: wrap;
            gap: 12px;
        }
        
        .top-section > div {
            flex: 1;
            min-width: 200px;
        }
        
        .radar-section {
            flex: 0 0 120px;
        }
        
        .bottom-section {
            display: flex !important;
            flex-wrap: wrap;
            gap: 12px;
        }
        
        .bottom-section > div {
            flex: 1;
            min-width: 250px;
        }
        
        .suggestions-grid {
            display: flex !important;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .suggestion-box {
            flex: 1;
            min-width: 120px;
        }
        
        .program-grid {
            display: flex !important;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .program-box {
            flex: 1;
            min-width: 150px;
        }
        
        /* Better table handling */
        .test-table {
            page-break-inside: auto;
        }
        
        .test-table thead {
            display: table-header-group;
        }
        
        .test-table tr {
            page-break-inside: avoid;
        }
        
        /* Improve font rendering */
        * {
            -webkit-print-color-adjust: exact !important;
            color-adjust: exact !important;
        }
        """
        
        # Create font configuration for better Korean font support
        font_config = FontConfiguration()
        
        # Create HTML document
        html_doc = HTML(string=html_content)
        
        # Create CSS for print optimization
        css_doc = CSS(string=print_css, font_config=font_config)
        
        # Generate PDF
        pdf_bytes = html_doc.write_pdf(
            stylesheets=[css_doc],
            font_config=font_config,
            optimize_images=True
        )
        
        return pdf_bytes
        
    except Exception as e:
        # Fallback error handling
        raise


def create_optimized_html_for_pdf(client_details: Dict[str, Any], 
                                 assessment_data: Dict[str, Any], 
                                 category_scores: Dict[str, float], 
                                 suggestions: Dict[str, List[str]],
                                 trainer_name: str = "트레이너") -> str:
    """
    Create HTML content specifically optimized for PDF generation
    
    This version includes print-specific optimizations and better layout handling
    """
    # Get the base HTML content
    html_content = create_html_report(
        client_details, 
        assessment_data, 
        category_scores, 
        suggestions,
        trainer_name
    )
    
    # Add PDF-specific modifications
    # Replace CSS grid with flexbox for better PDF support
    pdf_optimized_html = html_content.replace(
        'display: grid;',
        'display: flex; flex-wrap: wrap;'
    ).replace(
        'grid-template-columns: 1fr 1fr 120px;',
        'gap: 12px;'
    ).replace(
        'grid-template-columns: 1fr 1fr;',
        'gap: 12px;'
    ).replace(
        'grid-template-columns: repeat(7, 1fr);',
        'gap: 8px;'
    )
    
    return pdf_optimized_html


def test_weasyprint_generation():
    """
    Test function to verify WeasyPrint PDF generation works
    """
    # Sample test data
    test_client = {
        'name': '테스트고객',
        'age': 30,
        'gender': '남성',
        'height': 175,
        'weight': 70
    }
    
    test_assessment = {
        'date': '2025-06-03',
        'overhead_squat_score': 2,
        'overhead_squat_notes': '테스트 노트',
        'push_up_reps': 25,
        'push_up_score': 3,
        'push_up_notes': '테스트 노트',
        'single_leg_balance_right_eyes_open': 30,
        'single_leg_balance_left_eyes_open': 28,
        'single_leg_balance_right_eyes_closed': 15,
        'single_leg_balance_left_eyes_closed': 13,
        'toe_touch_distance': -5,
        'toe_touch_score': 2,
        'shoulder_mobility_right': 1.5,
        'shoulder_mobility_left': 1.8,
        'shoulder_mobility_score': 2,
        'farmer_carry_weight': 30,
        'farmer_carry_distance': 20,
        'farmer_carry_notes': '수행 시간: 40초',
        'harvard_step_test_notes': 'HR1: 115, HR2: 105, HR3: 95, PFI: 75.2'
    }
    
    test_scores = {
        'overall_score': 70.0,
        'strength_score': 17.5,
        'mobility_score': 15.5,
        'balance_score': 19.0,
        'cardio_score': 18.0
    }
    
    test_suggestions = {
        'strength': ['근력 훈련 지속', '복합 운동 추가'],
        'mobility': ['스트레칭 강화', '가동성 운동'],
        'balance': ['균형 훈련', '고유감각 향상'],
        'cardio': ['유산소 강화', '인터벌 훈련']
    }
    
    try:
        pdf_bytes = create_weasyprint_pdf(
            test_client,
            test_assessment, 
            test_scores,
            test_suggestions,
            '테스트트레이너'
        )
        
        # Save test PDF
        with open('test_weasyprint_report.pdf', 'wb') as f:
            f.write(pdf_bytes)
            
        print(f"WeasyPrint PDF generated successfully! Size: {len(pdf_bytes)} bytes")
        print("Test PDF saved as: test_weasyprint_report.pdf")
        return True
        
    except Exception as e:
        print(f"WeasyPrint PDF test failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when script is executed directly
    test_weasyprint_generation()