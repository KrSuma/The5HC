# app.py - Main Streamlit application

import streamlit as st
import matplotlib

matplotlib.use('Agg')  # Required for non-interactive environments

from db_utils import init_db
from ui_pages import (login_register_page, dashboard_page, dashboard_page_with_search,
                      clients_page, client_detail_page, new_assessment_page,
                      new_assessment_page_simplified, assessment_detail_page)


def main():
    # Initialize database
    init_db()

    st.set_page_config(
        page_title = "더파이브 헬스케어 Fitness Assessment",
        page_icon = "🏋️",
        layout = "wide"
    )

    # Add custom CSS
    st.markdown("""
    <style>
    .download-button {
        display: inline-block;
        padding: 10px 20px;
        background-color: #ff4b4b;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
    .stProgress > div > div > div {
        background-color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html = True)

    # Session state initialization
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'trainer_id' not in st.session_state:
        st.session_state.trainer_id = None
    if 'trainer_name' not in st.session_state:
        st.session_state.trainer_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
    if 'selected_assessment' not in st.session_state:
        st.session_state.selected_assessment = None
    if 'use_simplified_assessment' not in st.session_state:
        st.session_state.use_simplified_assessment = False
    if 'use_search_dashboard' not in st.session_state:
        st.session_state.use_search_dashboard = False

    # Page header
    st.title("더파이브 헬스케어 Fitness Assessment System")

    # Login / Registration Page
    if not st.session_state.logged_in:
        login_register_page()
    else:
        # Sidebar with navigation
        with st.sidebar:
            st.write(f"로그인: **{st.session_state.trainer_name}**")
            st.divider()

            if st.button("대시보드", use_container_width = True):
                st.session_state.current_page = "dashboard"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None

            if st.button("회원 관리", use_container_width = True):
                st.session_state.current_page = "clients"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None

            if st.button("새 평가", use_container_width = True):
                st.session_state.current_page = "new_assessment"
                st.session_state.selected_assessment = None

            st.divider()

            # Options
            st.subheader("옵션")
            st.checkbox("검색 기능이 있는 대시보드 사용",
                        key = "use_search_dashboard",
                        value = st.session_state.use_search_dashboard)

            st.checkbox("체크박스가 있는 간소화된 평가 폼 사용",
                        key = "use_simplified_assessment",
                        value = st.session_state.use_simplified_assessment)

            st.divider()
            if st.button("로그아웃", use_container_width = True):
                st.session_state.logged_in = False
                st.session_state.trainer_id = None
                st.session_state.trainer_name = None
                st.session_state.current_page = "login"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None
                st.rerun()

        # Main content area
        if st.session_state.current_page == "dashboard":
            if st.session_state.use_search_dashboard:
                dashboard_page_with_search()
            else:
                dashboard_page()
        elif st.session_state.current_page == "clients":
            clients_page()
        elif st.session_state.current_page == "client_detail":
            client_detail_page()
        elif st.session_state.current_page == "new_assessment":
            if st.session_state.use_simplified_assessment:
                new_assessment_page_simplified()
            else:
                new_assessment_page()
        elif st.session_state.current_page == "assessment_detail":
            assessment_detail_page()


if __name__ == "__main__":
    main()
