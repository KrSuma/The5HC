# html_report_generator.py - Functions for generating HTML reports matching the sample design

import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

from src.core.scoring import get_score_description
from src.core.recommendations import get_improvement_suggestions


def create_html_report(client_details: Dict[str, Any], 
                      assessment_data: Dict[str, Any], 
                      category_scores: Dict[str, float], 
                      suggestions: Dict[str, List[str]],
                      trainer_name: str = "트레이너") -> str:
    """
    Create an HTML report matching the sample design
    
    Args:
        client_details: Dictionary with client information
        assessment_data: Dictionary with assessment data
        category_scores: Dictionary with category scores
        suggestions: Dictionary with improvement suggestions
        trainer_name: Name of the trainer conducting the assessment
        
    Returns:
        str: Complete HTML report as string
    """
    
    # Calculate BMI
    height_m = client_details.get('height', 170) / 100
    weight = client_details.get('weight', 70)
    bmi = round(weight / (height_m ** 2), 1)
    
    # Overall score and rating
    overall_score = category_scores.get('overall_score', 0)
    overall_rating = get_score_description(overall_score)
    
    # Individual category scores
    strength_score = category_scores.get('strength_score', 0)
    mobility_score = category_scores.get('mobility_score', 0)
    balance_score = category_scores.get('balance_score', 0)
    cardio_score = category_scores.get('cardio_score', 0)
    
    # Calculate progress bar percentages
    strength_pct = min(100, max(0, (strength_score / 25) * 100))
    mobility_pct = min(100, max(0, (mobility_score / 25) * 100))
    balance_pct = min(100, max(0, (balance_score / 25) * 100))
    cardio_pct = min(100, max(0, (cardio_score / 25) * 100))
    
    # Parse assessment data for test results
    test_results = _extract_test_results(assessment_data)
    
    # Generate improvement suggestions by category
    suggestion_sections = _format_suggestions(suggestions)
    
    # Generate training program
    training_program = _generate_training_program(client_details, category_scores)
    
    # Calculate follow-up dates
    assessment_date = assessment_data.get('date', datetime.now().strftime("%Y-%m-%d"))
    try:
        current_date = datetime.strptime(assessment_date, "%Y-%m-%d")
        intermediate_check = current_date + timedelta(days=45)
        next_assessment = current_date + timedelta(days=90)
    except:
        current_date = datetime.now()
        intermediate_check = current_date + timedelta(days=45)
        next_assessment = current_date + timedelta(days=90)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>더파이브 헬스케어 체력 평가 보고서</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans KR', sans-serif;
            line-height: 1.2;
            color: #333;
            background: white;
            font-size: 10px;
        }}

        .page {{
            width: 210mm;
            height: 297mm;
            margin: 0 auto;
            padding: 10mm;
            background: white;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            position: relative;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: center;
            border-radius: 6px;
            margin-bottom: 12px;
        }}

        .header h1 {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 3px;
        }}

        .header p {{
            font-size: 11px;
            opacity: 0.9;
        }}

        .top-section {{
            display: grid;
            grid-template-columns: 1fr 1fr 120px;
            gap: 12px;
            margin-bottom: 12px;
        }}

        .section {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}

        .section h2 {{
            color: #667eea;
            margin-bottom: 8px;
            font-size: 12px;
            font-weight: 600;
        }}

        .client-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
            font-size: 9px;
        }}

        .info-item {{
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
            border-bottom: 1px solid #e9ecef;
        }}

        .info-label {{
            font-weight: 500;
            color: #6c757d;
        }}

        .info-value {{
            font-weight: 600;
            color: #343a40;
        }}

        .overall-score {{
            text-align: center;
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
            color: white;
            padding: 15px 8px;
            border-radius: 6px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .score-number {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 3px;
        }}

        .score-rating {{
            font-size: 11px;
            font-weight: 500;
        }}

        .category-scores {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .category-item {{
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}

        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 9px;
        }}

        .category-name {{
            font-weight: 600;
            color: #495057;
        }}

        .category-value {{
            font-weight: 700;
            color: #667eea;
        }}

        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 3px;
        }}

        .radar-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .radar-chart {{
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            border: 2px solid #667eea;
            margin-top: 8px;
        }}

        .chart-center {{
            width: 40px;
            height: 40px;
            background: #667eea;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 7px;
            text-align: center;
        }}

        .test-images {{
            margin-bottom: 10px;
        }}

        .image-placeholder {{
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            height: 150px;
        }}

        .placeholder-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
            height: 100%;
            align-items: center;
        }}

        .placeholder-item {{
            background: white;
            padding: 8px;
            border-radius: 6px;
            font-size: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
            color: #495057;
            font-weight: 500;
            height: 80px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}

        .test-results {{
            margin-bottom: 10px;
        }}

        .test-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            font-size: 8px;
        }}

        .test-table th {{
            background: #667eea;
            color: white;
            padding: 6px 4px;
            text-align: left;
            font-weight: 600;
            font-size: 9px;
        }}

        .test-table td {{
            padding: 4px;
            border-bottom: 1px solid #e9ecef;
            vertical-align: top;
        }}

        .test-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .grade-excellent {{ color: #28a745; font-weight: 600; }}
        .grade-good {{ color: #17a2b8; font-weight: 600; }}
        .grade-average {{ color: #ffc107; font-weight: 600; }}
        .grade-needs-improvement {{ color: #dc3545; font-weight: 600; }}

        .bottom-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 8px;
        }}

        .suggestions-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 8px;
        }}

        .suggestion-box {{
            background: white;
            padding: 8px;
            border-radius: 4px;
            border-left: 2px solid #667eea;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .suggestion-box h3 {{
            color: #667eea;
            margin-bottom: 5px;
            font-size: 9px;
            font-weight: 600;
        }}

        .suggestion-box ul {{
            list-style: none;
            padding: 0;
            font-size: 8px;
        }}

        .suggestion-box li {{
            padding: 1px 0;
            position: relative;
            padding-left: 10px;
            line-height: 1.2;
        }}

        .suggestion-box li:before {{
            content: "•";
            color: #667eea;
            position: absolute;
            left: 0;
            font-weight: bold;
        }}

        .training-program {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 10px;
            border-radius: 6px;
        }}

        .training-program h2 {{
            color: white;
            margin-bottom: 8px;
            font-size: 12px;
        }}

        .program-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}

        .program-box {{
            background: rgba(255,255,255,0.1);
            padding: 8px;
            border-radius: 4px;
            backdrop-filter: blur(10px);
        }}

        .program-box h3 {{
            margin-bottom: 5px;
            font-size: 9px;
        }}

        .program-box ul {{
            list-style: none;
            padding: 0;
            font-size: 8px;
        }}

        .program-box li {{
            padding: 1px 0;
            padding-left: 8px;
            position: relative;
            line-height: 1.1;
        }}

        .program-box li:before {{
            content: "→";
            position: absolute;
            left: 0;
            font-size: 7px;
        }}

        .footer {{
            position: absolute;
            bottom: 8mm;
            left: 10mm;
            right: 10mm;
            background: #343a40;
            color: white;
            text-align: center;
            padding: 5px;
            font-size: 7px;
            border-radius: 3px;
        }}

        @media print {{
            body {{ background: white; }}
            .page {{ box-shadow: none; margin: 0; }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="header">
            <h1>더파이브 헬스케어</h1>
            <p>체력 평가 보고서</p>
        </div>

        <div class="top-section">
            <div class="section">
                <h2>회원 정보</h2>
                <div class="client-info">
                    <div class="info-item">
                        <span class="info-label">이름:</span>
                        <span class="info-value">{client_details.get('name', 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">나이:</span>
                        <span class="info-value">{client_details.get('age', 'N/A')}세</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">성별:</span>
                        <span class="info-value">{client_details.get('gender', 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">키:</span>
                        <span class="info-value">{client_details.get('height', 'N/A')}cm</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">체중:</span>
                        <span class="info-value">{client_details.get('weight', 'N/A')}kg</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">BMI:</span>
                        <span class="info-value">{bmi}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">평가일:</span>
                        <span class="info-value">{assessment_date}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">트레이너:</span>
                        <span class="info-value">{trainer_name}</span>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>카테고리별 점수</h2>
                <div class="category-scores">
                    <div class="category-item">
                        <div class="category-header">
                            <span class="category-name">근력/근지구력</span>
                            <span class="category-value">{strength_score:.1f}/25</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {strength_pct:.0f}%"></div>
                        </div>
                    </div>

                    <div class="category-item">
                        <div class="category-header">
                            <span class="category-name">가동성/유연성</span>
                            <span class="category-value">{mobility_score:.1f}/25</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {mobility_pct:.0f}%"></div>
                        </div>
                    </div>

                    <div class="category-item">
                        <div class="category-header">
                            <span class="category-name">균형/협응성</span>
                            <span class="category-value">{balance_score:.1f}/25</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {balance_pct:.0f}%"></div>
                        </div>
                    </div>

                    <div class="category-item">
                        <div class="category-header">
                            <span class="category-name">심폐지구력</span>
                            <span class="category-value">{cardio_score:.1f}/25</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {cardio_pct:.0f}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="radar-section">
                <div class="overall-score">
                    <div class="score-number">{overall_score:.1f}</div>
                    <div class="score-rating">{overall_rating}</div>
                </div>
                <div class="radar-chart">
                    <div class="chart-center">체력<br>균형</div>
                </div>
            </div>
        </div>

        <div class="test-images">
            <div class="section">
                <h2>테스트 이미지</h2>
                <div class="image-placeholder">
                    <div class="placeholder-grid">
                        <div class="placeholder-item">오버헤드<br>스쿼트</div>
                        <div class="placeholder-item">푸시업</div>
                        <div class="placeholder-item">한발<br>균형</div>
                        <div class="placeholder-item">발끝<br>터치</div>
                        <div class="placeholder-item">어깨<br>가동성</div>
                        <div class="placeholder-item">파머스<br>캐리</div>
                        <div class="placeholder-item">하버드<br>스텝</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="test-results">
            <div class="section">
                <h2>테스트 결과</h2>
                <table class="test-table">
                    <thead>
                        <tr>
                            <th style="width: 20%">테스트</th>
                            <th style="width: 25%">결과</th>
                            <th style="width: 12%">등급</th>
                            <th style="width: 43%">비고</th>
                        </tr>
                    </thead>
                    <tbody>
                        {test_results}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="bottom-section">
            <div class="section">
                <h2>개선 제안</h2>
                <div class="suggestions-grid">
                    {suggestion_sections}
                </div>
            </div>

            <div class="training-program">
                <h2>권장 트레이닝 프로그램</h2>
                <div class="program-grid">
                    {training_program}
                </div>
            </div>
        </div>

        <div class="footer">
            더파이브 헬스케어 | 다음 평가: {next_assessment.strftime("%Y-%m-%d")} | 중간점검: {intermediate_check.strftime("%Y-%m-%d")} | 문의: 02-1234-5678
        </div>
    </div>
</body>
</html>"""
    
    return html_content


def _extract_test_results(assessment_data: Dict[str, Any]) -> str:
    """Extract and format test results for the HTML table"""
    
    results = []
    
    # 1. Overhead Squat
    squat_quality = ["통증 발생", "수행 불가능", "보상 동작 관찰됨", "완벽한 동작"]
    overhead_squat_score = int(assessment_data.get('overhead_squat_score', 0))
    squat_grade_class = _get_grade_class(overhead_squat_score, 3)
    
    results.append(f"""
        <tr>
            <td>오버헤드 스쿼트</td>
            <td>{overhead_squat_score}점/3점</td>
            <td><span class="{squat_grade_class}">{squat_quality[min(overhead_squat_score, 3)]}</span></td>
            <td>{assessment_data.get('overhead_squat_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 2. Push-up
    push_up_reps = int(assessment_data.get('push_up_reps', 0))
    push_up_score = int(assessment_data.get('push_up_score', 1))
    pushup_grade_class = _get_grade_class(push_up_score, 4)
    
    results.append(f"""
        <tr>
            <td>푸시업</td>
            <td>{push_up_reps}회</td>
            <td><span class="{pushup_grade_class}">{get_score_description(push_up_score, 4)}</span></td>
            <td>{assessment_data.get('push_up_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 3. Single Leg Balance
    right_open = assessment_data.get('single_leg_balance_right_eyes_open', 0)
    left_open = assessment_data.get('single_leg_balance_left_eyes_open', 0)
    right_closed = assessment_data.get('single_leg_balance_right_eyes_closed', 0)
    left_closed = assessment_data.get('single_leg_balance_left_eyes_closed', 0)
    
    avg_balance = (right_open + left_open + right_closed + left_closed) / 4
    balance_rating = "우수" if avg_balance > 25 else "좋음" if avg_balance > 15 else "보통" if avg_balance > 8 else "낮음"
    balance_grade_class = "grade-excellent" if avg_balance > 25 else "grade-good" if avg_balance > 15 else "grade-average" if avg_balance > 8 else "grade-needs-improvement"
    
    results.append(f"""
        <tr>
            <td>한발 균형</td>
            <td>눈뜸: {(right_open + left_open)/2:.0f}초<br>눈감음: {(right_closed + left_closed)/2:.0f}초</td>
            <td><span class="{balance_grade_class}">{balance_rating}</span></td>
            <td>{assessment_data.get('single_leg_balance_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 4. Toe Touch
    toe_touch_distance = assessment_data.get('toe_touch_distance', 0)
    toe_touch_score = int(assessment_data.get('toe_touch_score', 1))
    toe_touch_grade_class = _get_grade_class(toe_touch_score, 4)
    
    results.append(f"""
        <tr>
            <td>발끝 터치</td>
            <td>{toe_touch_distance}cm (바닥기준)</td>
            <td><span class="{toe_touch_grade_class}">{get_score_description(toe_touch_score, 4)}</span></td>
            <td>{assessment_data.get('toe_touch_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 5. Shoulder Mobility
    mobility_quality = ["통증 발생", "제한적 (>2 주먹)", "보통 (1.5 주먹)", "우수 (<1 주먹)"]
    shoulder_right = assessment_data.get('shoulder_mobility_right', 0)
    shoulder_left = assessment_data.get('shoulder_mobility_left', 0)
    shoulder_score = int(assessment_data.get('shoulder_mobility_score', 0))
    shoulder_grade_class = _get_grade_class(shoulder_score, 3)
    
    results.append(f"""
        <tr>
            <td>어깨 가동성</td>
            <td>우{shoulder_right}, 좌{shoulder_left} 주먹거리</td>
            <td><span class="{shoulder_grade_class}">{mobility_quality[min(shoulder_score, 3)]}</span></td>
            <td>{assessment_data.get('shoulder_mobility_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 6. Farmer's Carry
    farmers_weight = assessment_data.get('farmer_carry_weight', 0)
    farmers_distance = assessment_data.get('farmer_carry_distance', 0)
    
    # Extract time from notes if available
    fc_notes = assessment_data.get('farmer_carry_notes', '')
    time_match = re.search(r'(\d+)초', fc_notes)
    fc_time = int(time_match.group(1)) if time_match else 0
    
    farmers_score = assessment_data.get('strength_score', 0)
    farmers_rating = get_score_description(int(farmers_score/6.25), 4) if farmers_score > 0 else "보통"
    farmers_grade_class = _get_grade_class(int(farmers_score/6.25), 4) if farmers_score > 0 else "grade-average"
    
    results.append(f"""
        <tr>
            <td>파머스 캐리</td>
            <td>{farmers_weight}kg, {farmers_distance}m, {fc_time}초</td>
            <td><span class="{farmers_grade_class}">{farmers_rating}</span></td>
            <td>{assessment_data.get('farmer_carry_notes', '')[:50]}</td>
        </tr>
    """)
    
    # 7. Harvard Step Test
    notes = assessment_data.get('harvard_step_test_notes', '')
    pfi_match = re.search(r'PFI:\s*([0-9.]+)', notes)
    pfi = float(pfi_match.group(1)) if pfi_match else 0.0
    
    step_score = assessment_data.get('cardio_score', 0)
    step_rating = get_score_description(int(step_score/6.25), 4) if step_score > 0 else "보통"
    step_grade_class = _get_grade_class(int(step_score/6.25), 4) if step_score > 0 else "grade-average"
    
    results.append(f"""
        <tr>
            <td>하버드 스텝</td>
            <td>PFI: {pfi:.1f}</td>
            <td><span class="{step_grade_class}">{step_rating}</span></td>
            <td>{assessment_data.get('harvard_step_test_notes', '')[:50]}</td>
        </tr>
    """)
    
    return ''.join(results)


def _get_grade_class(score: int, max_score: int) -> str:
    """Get CSS class for grade based on score"""
    percentage = (score / max_score) * 100
    
    if percentage >= 80:
        return "grade-excellent"
    elif percentage >= 65:
        return "grade-good"
    elif percentage >= 50:
        return "grade-average"
    else:
        return "grade-needs-improvement"


def _format_suggestions(suggestions: Dict[str, List[str]]) -> str:
    """Format improvement suggestions into HTML"""
    
    categories = {
        'strength': '근력',
        'mobility': '가동성', 
        'balance': '균형',
        'cardio': '심폐'
    }
    
    suggestion_boxes = []
    
    for category, title in categories.items():
        category_suggestions = suggestions.get(category, [])
        
        if not category_suggestions:
            category_suggestions = [f"{title} 수준이 양호합니다", "현재 트레이닝을 계속하세요"]
        
        # Limit to 3 suggestions
        category_suggestions = category_suggestions[:3]
        
        suggestion_list = ''.join([f"<li>{suggestion}</li>" for suggestion in category_suggestions])
        
        suggestion_boxes.append(f"""
            <div class="suggestion-box">
                <h3>{title}</h3>
                <ul>
                    {suggestion_list}
                </ul>
            </div>
        """)
    
    return ''.join(suggestion_boxes)


def _generate_training_program(client_details: Dict[str, Any], category_scores: Dict[str, float]) -> str:
    """Generate personalized training program based on assessment"""
    
    age = client_details.get('age', 30)
    
    # Determine focus areas based on lowest scores
    strength_score = category_scores.get('strength_score', 15)
    mobility_score = category_scores.get('mobility_score', 15)
    balance_score = category_scores.get('balance_score', 15)
    cardio_score = category_scores.get('cardio_score', 15)
    
    # Weekly schedule
    if strength_score < 15:
        schedule = [
            "월: 전신근력 + 코어",
            "화: 유산소 + 가동성",
            "수: 하체근력 + 균형",
            "금: 상체근력 + 유연성"
        ]
    elif mobility_score < 15:
        schedule = [
            "월: 가동성 + 경미한 근력",
            "화: 심폐훈련 + 스트레칭",
            "수: 균형 + 유연성",
            "금: 전신운동 + 가동성"
        ]
    elif cardio_score < 15:
        schedule = [
            "월: 유산소 + 근력",
            "화: 인터벌 훈련",
            "수: 근력 + 균형",
            "금: 지구력 + 가동성"
        ]
    else:
        schedule = [
            "월: 상체근력 + 코어",
            "화: 심폐훈련 + 가동성", 
            "목: 하체근력 + 균형",
            "금: 전신운동 + 유연성"
        ]
    
    # Exercise intensity based on age
    if age < 30:
        intensity = [
            "근력: 8-12회 × 3세트",
            "유연성: 20-30초 홀드",
            "균형: 30-45초 홀드",
            "심폐: 75-85% 최대심박"
        ]
    elif age < 50:
        intensity = [
            "근력: 10-15회 × 3세트",
            "유연성: 30-40초 홀드", 
            "균형: 45-60초 홀드",
            "심폐: 70-80% 최대심박"
        ]
    else:
        intensity = [
            "근력: 12-15회 × 2-3세트",
            "유연성: 40-60초 홀드",
            "균형: 60초+ 홀드",
            "심폐: 65-75% 최대심박"
        ]
    
    schedule_html = ''.join([f"<li>{item}</li>" for item in schedule])
    intensity_html = ''.join([f"<li>{item}</li>" for item in intensity])
    
    return f"""
        <div class="program-box">
            <h3>주간 스케줄</h3>
            <ul>
                {schedule_html}
            </ul>
        </div>

        <div class="program-box">
            <h3>운동 강도</h3>
            <ul>
                {intensity_html}
            </ul>
        </div>
    """


def get_html_download_link(html_content: str, filename: str, text: str) -> str:
    """
    Generate a download link for the HTML report
    
    Args:
        html_content: HTML content as string
        filename: Name for the downloaded file
        text: Link text to display
        
    Returns:
        str: HTML download link
    """
    html_bytes = html_content.encode('utf-8')
    b64 = base64.b64encode(html_bytes).decode()
    href = f'<a href="data:text/html;charset=utf-8;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href