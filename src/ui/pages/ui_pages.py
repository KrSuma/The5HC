# ui_pages.py - UI pages for the Streamlit application with service layer integration

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import re

# Import services instead of direct database functions
from src.services.service_layer import (
    AuthService, ClientService, AssessmentService,
    DashboardService, AnalyticsService
)

# Import improved assessment scoring and report functions
from src.core.scoring import get_score_description
from src.core.recommendations import get_improvement_suggestions
from src.utils.pdf_utils import get_pdf_download_link
from src.utils.html_report_generator import create_html_report, get_html_download_link
from src.utils.weasyprint_pdf_generator import create_weasyprint_pdf


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
            
            # Button to go to session management
            def manage_sessions(client_id):
                st.session_state.selected_client_id = client_id
                st.session_state.current_page = "session_management"
                st.rerun()

            # Display the client list with buttons
            for _, row in client_df.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1.5, 1.5, 1.5])
                with col1:
                    st.write(f"**{row['이름']}**")
                with col2:
                    st.write(f"나이: {row['나이']}")
                with col3:
                    st.write(f"성별: {row['성별']}")
                with col4:
                    st.write(f"평가: {row['평가 수']}")
                with col5:
                    if st.button("상세 보기", key = f"view_{row['ID']}"):
                        view_client(row['ID'])
                with col6:
                    if st.button("세션 관리", key = f"session_{row['ID']}"):
                        manage_sessions(row['ID'])
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
            
            if submit_button:
                # Use a submission guard to prevent duplicate submissions
                if 'last_submission_time' not in st.session_state or \
                        (datetime.now().timestamp() - st.session_state.last_submission_time) > 5:

                    st.session_state.last_submission_time = datetime.now().timestamp()

                    if client_name and client_age and client_gender and client_height and client_weight:
                        # Add client using service
                        success, message = ClientService.add_client(
                            trainer_id=st.session_state.trainer_id,
                            name=client_name,
                            age=client_age,
                            gender=client_gender,
                            height=client_height,
                            weight=client_weight,
                            email=client_email,
                            phone=client_phone
                        )

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
            assessment_id = assessment['id']
            assessment_date = assessment['date']
            overall_score = assessment.get('overall_score', 0.0)

            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"**평가일:** {assessment_date}")
            with col2:
                if overall_score:
                    st.write(f"**종합 점수:** {overall_score:.1f}/100")
                else:
                    st.write("**종합 점수:** 계산 중...")
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
    
    # Session Management section
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("세션 관리", use_container_width=True):
            st.session_state.selected_client_id = client['id']
            st.session_state.current_page = "session_management"
            st.rerun()
    
    with col2:
        if st.button("회원 목록으로 돌아가기", use_container_width=True):
            st.session_state.current_page = "clients"
            st.session_state.selected_client = None
            st.rerun()


