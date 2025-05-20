# ui_pages.py - UI pages for the Streamlit application

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import re
import sqlite3

from db_utils import (authenticate, register_trainer, get_client_details, get_clients,
                      add_client, get_client_assessments, get_assessment_details,
                      save_assessment, get_recent_assessments, get_trainer_stats)
from assessment_scoring import (calculate_pushup_score, calculate_toe_touch_score,
                                calculate_single_leg_balance_score, calculate_step_test_score,
                                calculate_category_scores, get_score_description)
from recommendations import get_improvement_suggestions
from pdf_generator import create_pdf_report, get_pdf_download_link


def login_register_page():
    """Login and registration page"""
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        st.header("로그인")
        username = st.text_input("아이디", key = "login_username")
        password = st.text_input("비밀번호", type = "password", key = "login_password")

        if st.button("로그인", key = "login_button"):
            if username and password:
                trainer_id = authenticate(username, password)
                if trainer_id:
                    # Get trainer name
                    conn = sqlite3.connect('fitness_assessment.db')
                    c = conn.cursor()
                    c.execute("SELECT name FROM trainers WHERE id = ?", (trainer_id,))
                    trainer_name = c.fetchone()[0]
                    conn.close()

                    st.session_state.logged_in = True
                    st.session_state.trainer_id = trainer_id
                    st.session_state.trainer_name = trainer_name
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
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
                    success = register_trainer(new_username, new_password, name, email)
                    if success:
                        st.success("회원가입이 완료되었습니다! 로그인해주세요.")
                    else:
                        st.error("이미 사용 중인 아이디 또는 이메일입니다.")
            else:
                st.warning("모든 항목을 입력해주세요.")


