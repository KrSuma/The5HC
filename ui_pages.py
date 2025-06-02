# ui_pages.py - UI pages for the Streamlit application with service layer integration

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import re

# Import services instead of direct database functions
from services import (
    AuthService, ClientService, AssessmentService,
    DashboardService, AnalyticsService
)

# Import improved assessment scoring and PDF functions
from scoring import get_score_description
from recommendations import get_improvement_suggestions
from pdf_generator import create_pdf_report, get_pdf_download_link


def login_register_page():
    """Login and registration page using service layer"""
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        st.header("로그인")
        username = st.text_input("아이디", key = "login_username")
        password = st.text_input("비밀번호", type = "password", key = "login_password")

        if st.button("로그인", key = "login_button"):
            if username and password:
                success, message = AuthService.login(username, password)
                trainer_id = st.session_state.get('trainer_id') if success else None
                if success:
                    st.session_state.current_page = "dashboard"
                    st.session_state.success_message = message
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")

    with tab2:
        st.header("회원가입")
        new_username = st.text_input("아이디", key = "reg_username")
        new_password = st.text_input("비밀번호", type = "password", key = "reg_password")
        confirm_password = st.text_input("비밀번호 확인", type = "password", key = "confirm_password")
        name = st.text_input("이름", key = "reg_name")
        email = st.text_input("이메일", key = "reg_email")

        if st.button("회원가입", key = "register_button"):
            if new_username and new_password and confirm_password and name and email:
                if new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("유효하지 않은 이메일 주소입니다.")
                else:
                    success, message = AuthService.register(new_username, new_password, name, email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.warning("모든 항목을 입력해주세요.")


def dashboard_page():
    """Dashboard page showing recent assessments and stats using service layer"""
    st.header("대시보드")

    # Get trainer stats and recent assessments
    stats = DashboardService.get_trainer_stats(st.session_state.trainer_id)
    recent_assessments = DashboardService.get_recent_assessments(st.session_state.trainer_id)

    # Display stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("전체 회원", stats['total_clients'])
    with col2:
        st.metric("전체 평가", stats['total_assessments'])

    # Display recent assessments
    st.subheader("최근 평가")

    if recent_assessments:
        assessment_df = pd.DataFrame(
            recent_assessments,
            columns = ["ID", "회원 이름", "날짜", "종합 점수"]
        )

        # Add a description column
        assessment_df["상태"] = assessment_df["종합 점수"].apply(
            lambda score: get_score_description(score)
        )

        # Format the score with 1 decimal place
        assessment_df["종합 점수"] = assessment_df["종합 점수"].apply(
            lambda score: f"{score:.1f}/100"
        )

        st.dataframe(
            assessment_df,
            column_config = {
                "ID": None,  # Hide ID column
            },
            hide_index = True,
            use_container_width = True
        )

        if st.button("모든 평가 보기"):
            st.session_state.current_page = "clients"
            st.rerun()
    else:
        st.info("아직 기록된 평가가 없습니다. 회원을 추가하고 평가를 시작하세요.")

        if st.button("회원 추가"):
            st.session_state.current_page = "clients"
            st.rerun()


def dashboard_page_with_search():
    """Dashboard page showing recent assessments and stats with search functionality"""
    st.header("대시보드")

    # Get stats
    stats = DashboardService.get_trainer_stats(st.session_state.trainer_id)

    # Display stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("전체 회원", stats['total_clients'])
    with col2:
        st.metric("전체 평가", stats['total_assessments'])

    # Get all clients for search
    clients = ClientService.get_trainer_clients(st.session_state.trainer_id)
    client_dict = {client[0]: client[1] for client in clients}

    # Add search functionality
    st.subheader("평가 검색")

    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        # Offer different search options
        search_option = st.selectbox(
            "검색 기준",
            options = ["모든 평가", "회원명", "날짜", "점수 범위"]
        )

    # Create search criteria dictionary
    search_criteria = {}

    # Different search inputs based on selected option
    if search_option == "회원명":
        client_names = ["모든 회원"] + list(client_dict.values())
        selected_client_name = st.selectbox("회원 선택", client_names)

        if selected_client_name != "모든 회원":
            # Get the client_id from the name
            selected_client_id = [k for k, v in client_dict.items() if v == selected_client_name][0]
            search_criteria['client_id'] = selected_client_id

    elif search_option == "날짜":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", datetime.now() - pd.Timedelta(days = 30))
        with col2:
            end_date = st.date_input("종료일", datetime.now())

        # Convert to string format for comparison
        search_criteria['date_start'] = start_date.strftime("%Y-%m-%d")
        search_criteria['date_end'] = end_date.strftime("%Y-%m-%d")

    elif search_option == "점수 범위":
        col1, col2 = st.columns(2)
        with col1:
            min_score = st.slider("최소 점수", 0, 100, 0)
        with col2:
            max_score = st.slider("최대 점수", 0, 100, 100)

        search_criteria['score_min'] = min_score
        search_criteria['score_max'] = max_score

    # Search based on criteria
    if search_option == "모든 평가":
        filtered_assessments = DashboardService.get_recent_assessments(st.session_state.trainer_id, limit = 100)
    else:
        filtered_assessments = DashboardService.search_assessments(
            st.session_state.trainer_id,
            search_criteria
        )

    # Display filtered assessments
    st.subheader("평가 결과")

    if filtered_assessments:
        # Convert to DataFrame for easier manipulation
        assessment_df = pd.DataFrame(
            filtered_assessments,
            columns = ["ID", "회원 이름", "날짜", "종합 점수"]
        )

        # Add a description column
        assessment_df["상태"] = assessment_df["종합 점수"].apply(
            lambda score: get_score_description(score)
        )

        # Format the score with 1 decimal place
        assessment_df["종합 점수"] = assessment_df["종합 점수"].apply(
            lambda score: f"{score:.1f}/100"
        )

        st.dataframe(
            assessment_df,
            column_config = {
                "ID": None,  # Hide ID column
            },
            hide_index = True,
            use_container_width = True
        )

        # Get the selected assessment ID from the clicked row
        selected_assessment = st.selectbox(
            "평가 선택",
            options = [(a[0], f"{a[1]} - {a[2]} ({a[3]:.1f}/100)") for a in filtered_assessments],
            format_func = lambda x: x[1]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("선택한 평가 상세 보기"):
                st.session_state.selected_assessment = selected_assessment[0]
                st.session_state.current_page = "assessment_detail"
                st.rerun()

        with col2:
            if st.button("새 평가 실시"):
                st.session_state.current_page = "new_assessment"
                st.rerun()
    else:
        st.info("검색 조건에 맞는 평가 결과가 없습니다.")

        if st.button("새 평가 실시"):
            st.session_state.current_page = "new_assessment"
            st.rerun()


def clients_page():
    """Clients management page using service layer"""
    st.header("회원 관리")

    # Create tabs for client list and add new client
    tab1, tab2 = st.tabs(["회원 목록", "새 회원 추가"])

    with tab1:
        # Fetch clients for the logged-in trainer
        clients = ClientService.get_trainer_clients(st.session_state.trainer_id)

        if clients:
            # Display clients in a table
            client_df = pd.DataFrame(clients, columns = ["ID", "이름"])

            # Get assessment counts for each client
            client_df["평가 수"] = client_df["ID"].apply(
                lambda client_id: len(AssessmentService.get_client_assessments(client_id))
            )

            # Get client details for additional information
            client_df["나이"] = client_df["ID"].apply(
                lambda client_id: ClientService.get_client_details(client_id)["age"]
            )

            client_df["성별"] = client_df["ID"].apply(
                lambda client_id: ClientService.get_client_details(client_id)["gender"]
            )

            # Button to view client details
            def view_client(client_id):
                st.session_state.selected_client = client_id
                st.session_state.current_page = "client_detail"
                st.rerun()

            # Display the client list with a button to view details
            for _, row in client_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 2])
                with col1:
                    st.write(f"**{row['이름']}**")
                with col2:
                    st.write(f"나이: {row['나이']}")
                with col3:
                    st.write(f"성별: {row['성별']}")
                with col4:
                    st.write(f"평가 수: {row['평가 수']}")
                with col5:
                    if st.button("상세 보기", key = f"view_{row['ID']}"):
                        view_client(row['ID'])
                st.divider()
        else:
            st.info("등록된 회원이 없습니다. '새 회원 추가' 탭에서 첫 회원을 등록하세요.")

    with tab2:
        # Form to add a new client
        st.subheader("새 회원 추가")

        # Use a unique form key that includes the session timestamp to prevent resubmission
        form_key = f"add_client_form_{st.session_state.get('form_timestamp', datetime.now().timestamp())}"

        with st.form(form_key):
            client_name = st.text_input("이름")

            col1, col2 = st.columns(2)
            with col1:
                client_age = st.number_input("나이", min_value = 12, max_value = 100, value = 30)
                client_height = st.number_input("키 (cm)", min_value = 100.0, max_value = 250.0, value = 170.0,
                                                step = 0.1)
                client_email = st.text_input("이메일")

            with col2:
                client_gender = st.selectbox("성별", ["남성", "여성", "기타"])
                client_weight = st.number_input("체중 (kg)", min_value = 30.0, max_value = 200.0, value = 70.0,
                                                step = 0.1)
                client_phone = st.text_input("연락처")

            submit_button = st.form_submit_button("회원 추가")
            
            print(f"DEBUG: Form submitted: {submit_button}")
            if submit_button:
                print(f"DEBUG: Inside submit_button block")
                print(f"DEBUG: Session state trainer_id: {st.session_state.get('trainer_id', 'NOT FOUND')}")
                # Use a submission guard to prevent duplicate submissions
                if 'last_submission_time' not in st.session_state or \
                        (datetime.now().timestamp() - st.session_state.last_submission_time) > 5:

                    print(f"DEBUG: Passed submission guard")
                    st.session_state.last_submission_time = datetime.now().timestamp()

                    if client_name and client_age and client_gender and client_height and client_weight:
                        # Simplified - directly add client without checking existing names for now
                        print(f"DEBUG: About to add client {client_name} for trainer {st.session_state.trainer_id}")
                        # Add client using direct method for testing
                        from add_client import add_client_direct
                        success, result = add_client_direct(
                            st.session_state.trainer_id,
                            client_name,
                            client_age,
                            client_gender,
                            client_height,
                            client_weight,
                            client_email,
                            client_phone
                        )
                        message = f"{client_name} 회원이 추가되었습니다!" if success else str(result)

                        if success:
                            # Update form timestamp to force form recreation
                            st.session_state.form_timestamp = datetime.now().timestamp()
                            st.success(message)

                            # Switch to client list tab - using rerun to refresh the page
                            st.session_state.current_page = "clients"
                            st.rerun()
                        else:
                            st.error(f"회원 추가 실패: {message}")
                    else:
                        st.warning("필수 항목(이름, 나이, 성별, 키, 체중)을 모두 입력해주세요.")