def assessment_detail_page():
    """Page to view assessment results and generate PDF report using service layer"""
    if not st.session_state.selected_assessment:
        st.error("선택된 평가가 없습니다.")
        return

    try:
        # Get assessment details using service
        assessment = AssessmentService.get_assessment_details(st.session_state.selected_assessment)

        if not assessment:
            st.error("평가를 찾을 수 없습니다.")
            return

        # Get client details using service
        client_id = assessment.get('client_id')
        if not client_id:
            st.error("평가에서 회원 ID를 찾을 수 없습니다.")
            return
            
        client = ClientService.get_client_details(client_id)

        if not client:
            st.error(f"회원을 찾을 수 없습니다. (ID: {client_id})")
            return
    except Exception as e:
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {str(e)}")
        return

    try:
        # Build category scores dictionary from assessment data
        # Extract PFI from notes if available
        notes = assessment.get('harvard_step_test_notes', '')
        pfi_match = re.search(r'PFI:\s*([\d.]+)', notes)
        pfi = float(pfi_match.group(1)) if pfi_match else 0.0
        
        # Ensure all scores are numeric (convert None to 0)
        category_scores = {
            'overall_score': float(assessment.get('overall_score') or 0),
            'strength_score': float(assessment.get('strength_score') or 0),
            'mobility_score': float(assessment.get('mobility_score') or 0),
            'balance_score': float(assessment.get('balance_score') or 0),
            'cardio_score': float(assessment.get('cardio_score') or 0),
            'pfi': pfi
        }

        # Get improvement suggestions using improved function
        suggestions = get_improvement_suggestions(assessment, client)

        # Use analytics service to analyze asymmetries
        asymmetries = AnalyticsService.analyze_asymmetries(assessment)

        # Get priority areas for training focus
        priorities = AnalyticsService.identify_priority_areas(assessment)
    except Exception as e:
        st.error(f"평가 데이터 처리 중 오류가 발생했습니다: {str(e)}")
        # Provide defaults to continue with partial display
        category_scores = {
            'overall_score': 0,
            'strength_score': 0,
            'mobility_score': 0,
            'balance_score': 0,
            'cardio_score': 0,
            'pfi': 0
        }
        suggestions = {'strength': [], 'mobility': [], 'balance': [], 'cardio': []}
        asymmetries = {}
        priorities = []

    # Display assessment results
    st.header(f"체력 평가 결과: {client['name']}")
    st.subheader(f"평가일: {assessment['date']}")

    # Overall score and rating
    overall_score = float(assessment.get('overall_score') or 0)
    st.markdown(f"## 종합 체력 점수: {overall_score:.1f}/100")
    st.markdown(f"**등급:** {get_score_description(overall_score)}")

    # Create modern horizontal bar chart for better visualization
    st.subheader("Category Scores")
    
    # Prepare data
    categories = ['Strength & Endurance', 'Mobility & Flexibility', 'Balance & Coordination', 'Cardiovascular']
    scores = [
        float(assessment.get('strength_score') or 0),
        float(assessment.get('mobility_score') or 0),
        float(assessment.get('balance_score') or 0),
        float(assessment.get('cardio_score') or 0)
    ]
    percentages = [min(100, score / 25 * 100) for score in scores]
    
    # Create color mapping based on performance
    def get_color(percentage):
        if percentage >= 80:
            return '#2E8B57'  # Green for excellent
        elif percentage >= 60:
            return '#4682B4'  # Blue for good
        elif percentage >= 40:
            return '#DAA520'  # Gold for average
        else:
            return '#CD5C5C'  # Red for needs improvement
    
    colors = [get_color(p) for p in percentages]
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bars
    bars = ax.barh(categories, percentages, color=colors, alpha=0.8, height=0.6)
    
    # Customize the chart
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)', fontsize=12)
    ax.set_title('Fitness Assessment Category Scores', fontsize=14, fontweight='bold', pad=20)
    
    # Add score labels on bars
    for i, (bar, score, percentage) in enumerate(zip(bars, scores, percentages)):
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2, 
                f'{score:.1f}/25 ({percentage:.0f}%)', 
                ha='left', va='center', fontweight='bold', fontsize=10)
    
    # Add grid for better readability
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Remove spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Add performance zones background
    ax.axvspan(0, 40, alpha=0.1, color='red', label='Needs Improvement')
    ax.axvspan(40, 60, alpha=0.1, color='orange', label='Average')
    ax.axvspan(60, 80, alpha=0.1, color='blue', label='Good')
    ax.axvspan(80, 100, alpha=0.1, color='green', label='Excellent')
    
    # Adjust layout
    plt.tight_layout()
    
    # Display the chart
    st.pyplot(fig, use_container_width=False)

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

        squat_score = int(assessment.get('overhead_squat_score', 0))
        st.markdown(
            f"**점수:** {squat_score} - {squat_quality[squat_score] if squat_score < len(squat_quality) else '알 수 없음'}")

        if assessment.get('overhead_squat_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['overhead_squat_notes']}_")

    with test_tabs[1]:
        st.markdown("### 푸시업 (상지 근기능)")

        push_up_reps = int(assessment.get('push_up_reps', 0))
        push_up_score = int(assessment.get('push_up_score', 0))
        st.markdown(f"**반복 횟수:** {push_up_reps}")
        st.markdown(f"**등급:** {get_score_description(push_up_score, 4)}")

        if assessment.get('push_up_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['push_up_notes']}_")

    with test_tabs[2]:
        st.markdown("### 한 발 균형 (균형 및 협응성)")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**눈 뜬 상태:**")
            st.markdown(f"- 오른쪽 다리: {assessment.get('single_leg_balance_right_eyes_open', 0)} 초")
            st.markdown(f"- 왼쪽 다리: {assessment.get('single_leg_balance_left_eyes_open', 0)} 초")

        with col2:
            st.markdown("**눈 감은 상태:**")
            st.markdown(f"- 오른쪽 다리: {assessment.get('single_leg_balance_right_eyes_closed', 0)} 초")
            st.markdown(f"- 왼쪽 다리: {assessment.get('single_leg_balance_left_eyes_closed', 0)} 초")

        if assessment.get('single_leg_balance_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['single_leg_balance_notes']}_")

    with test_tabs[3]:
        st.markdown("### 발끝 터치 (하지 유연성)")

        toe_touch_distance = float(assessment.get('toe_touch_distance', 0))
        toe_touch_score = int(assessment.get('toe_touch_score', 0))
        st.markdown(f"**바닥에서의 거리:** {toe_touch_distance} cm")
        st.markdown(f"**등급:** {get_score_description(toe_touch_score, 4)}")

        if assessment.get('toe_touch_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['toe_touch_notes']}_")

    with test_tabs[4]:
        st.markdown("### 어깨 가동성 (상지 유연성)")

        shoulder_right = float(assessment.get('shoulder_mobility_right', 0))
        shoulder_left = float(assessment.get('shoulder_mobility_left', 0))
        st.markdown(f"**오른쪽 어깨 측정:** {shoulder_right} 주먹 거리")
        st.markdown(f"**왼쪽 어깨 측정:** {shoulder_left} 주먹 거리")

        mobility_quality = ["통증 발생", "제한적 (>2 주먹)", "보통 (1.5 주먹)", "우수 (<1 주먹)"]

        shoulder_score = int(assessment.get('shoulder_mobility_score', 0))
        st.markdown(f"**등급:** {mobility_quality[shoulder_score] if shoulder_score < len(mobility_quality) else '알 수 없음'}")

        if assessment.get('shoulder_mobility_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['shoulder_mobility_notes']}_")

    with test_tabs[5]:
        st.markdown("### 파머스 캐리 (악력 및 근지구력)")

        st.markdown(f"**사용 무게:** {assessment.get('farmer_carry_weight', 0)} kg")
        st.markdown(f"**이동 거리:** {assessment.get('farmer_carry_distance', 0)} m")
        
        # Extract time from notes if available
        fc_notes = assessment.get('farmer_carry_notes', '')
        time_match = re.search(r'수행 시간:\s*(\d+)초', fc_notes)
        fc_time = int(time_match.group(1)) if time_match else 0
        
        st.markdown(f"**시간:** {fc_time} 초")
        
        fc_score = assessment.get('strength_score', 0)
        if fc_score > 0:
            st.markdown(f"**등급:** {get_score_description(int(fc_score/6.25), 4)}")

        if assessment.get('farmer_carry_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['farmer_carry_notes']}_")

    with test_tabs[6]:
        st.markdown("### 하버드 3분 스텝 테스트 (심폐지구력)")

        # Extract HR values from notes if available
        notes = assessment.get('harvard_step_test_notes', '')
        hr1, hr2, hr3, pfi = 0, 0, 0, 0.0
        
        # Try to parse values from notes
        hr_match = re.search(r'HR1:\s*(\d+),\s*HR2:\s*(\d+),\s*HR3:\s*(\d+)', notes)
        pfi_match = re.search(r'PFI:\s*([\d.]+)', notes)
        
        if hr_match:
            hr1, hr2, hr3 = int(hr_match.group(1)), int(hr_match.group(2)), int(hr_match.group(3))
        if pfi_match:
            pfi = float(pfi_match.group(1))
        
        st.markdown("**회복기 심박수 (bpm):**")
        st.markdown(f"- 1:00-1:30 분: {hr1}")
        st.markdown(f"- 2:00-2:30 분: {hr2}")
        st.markdown(f"- 3:00-3:30 분: {hr3}")

        st.markdown(f"**체력 지수 (PFI):** {pfi:.1f}")
        
        # Get step test score from cardio score
        step_test_score = assessment.get('cardio_score', 0)
        if step_test_score > 0:
            st.markdown(f"**등급:** {get_score_description(int(step_test_score/6.25), 4)}")

        if assessment.get('harvard_step_test_notes'):
            st.markdown("**메모:**")
            st.markdown(f"_{assessment['harvard_step_test_notes']}_")

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
            fig, ax = plt.subplots(figsize = (8, 4))
            ax.plot(progress_data['dates'], progress_data['overall_scores'], marker = 'o', linestyle = '-',
                    color = '#ff4b4b')
            ax.set_title('Overall Fitness Score Progress')
            ax.set_xlabel('Assessment Date')
            ax.set_ylabel('Score (Out of 100)')
            ax.grid(True, alpha = 0.3)

            # Highlight current assessment
            current_index = progress_data['dates'].index(assessment['date']) if assessment['date'] in progress_data[
                'dates'] else -1
            if current_index >= 0:
                ax.plot([progress_data['dates'][current_index]], [progress_data['overall_scores'][current_index]],
                        marker = 'o', markersize = 10, color = 'blue')

            st.pyplot(fig, use_container_width=False)

        with progress_tabs[1]:
            # Create category scores progress chart
            fig, ax = plt.subplots(figsize = (8, 4))

            categories = ['strength', 'mobility', 'balance', 'cardio']
            category_names = {'strength': 'Strength', 'mobility': 'Mobility', 'balance': 'Balance', 'cardio': 'Cardio'}
            colors = {'strength': '#ff4b4b', 'mobility': '#4bbf73', 'balance': '#1f9bcf', 'cardio': '#f0ad4e'}

            for category in categories:
                ax.plot(progress_data['dates'], progress_data['category_scores'][category],
                        marker = 'o', linestyle = '-', label = category_names[category], color = colors[category])

            ax.set_title('Category Score Progress')
            ax.set_xlabel('Assessment Date')
            ax.set_ylabel('Score (Out of 25)')
            ax.grid(True, alpha = 0.3)
            ax.legend()

            st.pyplot(fig, use_container_width=False)

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

            fig, ax = plt.subplots(figsize = (8, 4))
            ax.plot(progress_data['dates'], progress_data['test_scores'][test_to_show],
                    marker = 'o', linestyle = '-', color = '#ff4b4b')

            test_names = {
                "overhead_squat": "Overhead Squat",
                "push_up": "Push Up",
                "shoulder_mobility": "Shoulder Mobility",
                "farmers_carry": "Farmers Carry",
                "step_test": "Harvard Step Test"
            }

            ax.set_title(f'{test_names[test_to_show]} Score Progress')
            ax.set_xlabel('Assessment Date')
            ax.set_ylabel('Score')
            ax.grid(True, alpha = 0.3)

            st.pyplot(fig, use_container_width=False)
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

    # Generate Reports
    st.divider()
    st.subheader("보고서 생성")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("HTML 보고서", use_container_width=True):
            try:
                # Get trainer name from session state
                trainer_name = st.session_state.get('trainer_name', '트레이너')
                
                # Create HTML report using improved function
                html_content = create_html_report(client, assessment, category_scores, suggestions, trainer_name)

                # Create download link
                st.markdown(
                    get_html_download_link(
                        html_content,
                        f"fitness_assessment_{client['name']}_{assessment['date']}.html",
                        "HTML 보고서 다운로드"
                    ),
                    unsafe_allow_html = True
                )
                
                # Show preview option
                with st.expander("보고서 미리보기"):
                    st.components.v1.html(html_content, height=600, scrolling=True)
                    
            except Exception as e:
                st.error(f"HTML 보고서 생성 중 오류가 발생했습니다: {str(e)}")

    with col2:
        if st.button("PDF 보고서", use_container_width=True):
            try:
                # Get trainer name from session state
                trainer_name = st.session_state.get('trainer_name', '트레이너')
                
                # Create WeasyPrint PDF report from HTML
                with st.spinner("고품질 PDF 생성 중..."):
                    pdf_bytes = create_weasyprint_pdf(client, assessment, category_scores, suggestions, trainer_name)

                # Create download link
                st.markdown(
                    get_pdf_download_link(
                        pdf_bytes,
                        f"fitness_assessment_{client['name']}_{assessment['date']}.pdf",
                        "PDF 보고서 다운로드"
                    ),
                    unsafe_allow_html = True
                )
                st.success("PDF 보고서가 생성되었습니다!")
                
            except Exception as e:
                st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
                st.info("PDF 생성에 실패했습니다. HTML 보고서를 사용해주세요.")

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


def session_management_page():
    """Session and credit management page"""
    st.title("세션 및 크레딧 관리")
    
    if 'selected_client_id' not in st.session_state:
        st.warning("세션을 관리할 고객을 먼저 선택해주세요.")
        if st.button("고객 목록으로 돌아가기"):
            st.session_state.current_page = "clients"
            st.rerun()
        return
    
    client_id = st.session_state.selected_client_id
    
    try:
        # Get client details
        client = ClientService.get_client_details(client_id)
        if not client:
            st.error("고객 정보를 찾을 수 없습니다.")
            return
        
        st.header(f"{client['name']} - 세션 관리")
        
        # Initialize session service
        from src.services.service_layer import SessionManagementService
        session_service = SessionManagementService()
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs(["패키지 관리", "세션 일정", "세션 기록", "결제 내역"])
        
        with tab1:
            st.subheader("세션 패키지")
            
            # Create new package
            with st.expander("새 패키지 생성"):
                col1, col2 = st.columns(2)
                
                with col1:
                    total_amount = st.number_input(
                        "총 결제 금액 (KRW)", 
                        min_value=0, 
                        value=300000, 
                        step=10000,
                        help="고객이 결제한 총 금액"
                    )
                    
                    session_price = st.number_input(
                        "세션당 가격 (KRW)", 
                        min_value=1000, 
                        value=60000, 
                        step=5000,
                        help="개별 세션의 가격"
                    )
                
                with col2:
                    package_name = st.text_input(
                        "패키지 이름 (선택사항)", 
                        placeholder="예: 5회 집중 트레이닝"
                    )
                    
                    notes = st.text_area(
                        "메모 (선택사항)", 
                        placeholder="패키지에 대한 추가 메모"
                    )
                
                total_sessions = total_amount // session_price if session_price > 0 else 0
                st.info(f"총 세션 수: {total_sessions}회")
                
                if st.button("패키지 생성"):
                    if total_amount > 0 and session_price > 0:
                        try:
                            package_id = session_service.create_package(
                                client_id, total_amount, session_price, package_name, notes
                            )
                            st.success(f"패키지가 생성되었습니다! (ID: {package_id})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"패키지 생성 중 오류: {e}")
                    else:
                        st.error("유효한 금액과 세션 가격을 입력해주세요.")
            
            # Display existing packages
            st.subheader("기존 패키지")
            
            try:
                packages = session_service.get_client_packages(client_id, active_only=False)
                
                if packages:
                    for package in packages:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                            
                            with col1:
                                package_title = package.package_name or f"패키지 #{package.id}"
                                status_color = "green" if package.is_active else "red"
                                status_text = "활성" if package.is_active else "비활성"
                                
                                st.markdown(f"**{package_title}** :{status_color}[{status_text}]")
                                # Handle both string and datetime objects for created_at
                                if isinstance(package.created_at, str):
                                    created_date = package.created_at[:10]
                                else:
                                    # Assume it's a datetime object
                                    created_date = package.created_at.strftime("%Y-%m-%d")
                                st.caption(f"생성일: {created_date}")
                            
                            with col2:
                                st.metric(
                                    "잔여 크레딧", 
                                    f"₩{package.remaining_credits:,}",
                                    help="남은 결제 금액"
                                )
                            
                            with col3:
                                st.metric(
                                    "잔여 세션", 
                                    f"{package.remaining_sessions}회",
                                    help="남은 세션 수"
                                )
                            
                            with col4:
                                utilization = ((package.total_sessions - package.remaining_sessions) / package.total_sessions * 100) if package.total_sessions > 0 else 0
                                st.metric(
                                    "사용률", 
                                    f"{utilization:.1f}%",
                                    help="패키지 사용률"
                                )
                            
                            # Package actions
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                if st.button(f"크레딧 추가", key=f"add_credit_{package.id}"):
                                    st.session_state.add_credit_package_id = package.id
                            
                            with action_col2:
                                if st.button(f"상세 보기", key=f"detail_{package.id}"):
                                    st.session_state.selected_package_id = package.id
                                    st.session_state.show_package_detail = True
                            
                            st.divider()
                else:
                    st.info("아직 생성된 패키지가 없습니다.")
                    
            except Exception as e:
                st.error(f"패키지 정보를 불러오는 중 오류: {e}")
            
            # Add credit modal
            if hasattr(st.session_state, 'add_credit_package_id'):
                with st.expander("크레딧 추가", expanded=True):
                    credit_amount = st.number_input(
                        "추가할 금액 (KRW)", 
                        min_value=0, 
                        value=60000, 
                        step=10000
                    )
                    
                    payment_method = st.selectbox(
                        "결제 방법", 
                        ["현금", "카드", "계좌이체", "기타"]
                    )
                    
                    description = st.text_area("메모 (선택사항)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("크레딧 추가"):
                            try:
                                session_service.add_credits(
                                    client_id, credit_amount, payment_method, description
                                )
                                st.success(f"₩{credit_amount:,} 크레딧이 추가되었습니다!")
                                del st.session_state.add_credit_package_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"크레딧 추가 중 오류: {e}")
                    
                    with col2:
                        if st.button("취소"):
                            del st.session_state.add_credit_package_id
                            st.rerun()
        
        with tab2:
            st.subheader("세션 일정 관리")
            
            # Get active packages for session scheduling
            try:
                active_packages = session_service.get_client_packages(client_id, active_only=True)
                
                if not active_packages:
                    st.warning("활성화된 패키지가 없습니다. 먼저 패키지를 생성해주세요.")
                else:
                    # Schedule new session
                    with st.expander("새 세션 예약"):
                        package_options = {
                            f"패키지 #{pkg.id} (잔여: {pkg.remaining_sessions}회)": pkg.id 
                            for pkg in active_packages if pkg.remaining_sessions > 0
                        }
                        
                        if not package_options:
                            st.warning("잔여 세션이 있는 패키지가 없습니다.")
                        else:
                            selected_package_name = st.selectbox(
                                "패키지 선택", 
                                list(package_options.keys())
                            )
                            selected_package_id = package_options[selected_package_name]
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                session_date = st.date_input(
                                    "세션 날짜", 
                                    value=datetime.now().date()
                                )
                                
                                session_time = st.time_input(
                                    "세션 시간", 
                                    value=datetime.now().replace(hour=10, minute=0).time()
                                )
                            
                            with col2:
                                session_duration = st.number_input(
                                    "세션 시간 (분)", 
                                    min_value=30, 
                                    value=60, 
                                    step=15
                                )
                                
                                session_notes = st.text_area("세션 메모 (선택사항)")
                            
                            if st.button("세션 예약"):
                                try:
                                    session_id = session_service.schedule_session(
                                        client_id, selected_package_id, 
                                        str(session_date), str(session_time),
                                        session_duration, session_notes
                                    )
                                    st.success(f"세션이 예약되었습니다! (ID: {session_id})")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"세션 예약 중 오류: {e}")
                    
                    # Display upcoming sessions
                    st.subheader("예정된 세션")
                    
                    try:
                        scheduled_sessions = session_service.get_client_sessions(client_id, "scheduled")
                        
                        if scheduled_sessions:
                            for session in scheduled_sessions:
                                with st.container():
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    
                                    with col1:
                                        st.markdown(f"**{session.session_date} {session.session_time or ''}**")
                                        st.caption(f"시간: {session.session_duration}분 | 비용: ₩{session.session_cost:,}")
                                        if session.notes:
                                            st.caption(f"메모: {session.notes}")
                                    
                                    with col2:
                                        if st.button("완료", key=f"complete_{session.id}"):
                                            try:
                                                session_service.complete_session(session.id)
                                                st.success("세션이 완료되었습니다!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"세션 완료 중 오류: {e}")
                                    
                                    with col3:
                                        if st.button("취소", key=f"cancel_{session.id}"):
                                            try:
                                                session_service.cancel_session(session.id, "사용자 취소")
                                                st.success("세션이 취소되었습니다!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"세션 취소 중 오류: {e}")
                                    
                                    st.divider()
                        else:
                            st.info("예정된 세션이 없습니다.")
                            
                    except Exception as e:
                        st.error(f"세션 정보를 불러오는 중 오류: {e}")
                        
            except Exception as e:
                st.error(f"패키지 정보를 불러오는 중 오류: {e}")
        
        with tab3:
            st.subheader("세션 기록")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox(
                    "상태 필터", 
                    ["전체", "완료", "취소"], 
                    index=0
                )
            
            with col2:
                limit = st.number_input(
                    "표시할 기록 수", 
                    min_value=5, 
                    max_value=100, 
                    value=20
                )
            
            # Get session history
            try:
                status_map = {"전체": None, "완료": "completed", "취소": "cancelled"}
                sessions = session_service.get_client_sessions(client_id, status_map[status_filter])
                
                if sessions:
                    # Limit results
                    sessions = sessions[:limit]
                    
                    for session in sessions:
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                status_color = {"completed": "green", "cancelled": "red", "scheduled": "blue"}
                                status_text = {"completed": "완료", "cancelled": "취소", "scheduled": "예정"}
                                
                                st.markdown(f"**{session.session_date} {session.session_time or ''}**")
                                st.markdown(f":{status_color.get(session.status, 'gray')}[{status_text.get(session.status, session.status)}]")
                                
                                if session.notes:
                                    st.caption(f"메모: {session.notes}")
                            
                            with col2:
                                st.metric("시간", f"{session.session_duration}분")
                            
                            with col3:
                                st.metric("비용", f"₩{session.session_cost:,}")
                            
                            st.divider()
                            
                    # Summary statistics
                    completed_sessions = [s for s in sessions if s.status == "completed"]
                    total_spent = sum(s.session_cost for s in completed_sessions)
                    
                    st.subheader("요약")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("총 세션", len(sessions))
                    
                    with col2:
                        st.metric("완료된 세션", len(completed_sessions))
                    
                    with col3:
                        st.metric("총 사용 금액", f"₩{total_spent:,}")
                        
                else:
                    st.info("세션 기록이 없습니다.")
                    
            except Exception as e:
                st.error(f"세션 기록을 불러오는 중 오류: {e}")
        
        with tab4:
            st.subheader("결제 내역")
            
            try:
                payments = session_service.get_payment_history(client_id)
                
                if payments:
                    for payment in payments:
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{payment.payment_date}**")
                                st.caption(f"방법: {payment.payment_method or 'N/A'}")
                                if payment.description:
                                    st.caption(f"설명: {payment.description}")
                            
                            with col2:
                                st.metric("금액", f"₩{payment.amount:,}")
                            
                            with col3:
                                if payment.package_id:
                                    st.caption(f"패키지 #{payment.package_id}")
                            
                            st.divider()
                    
                    # Payment summary
                    total_payments = sum(p.amount for p in payments)
                    st.metric("총 결제 금액", f"₩{total_payments:,}")
                    
                else:
                    st.info("결제 내역이 없습니다.")
                    
            except Exception as e:
                st.error(f"결제 내역을 불러오는 중 오류: {e}")
        
        # Back button
        st.divider()
        if st.button("고객 상세로 돌아가기"):
            st.session_state.current_page = "client_detail"
            st.rerun()
            
    except Exception as e:
        st.error(f"세션 관리 페이지를 불러오는 중 오류: {e}")
        if st.button("고객 목록으로 돌아가기"):
            st.session_state.current_page = "clients"
            st.rerun()