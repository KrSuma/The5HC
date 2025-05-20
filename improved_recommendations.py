# recommendations.py - Functions for generating improvement suggestions with enhanced personalization

from typing import Dict, List, Any

def get_improvement_suggestions(assessment_data: Dict[str, Any], client_details: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generate personalized improvement suggestions based on assessment results and client details
    
    Args:
        assessment_data: Dictionary containing assessment values
        client_details: Dictionary containing client information
        
    Returns:
        Dict[str, List[str]]: Dictionary of suggestions by category
    """
    suggestions = {
        'strength': [],
        'mobility': [],
        'balance': [],
        'cardio': []
    }

    # Extract client details for personalization
    age = client_details.get('age', 30)
    gender = client_details.get('gender', 'Male')
    is_older = age > 50
    is_youth = age < 18

    # Strength suggestions
    if assessment_data.get('push_up_score', 0) <= 2:
        if is_older:
            suggestions['strength'].append("지지 푸시업으로 시작하여 점진적으로 강도 높이기 (주 2회)")
            suggestions['strength'].append("밴드 지원 푸시업을 통한 관절 부담 감소")
        elif is_youth:
            suggestions['strength'].append("올바른 푸시업 폼 학습을 위한 미러 연습")
            suggestions['strength'].append("주 3회 점진적 푸시업 훈련 (무릎 푸시업부터 시작)")
        else:
            suggestions['strength'].append("점진적인 푸시업 훈련 주 2-3회 포함")
            suggestions['strength'].append("가슴 프레스와 삼두근 운동을 루틴에 추가")

    if assessment_data.get('farmers_carry_score', 0) <= 2:
        if is_older:
            suggestions['strength'].append("가벼운 무게로 시작하여 자세에 중점을 둔 그립 강화 훈련")
            suggestions['strength'].append("관절 친화적인 코어 강화 운동 추가")
        else:
            suggestions['strength'].append("데드 행, 파머스 워크와 같은 그립 강화 운동 포함")
            suggestions['strength'].append("플랭크와 회전 방지 운동으로 코어 강화")

    # Mobility suggestions
    if assessment_data.get('toe_touch_score', 0) <= 2:
        if is_older:
            suggestions['mobility'].append("앉은 자세에서 수행하는 햄스트링 스트레칭 일일 루틴")
            suggestions['mobility'].append("고관절 가동성 향상을 위한 부드러운 운동")
        else:
            suggestions['mobility'].append("햄스트링과 하부 등 부위를 위한 일일 스트레칭 루틴")
            suggestions['mobility'].append("힙 힌지 패턴 운동 연습")

    if assessment_data.get('shoulder_mobility_score', 0) <= 2:
        if gender in ['Female', '여성']:  # Female-specific suggestion
            suggestions['mobility'].append("흉근 및 승모근 긴장 완화를 위한 폼 롤링")
            suggestions['mobility'].append("내/외부 회전에 초점을 맞춘 어깨 가동성 운동")
        else:
            suggestions['mobility'].append("내/외부 회전에 초점을 맞춘 일일 어깨 가동성 운동")
            suggestions['mobility'].append("흉추 가동성 운동 포함")

    # Balance suggestions
    if (assessment_data.get('single_leg_balance_right_open', 0) < 30 or 
        assessment_data.get('single_leg_balance_left_open', 0) < 30):
        
        right_open = assessment_data.get('single_leg_balance_right_open', 0)
        left_open = assessment_data.get('single_leg_balance_left_open', 0)
        asymmetry = abs(right_open - left_open) > 10
        
        if asymmetry:
            weaker_side = "오른쪽" if right_open < left_open else "왼쪽"
            suggestions['balance'].append(f"{weaker_side} 다리 균형에 중점을 둔 대칭성 개선 운동")
        
        if is_older:
            suggestions['balance'].append("안전한 환경에서의 일일 균형 운동 (의자 지지 사용)")
            suggestions['balance'].append("태극권 또는 필라테스 기반 균형 향상 운동")
        else:
            suggestions['balance'].append("일일 한 발 균형 운동 실시")
            suggestions['balance'].append("맨발 고유감각 훈련 추가")

    if assessment_data.get('overhead_squat_score', 0) <= 2:
        observed_issues = []
        
        # Check for specific compensation patterns noted in assessment
        notes = assessment_data.get('overhead_squat_notes', '').lower()
        if '발 외회전' in notes or 'foot turn' in notes:
            observed_issues.append("발목 가동성 운동 및 맨발 스쿼트 연습")
        if '무릎 내반' in notes or 'knee valgus' in notes:
            observed_issues.append("고관절 외전근 강화 및 미니밴드 운동")
        if '상체 전방' in notes or 'forward lean' in notes:
            observed_issues.append("흉추 가동성 운동 및 코어 안정화 훈련")
        
        if observed_issues:
            for issue in observed_issues[:2]:  # Add up to 2 specific recommendations
                suggestions['balance'].append(issue)
        else:
            suggestions['balance'].append("맨몸 운동으로 스쿼트 메커니즘 개선")
            suggestions['balance'].append("발목 및 고관절 가동성 운동 포함")

    # Cardio suggestions
    if assessment_data.get('step_test_score', 0) <= 2:
        if is_older:
            suggestions['cardio'].append("저충격 유산소 운동 (수영, 사이클, 걷기) 주 3회")
            suggestions['cardio'].append("심박수 모니터링을 통한 안전한 강도 유지")
        elif age < 30:  # Younger clients
            suggestions['cardio'].append("HIIT와 전통적 유산소 훈련의 조합")
            suggestions['cardio'].append("스포츠 기반 심폐 활동 통합")
        else:
            suggestions['cardio'].append("유산소 훈련 점진적 증가 (걷기, 자전거, 수영)")
            suggestions['cardio'].append("주 1-2회 간격 훈련 포함")

    # Add BMI-specific recommendations if available
    if 'height' in client_details and 'weight' in client_details:
        height_m = client_details['height'] / 100
        weight_kg = client_details['weight']
        bmi = weight_kg / (height_m * height_m)
        
        if bmi > 25:  # Overweight
            suggestions['cardio'].append("심박수 목표 구간 내에서 유산소 운동 시간 점진적 증가")
            suggestions['strength'].append("대사량 증가를 위한 복합 운동 중심 근력 훈련")
        elif bmi < 18.5:  # Underweight
            suggestions['strength'].append("기초 근력 향상 및 제지방량 증가를 위한 저항 훈련 강화")

    # If no suggestions for a category, add maintenance suggestion
    if not suggestions['strength']:
        suggestions['strength'].append("현재 근력 능력 유지")
        suggestions['strength'].append("주 2-3회 전신 근력 훈련 계속")

    if not suggestions['mobility']:
        suggestions['mobility'].append("현재 유연성 수준 유지")
        suggestions['mobility'].append("일반적인 가동성 루틴 계속")

    if not suggestions['balance']:
        suggestions['balance'].append("현재 균형 능력 유지")
        suggestions['balance'].append("일상 생활에 균형 활동 통합")

    if not suggestions['cardio']:
        suggestions['cardio'].append("현재 심폐 능력 유지")
        suggestions['cardio'].append("다양한 유산소 활동 시도")

    return suggestions


def get_recommended_schedule(client_details: Dict[str, Any] = None, 
                             category_scores: Dict[str, float] = None) -> List[str]:
    """
    Return a recommended weekly training schedule personalized for the client
    
    Args:
        client_details: Optional dictionary with client information
        category_scores: Optional dictionary with category scores
        
    Returns:
        List[str]: List of recommended weekly schedule items
    """
    # Default schedule
    schedule_items = [
        "• 월요일: 상체 근력 (푸시업, 벤치 프레스) + 코어 운동",
        "• 화요일: 심폐 훈련 (30분 중강도 인터벌) + 가동성 운동",
        "• 목요일: 하체 근력 (스쿼트, 런지) + 균형 운동",
        "• 금요일: 전신 운동 (복합 운동) + 유연성 루틴"
    ]

    # If we have client details, personalize the schedule
    if client_details and category_scores:
        age = client_details.get('age', 30)
        
        # Identify lowest score area for additional focus
        area_scores = {
            'strength': category_scores.get('strength_score', 20),
            'mobility': category_scores.get('mobility_score', 20),
            'balance': category_scores.get('balance_score', 20),
            'cardio': category_scores.get('cardio_score', 20)
        }
        
        weakest_area = min(area_scores, key=area_scores.get)
        
        # Adjust schedule based on age and weakest area
        if age > 50:
            # For older clients, 3-day schedule with more rest
            if weakest_area == 'strength':
                schedule_items = [
                    "• 월요일: 상체 근력 (지지 푸시업, 밴드 운동) + 가벼운 유산소",
                    "• 수요일: 하체 근력 (지지 스쿼트, 브릿지) + 균형 운동",
                    "• 금요일: 유연성 및 가동성 (스트레칭) + 가벼운 전신 운동"
                ]
            elif weakest_area == 'mobility':
                schedule_items = [
                    "• 월요일: 상체 가동성 (어깨 운동) + 가벼운 근력 운동",
                    "• 수요일: 하체 유연성 (스트레칭) + 가벼운 유산소",
                    "• 금요일: 전신 가동성 워크숍 + 균형 운동"
                ]
            elif weakest_area == 'balance':
                schedule_items = [
                    "• 월요일: 균형 및 고유감각 훈련 + 상체 근력",
                    "• 수요일: 기능적 움직임 패턴 + 가벼운 유산소",
                    "• 금요일: 한발 균형 운동 + 유연성 루틴"
                ]
            else:  # cardio
                schedule_items = [
                    "• 월요일: 저강도 유산소 (워킹) + 가벼운 근력",
                    "• 수요일: 인터벌 워킹 + 유연성 운동",
                    "• 금요일: 순환 운동 (가벼운 강도) + 균형 훈련"
                ]
        elif age < 18:
            # For youth, focus on fundamentals and movement skills
            schedule_items = [
                "• 월요일: 기본 움직임 패턴 + 동적 유연성",
                "• 화요일: 맨몸 근력 운동 + 균형/협응 훈련",
                "• 목요일: 스포츠 기반 심폐 활동 + 플라이오메트릭스",
                "• 토요일: 혼합 훈련 (재미있는 챌린지와 게임)"
            ]
        else:
            # For regular adults, add an extra day for the weakest area
            extra_day = ""
            if weakest_area == 'strength':
                extra_day = "• 토요일: 추가 근력 훈련 (약점 부위 집중) + 가벼운 유산소"
            elif weakest_area == 'mobility':
                extra_day = "• 토요일: 집중 가동성 세션 (요가 또는 심화 스트레칭)"
            elif weakest_area == 'balance':
                extra_day = "• 토요일: 심화 균형 훈련 + 고유감각 향상 운동"
            else:  # cardio
                extra_day = "• 토요일: 장거리 저강도 유산소 또는 인터벌 훈련"
                
            schedule_items.append(extra_day)
    
    return schedule_items


def get_intensity_recommendations(client_details: Dict[str, Any] = None) -> List[str]:
    """
    Return recommended exercise intensity guidelines personalized for the client
    
    Args:
        client_details: Optional dictionary with client information
        
    Returns:
        List[str]: List of recommended intensity guidelines
    """
    # Default intensity recommendations
    intensity_items = [
        "• 근력: 중간 부하 (8-12회 반복 × 3세트)",
        "• 유연성: 20-30초 홀드 × 2-3세트",
        "• 균형: 30-45초 홀드 × 3세트",
        "• 심폐: 최대 심박수의 70-80%"
    ]

    # If we have client details, personalize the intensity
    if client_details:
        age = client_details.get('age', 30)
        gender = client_details.get('gender', 'Male')
        
        if age > 60:
            intensity_items = [
                "• 근력: 가벼운-중간 부하 (10-15회 반복 × 2-3세트)",
                "• 유연성: 30-60초 홀드 × 2세트",
                "• 균형: 15-30초 홀드 × 4-5세트 (지지대 활용)",
                "• 심폐: 최대 심박수의 60-70%"
            ]
        elif age > 50:
            intensity_items = [
                "• 근력: 중간 부하 (10-12회 반복 × 2-3세트)",
                "• 유연성: 30-45초 홀드 × 2세트",
                "• 균형: 20-40초 홀드 × 3세트",
                "• 심폐: 최대 심박수의 65-75%"
            ]
        elif age < 18:
            intensity_items = [
                "• 근력: 가벼운-중간 부하 (12-15회 반복 × 3세트), 올바른 폼에 중점",
                "• 유연성: 15-20초 홀드 × 3세트, 동적 스트레칭 우선",
                "• 균형: 기능적 훈련 통합, 다양한 표면 활용",
                "• 심폐: 다양한 강도의 인터벌 및 게임 기반 활동"
            ]
        elif 'exercise_experience' in client_details:
            # If we have experience information, further customize
            experience = client_details['exercise_experience']
            if experience == 'beginner':
                intensity_items = [
                    "• 근력: 가벼운 부하 (12-15회 반복 × 2세트)",
                    "• 유연성: 15-20초 홀드 × 2세트",
                    "• 균형: 15-30초 홀드 × 2세트",
                    "• 심폐: 최대 심박수의 60-70%"
                ]
            elif experience == 'advanced':
                intensity_items = [
                    "• 근력: 중간-높은 부하 (6-10회 반복 × 4세트)",
                    "• 유연성: 30-45초 홀드 × 3세트",
                    "• 균형: 고난도 균형 동작 30-60초 × 3세트",
                    "• 심폐: 최대 심박수의 75-85%, 인터벌 훈련 포함"
                ]
    
    return intensity_items