def client_detail_page():
    """Client detail page showing client info and past assessments using service layer"""
    if not st.session_state.selected_client:
        st.error("선택된 회원이 없습니다.")
        return

    # Get client details using service
    client = ClientService.get_client_details(st.session_state.selected_client)

    if not client:
        st.error("회원을 찾을 수 없습니다.")
        return

    # Display client info
    st.header(f"회원: {client['name']}")

    # Client details section
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("개인 정보")
        st.write(f"**나이:** {client['age']}")
        st.write(f"**성별:** {client['gender']}")
        st.write(f"**키:** {client['height']} cm")
        st.write(f"**체중:** {client['weight']} kg")

        # Calculate BMI using service
        bmi = ClientService.calculate_bmi(client)
        st.write(f"**BMI:** {bmi:.1f}")

    with col2:
        st.subheader("연락처 정보")
        st.write(f"**이메일:** {client['email'] or '미입력'}")
        st.write(f"**연락처:** {client['phone'] or '미입력'}")
        st.write(f"**등록일:** {client['created_at']}")

    # Assessments section
    st.divider()
    st.subheader("체력 평가 기록")

    # Get client assessments using service
    assessments = AssessmentService.get_client_assessments(client['id'])

    if assessments:
        # Button to start new assessment
        if st.button("새 평가 실시"):
            st.session_state.selected_client = client['id']
            st.session_state.current_page = "new_assessment"
            st.rerun()

        st.write(f"총 평가 수: {len(assessments)}")

        # Display assessments in reverse chronological order
        for assessment in assessments:
            assessment_id, assessment_date, overall_score = assessment

            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**평가일:** {assessment_date}")
            with col2:
                st.write(f"**종합 점수:** {overall_score:.1f}/100")
            with col3:
                if st.button("상세 보기", key = f"view_assessment_{assessment_id}"):
                    st.session_state.selected_assessment = assessment_id
                    st.session_state.current_page = "assessment_detail"
                    st.rerun()
            st.divider()
    else:
        st.info("아직 기록된 평가가 없습니다.")

        if st.button("첫 평가 실시"):
            st.session_state.selected_client = client['id']
            st.session_state.current_page = "new_assessment"
            st.rerun()


