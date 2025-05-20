# pdf_generator.py - Functions for generating PDF reports with improved font handling and optimization

import io
import os
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import base64
from typing import Dict, List, Any, Optional, Tuple, BinaryIO

from improved_assessment_scoring import get_score_description
from improved_recommendations import get_recommended_schedule, get_intensity_recommendations


class FitnessPDF(FPDF):
    """Extended FPDF class with Korean font support and fallback mechanism"""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.korean_fonts_loaded = self._setup_korean_fonts()
        
    def _setup_korean_fonts(self) -> bool:
        """
        Setup Korean fonts if available, with fallback to standard fonts
        
        Returns:
            bool: True if Korean fonts were loaded, False otherwise
        """
        try:
            if os.path.exists('NanumGothic.ttf') and os.path.exists('NanumGothicBold.ttf'):
                self.add_font('NanumGothic', '', 'NanumGothic.ttf', uni=True)
                self.add_font('NanumGothicBold', '', 'NanumGothicBold.ttf', uni=True)
                return True
            else:
                print("Korean fonts not found. Using fallback fonts.")
                return False
        except Exception as e:
            print(f"Error loading Korean fonts: {e}")
            return False
    
    def set_korean_font(self, style='', size=12):
        """Set font with fallback mechanism for Korean text"""
        if self.korean_fonts_loaded:
            font_family = 'NanumGothicBold' if style == 'B' else 'NanumGothic'
            self.set_font(font_family, '', size)
        else:
            # Fallback to standard fonts
            self.set_font('Arial', style, size)


def create_radar_chart_for_pdf(category_scores: Dict[str, float], dpi: int = 150) -> BinaryIO:
    """
    Create a radar chart of fitness category scores for PDF inclusion
    
    Args:
        category_scores: Dictionary containing category scores
        dpi: DPI for the output image (higher for better quality, lower for smaller file size)
        
    Returns:
        BinaryIO: Image buffer containing the radar chart
    """
    # Convert scores to percentages
    strength_pct = min(100, max(0, category_scores['strength_score'] / 25 * 100))
    mobility_pct = min(100, max(0, category_scores['mobility_score'] / 25 * 100))
    balance_pct = min(100, max(0, category_scores['balance_score'] / 25 * 100))
    cardio_pct = min(100, max(0, category_scores['cardio_score'] / 25 * 100))

    # Create figure with specified DPI
    fig = plt.figure(figsize=(4, 4), dpi=dpi)
    ax = fig.add_subplot(111, polar=True)

    # Categories and values
    categories = ['근력', '가동성', '균형', '심폐지구력']
    values = [strength_pct, mobility_pct, balance_pct, cardio_pct]

    # Number of categories
    N = len(categories)

    # Create angles for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop

    # Add values
    values += values[:1]  # Close the loop

    # Draw the plot
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='#ff4b4b')
    ax.fill(angles, values, alpha=0.25, color='#ff4b4b')

    # Draw circular gridlines
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    # Set y-axis limits
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], color='gray', fontsize=8)

    # Remove grid and spines
    ax.grid(True, alpha=0.3)
    ax.spines['polar'].set_visible(False)

    # Adjust label positions for better readability
    for i, label in enumerate(ax.get_xticklabels()):
        angle_rad = angles[i]
        if angle_rad == 0:  # Top
            label.set_ha('center')
            label.set_va('bottom')
        elif 0 < angle_rad < np.pi:  # Right side
            label.set_ha('left')
            label.set_va('center')
        elif angle_rad == np.pi:  # Bottom
            label.set_ha('center')
            label.set_va('top')
        else:  # Left side
            label.set_ha('right')
            label.set_va('center')

    # Save the chart as a temporary image to include in PDF
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=dpi)
    img_buffer.seek(0)
    plt.close()

    return img_buffer


