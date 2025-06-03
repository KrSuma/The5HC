"""
Login and registration page
"""
import streamlit as st

from ...services.auth_service import AuthService


def render_login_page():
    """Render login and registration page"""
    auth_service = AuthService()
    
    st.title("더파이브 헬스케어 Fitness Assessment System")
    st.subheader("트레이너 로그인")
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        st.header("로그인")
        username = st.text_input("아이디", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")

        if st.button("로그인", key="login_button"):
            if username and password:
                success, message, session_data = auth_service.login(username, password)
                if success:
                    # Store session data
                    st.session_state.session_id = session_data['session_id']
                    st.session_state.trainer_id = session_data['trainer_id']
                    st.session_state.username = session_data['username']
                    st.session_state.authenticated = True
                    st.session_state.current_page = "dashboard"
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")

    with tab2:
        st.header("회원가입")
        new_username = st.text_input("아이디", key="reg_username")
        new_password = st.text_input("비밀번호", type="password", key="reg_password")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="confirm_password")
        name = st.text_input("이름", key="reg_name")
        email = st.text_input("이메일", key="reg_email")

        if st.button("회원가입", key="register_button"):
            if not all([new_username, new_password, confirm_password, name, email]):
                st.warning("모든 필드를 입력해주세요.")
            elif new_password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                success, message = auth_service.register(new_username, new_password, name, email)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def check_authentication():
    """Check if user is authenticated"""
    if 'session_id' not in st.session_state:
        return False
    
    auth_service = AuthService()
    session = auth_service.validate_session(st.session_state.session_id)
    
    if session:
        # Update session data
        st.session_state.trainer_id = session['trainer_id']
        st.session_state.username = session['username']
        st.session_state.authenticated = True
        return True
    else:
        # Clear invalid session
        for key in ['session_id', 'trainer_id', 'username', 'authenticated']:
            if key in st.session_state:
                del st.session_state[key]
        return False


def logout():
    """Logout user"""
    if 'session_id' in st.session_state:
        auth_service = AuthService()
        auth_service.logout(st.session_state.session_id)
    
    # Clear session state
    for key in ['session_id', 'trainer_id', 'username', 'authenticated', 'current_page']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()