def assessment_detail_page():
    """Page to view assessment results and generate PDF report using service layer"""
    if not st.session_state.selected_assessment:
        st.error("선택된 평가가 없습니다.")
        return

    # Get assessment details using service
    assessment = AssessmentService.get_assessment_details(st.session_state.selected_assessment)

    if not assessment:
        st.error("평가를 찾을 수 없습니다.")
        return

    # Get client details using service
    client = ClientService.get_client_details(assessment['client_id'])

    if not client:
        st.error("회원을 찾을 수 없습니다.")
        return

    # Build category scores dictionary from assessment data
    category_scores = {
        'overall_score': assessment['overall_score'],
        'strength_score': assessment['strength_score'],
        'mobility_score': assessment['mobility_score'],
        'balance_score': assessment['balance_score'],
        'cardio_score': assessment['cardio_score'],
        'pfi': assessment['step_test_pfi']
    }

    # Get improvement suggestions using improved function
    suggestions = get_improvement_suggestions(assessment, client)

    # Use analytics service to analyze asymmetries
    asymmetries = AnalyticsService.analyze_asymmetries(assessment)

    # Get priority areas for training focus
    priorities = AnalyticsService.identify_priority_areas(assessment)

    # Display assessment results
    st.header(f"체력 평가 결과: {client['name']}")
    st.subheader(f"평가일: {assessment['date']}")

    # Overall score and rating
    st.markdown(f"## 종합 체력 점수: {assessment['overall_score']:.1f}/100")
    st.markdown(f"**등급:** {get_score_description(assessment['overall_score'])}")

    # Create 2 columns for the visualization and category scores
    col1, col2 = st.columns([3, 2])

    with col1:
        # Generate and display radar chart
        fig, ax = plt.subplots(figsize = (6, 6), subplot_kw = dict(polar = True))

        # Categories and values
        categories = ['근력', '가동성', '균형', '심폐지구력']
        values = [
            category_scores['strength_score'] / 25 * 100,
            category_scores['mobility_score'] / 25 * 100,
            category_scores['balance_score'] / 25 * 100,
            category_scores['cardio_score'] / 25 * 100
        ]

        # Number of variables
        N = len(categories)

        # Create angles for each category
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop

        # Values need to be circular too
        values += values[:1]

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

        st.pyplot(fig)

    with col2:
        # Display category scores
        st.subheader("카테고리 점수")

        st.markdown(f"**근력 및 근지구력:** {assessment['strength_score']:.1f}/25")
        strength_value = float(assessment['strength_score']) / 25
        st.progress(max(0.0, min(1.0, strength_value)))

        st.markdown(f"**가동성 및 유연성:** {assessment['mobility_score']:.1f}/25")
        mobility_value = float(assessment['mobility_score']) / 25
        st.progress(max(0.0, min(1.0, mobility_value)))

        st.markdown(f"**균형 및 협응성:** {assessment['balance_score']:.1f}/25")
        balance_value = float(assessment['balance_score']) / 25
        st.progress(max(0.0, min(1.0, balance_value)))

        st.markdown(f"**심폐지구력:** {assessment['cardio_score']:.1f}/25")
        cardio_value = float(assessment['cardio_score']) / 25
        st.progress(max(0.0, min(1.0, cardio_value)))

    # Display any significant asymmetries
    if asymmetries:
        st.divider()
        st.subheader("감지된 불균형")

        if 'balance' in asymmetries and asymmetries['balance']['significant']:
            st.warning(
                f"**균형 능력의 좌우 불균형 감지:** " +
                f"눈 뜬 상태 {asymmetries['balance']['open_eyes_difference']}초, " +
                f"눈 감은 상태 {asymmetries['balance']['closed_eyes_difference']}초 차이. " +
                f"{asymmetries['balance']['weaker_side'].capitalize()} 쪽 집중 훈련 권장."
            )

        if 'shoulder' in asymmetries and asymmetries['shoulder']['significant']:
            st.warning(
                f"**어깨 가동성의 좌우 불균형 감지:** " +
                f"{asymmetries['shoulder']['difference']:.1f} 주먹 거리 차이. " +
                f"{asymmetries['shoulder']['tighter_side'].capitalize()} 쪽 어깨 가동성 개선 권장."
            )

    # Priority training areas
    if priorities:
        st.divider()
        st.subheader("우선 집중 영역")

        priority_descriptions = {
            'strength': "**근력 및 근지구력:** 현재 수준이 낮으므로 집중적인 근력 훈련이 필요합니다.",
            'mobility': "**가동성 및 유연성:** 제한된 가동성이 감지되어 집중적인 개선이 필요합니다.",
            'balance': "**균형 및 협응성:** 균형 능력 향상을 위한 훈련이 우선적으로 필요합니다.",
            'cardio': "**심폐지구력:** 심폐 기능 향상을 위한 유산소 훈련이 우선시되어야 합니다.",
            'balance_asymmetry': "**균형의 좌우 불균형:** 감지된 불균형을 해소하기 위한 대칭성 향상 훈련이 필요합니다.",
            'shoulder_asymmetry': "**어깨 가동성의 좌우 불균형:** 어깨 가동성의 대칭성을 향상시키는 운동이 필요합니다.",
            'squat_pain': "**스쿼트 통증:** 통증 원인 파악 및 제거를 위한 접근이 필요합니다. 전문가 상담을 권장합니다.",
            'shoulder_pain': "**어깨 통증:** 어깨 통증 원인 파악 및 제거를 위한 접근이 필요합니다. 전문가 상담을 권장합니다."
        }

        for priority in priorities:
            if priority in priority_descriptions:
                st.write(priority_descriptions[priority])

    # Individual test results
    st.divider()
    st.subheader("테스트 결과")

    # Use tabs for displaying the test results
    test_tabs = st.tabs([
        "오버헤드 스쿼트", "푸시업", "한 발 균형",
        "발끝 터치", "어깨 가동성", "파머스 캐리", "하버드 스텝 테스트"
    ])

    with test_tabs[0]:
        st.markdown("### 오버헤드 스쿼트 (하지 근기능)")

        squat_quality = ["통증 발생", "수행 불가능", "보상 동작 관찰됨", "완벽한 동작"]

        st.markdown(
            f"**점수:** {assessment['overhead_squat_score']} - {squat_quality[assessment['overhead_squat_score']]}")

        if assessment['overhead_squat_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['overhead_squat_notes']}_")

    with test_tabs[1]:
        st.markdown("### 푸시업 (상지 근기능)")

        st.markdown(f"**반복 횟수:** {assessment['push_up_reps']}")
        st.markdown(f"**등급:** {get_score_description(assessment['push_up_score'], 4)}")

        if assessment['push_up_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['push_up_notes']}_")

    with test_tabs[2]:
        st.markdown("### 한 발 균형 (균형 및 협응성)")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**눈 뜬 상태:**")
            st.markdown(f"- 오른쪽 다리: {assessment['single_leg_balance_right_open']} 초")
            st.markdown(f"- 왼쪽 다리: {assessment['single_leg_balance_left_open']} 초")

        with col2:
            st.markdown("**눈 감은 상태:**")
            st.markdown(f"- 오른쪽 다리: {assessment['single_leg_balance_right_closed']} 초")
            st.markdown(f"- 왼쪽 다리: {assessment['single_leg_balance_left_closed']} 초")

        if assessment['single_leg_balance_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['single_leg_balance_notes']}_")

    with test_tabs[3]:
        st.markdown("### 발끝 터치 (하지 유연성)")

        st.markdown(f"**바닥에서의 거리:** {assessment['toe_touch_distance']} cm")
        st.markdown(f"**등급:** {get_score_description(assessment['toe_touch_score'], 4)}")

        if assessment['toe_touch_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['toe_touch_notes']}_")

    with test_tabs[4]:
        st.markdown("### 어깨 가동성 (상지 유연성)")

        st.markdown(f"**오른쪽 어깨 측정:** {assessment['shoulder_mobility_right']} 주먹 거리")
        st.markdown(f"**왼쪽 어깨 측정:** {assessment['shoulder_mobility_left']} 주먹 거리")

        mobility_quality = ["통증 발생", "제한적 (>2 주먹)", "보통 (1.5 주먹)", "우수 (<1 주먹)"]

        st.markdown(f"**등급:** {mobility_quality[assessment['shoulder_mobility_score']]}")

        if assessment['shoulder_mobility_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['shoulder_mobility_notes']}_")

    with test_tabs[5]:
        st.markdown("### 파머스 캐리 (악력 및 근지구력)")

        st.markdown(f"**사용 무게:** {assessment['farmers_carry_weight']} kg")
        st.markdown(f"**이동 거리:** {assessment['farmers_carry_distance']} m")
        st.markdown(f"**시간:** {assessment['farmers_carry_time']} 초")
        st.markdown(f"**등급:** {get_score_description(assessment['farmers_carry_score'], 4)}")

        if assessment['farmers_carry_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['farmers_carry_notes']}_")

    with test_tabs[6]:
        st.markdown("### 하버드 3분 스텝 테스트 (심폐지구력)")

        st.markdown("**회복기 심박수 (bpm):**")
        st.markdown(f"- 1:00-1:30 분: {assessment['step_test_hr1']}")
        st.markdown(f"- 2:00-2:30 분: {assessment['step_test_hr2']}")
        st.markdown(f"- 3:00-3:30 분: {assessment['step_test_hr3']}")

        st.markdown(f"**체력 지수 (PFI):** {assessment['step_test_pfi']:.1f}")
        st.markdown(f"**등급:** {get_score_description(assessment['step_test_score'], 4)}")

        if assessment['step_test_notes']:
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['step_test_notes']}_")

    # Progress tracking section
    st.divider()
    st.subheader("진행 상황 추적")

    # Get client's progress data
    progress_data = AnalyticsService.get_client_progress(client['id'])

    if len(progress_data['dates']) > 1:
        # Show progress charts if there are multiple assessments
        progress_tabs = st.tabs(["전체 점수", "카테고리별 점수", "개별 테스트"])

        with progress_tabs[0]:
            # Create overall score progress chart
            fig, ax = plt.subplots(figsize = (10, 5))
            ax.plot(progress_data['dates'], progress_data['overall_scores'], marker = 'o', linestyle = '-',
                    color = '#ff4b4b')
            ax.set_title('전체 체력 점수 변화')
            ax.set_xlabel('평가 날짜')
            ax.set_ylabel('점수 (100점 만점)')
            ax.grid(True, alpha = 0.3)

            # Highlight current assessment
            current_index = progress_data['dates'].index(assessment['date']) if assessment['date'] in progress_data[
                'dates'] else -1
            if current_index >= 0:
                ax.plot([progress_data['dates'][current_index]], [progress_data['overall_scores'][current_index]],
                        marker = 'o', markersize = 10, color = 'blue')

            st.pyplot(fig)

        with progress_tabs[1]:
            # Create category scores progress chart
            fig, ax = plt.subplots(figsize = (10, 5))

            categories = ['strength', 'mobility', 'balance', 'cardio']
            category_names = {'strength': '근력', 'mobility': '가동성', 'balance': '균형', 'cardio': '심폐지구력'}
            colors = {'strength': '#ff4b4b', 'mobility': '#4bbf73', 'balance': '#1f9bcf', 'cardio': '#f0ad4e'}

            for category in categories:
                ax.plot(progress_data['dates'], progress_data['category_scores'][category],
                        marker = 'o', linestyle = '-', label = category_names[category], color = colors[category])

            ax.set_title('카테고리별 점수 변화')
            ax.set_xlabel('평가 날짜')
            ax.set_ylabel('점수 (25점 만점)')
            ax.grid(True, alpha = 0.3)
            ax.legend()

            st.pyplot(fig)

        with progress_tabs[2]:
            # Create individual test scores progress chart
            test_to_show = st.selectbox(
                "테스트 선택",
                options = ["overhead_squat", "push_up", "shoulder_mobility", "farmers_carry", "step_test"],
                format_func = lambda x: {
                    "overhead_squat": "오버헤드 스쿼트",
                    "push_up": "푸시업",
                    "shoulder_mobility": "어깨 가동성",
                    "farmers_carry": "파머스 캐리",
                    "step_test": "하버드 스텝 테스트"
                }[x]
            )

            fig, ax = plt.subplots(figsize = (10, 5))
            ax.plot(progress_data['dates'], progress_data['test_scores'][test_to_show],
                    marker = 'o', linestyle = '-', color = '#ff4b4b')

            test_names = {
                "overhead_squat": "오버헤드 스쿼트",
                "push_up": "푸시업",
                "shoulder_mobility": "어깨 가동성",
                "farmers_carry": "파머스 캐리",
                "step_test": "하버드 스텝 테스트"
            }

            ax.set_title(f'{test_names[test_to_show]} 점수 변화')
            ax.set_xlabel('평가 날짜')
            ax.set_ylabel('점수')
            ax.grid(True, alpha = 0.3)

            st.pyplot(fig)
    else:
        st.info("진행 상황을 추적하려면 최소 두 번 이상의 평가가 필요합니다.")

    # Improvement suggestions
    st.divider()
    st.subheader("개선 제안")

    suggestion_tabs = st.tabs(["근력", "가동성", "균형", "심폐지구력"])

    with suggestion_tabs[0]:
        if suggestions['strength']:
            for suggestion in suggestions['strength']:
                st.markdown(f"- {suggestion}")
        else:
            st.markdown("_근력 및 근지구력 수준이 양호합니다. 현재 트레이닝을 계속하세요._")

    with suggestion_tabs[1]:
        if suggestions['mobility']:
            for suggestion in suggestions['mobility']:
                st.markdown(f"- {suggestion}")
        else:
            st.markdown("_가동성 및 유연성 수준이 양호합니다. 현재 트레이닝을 계속하세요._")

    with suggestion_tabs[2]:
        if suggestions['balance']:
            for suggestion in suggestions['balance']:
                st.markdown(f"- {suggestion}")
        else:
            st.markdown("_균형 및 협응성 수준이 양호합니다. 현재 트레이닝을 계속하세요._")

    with suggestion_tabs[3]:
        if suggestions['cardio']:
            for suggestion in suggestions['cardio']:
                st.markdown(f"- {suggestion}")
        else:
            st.markdown("_심폐지구력 수준이 양호합니다. 현재 트레이닝을 계속하세요._")

    # Generate PDF Report
    st.divider()
    st.subheader("보고서 생성")

    if st.button("PDF 보고서 생성"):
        try:
            # Create PDF report using improved function
            pdf_bytes = create_pdf_report(client, assessment, category_scores, suggestions)

            # Create download link
            st.markdown(
                get_pdf_download_link(
                    pdf_bytes,
                    f"fitness_assessment_{client['name']}_{assessment['date']}.pdf",
                    "PDF 보고서 다운로드"
                ),
                unsafe_allow_html = True
            )
        except Exception as e:
            st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
            st.info("이 오류는 한글 폰트가 설치되지 않은 경우 발생할 수 있습니다.")

    # Navigation buttons
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("회원 정보로 돌아가기"):
            st.session_state.current_page = "client_detail"
            st.rerun()

    with col2:
        if st.button("새 평가"):
            st.session_state.current_page = "new_assessment"
            st.session_state.selected_assessment = None
            st.rerun()