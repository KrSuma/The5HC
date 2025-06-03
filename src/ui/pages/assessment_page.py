def new_assessment_page():
    """Enhanced page to conduct a new fitness assessment with structured compensation pattern tracking"""
    import streamlit as st
    from datetime import datetime

    # Import needed functions from improved modules
    from src.core.scoring import (
        calculate_pushup_score, calculate_toe_touch_score, calculate_single_leg_balance_score,
        calculate_step_test_score, calculate_category_scores
    )
    from src.core.recommendations import get_improvement_suggestions

    # Import service layer instead of direct database access
    from src.services.service_layer import ClientService, AssessmentService

    if not st.session_state.selected_client:
        # If no client is selected, allow selecting one
        st.header("새 체력 평가")
        st.subheader("회원 선택")

        # Use ClientService instead of direct get_clients function
        clients = ClientService.get_trainer_clients(st.session_state.trainer_id)

        if not clients:
            st.warning("등록된 회원이 없습니다. 먼저 회원을 추가해주세요.")
            if st.button("회원 추가"):
                st.session_state.current_page = "clients"
                st.rerun()
            return

        # Create a selection widget for clients
        client_options = {client[1]: client[0] for client in clients}
        selected_client_name = st.selectbox("회원 선택", list(client_options.keys()))

        if st.button("계속"):
            st.session_state.selected_client = client_options[selected_client_name]
            st.rerun()

        return

    # Get client details using ClientService
    client = ClientService.get_client_details(st.session_state.selected_client)

    if not client:
        st.error("회원을 찾을 수 없습니다.")
        return

    st.header(f"{client['name']} 회원 체력 평가")
    st.write(
        f"**나이:** {client['age']} | **성별:** {client['gender']} | **키:** {client['height']} cm | **체중:** {client['weight']} kg | **BMI:** {client['weight'] / ((client['height'] / 100) ** 2):.1f}")

    # Create tabs for different assessment sections
    tabs = st.tabs([
        "1. 오버헤드 스쿼트",
        "2. 푸시업",
        "3. 한 발 균형",
        "4. 발끝 터치",
        "5. 어깨 가동성",
        "6. 파머스 캐리",
        "7. 하버드 스텝"
    ])

    # Dictionary to store all assessment data
    assessment_data = {
        'client_id': client['id'],
        'trainer_id': st.session_state.trainer_id,
        'date': datetime.now().strftime("%Y-%m-%d"),
    }

    # 1. Overhead Squat tab
    with tabs[0]:
        st.subheader("1. 오버헤드 스쿼트 (하지 근기능)")

        # Score selection
        overhead_squat_score = st.selectbox(
            "수행 품질",
            [
                (0, "동작 중 통증 발생"),
                (1, "깊은 스쿼트 수행 불가능"),
                (2, "보상 동작 관찰됨 (발 뒤꿈치 들림, 무릎 내반 등)"),
                (3, "완벽한 동작 (상체 수직 유지, 대퇴가 수평 이하, 무릎 정렬)")
            ],
            format_func = lambda x: x[1]
        )
        assessment_data['overhead_squat_score'] = overhead_squat_score[0]

        # Structured compensation pattern tracking
        st.subheader("보상 패턴 체크")
        compensation_patterns = {
            "발 외회전": st.checkbox("발이 외회전됨", key = "ohsquat_foot_turnout"),
            "무릎 내반": st.checkbox("무릎 내반(Valgus) 발생", key = "ohsquat_knee_valgus"),
            "상체 전방 기울임": st.checkbox("상체가 과도하게 전방으로 기울어짐", key = "ohsquat_forward_lean"),
            "발뒤꿈치 들림": st.checkbox("발뒤꿈치가 들림", key = "ohsquat_heel_rise"),
            "팔 전방 하강": st.checkbox("팔이 전방으로 떨어짐", key = "ohsquat_arm_drop"),
            "균형 불안정": st.checkbox("테스트 중 균형 불안정 관찰됨", key = "ohsquat_balance_issue")
        }

        # Generate notes automatically from checked patterns
        compensation_notes = ", ".join([k for k, v in compensation_patterns.items() if v])

        # Additional notes field
        additional_notes = st.text_area("추가 메모", key = "ohsquat_additional_notes")

        if compensation_notes:
            overhead_squat_notes = f"관찰된 보상 패턴: {compensation_notes}"
            if additional_notes:
                overhead_squat_notes += f"\n추가 메모: {additional_notes}"
        else:
            overhead_squat_notes = additional_notes

        assessment_data['overhead_squat_notes'] = overhead_squat_notes

        # Show recommendations based on compensation patterns
        if any(compensation_patterns.values()):
            st.subheader("즉각적인 교정 제안")
            recommendations = []

            if compensation_patterns["발 외회전"]:
                recommendations.append("• 발목 가동성 제한 가능성. 종아리 스트레칭 및 발목 관절 가동술을 권장합니다.")

            if compensation_patterns["무릎 내반"]:
                recommendations.append("• 고관절 외전근(중둔근) 약화 징후. 클램쉘 운동 및 미니밴드 스쿼트를 통한 고관절 안정화가 필요합니다.")

            if compensation_patterns["상체 전방 기울임"]:
                recommendations.append("• 흉추 확장성 제한 또는 고관절 가동성 부족. 흉추 폼 롤링 및 고관절 굴곡근 스트레칭을 권장합니다.")

            if compensation_patterns["발뒤꿈치 들림"]:
                recommendations.append("• 발목 배측굴곡 제한. 아킬레스건 스트레칭과 발목 가동성 운동이 필요합니다.")

            if compensation_patterns["팔 전방 하강"]:
                recommendations.append("• 어깨 굴곡 제한 또는 견갑 안정성 부족. 월 슬라이드와 견갑 안정화 운동을 권장합니다.")

            if compensation_patterns["균형 불안정"]:
                recommendations.append("• 코어 안정성 부족. 플랭크 변형과 균형 훈련을 통한 안정성 향상이 필요합니다.")

            for recommendation in recommendations:
                st.write(recommendation)

    # 2. Push Up tab
    with tabs[1]:
        st.subheader("2. 푸시업 (상지 근기능)")

        # Push-up reps input
        push_up_reps = st.number_input("반복 횟수", min_value = 0, max_value = 100, value = 0, step = 1,
                                       key = "pushup_reps")
        assessment_data['push_up_reps'] = push_up_reps

        # Structured compensation pattern tracking for push-ups
        st.subheader("보상 패턴 체크")
        pushup_compensation_patterns = {
            "요추 과신전": st.checkbox("허리가 과도하게 처짐", key = "pushup_lumbar_extension"),
            "견갑골 익상": st.checkbox("날개 견갑 관찰 (견갑골이 튀어나옴)", key = "pushup_scapular_winging"),
            "어깨 전방 돌출": st.checkbox("어깨가 앞으로 내밀어짐", key = "pushup_shoulder_protrusion"),
            "팔꿈치 벌어짐": st.checkbox("팔꿈치가 과도하게 벌어짐", key = "pushup_elbow_flare"),
            "머리 전방 위치": st.checkbox("머리가 앞으로 빠짐", key = "pushup_forward_head")
        }

        # Generate notes
        pushup_comp_notes = ", ".join([k for k, v in pushup_compensation_patterns.items() if v])
        additional_pushup_notes = st.text_area("추가 메모", key = "pushup_additional_notes")

        if pushup_comp_notes:
            push_up_notes = f"관찰된 보상 패턴: {pushup_comp_notes}"
            if additional_pushup_notes:
                push_up_notes += f"\n추가 메모: {additional_pushup_notes}"
        else:
            push_up_notes = additional_pushup_notes

        assessment_data['push_up_notes'] = push_up_notes

        # Calculate push-up score based on gender, age and reps
        assessment_data['push_up_score'] = calculate_pushup_score(client['gender'], client['age'], push_up_reps)

        # Show calculated score
        st.info(
            f"점수: {assessment_data['push_up_score']}/4 - {['낮음', '보통', '좋음', '우수'][assessment_data['push_up_score'] - 1]}")

    # 3. Single Leg Balance tab
    with tabs[2]:
        st.subheader("3. 한 발 균형 (균형 및 협응성)")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**오른쪽 다리**")
            slb_right_open = st.number_input("눈 뜬 상태 (초)", min_value = 0, max_value = 60, value = 0, step = 1,
                                             key = "slb_right_open")
            slb_right_closed = st.number_input("눈 감은 상태 (초)", min_value = 0, max_value = 60, value = 0, step = 1,
                                               key = "slb_right_closed")
            assessment_data['single_leg_balance_right_eyes_open'] = slb_right_open
            assessment_data['single_leg_balance_right_eyes_closed'] = slb_right_closed

        with col2:
            st.write("**왼쪽 다리**")
            slb_left_open = st.number_input("눈 뜬 상태 (초)", min_value = 0, max_value = 60, value = 0, step = 1,
                                            key = "slb_left_open")
            slb_left_closed = st.number_input("눈 감은 상태 (초)", min_value = 0, max_value = 60, value = 0, step = 1,
                                              key = "slb_left_closed")
            assessment_data['single_leg_balance_left_eyes_open'] = slb_left_open
            assessment_data['single_leg_balance_left_eyes_closed'] = slb_left_closed

        # Check for significant asymmetry
        open_asymmetry = abs(slb_right_open - slb_left_open)
        closed_asymmetry = abs(slb_right_closed - slb_left_closed)

        if open_asymmetry > 5 or closed_asymmetry > 5:
            st.warning(f"좌우 비대칭 발견: 눈 뜬 상태 {open_asymmetry}초 차이, 눈 감은 상태 {closed_asymmetry}초 차이")
            asymmetry_note = f"좌우 비대칭: 눈 뜬 상태 {open_asymmetry}초, 눈 감은 상태 {closed_asymmetry}초 차이. "
        else:
            asymmetry_note = ""

        # Structured compensation pattern tracking
        st.subheader("관찰된 문제")
        slb_issues = {
            "골반 측방 기울임": st.checkbox("골반이 옆으로 기울어짐", key = "slb_pelvic_drop"),
            "과도한 족저굴곡": st.checkbox("발끝으로 서기 시도", key = "slb_toe_standing"),
            "과도한 팔 움직임": st.checkbox("균형을 위한 과도한 팔 움직임", key = "slb_arm_movement"),
            "무릎 흔들림": st.checkbox("무릎의 과도한 내외측 흔들림", key = "slb_knee_wobble"),
            "체간 회전": st.checkbox("몸통이 회전함", key = "slb_trunk_rotation")
        }

        slb_issues_noted = ", ".join([k for k, v in slb_issues.items() if v])
        additional_slb_notes = st.text_area("추가 메모", key = "slb_additional_notes")

        if slb_issues_noted:
            single_leg_balance_notes = f"{asymmetry_note}관찰된 문제: {slb_issues_noted}"
            if additional_slb_notes:
                single_leg_balance_notes += f"\n추가 메모: {additional_slb_notes}"
        else:
            single_leg_balance_notes = f"{asymmetry_note}{additional_slb_notes}"

        assessment_data['single_leg_balance_notes'] = single_leg_balance_notes

        # Calculate single leg balance score
        balance_score = calculate_single_leg_balance_score(slb_right_open, slb_left_open, slb_right_closed,
                                                           slb_left_closed)
        st.info(f"균형 점수: {balance_score:.1f}/4.0")

    # 4. Toe Touch tab
    with tabs[3]:
        st.subheader("4. 발끝 터치 (하지 유연성)")

        # Toe touch distance input
        toe_touch_distance = st.number_input(
            "바닥에서의 거리 (cm, 음수=바닥 위, 양수=바닥 아래)",
            min_value = -30.0, max_value = 20.0, value = 0.0, step = 0.5, key = "toe_touch_distance"
        )
        assessment_data['toe_touch_distance'] = toe_touch_distance

        # Calculate toe touch score
        toe_touch_score = calculate_toe_touch_score(toe_touch_distance)
        assessment_data['toe_touch_score'] = toe_touch_score

        # Show calculated score
        st.info(f"점수: {toe_touch_score}/4 - {['낮음', '보통', '좋음', '우수'][toe_touch_score - 1]}")

        # Structured compensation pattern tracking
        st.subheader("보상 패턴 체크")
        toe_touch_patterns = {
            "무릎 굴곡": st.checkbox("무릎이 구부러짐", key = "tt_knee_bend"),
            "흉추 과도 굴곡": st.checkbox("등이 과도하게 굽혀짐", key = "tt_thoracic_flexion"),
            "골반 후방 틸트 부족": st.checkbox("골반 움직임 제한", key = "tt_pelvic_limitation"),
            "발목 제한": st.checkbox("발목 움직임 제한", key = "tt_ankle_limitation")
        }

        tt_patterns_noted = ", ".join([k for k, v in toe_touch_patterns.items() if v])
        additional_tt_notes = st.text_area("추가 메모", key = "tt_additional_notes")

        if tt_patterns_noted:
            toe_touch_notes = f"관찰된 보상 패턴: {tt_patterns_noted}"
            if additional_tt_notes:
                toe_touch_notes += f"\n추가 메모: {additional_tt_notes}"
        else:
            toe_touch_notes = additional_tt_notes

        assessment_data['toe_touch_notes'] = toe_touch_notes

    # 5. FMS Shoulder Mobility tab
    with tabs[4]:
        st.subheader("5. FMS 어깨 가동성 (상지 유연성)")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**오른쪽 어깨**")
            shoulder_mobility_right = st.number_input("주먹 거리 (오른손 위)", min_value = 0.0, max_value = 5.0, value = 1.5,
                                                      step = 0.5, key = "sm_right")
            right_shoulder_score = st.selectbox(
                "점수",
                [
                    (0, "통증 발생"),
                    (1, "제한적 (>2 주먹)"),
                    (2, "보통 (1.5 주먹)"),
                    (3, "우수 (<1 주먹)")
                ],
                format_func = lambda x: x[1],
                key = "sm_right_score"
            )[0]

        with col2:
            st.write("**왼쪽 어깨**")
            shoulder_mobility_left = st.number_input("주먹 거리 (왼손 위)", min_value = 0.0, max_value = 5.0, value = 1.5,
                                                     step = 0.5, key = "sm_left")
            left_shoulder_score = st.selectbox(
                "점수",
                [
                    (0, "통증 발생"),
                    (1, "제한적 (>2 주먹)"),
                    (2, "보통 (1.5 주먹)"),
                    (3, "우수 (<1 주먹)")
                ],
                format_func = lambda x: x[1],
                key = "sm_left_score"
            )[0]

        assessment_data['shoulder_mobility_right'] = shoulder_mobility_right
        assessment_data['shoulder_mobility_left'] = shoulder_mobility_left

        # Use lower score for overall rating as per FMS guidelines
        shoulder_mobility_score = min(right_shoulder_score, left_shoulder_score)
        assessment_data['shoulder_mobility_score'] = shoulder_mobility_score

        # Check for asymmetry
        if abs(right_shoulder_score - left_shoulder_score) >= 1:
            st.warning("어깨 가동성의 좌우 비대칭이 감지되었습니다. 약한 쪽에 집중적인 훈련이 필요합니다.")
            asymmetry_note = "좌우 비대칭 감지됨. "
        else:
            asymmetry_note = ""

        # Structured compensation pattern tracking
        st.subheader("관찰된 문제")
        shoulder_issues = {
            "경추 측굴/회전": st.checkbox("목이 옆으로 기울어짐", key = "sm_cervical_tilt"),
            "어깨 올림": st.checkbox("어깨가 올라감", key = "sm_shoulder_elevation"),
            "흉추 보상": st.checkbox("흉추의 과도한 움직임", key = "sm_thoracic_compensation"),
            "팔꿈치 굴곡": st.checkbox("팔꿈치가 과도하게 구부러짐", key = "sm_elbow_flexion")
        }

        sm_issues_noted = ", ".join([k for k, v in shoulder_issues.items() if v])
        additional_sm_notes = st.text_area("추가 메모", key = "sm_additional_notes")

        if sm_issues_noted:
            shoulder_mobility_notes = f"{asymmetry_note}관찰된 문제: {sm_issues_noted}"
            if additional_sm_notes:
                shoulder_mobility_notes += f"\n추가 메모: {additional_sm_notes}"
        else:
            shoulder_mobility_notes = f"{asymmetry_note}{additional_sm_notes}"

        assessment_data['shoulder_mobility_notes'] = shoulder_mobility_notes

    # 6. Farmer's Carry tab
    with tabs[5]:
        st.subheader("6. 파머스 캐리 (악력 및 근지구력)")

        farmers_carry_weight = st.number_input("사용 무게 (kg)", min_value = 0.0, max_value = 100.0, value = 0.0,
                                               step = 2.5, key = "fc_weight")

        col1, col2 = st.columns(2)
        with col1:
            farmers_carry_distance = st.number_input("이동 거리 (m)", min_value = 0.0, max_value = 100.0, value = 0.0,
                                                     step = 1.0, key = "fc_distance")
        with col2:
            farmers_carry_time = st.number_input("시간 (초)", min_value = 0, max_value = 120, value = 0, step = 1,
                                                 key = "fc_time")

        assessment_data['farmer_carry_weight'] = farmers_carry_weight
        assessment_data['farmer_carry_distance'] = farmers_carry_distance
        # farmer_carry_time stored in notes since no DB column exists

        farmers_carry_score = st.selectbox(
            "수행 평가",
            [
                (1, "저조 - 심각한 자세 문제와 함께 10m 미만 이동"),
                (2, "보통 - 중간 정도의 자세 문제와 함께 10-20m 이동"),
                (3, "양호 - 경미한 자세 문제와 함께 20-30m 이동"),
                (4, "우수 - 완벽한 자세로 30m 이상 이동")
            ],
            format_func = lambda x: x[1],
            key = "fc_score"
        )[0]

        assessment_data['farmer_carry_score'] = farmers_carry_score

        # Structured compensation pattern tracking
        st.subheader("관찰된 문제")
        carry_issues = {
            "어깨 올림": st.checkbox("어깨가 지속적으로 올라감", key = "fc_shoulder_elevation"),
            "측방 체간 굴곡": st.checkbox("몸통이 한쪽으로 기울어짐", key = "fc_lateral_flexion"),
            "비정상 보행": st.checkbox("비정상적인 보행 패턴", key = "fc_gait_abnormal"),
            "요추 과신전": st.checkbox("허리가 과도하게 아치형", key = "fc_lumbar_extension"),
            "손목 굴곡": st.checkbox("손목이 구부러짐", key = "fc_wrist_flexion")
        }

        fc_issues_noted = ", ".join([k for k, v in carry_issues.items() if v])
        additional_fc_notes = st.text_area("추가 메모", key = "fc_additional_notes")

        # Include time in notes since no DB column exists
        time_info = f"수행 시간: {farmers_carry_time}초"
        
        if fc_issues_noted:
            farmers_carry_notes = f"{time_info}\n관찰된 문제: {fc_issues_noted}"
            if additional_fc_notes:
                farmers_carry_notes += f"\n추가 메모: {additional_fc_notes}"
        else:
            farmers_carry_notes = time_info
            if additional_fc_notes:
                farmers_carry_notes += f"\n추가 메모: {additional_fc_notes}"

        assessment_data['farmer_carry_notes'] = farmers_carry_notes

    # 7. Harvard 3-min Step Test tab
    with tabs[6]:
        st.subheader("7. 하버드 3분 스텝 테스트 (심폐지구력)")

        step_test_hr1 = st.number_input("회복기 심박수 1 (1:00-1:30 분, bpm)", min_value = 40, max_value = 220, value = 90,
                                        step = 1, key = "hr1")
        step_test_hr2 = st.number_input("회복기 심박수 2 (2:00-2:30 분, bpm)", min_value = 40, max_value = 220, value = 80,
                                        step = 1, key = "hr2")
        step_test_hr3 = st.number_input("회복기 심박수 3 (3:00-3:30 분, bpm)", min_value = 40, max_value = 220, value = 70,
                                        step = 1, key = "hr3")

        # Map to database schema - store average heart rate and duration
        avg_heart_rate = (step_test_hr1 + step_test_hr2 + step_test_hr3) / 3
        assessment_data['harvard_step_test_heart_rate'] = int(avg_heart_rate)
        assessment_data['harvard_step_test_duration'] = 180.0  # 3 minutes

        # Calculate Harvard Step Test score and PFI
        step_test_score, pfi = calculate_step_test_score(step_test_hr1, step_test_hr2, step_test_hr3)
        # Store additional data in notes as JSON
        import json
        step_test_data = {
            'hr1': step_test_hr1,
            'hr2': step_test_hr2, 
            'hr3': step_test_hr3,
            'pfi': pfi,
            'score': step_test_score
        }

        # Show calculated PFI
        st.info(f"체력 지수 (PFI): {pfi:.1f} - 점수: {step_test_score}/4 - {['낮음', '보통', '좋음', '우수'][step_test_score - 1]}")

        # Observations
        step_test_notes = st.text_area("관찰 및 메모 (피로 징후, 호흡 패턴, 제한사항 등)", key = "st_notes")
        
        # Combine user notes with step test data
        complete_notes = f"HR1: {step_test_hr1}, HR2: {step_test_hr2}, HR3: {step_test_hr3}, PFI: {pfi:.1f}, Score: {step_test_score}/4"
        if step_test_notes:
            complete_notes += f"\nNotes: {step_test_notes}"
        
        assessment_data['harvard_step_test_notes'] = complete_notes

    # Submit button outside of tabs
    st.divider()
    if st.button("계산 및 평가 저장", type = "primary"):
        # Calculate category scores based on inputted data
        category_scores = calculate_category_scores(assessment_data, client)

        # Update assessment data with overall scores
        assessment_data.update({
            'overall_score': category_scores['overall_score'],
            'strength_score': category_scores['strength_score'],
            'mobility_score': category_scores['mobility_score'],
            'balance_score': category_scores['balance_score'],
            'cardio_score': category_scores['cardio_score'],
            'shoulder_mobility_score': assessment_data.get('shoulder_mobility_score', 0),
            'farmer_carry_score': assessment_data.get('farmer_carry_score', 0)
        })

        # Save assessment directly to bypass service layer issues
        try:
            from src.data.database import save_assessment as db_save_assessment
            assessment_id = db_save_assessment(assessment_data)
            if assessment_id:
                success = True
                message = "평가가 저장되었습니다!"
            else:
                success = False
                message = "평가 저장에 실패했습니다."
        except Exception as e:
            success = False
            message = f"평가 저장 중 오류가 발생했습니다: {str(e)}"
            print(f"DEBUG: Assessment save error: {e}")

        if success:
            st.session_state.success_message = message
            st.session_state.current_page = "dashboard"
            st.rerun()
        else:
            st.error(message)
            st.session_state.error_message = message