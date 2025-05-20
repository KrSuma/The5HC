# simplified_add_client.py - A simplified page for adding clients

import streamlit as st
import sqlite3
from datetime import datetime


def add_client_direct(trainer_id, name, age, gender, height, weight, email = "", phone = ""):
    """Add a client directly to the database with minimal dependencies"""
    try:
        # Connect directly to the database
        conn = sqlite3.connect('fitness_assessment.db')
        c = conn.cursor()

        registration_date = datetime.now().strftime("%Y-%m-%d")

        # Check if the client already exists
        c.execute("SELECT COUNT(*) FROM clients WHERE trainer_id = ? AND name = ?",
                  (trainer_id, name))
        count = c.fetchone()[0]

        if count > 0:
            conn.close()
            return False, "해당 이름의 회원이 이미 존재합니다."

        # Insert the new client
        c.execute(
            "INSERT INTO clients (trainer_id, name, age, gender, height, weight, email, phone, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (trainer_id, name, age, gender, height, weight, email, phone, registration_date)
        )

        client_id = c.lastrowid
        conn.commit()
        conn.close()

        return True, client_id
    except Exception as e:
        print(f"Error adding client: {e}")
        return False, str(e)


def simplified_add_client_page():
    """A simplified page for adding clients that works independently of other code"""
    st.header("회원 추가")

    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

    if not st.session_state.form_submitted:
        with st.form("simplified_add_client_form"):
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
                # Validate required fields
                if not client_name or not client_age or not client_gender or not client_height or not client_weight:
                    st.error("필수 항목(이름, 나이, 성별, 키, 체중)을 모두 입력해주세요.")
                else:
                    # Mark form as submitted to prevent resubmission
                    st.session_state.form_submitted = True
                    st.session_state.submission_data = {
                        'name': client_name,
                        'age': client_age,
                        'gender': client_gender,
                        'height': client_height,
                        'weight': client_weight,
                        'email': client_email,
                        'phone': client_phone
                    }
                    st.rerun()  # Force rerun with the form_submitted flag set

    else:  # Form has been submitted
        # Retrieve submission data
        data = st.session_state.submission_data

        # Process the submission
        success, result = add_client_direct(
            st.session_state.trainer_id,
            data['name'],
            data['age'],
            data['gender'],
            data['height'],
            data['weight'],
            data['email'],
            data['phone']
        )

        if success:
            st.success(f"{data['name']} 회원이 성공적으로 추가되었습니다!")
            if st.button("회원 목록으로 돌아가기"):
                # Reset the submission state
                st.session_state.form_submitted = False
                if 'submission_data' in st.session_state:
                    del st.session_state.submission_data

                # Navigate to clients page
                st.session_state.current_page = "clients"
                st.rerun()
        else:
            st.error(f"회원 추가 실패: {result}")
            if st.button("다시 시도"):
                # Reset the submission state
                st.session_state.form_submitted = False
                if 'submission_data' in st.session_state:
                    del st.session_state.submission_data
                st.rerun()


# If this file is run directly, show a message
if __name__ == "__main__":
    st.write("이 파일은 직접 실행하면 안됩니다. main.py를 통해 실행하세요.")