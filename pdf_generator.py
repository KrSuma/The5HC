# pdf_generator.py - Functions for generating PDF reports

import io
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import base64
from recommendations import get_recommended_schedule, get_intensity_recommendations
from assessment_scoring import get_score_description


def create_radar_chart_for_pdf(category_scores):
    """Create a radar chart of fitness category scores for PDF inclusion"""
    # Convert scores to percentages
    strength_pct = category_scores['strength_score'] / 25 * 100
    mobility_pct = category_scores['mobility_score'] / 25 * 100
    balance_pct = category_scores['balance_score'] / 25 * 100
    cardio_pct = category_scores['cardio_score'] / 25 * 100

    # Create figure
    fig = plt.figure(figsize = (4, 4))
    ax = fig.add_subplot(111, polar = True)

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
    ax.plot(angles, values, linewidth = 2, linestyle = 'solid', color = '#ff4b4b')
    ax.fill(angles, values, alpha = 0.25, color = '#ff4b4b')

    # Draw circular gridlines
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)

    # Set y-axis limits
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], color = 'gray', fontsize = 8)

    # Remove grid and spines
    ax.grid(True, alpha = 0.3)
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
    plt.savefig(img_buffer, format = 'png', bbox_inches = 'tight', dpi = 150)
    img_buffer.seek(0)
    plt.close()

    return img_buffer


