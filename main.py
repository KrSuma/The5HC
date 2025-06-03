# main_improved.py - Main Streamlit application with security improvements

import streamlit as st
import matplotlib

matplotlib.use('Agg')  # Required for non-interactive environments

# Import improved modules with security features
from src.services.service_layer import (
    AppInitService, AuthService, ClientService,
    AssessmentService, DashboardService, AnalyticsService
)

# Import session management
from src.services.auth import (
    session_manager, ActivityTracker
)

# Import configuration
from config.settings import config

# Import custom logging
from src.utils.app_logging import app_logger, error_logger

# Import UI pages
from src.ui.pages.ui_pages import (
    login_register_page, dashboard_page, dashboard_page_with_search,
    clients_page, client_detail_page, assessment_detail_page, session_management_page
)

# Import our enhanced assessment page
from src.ui.pages.assessment_page import new_assessment_page

# Import simplified add client page for direct client addition
from src.services.add_client import simplified_add_client_page


def main():
    """Main application function with security improvements"""

    # Initialize application
    try:
        AppInitService.initialize()
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        return

    st.set_page_config(
        page_title = config.app['app_name'],
        page_icon = "🏋️",
        layout = "wide"
    )

    # Add custom CSS with theme colors from config
    theme = config.streamlit['theme']
    st.markdown(f"""
    <style>
    .download-button {{
        display: inline-block;
        padding: 10px 20px;
        background-color: {theme['primary_color']};
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }}
    .stProgress > div > div > div {{
        background-color: {theme['primary_color']};
    }}
    .error-message {{
        color: #d32f2f;
        padding: 10px;
        background-color: #ffeeee;
        border-radius: 5px;
        margin: 10px 0;
    }}
    .success-message {{
        color: #388e3c;
        padding: 10px;
        background-color: #eeffee;
        border-radius: 5px;
        margin: 10px 0;
    }}
    .info-message {{
        color: #1976d2;
        padding: 10px;
        background-color: #eef6ff;
        border-radius: 5px;
        margin: 10px 0;
    }}
    </style>
    """, unsafe_allow_html = True)

    # Removed auto-logout check - sessions no longer expire

    # Session state initialization with error handling
    for key, default in [
        ('logged_in', False),
        ('trainer_id', None),
        ('trainer_name', None),
        ('current_page', "login"),
        ('selected_client', None),
        ('selected_assessment', None),
        ('error_message', None),
        ('success_message', None),
        ('info_message', None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Page header
    st.title(config.app['app_name'])

    # Removed session timeout warning - sessions no longer expire

    # Display any error messages
    if st.session_state.error_message:
        st.markdown(f'<div class="error-message">{st.session_state.error_message}</div>', unsafe_allow_html = True)
        st.session_state.error_message = None

    # Display any success messages
    if st.session_state.success_message:
        st.markdown(f'<div class="success-message">{st.session_state.success_message}</div>', unsafe_allow_html = True)
        st.session_state.success_message = None

    # Display any info messages
    if st.session_state.info_message:
        st.markdown(f'<div class="info-message">{st.session_state.info_message}</div>', unsafe_allow_html = True)
        st.session_state.info_message = None

    # Login / Registration Page
    if not st.session_state.logged_in:
        # Check if session is still valid
        if not session_manager.validate_session():
            login_register_page()
        else:
            # Restore session
            st.session_state.logged_in = True
            st.rerun()
    else:
        # Validate session on each page load
        if not session_manager.validate_session():
            st.error("로그인이 필요합니다.")
            st.session_state.current_page = "login"
            st.rerun()
            return

        # Sidebar with navigation
        with st.sidebar:
            st.write(f"로그인: **{st.session_state.trainer_name}**")

            st.divider()

            if st.button("대시보드", use_container_width = True):
                st.session_state.current_page = "dashboard"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None
                ActivityTracker.log_activity("navigate", {"page": "dashboard"})

            if st.button("회원 관리", use_container_width = True):
                st.session_state.current_page = "clients"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None
                ActivityTracker.log_activity("navigate", {"page": "clients"})

            if st.button("새 회원 추가", use_container_width = True):
                st.session_state.current_page = "add_client"
                st.session_state.selected_client = None
                st.session_state.selected_assessment = None
                ActivityTracker.log_activity("navigate", {"page": "add_client"})

            if st.button("새 평가", use_container_width = True):
                st.session_state.current_page = "new_assessment"
                st.session_state.selected_assessment = None
                ActivityTracker.log_activity("navigate", {"page": "new_assessment"})

            st.divider()

            if st.button("로그아웃", use_container_width = True):
                AuthService.logout()
                st.session_state.success_message = "로그아웃 되었습니다."
                st.rerun()

        # Main content area with error handling
        try:
            if st.session_state.current_page == "dashboard":
                dashboard_page_with_search()
            elif st.session_state.current_page == "clients":
                clients_page()
            elif st.session_state.current_page == "add_client":
                simplified_add_client_page()
            elif st.session_state.current_page == "client_detail":
                client_detail_page()
            elif st.session_state.current_page == "new_assessment":
                # Always use our improved assessment page
                new_assessment_page()
            elif st.session_state.current_page == "assessment_detail":
                assessment_detail_page()
            elif st.session_state.current_page == "session_management":
                session_management_page()
        except Exception as e:
            error_logger.log_error(e, context = {
                'page': st.session_state.current_page,
                'user_id': st.session_state.trainer_id
            })
            st.error(f"페이지 로딩 중 오류가 발생했습니다: {str(e)}")
            st.session_state.error_message = "페이지 로딩 중 오류가 발생했습니다. 다시 시도해주세요."
            st.session_state.current_page = "dashboard"
            st.rerun()


if __name__ == "__main__":
    main()