def dashboard_page():
    """Dashboard page showing recent assessments and stats"""
    st.header("대시보드")

    # Get trainer stats and recent assessments
    stats = get_trainer_stats(st.session_state.trainer_id)
    recent_assessments = get_recent_assessments(st.session_state.trainer_id)

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

    # Fetch recent assessments
    conn = sqlite3.connect('fitness_assessment.db')
    c = conn.cursor()

    # Count total clients and assessments
    c.execute("SELECT COUNT(*) FROM clients WHERE trainer_id = ?", (st.session_state.trainer_id,))
    total_clients = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM assessments WHERE trainer_id = ?", (st.session_state.trainer_id,))
    total_assessments = c.fetchone()[0]

    # Fetch all clients for search functionality
    c.execute("SELECT id, name FROM clients WHERE trainer_id = ? ORDER BY name", (st.session_state.trainer_id,))
    all_clients = c.fetchall()
    client_dict = {client[0]: client[1] for client in all_clients}

    # Fetch all assessments for the trainer
    c.execute("""
              SELECT a.id, a.client_id, c.name, a.date, a.overall_score
              FROM assessments a
                       JOIN clients c ON a.client_id = c.id
              WHERE a.trainer_id = ?
              ORDER BY a.date DESC
              """, (st.session_state.trainer_id,))

    all_assessments = c.fetchall()
    conn.close()

    # Display stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("전체 회원", total_clients)
    with col2:
        st.metric("전체 평가", total_assessments)

    # Add search functionality
    st.subheader("평가 검색")

    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        # Offer different search options
        search_option = st.selectbox(
            "검색 기준",
            options = ["모든 평가", "회원명", "날짜", "점수 범위"]
        )

    # Different search inputs based on selected option
    if search_option == "회원명":
        client_names = ["모든 회원"] + list(client_dict.values())
        selected_client_name = st.selectbox("회원 선택", client_names)

        if selected_client_name != "모든 회원":
            # Get the client_id from the name
            selected_client_id = [k for k, v in client_dict.items() if v == selected_client_name][0]
            # Filter assessments by client_id
            filtered_assessments = [a for a in all_assessments if a[1] == selected_client_id]
        else:
            filtered_assessments = all_assessments

    elif search_option == "날짜":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", datetime.now() - pd.Timedelta(days = 30))
        with col2:
            end_date = st.date_input("종료일", datetime.now())

        # Convert to string format for comparison
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Filter assessments by date range
        filtered_assessments = [a for a in all_assessments if start_date_str <= a[3] <= end_date_str]

    elif search_option == "점수 범위":
        col1, col2 = st.columns(2)
        with col1:
            min_score = st.slider("최소 점수", 0, 100, 0)
        with col2:
            max_score = st.slider("최대 점수", 0, 100, 100)

        # Filter assessments by score range
        filtered_assessments = [a for a in all_assessments if min_score <= a[4] <= max_score]

    else:  # "모든 평가"
        filtered_assessments = all_assessments

    # Display filtered assessments
    st.subheader("평가 결과")

    if filtered_assessments:
        # Convert to DataFrame for easier manipulation
        assessment_df = pd.DataFrame(
            filtered_assessments,
            columns = ["ID", "Client_ID", "회원 이름", "날짜", "종합 점수"]
        )

        # Add a description column
        assessment_df["상태"] = assessment_df["종합 점수"].apply(
            lambda score: get_score_description(score)
        )

        # Format the score with 1 decimal place
        assessment_df["종합 점수"] = assessment_df["종합 점수"].apply(
            lambda score: f"{score:.1f}/100"
        )

        # Remove unnecessary columns
        assessment_df = assessment_df.drop(columns = ["Client_ID"])

        st.dataframe(
            assessment_df,
            column_config = {
                "ID": None,  # Hide ID column
            },
            hide_index = True,
            use_container_width = True
        )

        # Function to view assessment details
        def view_assessment(assessment_id):
            st.session_state.selected_assessment = assessment_id
            st.session_state.current_page = "assessment_detail"
            st.rerun()

        # Get the selected assessment ID from the clicked row
        selected_assessment = st.selectbox(
            "평가 선택",
            options = [(a[0], f"{a[2]} - {a[3]} ({a[4]:.1f}/100)") for a in filtered_assessments],
            format_func = lambda x: x[1]
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("선택한 평가 상세 보기"):
                view_assessment(selected_assessment[0])

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
    """Clients management page"""
    st.header("회원 관리")

    # Create tabs for client list and add new client
    tab1, tab2 = st.tabs(["회원 목록", "새 회원 추가"])

    with tab1:
        # Fetch clients for the logged-in trainer
        clients = get_clients(st.session_state.trainer_id)

        if clients:
            # Display clients in a table
            client_df = pd.DataFrame(clients, columns = ["ID", "이름"])

            # Get assessment counts for each client
            client_df["평가 수"] = client_df["ID"].apply(
                lambda client_id: len(get_client_assessments(client_id))
            )

            # Get client details for additional information
            client_df["나이"] = client_df["ID"].apply(
                lambda client_id: get_client_details(client_id)["age"]
            )

            client_df["성별"] = client_df["ID"].apply(
                lambda client_id: get_client_details(client_id)["gender"]
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

        with st.form("add_client_form"):
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
                if client_name and client_age and client_gender and client_height and client_weight:
                    # Add client to database
                    client_id = add_client(
                        st.session_state.trainer_id,
                        client_name,
                        client_age,
                        client_gender,
                        client_height,
                        client_weight,
                        client_email,
                        client_phone
                    )

                    if client_id:
                        st.success(f"{client_name} 회원이 추가되었습니다!")
                        # Switch to client list tab
                        st.session_state.current_page = "clients"
                        st.rerun()
                else:
                    st.warning("필수 항목(이름, 나이, 성별, 키, 체중)을 모두 입력해주세요.")


def client_detail_page():
    """Client detail page showing client info and past assessments"""
    if not st.session_state.selected_client:
        st.error("선택된 회원이 없습니다.")
        return

    # Get client details
    client = get_client_details(st.session_state.selected_client)

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
        st.write(f"**BMI:** {client['weight'] / ((client['height'] / 100) ** 2):.1f}")

    with col2:
        st.subheader("연락처 정보")
        st.write(f"**이메일:** {client['email'] or '미입력'}")
        st.write(f"**연락처:** {client['phone'] or '미입력'}")
        st.write(f"**등록일:** {client['registration_date']}")

    # Assessments section
    st.divider()
    st.subheader("체력 평가 기록")

    # Get client assessments
    assessments = get_client_assessments(client['id'])

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


def new_assessment_page():
    """Page to conduct a new fitness assessment"""
    if not st.session_state.selected_client:
        # If no client is selected, allow selecting one
        st.header("새 체력 평가")
        st.subheader("회원 선택")

        clients = get_clients(st.session_state.trainer_id)

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

    # Get client details
    client = get_client_details(st.session_state.selected_client)

    if not client:
        st.error("회원을 찾을 수 없습니다.")
        return

    st.header(f"{client['name']} 회원 체력 평가")
    st.write(
        f"**나이:** {client['age']} | **성별:** {client['gender']} | **키:** {client['height']} cm | **체중:** {client['weight']} kg")

    # Create a form for the assessment
    with st.form("assessment_form"):
        st.subheader("1. 오버헤드 스쿼트 (하지 근기능)")
        overhead_squat_score = st.selectbox(
            "수행 품질",
            [
                (0, "동작 중 통증 발생"),
                (1, "깊은 스쿼트 수행 불가능"),
                (2, "보상 동작 관찰됨 (발 뒤꿈치 들림, 무릎 내반 등)"),
                (3, "완벽한 동작 (상체 수직 유지, 대퇴가 수평 이하, 무릎 정렬)")
            ],
            format_func = lambda x: x[1]
        )[0]
        overhead_squat_notes = st.text_area("메모 (보상 동작, 제한사항 등)", key = "overhead_squat_notes")

        st.divider()
        st.subheader("2. 푸시업 (상지 근기능)")
        push_up_reps = st.number_input("반복 횟수", min_value = 0, max_value = 100, value = 0, step = 1)
        push_up_notes = st.text_area("메모 (폼 이슈, 제한사항 등)", key = "push_up_notes")

        st.divider()
        st.subheader("3. 한 발 균형 (균형 및 협응성)")
        col1, col2 = st.columns(2)
        with col1:
            single_leg_balance_right_open = st.number_input("오른쪽 다리, 눈 뜬 상태 (초)", min_value = 0, max_value = 60,
                                                            value = 0, step = 1)
            single_leg_balance_right_closed = st.number_input("오른쪽 다리, 눈 감은 상태 (초)", min_value = 0, max_value = 60,
                                                              value = 0, step = 1)
        with col2:
            single_leg_balance_left_open = st.number_input("왼쪽 다리, 눈 뜬 상태 (초)", min_value = 0, max_value = 60,
                                                           value = 0, step = 1)
            single_leg_balance_left_closed = st.number_input("왼쪽 다리, 눈 감은 상태 (초)", min_value = 0, max_value = 60,
                                                             value = 0, step = 1)
        single_leg_balance_notes = st.text_area("메모 (안정성 문제, 좌우 비대칭 등)", key = "single_leg_balance_notes")

        st.divider()
        st.subheader("4. 발끝 터치 (하지 유연성)")
        toe_touch_distance = st.number_input(
            "바닥에서의 거리 (cm, 음수=바닥 위, 양수=바닥 아래)",
            min_value = -30.0, max_value = 20.0, value = 0.0, step = 0.5
        )
        toe_touch_notes = st.text_area("메모 (제한사항, 보상 동작 등)", key = "toe_touch_notes")

        st.divider()
        st.subheader("5. FMS 어깨 가동성 (상지 유연성)")
        col1, col2 = st.columns(2)
        with col1:
            shoulder_mobility_right = st.number_input("오른쪽 어깨 측정 (주먹 거리)", min_value = 0.0, max_value = 5.0,
                                                      value = 1.5, step = 0.5)
        with col2:
            shoulder_mobility_left = st.number_input("왼쪽 어깨 측정 (주먹 거리)", min_value = 0.0, max_value = 5.0, value = 1.5,
                                                     step = 0.5)

        shoulder_mobility_score = st.selectbox(
            "가동성 점수 (가장 열악한 측면 기준)",
            [
                (0, "클리어링 테스트에서 통증 발생"),
                (1, "주먹 2개 이상 거리"),
                (2, "주먹 1.5개 거리"),
                (3, "주먹 1개 이하 거리")
            ],
            format_func = lambda x: x[1]
        )[0]
        shoulder_mobility_notes = st.text_area("메모 (비대칭, 제한사항 등)", key = "shoulder_mobility_notes")

        st.divider()
        st.subheader("6. 파머스 캐리 (악력 및 근지구력)")
        farmers_carry_weight = st.number_input("사용 무게 (kg)", min_value = 0.0, max_value = 100.0, value = 0.0,
                                               step = 2.5)
        col1, col2 = st.columns(2)
        with col1:
            farmers_carry_distance = st.number_input("이동 거리 (m)", min_value = 0.0, max_value = 100.0, value = 0.0,
                                                     step = 1.0)
        with col2:
            farmers_carry_time = st.number_input("시간 (초)", min_value = 0, max_value = 120, value = 0, step = 1)
        farmers_carry_score = st.selectbox(
            "수행 평가",
            [
                (1, "저조 - 심각한 자세 문제와 함께 10m 미만 이동"),
                (2, "보통 - 중간 정도의 자세 문제와 함께 10-20m 이동"),
                (3, "양호 - 경미한 자세 문제와 함께 20-30m 이동"),
                (4, "우수 - 완벽한 자세로 30m 이상 이동")
            ],
            format_func = lambda x: x[1]
        )[0]
        farmers_carry_notes = st.text_area("메모 (자세 문제, 그립 피로 등)", key = "farmers_carry_notes")

        st.divider()
        st.subheader("7. 하버드 3분 스텝 테스트 (심폐지구력)")
        step_test_hr1 = st.number_input("회복기 심박수 1 (1:00-1:30 분, bpm)", min_value = 40, max_value = 220, value = 90,
                                        step = 1)
        step_test_hr2 = st.number_input("회복기 심박수 2 (2:00-2:30 분, bpm)", min_value = 40, max_value = 220, value = 80,
                                        step = 1)
        step_test_hr3 = st.number_input("회복기 심박수 3 (3:00-3:30 분, bpm)", min_value = 40, max_value = 220, value = 70,
                                        step = 1)
        step_test_notes = st.text_area("메모 (피로 징후, 제한사항 등)", key = "step_test_notes")

        st.divider()
        submit = st.form_submit_button("계산 및 평가 저장")

        if submit:
            # Calculate scores based on inputted data
            # Prepare push-up score (gender and age dependent)
            push_up_score = calculate_pushup_score(client['gender'], client['age'], push_up_reps)

            # Calculate toe touch score
            toe_touch_score = calculate_toe_touch_score(toe_touch_distance)

            # Calculate single leg balance score
            single_leg_balance_score = calculate_single_leg_balance_score(
                single_leg_balance_right_open,
                single_leg_balance_left_open,
                single_leg_balance_right_closed,
                single_leg_balance_left_closed
            )

            # Calculate Harvard Step Test score and PFI
            step_test_score, pfi = calculate_step_test_score(step_test_hr1, step_test_hr2, step_test_hr3)

            # Collect assessment data
            assessment_data = {
                'client_id': client['id'],
                'trainer_id': st.session_state.trainer_id,
                'date': datetime.now().strftime("%Y-%m-%d"),

                'overhead_squat_score': overhead_squat_score,
                'overhead_squat_notes': overhead_squat_notes,

                'push_up_score': push_up_score,
                'push_up_reps': push_up_reps,
                'push_up_notes': push_up_notes,

                'single_leg_balance_right_open': single_leg_balance_right_open,
                'single_leg_balance_left_open': single_leg_balance_left_open,
                'single_leg_balance_right_closed': single_leg_balance_right_closed,
                'single_leg_balance_left_closed': single_leg_balance_left_closed,
                'single_leg_balance_notes': single_leg_balance_notes,

                'toe_touch_score': toe_touch_score,
                'toe_touch_distance': toe_touch_distance,
                'toe_touch_notes': toe_touch_notes,

                'shoulder_mobility_right': shoulder_mobility_right,
                'shoulder_mobility_left': shoulder_mobility_left,
                'shoulder_mobility_score': shoulder_mobility_score,
                'shoulder_mobility_notes': shoulder_mobility_notes,

                'farmers_carry_weight': farmers_carry_weight,
                'farmers_carry_distance': farmers_carry_distance,
                'farmers_carry_time': farmers_carry_time,
                'farmers_carry_score': farmers_carry_score,
                'farmers_carry_notes': farmers_carry_notes,

                'step_test_hr1': step_test_hr1,
                'step_test_hr2': step_test_hr2,
                'step_test_hr3': step_test_hr3,
                'step_test_pfi': pfi,
                'step_test_score': step_test_score,
                'step_test_notes': step_test_notes
            }

            # Calculate category scores
            category_scores = calculate_category_scores(assessment_data, client)

            # Update assessment data with overall scores
            assessment_data.update({
                'overall_score': category_scores['overall_score'],
                'strength_score': category_scores['strength_score'],
                'mobility_score': category_scores['mobility_score'],
                'balance_score': category_scores['balance_score'],
                'cardio_score': category_scores['cardio_score']
            })

            # Save assessment to database
            assessment_id = save_assessment(assessment_data)

            if assessment_id:
                st.session_state.selected_assessment = assessment_id
                st.session_state.current_page = "assessment_detail"
                st.success("평가가 저장되었습니다!")
                st.rerun()
            else:
                st.error("평가 저장 중 오류가 발생했습니다.")


def new_assessment_page_simplified():
    """Page to conduct a new fitness assessment with simplified input options"""
    import streamlit as st

    if not st.session_state.selected_client:
        st.header("새 체력 평가")
        st.subheader("회원 선택")
        clients = get_clients(st.session_state.trainer_id)

        if not clients:
            st.warning("등록된 회원이 없습니다. 먼저 회원을 추가해주세요.")
            if st.button("회원 추가"):
                st.session_state.current_page = "clients"
                st.rerun()
            return

        client_options = {client[1]: client[0] for client in clients}
        selected_client_name = st.selectbox("회원 선택", list(client_options.keys()))

        if st.button("계속"):
            st.session_state.selected_client = client_options[selected_client_name]
            st.rerun()
        return

    client = get_client_details(st.session_state.selected_client)
    if not client:
        st.error("회원을 찾을 수 없습니다.")
        return

    st.header(f"{client['name']} 회원 체력 평가")
    st.write(
        f"**나이:** {client['age']} | **성별:** {client['gender']} | **키:** {client['height']} cm | **체중:** {client['weight']} kg"
    )

    with st.form("assessment_form"):
        # 1. 오버헤드 스쿼트 (하지 근기능)
        st.subheader("1. 오버헤드 스쿼트 (하지 근기능)")
        overhead_squat_score = st.radio(
            "수행 품질",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "동작 중 통증 발생",
                1: "깊은 스쿼트 수행 불가능",
                2: "보상 동작 관찰됨 (발 뒤꿈치 들림, 무릎 내반 등)",
                3: "완벽한 동작 (상체 수직 유지, 대퇴가 수평 이하, 무릎 정렬)"
            }[x],
            horizontal=True
        )
        oh_squat_obs1 = st.checkbox("발 뒤꿈치 들림")
        oh_squat_obs2 = st.checkbox("무릎 내반(Valgus)")
        oh_squat_obs3 = st.checkbox("과도한 상체 전방 기울임")
        oh_squat_obs4 = st.checkbox("팔 전방 하강")
        oh_squat_notes = st.text_input("기타 메모 (선택사항)", key="overhead_squat_notes")

        # 2. 푸시업 테스트 (상지 근기능)
        st.subheader("2. 푸시업 테스트 (상지 근기능)")
        push_up_score = st.radio(
            "수행 횟수에 따른 점수",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "5개 미만",
                1: "5~10개",
                2: "11~20개",
                3: "21개 이상"
            }[x],
            horizontal=True
        )
        pushup_notes = st.text_input("관찰 및 메모 (선택사항)", key="pushup_notes")

        # 3. 싱글 레그 밸런스 (좌/우) (평형성)
        st.subheader("3. 싱글 레그 밸런스 (좌/우) (평형성)")
        single_leg_balance_right_open = st.number_input(
            "오른발-눈 뜸(초)", min_value=0, max_value=120, value=0, step=1)
        single_leg_balance_left_open = st.number_input(
            "왼발-눈 뜸(초)", min_value=0, max_value=120, value=0, step=1)
        single_leg_notes = st.text_input("관찰 및 메모 (선택사항)", key="single_leg_notes")

        # 4. 토 터치 (하지 유연성)
        st.subheader("4. 토 터치 (하지 유연성)")
        toe_touch_score = st.radio(
            "유연성 평가",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "손끝이 발에 닿지 않음",
                1: "손끝이 발에 닿음",
                2: "손바닥이 발등을 덮음",
                3: "손바닥이 발에 완전히 닿음"
            }[x],
            horizontal=True
        )
        toe_touch_notes = st.text_input("관찰 및 메모 (선택사항)", key="toe_touch_notes")

        # 5. FMS 숄더 모빌리티 (상지 유연성)
        st.subheader("5. FMS 숄더 모빌리티 (상지 유연성)")
        shoulder_mobility_score = st.radio(
            "양손 간 거리",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "동작 중 통증",
                1: "손 간 거리가 신장 1.5배 이상",
                2: "손 간 거리가 신장 1~1.5배",
                3: "손 간 거리가 신장 1배 미만"
            }[x],
            horizontal=True
        )
        shoulder_mobility_notes = st.text_input("관찰 및 메모 (선택사항)", key="shoulder_mobility_notes")

        # 6. 파머스 캐리 (악력 및 근지구력)
        st.subheader("6. 파머스 캐리 (악력 및 근지구력)")
        farmers_carry_score = st.radio(
            "평가 점수",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "5m 미만 이동",
                1: "5-10m 이동",
                2: "11-20m 이동",
                3: "20m 이상 지속"
            }[x],
            horizontal=True
        )
        farmers_carry_notes = st.text_input("관찰 및 메모 (선택사항)", key="farmers_carry_notes")

        # 7. 하버드 스텝 테스트 (심폐지구력)
        st.subheader("7. 하버드 스텝 테스트 (심폐지구력)")
        step_test_score = st.radio(
            "점수 등급",
            [0, 1, 2, 3],
            format_func=lambda x: {
                0: "심각히 낮음",
                1: "평균 이하",
                2: "평균",
                3: "우수"
            }[x],
            horizontal=True
        )
        step_test_notes = st.text_input("관찰 및 메모 (선택사항)", key="step_test_notes")

        # 제출 버튼
        submit = st.form_submit_button("계산 및 평가 저장")

        if submit:
            st.success("평가가 저장되었습니다!")
            # 여기에 저장 및 점수 계산 코드를 추가하세요

def assessment_detail_page():
    """Page to view assessment results and generate PDF report"""
    if not st.session_state.selected_assessment:
        st.error("선택된 평가가 없습니다.")
        return

    # Get assessment details
    assessment = get_assessment_details(st.session_state.selected_assessment)

    if not assessment:
        st.error("평가를 찾을 수 없습니다.")
        return

    # Get client details
    client = get_client_details(assessment['client_id'])

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

    # Get improvement suggestions
    suggestions = get_improvement_suggestions(assessment, client)

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
        # Create PDF report
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