def create_pdf_report(client_details: Dict[str, Any], 
                     assessment_data: Dict[str, Any], 
                     category_scores: Dict[str, float], 
                     suggestions: Dict[str, List[str]]) -> bytes:
    """
    Create a PDF report with assessment results in landscape format
    
    Args:
        client_details: Dictionary with client information
        assessment_data: Dictionary with assessment data
        category_scores: Dictionary with category scores
        suggestions: Dictionary with improvement suggestions
        
    Returns:
        bytes: PDF report as bytes
    """
    pdf = FitnessPDF(orientation='L', format='A4')  # Landscape orientation
    pdf.add_page()

    # Set margin
    pdf.set_margin(10)

    # Title
    pdf.set_korean_font('B', 18)
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, 10, 277, 20, 'F')
    pdf.cell(277, 20, '더파이브 헬스케어 체력 평가 보고서', 0, 1, 'C')
    pdf.line(10, 32, 287, 32)
    pdf.ln(5)

    # Left side - Client Info and Category Scores
    # Client Information
    pdf.set_korean_font('B', 14)
    pdf.cell(120, 10, '회원 정보', 0, 1, 'L')
    pdf.set_korean_font('', 11)

    pdf.cell(20, 8, '이름:', 0, 0, 'L')
    pdf.cell(100, 8, client_details.get('name', 'N/A'), 0, 1, 'L')

    pdf.cell(20, 8, '나이:', 0, 0, 'L')
    pdf.cell(100, 8, str(client_details.get('age', 'N/A')), 0, 1, 'L')

    pdf.cell(20, 8, '성별:', 0, 0, 'L')
    pdf.cell(100, 8, client_details.get('gender', 'N/A'), 0, 1, 'L')

    pdf.cell(20, 8, '평가일:', 0, 0, 'L')
    pdf.cell(100, 8, assessment_data.get('date', 'N/A'), 0, 1, 'L')

    pdf.ln(5)

    # Category Scores
    pdf.set_korean_font('B', 14)
    pdf.cell(120, 10, '카테고리 점수', 0, 1, 'L')
    pdf.set_korean_font('', 11)

    # Function to draw progress bar
    def draw_progress_bar(y_position: float, score: float, max_score: float = 25) -> None:
        bar_width = 80
        progress = min(1.0, max(0.0, score / max_score))
        pdf.set_draw_color(220, 220, 220)
        pdf.set_fill_color(220, 220, 220)
        pdf.rect(30, y_position, bar_width, 4, 'F')
        pdf.set_fill_color(255, 75, 75)
        pdf.rect(30, y_position, bar_width * progress, 4, 'F')

    # Strength
    strength_score = category_scores.get('strength_score', 0)
    pdf.cell(60, 8, '근력 및 근지구력:', 0, 0, 'L')
    pdf.cell(20, 8, f"{strength_score:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(strength_score, 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), strength_score)
    pdf.ln(8)

    # Mobility
    mobility_score = category_scores.get('mobility_score', 0)
    pdf.cell(60, 8, '가동성 및 유연성:', 0, 0, 'L')
    pdf.cell(20, 8, f"{mobility_score:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(mobility_score, 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), mobility_score)
    pdf.ln(8)

    # Balance
    balance_score = category_scores.get('balance_score', 0)
    pdf.cell(60, 8, '균형 및 협응성:', 0, 0, 'L')
    pdf.cell(20, 8, f"{balance_score:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(balance_score, 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), balance_score)
    pdf.ln(8)

    # Cardio
    cardio_score = category_scores.get('cardio_score', 0)
    pdf.cell(60, 8, '심폐지구력:', 0, 0, 'L')
    pdf.cell(20, 8, f"{cardio_score:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(cardio_score, 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), cardio_score)

    # Right side - Overall Score and Radar Chart
    pdf.set_xy(140, 40)

    # Overall Score
    overall_score = category_scores.get('overall_score', 0)
    pdf.set_korean_font('B', 14)
    pdf.cell(120, 10, '종합 체력 점수', 0, 1, 'L')
    pdf.set_xy(140, 55)
    pdf.set_korean_font('B', 26)
    pdf.set_text_color(255, 75, 75)
    pdf.cell(60, 15, f"{overall_score:.1f}/100", 0, 0, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_korean_font('B', 18)
    pdf.cell(60, 15, get_score_description(overall_score), 0, 1, 'L')

    # Radar Chart
    radar_chart = create_radar_chart_for_pdf(category_scores)
    pdf.image(radar_chart, x=140, y=85, w=120, h=90)

    # Test Results - Top half of page
    pdf.set_xy(10, 180)
    pdf.set_korean_font('B', 14)
    pdf.cell(277, 10, '테스트 결과', 0, 1, 'L')

    # Table headers
    header_h = 10
    pdf.set_fill_color(245, 245, 245)
    pdf.set_korean_font('B', 11)
    pdf.cell(60, header_h, '테스트', 1, 0, 'C', True)
    pdf.cell(70, header_h, '결과', 1, 0, 'C', True)
    pdf.cell(60, header_h, '등급', 1, 0, 'C', True)
    pdf.cell(87, header_h, '비고', 1, 1, 'C', True)
    pdf.set_korean_font('', 10)

    # Table rows - Refactored to use a helper function
    row_h = 10

    def render_test_row(test_name: str, score_text: str, rating_text: str, notes: str, fill: bool = False) -> None:
        """Helper function to render a test result row in the PDF table"""
        if fill:
            pdf.set_fill_color(249, 249, 249)
        pdf.cell(60, row_h, test_name, 1, 0, 'L', fill)
        pdf.cell(70, row_h, score_text, 1, 0, 'L', fill)
        pdf.cell(60, row_h, rating_text, 1, 0, 'L', fill)
        pdf.cell(87, row_h, notes[:30], 1, 1, 'L', fill)

    # 1. Overhead Squat
    squat_quality = ["통증 발생", "수행 불가능", "보상 동작 관찰됨", "완벽한 동작"]
    overhead_squat_score = assessment_data.get('overhead_squat_score', 0)
    render_test_row(
        '1. 오버헤드 스쿼트', 
        f"{overhead_squat_score}점 / 3점", 
        f"{squat_quality[min(overhead_squat_score, 3)]}", 
        assessment_data.get('overhead_squat_notes', '')
    )

    # 2. Push-up
    push_up_reps = assessment_data.get('push_up_reps', 0)
    push_up_score = assessment_data.get('push_up_score', 1)
    render_test_row(
        '2. 푸시업 테스트', 
        f"{push_up_reps}회", 
        get_score_description(push_up_score, 4), 
        assessment_data.get('push_up_notes', ''),
        True
    )

    # 3. Single Leg Balance
    pdf.cell(60, row_h * 2, '3. 한 발 균형', 1, 0, 'L')
    
    slb_right_open = assessment_data.get('single_leg_balance_right_open', 0)
    slb_left_open = assessment_data.get('single_leg_balance_left_open', 0)
    pdf.cell(70, row_h, f"눈 뜬 상태: R {slb_right_open}초, L {slb_left_open}초", 1, 0, 'L')
    
    avg_balance_open = (slb_right_open + slb_left_open) / 2
    open_rating = "우수" if avg_balance_open > 30 else "보통" if avg_balance_open > 15 else "낮음"
    pdf.cell(60, row_h, open_rating, 1, 0, 'L')
    
    pdf.cell(87, row_h * 2, assessment_data.get('single_leg_balance_notes', '')[:60], 1, 0, 'L')
    pdf.set_xy(10 + 60, pdf.get_y() + row_h)
    
    slb_right_closed = assessment_data.get('single_leg_balance_right_closed', 0)
    slb_left_closed = assessment_data.get('single_leg_balance_left_closed', 0)
    pdf.cell(70, row_h, f"눈 감은 상태: R {slb_right_closed}초, L {slb_left_closed}초", 1, 0, 'L')
    
    avg_balance_closed = (slb_right_closed + slb_left_closed) / 2
    closed_rating = "우수" if avg_balance_closed > 20 else "보통" if avg_balance_closed > 10 else "낮음"
    pdf.cell(60, row_h, closed_rating, 1, 1, 'L')

    # 4. Toe Touch
    toe_touch_distance = assessment_data.get('toe_touch_distance', 0)
    toe_touch_score = assessment_data.get('toe_touch_score', 1)
    render_test_row(
        '4. 발끝 터치 테스트', 
        f"{toe_touch_distance} cm", 
        get_score_description(toe_touch_score, 4), 
        assessment_data.get('toe_touch_notes', ''),
        True
    )

    # Page 2
    pdf.add_page()

    # Header for page 2
    pdf.set_korean_font('B', 14)
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, 10, 277, 15, 'F')
    pdf.cell(277, 15, '더파이브 헬스케어 체력 평가 보고서 - 계속', 0, 1, 'C')
    pdf.line(10, 27, 287, 27)
    pdf.ln(5)

    # Continue table from previous page
    pdf.set_korean_font('', 10)

    # 5. Shoulder Mobility
    mobility_quality = ["통증 발생", "제한적 (>2 주먹)", "보통 (1.5 주먹)", "우수 (<1 주먹)"]
    shoulder_mobility_score = assessment_data.get('shoulder_mobility_score', 0)
    shoulder_mobility_right = assessment_data.get('shoulder_mobility_right', 0)
    shoulder_mobility_left = assessment_data.get('shoulder_mobility_left', 0)
    render_test_row(
        '5. 어깨 가동성', 
        f"R: {shoulder_mobility_right}, L: {shoulder_mobility_left} (주먹 거리)", 
        mobility_quality[min(shoulder_mobility_score, 3)], 
        assessment_data.get('shoulder_mobility_notes', '')
    )

    # 6. Farmer's Carry
    farmers_carry_weight = assessment_data.get('farmers_carry_weight', 0)
    farmers_carry_distance = assessment_data.get('farmers_carry_distance', 0)
    farmers_carry_time = assessment_data.get('farmers_carry_time', 0)
    farmers_carry_score = assessment_data.get('farmers_carry_score', 1)
    render_test_row(
        '6. 파머스 캐리', 
        f"{farmers_carry_weight}kg, {farmers_carry_distance}m, {farmers_carry_time}초", 
        get_score_description(farmers_carry_score, 4), 
        assessment_data.get('farmers_carry_notes', ''),
        True
    )

    # 7. Harvard Step Test
    pdf.cell(60, row_h * 2, '7. 하버드 3분 스텝 테스트', 1, 0, 'L')
    
    step_test_pfi = assessment_data.get('step_test_pfi', 0)
    pdf.cell(70, row_h, f"PFI: {step_test_pfi:.1f}", 1, 0, 'L')
    
    step_test_score = assessment_data.get('step_test_score', 1)
    pdf.cell(60, row_h, get_score_description(step_test_score, 4), 1, 0, 'L')
    
    pdf.cell(87, row_h * 2, assessment_data.get('step_test_notes', '')[:60], 1, 0, 'L')
    pdf.set_xy(10 + 60, pdf.get_y() + row_h)
    
    hr1 = assessment_data.get('step_test_hr1', 0)
    hr2 = assessment_data.get('step_test_hr2', 0)
    hr3 = assessment_data.get('step_test_hr3', 0)
    pdf.cell(70, row_h, f"회복기 심박수: {hr1}/{hr2}/{hr3} bpm", 1, 0, 'L')
    
    pdf.cell(60, row_h, '', 1, 1, 'L')
    pdf.ln(5)

    # Improvement Suggestions
    pdf.set_korean_font('B', 14)
    pdf.cell(277, 10, '개선 제안', 0, 1, 'L')
    pdf.ln(2)

    # 2x2 grid for suggestions
    box_width = 130
    box_height = 40
    pdf.set_korean_font('B', 12)

    # Strength
    pdf.cell(box_width, 8, '근력 및 근지구력', 0, 0, 'L')
    pdf.set_x(10 + box_width + 17)
    # Mobility
    pdf.cell(box_width, 8, '가동성 및 유연성', 0, 1, 'L')

    # Strength box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), box_width, box_height, 'F')
    pdf.set_korean_font('', 10)

    y_pos = pdf.get_y() + 5
    for suggestion in suggestions.get('strength', [])[:3]:  # Limit to 3 suggestions
        pdf.set_xy(15, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    # Mobility box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10 + box_width + 17, pdf.get_y() - box_height, box_width, box_height, 'F')

    y_pos = pdf.get_y() - box_height + 5
    for suggestion in suggestions.get('mobility', [])[:3]:  # Limit to 3 suggestions
        pdf.set_xy(15 + box_width + 17, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    pdf.ln(box_height + 5)

    # Balance
    pdf.set_korean_font('B', 12)
    pdf.cell(box_width, 8, '균형 및 협응성', 0, 0, 'L')
    pdf.set_x(10 + box_width + 17)
    # Cardio
    pdf.cell(box_width, 8, '심폐지구력', 0, 1, 'L')

    # Balance box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), box_width, box_height, 'F')
    pdf.set_korean_font('', 10)

    y_pos = pdf.get_y() + 5
    for suggestion in suggestions.get('balance', [])[:3]:  # Limit to 3 suggestions
        pdf.set_xy(15, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    # Cardio box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10 + box_width + 17, pdf.get_y() - box_height, box_width, box_height, 'F')

    y_pos = pdf.get_y() - box_height + 5
    for suggestion in suggestions.get('cardio', [])[:3]:  # Limit to 3 suggestions
        pdf.set_xy(15 + box_width + 17, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    pdf.ln(box_height + 10)

    # Training Schedule
    pdf.set_korean_font('B', 14)
    pdf.cell(277, 10, '권장 트레이닝 프로그램', 0, 1, 'L')

    # Schedule box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), 277, 50, 'F')

    # Weekly Schedule - Get personalized schedule based on client details and scores
    schedule_items = get_recommended_schedule(client_details, category_scores)

    # Weekly Schedule
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_korean_font('B', 11)
    pdf.cell(100, 5, '주간 스케줄', 0, 1, 'L')
    pdf.set_korean_font('', 10)

    for item in schedule_items:
        pdf.set_x(15)
        pdf.cell(130, 5, item, 0, 1, 'L')
        pdf.ln(3)

    # Intensity - Get personalized intensity recommendations
    intensity_items = get_intensity_recommendations(client_details)

    # Intensity
    pdf.set_xy(160, pdf.get_y() - 35)
    pdf.set_korean_font('B', 11)
    pdf.cell(100, 5, '운동 강도 및 볼륨', 0, 1, 'L')
    pdf.set_korean_font('', 10)

    for item in intensity_items:
        pdf.set_x(160)
        pdf.cell(130, 5, item, 0, 1, 'L')
        pdf.ln(3)

    pdf.ln(5)

    # Notes and Follow-up Section (2 columns)
    # Trainer notes
    pdf.set_korean_font('B', 12)
    pdf.cell(170, 8, '트레이너 메모', 0, 0, 'L')
    pdf.set_x(190)
    pdf.cell(97, 8, '후속 일정', 0, 1, 'L')

    # Notes box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), 170, 30, 'F')
    pdf.set_korean_font('', 9)
    pdf.set_xy(15, pdf.get_y() + 5)

    # Split notes into multiple lines if needed
    notes = assessment_data.get('overhead_squat_notes', '')
    if notes:
        max_chars = 80
        for i in range(0, len(notes), max_chars):
            pdf.set_x(15)
            pdf.cell(160, 5, notes[i:i + max_chars], 0, 1, 'L')

    # Follow-up box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(190, pdf.get_y() - 25, 97, 30, 'F')
    pdf.set_korean_font('', 10)
    pdf.set_xy(195, pdf.get_y() - 20)
    
    # Calculate next assessment dates based on current date
    from datetime import datetime, timedelta
    current_date = datetime.strptime(assessment_data.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
    
    followup_date = current_date + timedelta(days=30)
    next_assessment_date = current_date + timedelta(days=60)
    
    pdf.cell(87, 5, f'중간 점검: {followup_date.strftime("%Y년 %m월 %d일")}', 0, 1, 'L')
    pdf.set_x(195)
    pdf.cell(87, 5, f'다음 평가: {next_assessment_date.strftime("%Y년 %m월 %d일")}', 0, 1, 'L')

    # Footer for both pages
    for i in range(1, pdf.page + 1):
        pdf.set_page(i)
        pdf.set_xy(10, 195)
        pdf.set_korean_font('', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f'더파이브 헬스케어 체력 평가 보고서 - {i}/2', 0, 0, 'C')

    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin1')  # For binary output


def get_pdf_download_link(pdf_bytes: bytes, filename: str, text: str) -> str:
    """
    Generate a download link for the PDF report
    
    Args:
        pdf_bytes: PDF content as bytes
        filename: Name for the downloaded file
        text: Link text to display
        
    Returns:
        str: HTML download link
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href