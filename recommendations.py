# recommendations.py - Functions for generating improvement suggestions

def get_improvement_suggestions(assessment_data, client_details):
    """Generate personalized improvement suggestions based on assessment results"""
    suggestions = {
        'strength': [],
        'mobility': [],
        'balance': [],
        'cardio': []
    }

    # Strength suggestions
    if assessment_data['push_up_score'] <= 2:
        suggestions['strength'].append("점진적인 푸시업 훈련 주 2-3회 포함")
        suggestions['strength'].append("가슴 프레스와 삼두근 운동을 루틴에 추가")

    if assessment_data['farmers_carry_score'] <= 2:
        suggestions['strength'].append("데드 행, 파머스 워크와 같은 그립 강화 운동 포함")
        suggestions['strength'].append("플랭크와 회전 방지 운동으로 코어 강화")

    # Mobility suggestions
    if assessment_data['toe_touch_score'] <= 2:
        suggestions['mobility'].append("햄스트링과 하부 등 부위를 위한 일일 스트레칭 루틴")
        suggestions['mobility'].append("힙 힌지 패턴 운동 연습")

    if assessment_data['shoulder_mobility_score'] <= 2:
        suggestions['mobility'].append("내/외부 회전에 초점을 맞춘 일일 어깨 가동성 운동")
        suggestions['mobility'].append("흉추 가동성 운동 포함")

    # Balance suggestions
    if assessment_data['single_leg_balance_right_open'] < 30 or assessment_data['single_leg_balance_left_open'] < 30:
        suggestions['balance'].append("일일 한 발 균형 운동 실시")
        suggestions['balance'].append("맨발 고유감각 훈련 추가")

    if assessment_data['overhead_squat_score'] <= 2:
        suggestions['balance'].append("맨몸 운동으로 스쿼트 메커니즘 개선")
        suggestions['balance'].append("발목 및 고관절 가동성 운동 포함")

    # Cardio suggestions
    if assessment_data['step_test_score'] <= 2:
        suggestions['cardio'].append("유산소 훈련 점진적 증가 (걷기, 자전거, 수영)")
        suggestions['cardio'].append("주 1-2회 간격 훈련 포함")

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


def get_recommended_schedule():
    """Return a recommended weekly training schedule"""
    schedule_items = [
        "• 월요일: 상체 근력 (푸시업, 벤치 프레스) + 코어 운동",
        "• 화요일: 심폐 훈련 (30분 중강도 인터벌) + 가동성 운동",
        "• 목요일: 하체 근력 (스쿼트, 런지) + 균형 운동",
        "• 금요일: 전신 운동 (복합 운동) + 유연성 루틴"
    ]
    return schedule_items


def get_intensity_recommendations():
    """Return recommended exercise intensity guidelines"""
    intensity_items = [
        "• 근력: 중간 부하 (8-12회 반복 × 3세트)",
        "• 유연성: 20-30초 홀드 × 2-3세트",
        "• 균형: 30-45초 홀드 × 3세트",
        "• 심폐: 최대 심박수의 70-80%"
    ]
    return intensity_items