def create_pdf_report(client_details, assessment_data, category_scores, suggestions):
    """Create a PDF report with assessment results in landscape format without images"""
    pdf = FPDF(orientation = 'L', format = 'A4')  # Landscape orientation
    pdf.add_page()

    # Set margin
    pdf.set_margin(10)

    # Set up fonts
    pdf.add_font('NanumGothic', '', 'NanumGothic.ttf', uni = True)  # Korean font
    pdf.add_font('NanumGothicBold', '', 'NanumGothicBold.ttf', uni = True)  # Korean bold font

    # Title
    pdf.set_font('NanumGothicBold', '', 18)
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, 10, 277, 20, 'F')
    pdf.cell(277, 20, '더파이브 헬스케어 체력 평가 보고서', 0, 1, 'C')
    pdf.line(10, 32, 287, 32)
    pdf.ln(5)

    # Left side - Client Info and Category Scores
    # Client Information
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(120, 10, '회원 정보', 0, 1, 'L')
    pdf.set_font('NanumGothic', '', 11)

    pdf.cell(20, 8, '이름:', 0, 0, 'L')
    pdf.cell(100, 8, client_details['name'], 0, 1, 'L')

    pdf.cell(20, 8, '나이:', 0, 0, 'L')
    pdf.cell(100, 8, str(client_details['age']), 0, 1, 'L')

    pdf.cell(20, 8, '성별:', 0, 0, 'L')
    pdf.cell(100, 8, client_details['gender'], 0, 1, 'L')

    pdf.cell(20, 8, '평가일:', 0, 0, 'L')
    pdf.cell(100, 8, assessment_data['date'], 0, 1, 'L')

    pdf.ln(5)

    # Category Scores
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(120, 10, '카테고리 점수', 0, 1, 'L')
    pdf.set_font('NanumGothic', '', 11)

    # Function to draw progress bar
    def draw_progress_bar(y_position, score, max_score = 25):
        bar_width = 80
        progress = score / max_score
        pdf.set_draw_color(220, 220, 220)
        pdf.set_fill_color(220, 220, 220)
        pdf.rect(30, y_position, bar_width, 4, 'F')
        pdf.set_fill_color(255, 75, 75)
        pdf.rect(30, y_position, bar_width * progress, 4, 'F')

    # Strength
    pdf.cell(60, 8, '근력 및 근지구력:', 0, 0, 'L')
    pdf.cell(20, 8, f"{category_scores['strength_score']:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(category_scores['strength_score'], 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), category_scores['strength_score'])
    pdf.ln(8)

    # Mobility
    pdf.cell(60, 8, '가동성 및 유연성:', 0, 0, 'L')
    pdf.cell(20, 8, f"{category_scores['mobility_score']:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(category_scores['mobility_score'], 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), category_scores['mobility_score'])
    pdf.ln(8)

    # Balance
    pdf.cell(60, 8, '균형 및 협응성:', 0, 0, 'L')
    pdf.cell(20, 8, f"{category_scores['balance_score']:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(category_scores['balance_score'], 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), category_scores['balance_score'])
    pdf.ln(8)

    # Cardio
    pdf.cell(60, 8, '심폐지구력:', 0, 0, 'L')
    pdf.cell(20, 8, f"{category_scores['cardio_score']:.1f}/25", 0, 0, 'L')
    pdf.cell(40, 8, get_score_description(category_scores['cardio_score'], 25), 0, 1, 'L')
    draw_progress_bar(pdf.get_y(), category_scores['cardio_score'])

    # Right side - Overall Score and Radar Chart
    pdf.set_xy(140, 40)

    # Overall Score
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(120, 10, '종합 체력 점수', 0, 1, 'L')
    pdf.set_xy(140, 55)
    pdf.set_font('NanumGothicBold', '', 26)
    pdf.set_text_color(255, 75, 75)
    pdf.cell(60, 15, f"{category_scores['overall_score']:.1f}/100", 0, 0, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('NanumGothicBold', '', 18)
    pdf.cell(60, 15, get_score_description(category_scores['overall_score']), 0, 1, 'L')

    # Radar Chart
    radar_chart = create_radar_chart_for_pdf(category_scores)
    pdf.image(radar_chart, x = 140, y = 85, w = 120, h = 90)

    # Test Results - Top half of page
    pdf.set_xy(10, 180)
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(277, 10, '테스트 결과', 0, 1, 'L')

    # Table headers
    header_h = 10
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('NanumGothicBold', '', 11)
    pdf.cell(60, header_h, '테스트', 1, 0, 'C', True)
    pdf.cell(70, header_h, '결과', 1, 0, 'C', True)
    pdf.cell(60, header_h, '등급', 1, 0, 'C', True)
    pdf.cell(87, header_h, '비고', 1, 1, 'C', True)
    pdf.set_font('NanumGothic', '', 10)

    # Table rows
    row_h = 10

    # 1. Overhead Squat
    squat_quality = ["통증 발생", "수행 불가능", "보상 동작 관찰됨", "완벽한 동작"]
    pdf.cell(60, row_h, '1. 오버헤드 스쿼트', 1, 0, 'L')
    pdf.cell(70, row_h, f"{assessment_data['overhead_squat_score']}점 / 3점", 1, 0, 'L')
    pdf.cell(60, row_h, f"{squat_quality[assessment_data['overhead_squat_score']]}", 1, 0, 'L')
    pdf.cell(87, row_h, assessment_data['overhead_squat_notes'][:30], 1, 1, 'L')

    # 2. Push-up
    pdf.set_fill_color(249, 249, 249)
    pdf.cell(60, row_h, '2. 푸시업 테스트', 1, 0, 'L', True)
    pdf.cell(70, row_h, f"{assessment_data['push_up_reps']}회", 1, 0, 'L', True)
    pdf.cell(60, row_h, get_score_description(assessment_data['push_up_score'], 4), 1, 0, 'L', True)
    pdf.cell(87, row_h, assessment_data['push_up_notes'][:30], 1, 1, 'L', True)

    # 3. Single Leg Balance
    pdf.cell(60, row_h * 2, '3. 한 발 균형', 1, 0, 'L')
    pdf.cell(70, row_h,
             f"눈 뜬 상태: R {assessment_data['single_leg_balance_right_open']}초, L {assessment_data['single_leg_balance_left_open']}초",
             1, 0, 'L')
    avg_balance_open = (assessment_data['single_leg_balance_right_open'] + assessment_data[
        'single_leg_balance_left_open']) / 2
    open_rating = "우수" if avg_balance_open > 30 else "보통" if avg_balance_open > 15 else "낮음"
    pdf.cell(60, row_h, open_rating, 1, 0, 'L')
    pdf.cell(87, row_h * 2, assessment_data['single_leg_balance_notes'][:60], 1, 0, 'L')
    pdf.set_xy(10 + 60, pdf.get_y() + row_h)
    pdf.cell(70, row_h,
             f"눈 감은 상태: R {assessment_data['single_leg_balance_right_closed']}초, L {assessment_data['single_leg_balance_left_closed']}초",
             1, 0, 'L')
    avg_balance_closed = (assessment_data['single_leg_balance_right_closed'] + assessment_data[
        'single_leg_balance_left_closed']) / 2
    closed_rating = "우수" if avg_balance_closed > 20 else "보통" if avg_balance_closed > 10 else "낮음"
    pdf.cell(60, row_h, closed_rating, 1, 1, 'L')

    # 4. Toe Touch
    pdf.set_fill_color(249, 249, 249)
    pdf.cell(60, row_h, '4. 발끝 터치 테스트', 1, 0, 'L', True)
    pdf.cell(70, row_h, f"{assessment_data['toe_touch_distance']} cm", 1, 0, 'L', True)
    pdf.cell(60, row_h, get_score_description(assessment_data['toe_touch_score'], 4), 1, 0, 'L', True)
    pdf.cell(87, row_h, assessment_data['toe_touch_notes'][:30], 1, 1, 'L', True)

    # Page 2
    pdf.add_page()

    # Header for page 2
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, 10, 277, 15, 'F')
    pdf.cell(277, 15, '더파이브 헬스케어 체력 평가 보고서 - 계속', 0, 1, 'C')
    pdf.line(10, 27, 287, 27)
    pdf.ln(5)

    # Continue table from previous page
    pdf.set_font('NanumGothic', '', 10)

    # 5. Shoulder Mobility
    mobility_quality = ["통증 발생", "제한적 (>2 주먹)", "보통 (1.5 주먹)", "우수 (<1 주먹)"]
    pdf.cell(60, row_h, '5. 어깨 가동성', 1, 0, 'L')
    pdf.cell(70, row_h,
             f"R: {assessment_data['shoulder_mobility_right']}, L: {assessment_data['shoulder_mobility_left']} (주먹 거리)",
             1, 0, 'L')
    pdf.cell(60, row_h, mobility_quality[assessment_data['shoulder_mobility_score']], 1, 0, 'L')
    pdf.cell(87, row_h, assessment_data['shoulder_mobility_notes'][:30], 1, 1, 'L')

    # 6. Farmer's Carry
    pdf.set_fill_color(249, 249, 249)
    pdf.cell(60, row_h, '6. 파머스 캐리', 1, 0, 'L', True)
    pdf.cell(70, row_h,
             f"{assessment_data['farmers_carry_weight']}kg, {assessment_data['farmers_carry_distance']}m, {assessment_data['farmers_carry_time']}초",
             1, 0, 'L', True)
    pdf.cell(60, row_h, get_score_description(assessment_data['farmers_carry_score'], 4), 1, 0, 'L', True)
    pdf.cell(87, row_h, assessment_data['farmers_carry_notes'][:30], 1, 1, 'L', True)

    # 7. Harvard Step Test
    pdf.cell(60, row_h * 2, '7. 하버드 3분 스텝 테스트', 1, 0, 'L')
    pdf.cell(70, row_h, f"PFI: {assessment_data['step_test_pfi']:.1f}", 1, 0, 'L')
    pdf.cell(60, row_h, get_score_description(assessment_data['step_test_score'], 4), 1, 0, 'L')
    pdf.cell(87, row_h * 2, assessment_data['step_test_notes'][:60], 1, 0, 'L')
    pdf.set_xy(10 + 60, pdf.get_y() + row_h)
    pdf.cell(70, row_h,
             f"회복기 심박수: {assessment_data['step_test_hr1']}/{assessment_data['step_test_hr2']}/{assessment_data['step_test_hr3']} bpm",
             1, 0, 'L')
    pdf.cell(60, row_h, '', 1, 1, 'L')
    pdf.ln(5)

    # Improvement Suggestions
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(277, 10, '개선 제안', 0, 1, 'L')
    pdf.ln(2)

    # 2x2 grid for suggestions
    box_width = 130
    box_height = 40
    pdf.set_font('NanumGothicBold', '', 12)

    # Strength
    pdf.cell(box_width, 8, '근력 및 근지구력', 0, 0, 'L')
    pdf.set_x(10 + box_width + 17)
    # Mobility
    pdf.cell(box_width, 8, '가동성 및 유연성', 0, 1, 'L')

    # Strength box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), box_width, box_height, 'F')
    pdf.set_font('NanumGothic', '', 10)

    y_pos = pdf.get_y() + 5
    for suggestion in suggestions['strength']:
        pdf.set_xy(15, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    # Mobility box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10 + box_width + 17, pdf.get_y() - box_height, box_width, box_height, 'F')

    y_pos = pdf.get_y() - box_height + 5
    for suggestion in suggestions['mobility']:
        pdf.set_xy(15 + box_width + 17, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    pdf.ln(box_height + 5)

    # Balance
    pdf.set_font('NanumGothicBold', '', 12)
    pdf.cell(box_width, 8, '균형 및 협응성', 0, 0, 'L')
    pdf.set_x(10 + box_width + 17)
    # Cardio
    pdf.cell(box_width, 8, '심폐지구력', 0, 1, 'L')

    # Balance box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), box_width, box_height, 'F')
    pdf.set_font('NanumGothic', '', 10)

    y_pos = pdf.get_y() + 5
    for suggestion in suggestions['balance']:
        pdf.set_xy(15, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    # Cardio box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10 + box_width + 17, pdf.get_y() - box_height, box_width, box_height, 'F')

    y_pos = pdf.get_y() - box_height + 5
    for suggestion in suggestions['cardio']:
        pdf.set_xy(15 + box_width + 17, y_pos)
        pdf.cell(box_width - 10, 5, f"• {suggestion}", 0, 1, 'L')
        y_pos += 8

    pdf.ln(box_height + 10)

    # Training Schedule
    pdf.set_font('NanumGothicBold', '', 14)
    pdf.cell(277, 10, '권장 트레이닝 프로그램', 0, 1, 'L')

    # Schedule box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), 277, 50, 'F')

    # Weekly Schedule
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('NanumGothicBold', '', 11)
    pdf.cell(100, 5, '주간 스케줄', 0, 1, 'L')
    pdf.set_font('NanumGothic', '', 10)

    schedule_items = get_recommended_schedule()

    for item in schedule_items:
        pdf.set_x(15)
        pdf.cell(130, 5, item, 0, 1, 'L')
        pdf.ln(3)

    # Intensity
    pdf.set_xy(160, pdf.get_y() - 35)
    pdf.set_font('NanumGothicBold', '', 11)
    pdf.cell(100, 5, '운동 강도 및 볼륨', 0, 1, 'L')
    pdf.set_font('NanumGothic', '', 10)

    intensity_items = get_intensity_recommendations()

    for item in intensity_items:
        pdf.set_x(160)
        pdf.cell(130, 5, item, 0, 1, 'L')
        pdf.ln(3)

    pdf.ln(5)

    # Notes and Follow-up Section (2 columns)
    # Trainer notes
    pdf.set_font('NanumGothicBold', '', 12)
    pdf.cell(170, 8, '트레이너 메모', 0, 0, 'L')
    pdf.set_x(190)
    pdf.cell(97, 8, '후속 일정', 0, 1, 'L')

    # Notes box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(10, pdf.get_y(), 170, 30, 'F')
    pdf.set_font('NanumGothic', '', 9)
    pdf.set_xy(15, pdf.get_y() + 5)

    # Split notes into multiple lines if needed
    if assessment_data['overhead_squat_notes']:
        notes = assessment_data['overhead_squat_notes']
        max_chars = 80
        for i in range(0, len(notes), max_chars):
            pdf.set_x(15)
            pdf.cell(160, 5, notes[i:i + max_chars], 0, 1, 'L')

    # Follow-up box
    pdf.set_fill_color(249, 249, 249)
    pdf.rect(190, pdf.get_y() - 25, 97, 30, 'F')
    pdf.set_font('NanumGothic', '', 10)
    pdf.set_xy(195, pdf.get_y() - 20)
    pdf.cell(87, 5, '중간 점검: 2025년 6월 25일', 0, 1, 'L')
    pdf.set_x(195)
    pdf.cell(87, 5, '다음 평가: 2025년 8월 10일', 0, 1, 'L')

    # Footer for both pages
    for i in range(1, pdf.page + 1):
        pdf.set_page(i)
        pdf.set_xy(10, 195)
        pdf.set_font('NanumGothic', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f'더파이브 헬스케어 체력 평가 보고서 - {i}/2', 0, 0, 'C')

    # Return PDF as bytes
    return pdf.output(dest = 'S').encode('latin1')  # For binary output


def get_pdf_download_link(pdf_bytes, filename, text):
    """Generate a download link for the PDF report"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href